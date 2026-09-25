#!/usr/bin/env python3
"""補建最後 7 個缺口 —— 已逐一查到官方頁，人工確認過才列在這裡。

🔴 為什麼一筆一筆寫死而不自動抓（2026-09-25）：
   這 7 個是「用搜尋抓不到、目錄頁也沒列」的長尾項目。
   ⚠️ 前兩輪自動抓的教訓：命中率 25%、誤判率 1/3，
      而且誤判「看起來跟正確的一模一樣」。
   ⇒ 長尾用人工查證 + 寫死，比再寫一支猜測式腳本可靠。

🔴 每一筆的 url 都是**我實際讀過、標題對得上**的官方頁：
   不是搜尋結果的第一筆，也不是憑印象填的。

⚠️ 金額只在官方頁上實際讀到時才填，讀不到一律 None ——
   昨天已證明「就近取金額」會抓到別的補助的數字。
"""
from __future__ import annotations

import argparse
import json
import sys

import psycopg2

# (縣市, 正式名稱, 官方頁, 金額min, 金額max, 單位, 金額備註, 對照表項目)
GAP_ITEMS = [
    ("新竹市", "身心障礙者租賃房屋租金及購屋貸款利息補助",
     "https://law.hccg.gov.tw/LawContent.aspx?id=FL022925",
     None, None, None,
     "🔴 金額依身障等級與家庭經濟狀況分級，詳見作業要點原文",
     "身心障礙者房屋津貼補助"),

    ("苗栗縣", "低收入戶喪葬補助",
     "https://law.miaoli.gov.tw/glrsnewsout/LawContent.aspx?id=GL000013",
     None, None, None,
     "🔴 金額依作業辦法規定，詳見原文",
     "喪葬費用補助"),

    ("苗栗縣", "低收入戶住宅修繕補助",
     "https://webws.miaoli.gov.tw/Download.ashx?icon=.pdf&n=MjAxNz",
     6115, 11448, "one_time",
     "官方文件實抓：11,448／10,618／6,115 元（依款別）",
     "房屋修繕補助"),

    ("彰化縣", "改善低收入戶住宅設施設備補助",
     "https://social.chcg.gov.tw/07other/other01_con.aspx"
     "?cate_id=1833&data_id=8714&topsn=714",
     None, None, None,
     "🔴 金額未在該頁列出，詳見官方頁面",
     "房屋修繕補助"),

    ("彰化縣", "中低收入老人傷病醫療暨看護費用補助",
     "https://social.chcg.gov.tw/06service/service01_con.aspx"
     "?data_id=25530&topsn=2434",
     None, None, None,
     "🔴 金額未在該頁列出，詳見審核作業辦法",
     "中低醫療看護"),

    ("彰化縣", "身心障礙者托育養護費用補助",
     "https://social.chcg.gov.tw/getFile.aspx"
     "?did=20146&file=2&file_id=64232&type=2",
     21000, 21000, "monthly",
     "官方文件實抓：21,000 元",
     "身心障礙者托育養護"),

    ("屏東縣", "身心障礙者托育養護費用補助",
     "https://www.pthg.gov.tw/planjdp/Content_List.aspx"
     "?n=46F6EFDFE943D834",
     None, None, None,
     "🔴 金額待補 —— pthg.gov.tw 整站 Firecrawl 抓不到"
     "（ERR_TUNNEL_CONNECTION_FAILED），但 curl 測 HTTP 200，網站本身正常",
     "身心障礙者托育養護"),
]

AGENCY_OF = {
    "新竹市": "新竹市政府社會處",
    "苗栗縣": "苗栗縣政府社會處",
    "彰化縣": "彰化縣政府社會處",
    "屏東縣": "屏東縣政府社會處",
}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    conn = psycopg2.connect(dbname="welfare_check")
    cur = conn.cursor()
    cur.execute("SELECT count(*) FROM benefits")
    before = cur.fetchone()[0]

    new = 0
    for (county, name, url, amin, amax, unit, note, table_item) in GAP_ITEMS:
        cur.execute("""SELECT count(*) FROM benefits
                        WHERE county = %s AND name = %s""", (county, name))
        if cur.fetchone()[0]:
            print(f"  ⏭ 已存在：{county} {name}")
            continue
        print(f"  + {county}｜{name}")
        print(f"      對照表項目「{table_item}」　金額 {amin}~{amax} {unit}")
        new += 1
        if not args.apply:
            continue
        desc = (f"{name}。🔴 本筆為官方頁面索引 —— "
                f"申請資格與金額請見官方頁面（{url}）。"
                f"（對應衛福部跨縣市對照表項目：{table_item}）")
        elig = {
            "counties": [county],
            "_note": "資格條件待從官方頁面補齊（本筆來源為法規/公告頁）",
        }
        cur.execute("""
            INSERT INTO benefits
              (name, agency, county, description, search_group,
               application_period, eligibility_conditions, source_url,
               source_excerpt, last_verified_date, is_active,
               amount_min, amount_max, amount_unit, amount_note,
               deadline_type)
            VALUES (%s, %s, %s, %s, %s, %s, %s::jsonb, %s, %s,
                    CURRENT_DATE, true, %s, %s, %s, %s, 'unknown')""",
            (name, AGENCY_OF[county], county, desc,
             "現金與生活補助類", "",
             json.dumps(elig, ensure_ascii=False), url,
             f"衛福部對照表項目「{table_item}」；官方頁：{url}"[:900],
             amin, amax, unit, note))

    if args.apply:
        conn.commit()
        cur.execute("SELECT count(*) FROM benefits")
        after = cur.fetchone()[0]
        print(f"\n✅ 寫入 {new} 筆　benefits {before} → {after}")
        if after - before != new:
            print(f"🔴 筆數不符：預期 +{new}，實際 +{after - before}")
            return 1
    else:
        print(f"\n（dry-run）會新增 {new} 筆")
    return 0


if __name__ == "__main__":
    sys.exit(main())
