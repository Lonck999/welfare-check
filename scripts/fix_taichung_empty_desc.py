#!/usr/bin/env python3
"""補齊臺中市 3 筆空描述（2026-09-25）。

🔴 為什麼要寫成腳本而不是只跑一次 SQL：
   那三筆是直接 UPDATE 資料庫的，**沒有檔案變動 ⇒ git 什麼都記不到**。
   ⚠️ 等於這批修正無法重現、無法審查、重建資料庫就消失。

背景：端到端驗證（verify_delivery_p1p4）抓到 3 筆 description < 10 字。
   來源是 data.gov.tw 的臺中市資料集，「說明」欄只寫「詳閱網址」。

🔴 查證時抓到一個**來源資料本身的錯誤**：
   「原住民低收入戶及中低收入戶補助項目」的說明欄寫的是「幼兒托教補助」
   —— 名稱與內容對不上。已在描述裡明講，不掩蓋。

🔴 金額的處理原則（這支最重要的一條）：
   幼兒托教補助搜到的是 **2015 年的市政新聞稿**
   （每學期公立 8,500／私立 10,000 元），距今 11 年。
   ⇒ **刻意不填 amount_*，只標「待查證」並附主管機關電話。**
   ⚠️ 寧可標待查證，也不把 11 年前的數字寫成現行金額 ——
      那會讓使用者拿去申請時才發現對不上。
"""
from __future__ import annotations

import argparse
import sys

import psycopg2

IPD = "https://www.ipd.taichung.gov.tw/"
LAW = "https://law.taichung.gov.tw/LawContent.aspx?id=GL002227"

RENT_EXCERPT = (
    "五、符合補助資格者，補助每戶每月新臺幣五千元為上限，若未逾上限者，"
    "覈實補助，補助期限為每年十二個月，原則每月核撥一次"
)

RENT_DESC = (
    "臺中市經濟弱勢原住民住宅租金補助。補助每戶每月新臺幣 5,000 元為上限，"
    "未逾上限者覈實補助，補助期限每年 12 個月，原則每月核撥一次。"
    "申請資格：①設籍臺中市且成年之原住民，申請人須與房屋承租人為同一人 "
    "②家庭總收入按全家人口平均分配，每人每月未超過本市當年度最低生活費標準 2 倍 "
    "③房屋出租人不得為申請人三等親內親屬。"
    "應備文件：申請表（附表一）、租賃契約、領款收據（附表二）及金融帳戶存摺封面影本。"
    "🔴 補助期間不得再向其他機關申請相關租金補助，重複申請即中止並追回。"
    f"（依《臺中市政府原住民族事務委員會經濟弱勢原住民住宅租金補助要點》，{LAW}）"
)

STALE_NOTE = (
    "🔴 金額待查證 —— 搜尋只找到 2015 年的市政新聞稿"
    "（每學期公立 8,500／私立 10,000 元），距今 11 年，不可當成現行標準。"
    "請洽臺中市原住民族事務委員會 04-22289111。"
)

TOEDU_DESC = (
    "臺中市原住民幼兒托教補助。補助對象需具原住民身分、年滿 3 足歲至 4 足歲之"
    "原住民幼兒（即中小班），無設籍限制，就讀本市立案公私立幼兒園。"
    "⚠️ 與教育局「托育一條龍」政策為整合性辦理（非擇一或雙向請領）："
    "需先依身分別向原民會申請，符合托育一條龍者"
    "（幼兒與監護人一方須同時設籍本市）如有差額由教育局另行撥付。"
    "🔴 年滿 2 足歲未滿 3 歲（幼幼班）及 5 足歲未滿 6 歲（大班）者一律改申請"
    "教育局「托育一條龍」及教育部「免學費補助」。" + STALE_NOTE
)

LOWINC_DESC = (
    "臺中市原住民低收入戶及中低收入戶補助項目。🔴 本筆為官方資料集索引 —— "
    "來源（data.gov.tw/dataset/138588）僅提供項目名稱，未含補助金額與資格門檻。"
    "實際補助項目、金額與申請條件請洽臺中市政府原住民族事務委員會"
    f"（04-22289111，{IPD}）。"
    "⚠️ 本筆名稱與原始資料的「說明」欄位不一致（說明欄寫「幼兒托教補助」），"
    "來源資料本身即有此問題，待向主管機關確認實際涵蓋範圍。"
)

# (name, description, source_url, amount_min, amount_max, unit, note, excerpt)
FIXES = [
    ("經濟弱勢原住民住宅租金補助", RENT_DESC, LAW, 5000, 5000, "monthly",
     "官方法規原文實抓：補助每戶每月新臺幣五千元為上限，補助期限為每年十二個月",
     RENT_EXCERPT),
    # 🔴 下面兩筆金額一律 None —— 見檔頭說明
    ("原住民幼兒托教補助", TOEDU_DESC, IPD, None, None, None, None, None),
    ("原住民低收入戶及中低收入戶補助項目", LOWINC_DESC, IPD,
     None, None, None, None, None),
]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    conn = psycopg2.connect(dbname="welfare_check")
    cur = conn.cursor()

    for (name, desc, url, amin, amax, unit, anote, excerpt) in FIXES:
        cur.execute("""SELECT id, length(description) FROM benefits
                        WHERE county = '臺中市' AND name = %s""", (name,))
        row = cur.fetchone()
        if not row:
            print(f"  🔴 找不到：{name}")
            return 1
        bid, cur_len = row
        print(f"  · {name}（id={bid}，現有描述 {cur_len} 字 → {len(desc)} 字）")
        if amin:
            print(f"      金額 {amin:,}/{unit}")
        else:
            print("      🔴 金額不填（來源過期或無資料）")
        if not args.apply:
            continue
        if excerpt:
            cur.execute("""UPDATE benefits
                              SET description=%s, source_url=%s,
                                  source_excerpt=%s,
                                  amount_min=%s, amount_max=%s,
                                  amount_unit=%s, amount_note=%s,
                                  last_verified_date=CURRENT_DATE
                            WHERE id=%s""",
                        (desc, url, excerpt, amin, amax, unit, anote, bid))
        else:
            cur.execute("""UPDATE benefits
                              SET description=%s, source_url=%s,
                                  last_verified_date=CURRENT_DATE
                            WHERE id=%s""", (desc, url, bid))

    if args.apply:
        conn.commit()
        cur.execute("""SELECT count(*) FROM benefits
                        WHERE description IS NULL OR length(description)<10""")
        left = cur.fetchone()[0]
        print(f"\n✅ 已套用　仍過短：{left} 筆")
        return 1 if left else 0
    print("\n（dry-run）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
