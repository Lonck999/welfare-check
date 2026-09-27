#!/usr/bin/env python3
"""把「分類標籤型」的一筆補助拆成多筆真實補助（A 方案，Lonck 2026-09-27 選）。

🔴 為什麼需要它：這批空殼的主題名有一部分是**我們自己編的分類標籤**，
   官方頁上永遠找不到同名的東西：

     「工作地點縣市勞工局補助（地方明細）」  ← 機關名，不是補助名
     「老人其他福利（重陽禮金/敬老卡…）」    ← 一個名字包兩種補助
     「環保節能補助（電動機車地方加碼）」    ← 分類名

   高雄那頁實際有 4 個獨立補助：
     求職交通補助金      500      yearly
     異地就業交通補助金  1,000~3,000  monthly
     搬遷補助金        30,000    one_time
     租屋補助金         5,000     monthly
   ⚠️ 四項全部 same_topic=False ⇒ 主項目只能靠「取金額最大」推測
   🔴 壓成一筆「500~30,000」使用者不知道自己能領哪個、要準備什麼
      （求職交通要找工作、搬遷要收據、租屋要租約 —— 資格完全不同）

═══ 寫入規則 ═══
· 拆出的每一項 → 新增一筆 benefits（帶自己的金額、單位、證據）
· 🔴 原本那筆標 is_active=false 並在描述註明「已拆分為 N 筆」
  ⚠️ **保留不刪** —— 否則月更比對時會把它當成新缺口再抓一次
· 🔴 同縣市同名已存在就跳過（可重複執行，不會產生重複）
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import time

import psycopg2

sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent))
from refetch_empty_shells import best_page  # noqa: E402
from split_subsidy_items import latest_only, split_items  # noqa: E402

SP = re.compile(r"\s+")

# 🔴 只處理「拆得出 >= 2 項」的，其餘留給 refetch_empty_shells 走 A/C
MIN_ITEMS = 2


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--topic", required=True, help="主題名（子字串比對）")
    ap.add_argument("--limit", type=int, default=0)
    args = ap.parse_args()

    conn = psycopg2.connect(dbname="welfare_check")
    cur = conn.cursor()
    cur.execute("""SELECT id, county, name, agency, search_group
                     FROM benefits
                    WHERE name LIKE %s
                      AND description ~ '未查得|查無|待補|尚未'
                      AND county IS NOT NULL
                    ORDER BY county""", (f"%{args.topic}%",))
    rows = cur.fetchall()
    if args.limit:
        rows = rows[: args.limit]
    print(f"待處理 {len(rows)} 筆\n")

    split_n = new_n = skip_n = 0
    for bid, county, name, agency, sgroup in rows:
        print(f"  · {county} {name[:34]}")
        hit = best_page(county, name)
        if not hit:
            skip_n += 1
            print("      🔴 找不到官方頁 → 不動")
            continue
        url, txt = hit
        items = latest_only(split_items(txt))
        if len(items) < MIN_ITEMS:
            skip_n += 1
            print(f"      ⏭ 只拆出 {len(items)} 項 → 留給 refetch 處理")
            continue

        split_n += 1
        print(f"      🔸 拆出 {len(items)} 項")
        made = 0
        for it in items:
            new_name = f"{it.name}（{county}）"
            cur.execute("""SELECT id FROM benefits
                            WHERE county=%s AND name=%s""",
                        (county, new_name))
            if cur.fetchone():
                print(f"         ⏭ 已存在：{new_name}")
                continue
            rng = (f"{it.amount_min:,} 元" if it.amount_min == it.amount_max
                   else f"{it.amount_min:,}~{it.amount_max:,} 元")
            u = {"monthly": "每月", "yearly": "每年",
                 "one_time": "一次性"}.get(it.amount_unit or "", "")
            desc = (f"{county}{it.name}。補助金額 {u} {rng}（官方頁面實抓）。"
                    f"金額出處：{'；'.join(it.evidence[:2])}。"
                    f"⚠️ 本筆自「{re.sub(r'[（(].*?[)）]', '', name).strip()}」"
                    f"拆出 —— 原資料把同一頁的多個補助併成一筆，"
                    f"資格與應備文件請以官方頁為準。"
                    f"（來源：{url}）")
            print(f"         + {new_name}　{rng} {u}")
            made += 1
            new_n += 1
            if not args.apply:
                continue
            cur.execute("""
                INSERT INTO benefits
                  (name, agency, county, description, search_group,
                   application_period, eligibility_conditions, source_url,
                   source_excerpt, last_verified_date, is_active,
                   amount_min, amount_max, amount_unit, amount_note,
                   deadline_type)
                VALUES (%s,%s,%s,%s,%s,%s,%s::jsonb,%s,%s,
                        CURRENT_DATE,true,%s,%s,%s,%s,'unknown')""",
                (new_name, agency, county, desc, sgroup, "",
                 json.dumps({"counties": [county],
                             "_note": "資格條件待從官方頁面補齊"},
                            ensure_ascii=False),
                 url, SP.sub(" ", it.raw)[:900],
                 it.amount_min, it.amount_max, it.amount_unit,
                 "官方頁面實抓：" + "；".join(it.evidence[:3])))

        if args.apply and made:
            # 🔴 原筆標停用但**保留** —— 不然月更會把它當新缺口再抓
            cur.execute("""UPDATE benefits
                              SET is_active=false,
                                  description = %s,
                                  last_verified_date=CURRENT_DATE
                            WHERE id=%s""",
                        (f"（已於 2026-09-27 拆分為 {made} 筆獨立補助，"
                         f"本筆不再顯示）原名：{name}。"
                         f"🔴 拆分原因：本筆名稱是分類標籤而非實際補助名稱，"
                         f"官方頁（{url}）上有 {len(items)} 個獨立補助，"
                         f"各自的金額與資格都不同。", bid))
            conn.commit()
        time.sleep(1)

    print(f"\n{'✅ 已寫入' if args.apply else '（dry-run）'}"
          f"　拆分 {split_n} 筆 → 新增 {new_n} 筆　跳過 {skip_n}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
