#!/usr/bin/env python3
"""把 harvest_directory_pages 抓到的候選項目寫入 benefits。

🔴 這批的品質定位（不可誇大）：
   來源是縣市社會局「補助總覽/津貼專區」的**目錄頁**，
   所以我們拿到的是**項目名稱 + 官方頁面連結**，
   **沒有金額、沒有資格門檻**（那些在各自的內頁）。

   ⇒ 寫入時：
     · description 誠實標「本筆為官方項目索引」
     · eligibility_conditions 只填 counties + _note
     · 🔴 **絕不猜金額或年齡** —— 昨天試抓已證明「就近取金額」
       會抓到別的補助的數字（宜蘭 100 元工本費、彰化 220 萬貸款）

⚠️ 輸入必須是 **人工看過** 的清單（directory_items_clean.json），
   不是 harvest 的原始輸出 —— 原始輸出含「社會救助科」「補助資訊」
   這種分類名與目錄標題。
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

import psycopg2

VALID_COUNTIES = {
    "臺北市", "新北市", "桃園市", "臺中市", "臺南市", "高雄市",
    "基隆市", "新竹市", "新竹縣", "苗栗縣", "彰化縣", "南投縣",
    "雲林縣", "嘉義市", "嘉義縣", "屏東縣", "宜蘭縣", "花蓮縣",
    "臺東縣", "澎湖縣", "金門縣", "連江縣",
}

AGENCY_OF = {
    "彰化縣": "彰化縣政府社會處", "新竹市": "新竹市政府社會處",
    "雲林縣": "雲林縣政府社會處", "基隆市": "基隆市政府社會處",
    "宜蘭縣": "宜蘭縣政府社會處", "苗栗縣": "苗栗縣政府社會處",
    "屏東縣": "屏東縣政府社會處", "南投縣": "南投縣政府社會及勞動局",
    "新竹縣": "新竹縣政府社會處",
}

# 🔴 彰化的項目名帶編號前綴（1-1、2-3…），那是目錄編號不是補助名稱的一部分
NUM_PREFIX = re.compile(r"^\d+-\d+\s*")


def clean_name(raw: str) -> str:
    name = NUM_PREFIX.sub("", raw).strip()
    # 全形/半形空白統一，並把「申請表」「實施計畫」等後綴保留
    #（那些是官方正式名稱的一部分，不可擅自刪）
    return re.sub(r"\s+", "", name)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", default="/tmp/directory_items_clean.json")
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    data = json.loads(Path(args.input).read_text(encoding="utf-8"))
    conn = psycopg2.connect(dbname="welfare_check")
    cur = conn.cursor()

    cur.execute("SELECT count(*) FROM benefits")
    before = cur.fetchone()[0]

    total_new = total_dup = 0
    for county, items in data.items():
        if county not in VALID_COUNTIES:
            print(f"🔴 「{county}」不是合法縣市名，跳過")
            return 1
        cur.execute("SELECT name FROM benefits WHERE county = %s", (county,))
        existing = {re.sub(r"\s+", "", n) for (n,) in cur.fetchall()}

        new = dup = 0
        for it in items:
            name = clean_name(it["name"])
            if not name:
                continue
            if name in existing:
                dup += 1
                continue
            existing.add(name)          # 防同批重複
            url = it.get("url", "")
            if not url.startswith("http"):
                # 🔴 相對連結要補完網域，否則 source_url 不合法
                print(f"  ⚠️ {county} {name[:24]} 的連結是相對路徑，跳過")
                continue
            # 🔴 名稱本身常已含縣市名（「彰化縣政府生育補助」）——
            #    再加前綴會變成「彰化縣彰化縣政府生育補助」
            prefix = "" if name.startswith(county) else county
            desc = (f"{prefix}{name}。🔴 本筆為官方項目索引 —— "
                    f"金額與詳細資格請見官方頁面（{url}）。")
            elig = {
                "counties": [county],
                "_note": "金額與資格條件待從官方頁面補齊（本筆來源為目錄頁）",
            }
            new += 1
            if args.apply:
                cur.execute("""
                    INSERT INTO benefits
                      (name, agency, county, description, search_group,
                       application_period, eligibility_conditions, source_url,
                       source_excerpt, last_verified_date, is_active,
                       deadline_type)
                    VALUES (%s, %s, %s, %s, %s, %s, %s::jsonb, %s, %s,
                            CURRENT_DATE, true, 'unknown')""",
                    (name, AGENCY_OF[county], county, desc,
                     "現金與生活補助類",
                     "",                 # 🔴 目錄頁沒有期限資訊 → 留空不猜
                     json.dumps(elig, ensure_ascii=False), url,
                     f"來源：{county}社會處補助目錄頁　項目名稱：{it['name']}"))
        total_new += new
        total_dup += dup
        print(f"  {county}　新增 {new}　已存在 {dup}")

    if args.apply:
        conn.commit()
        cur.execute("SELECT count(*) FROM benefits")
        after = cur.fetchone()[0]
        print(f"\n✅ 寫入 {total_new} 筆　benefits {before} → {after}")
        # 🔴 驗終點
        if after - before != total_new:
            print(f"🔴 筆數不符：預期 +{total_new}，實際 +{after - before}")
            return 1
    else:
        print(f"\n（dry-run）會新增 {total_new} 筆，已存在 {total_dup}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
