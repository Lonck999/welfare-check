#!/usr/bin/env python3
"""匯入中央部會的「可列舉」補助來源 → benefits。

🔴 為什麼要另寫一支（不併進 import_county_opendata.py）：
   中央來源的顆粒度與地方完全不同 ——
   地方是「一筆 = 一個補助」，中央這批是「一筆 = 一篇說明文章」，
   同一個給付會有 2~6 篇（簡介／請領要件／計算方式／申請方式）。
   ⇒ 必須先**按給付種類 group**，把多篇說明合併成一筆補助。

🔴 判準（2026-09-25 實測後定）：
   資料集的「一筆」對不對得上「一個補助」—— 對不上就要先聚合。
   ⚠️ 直接照抄會產生 65 筆「勞保年金簡介」這種不是補助的條目。

已納入的來源：
  · 勞保局業管年金給付介紹（data.gov.tw/dataset/6062）
    14 種給付 × 2~6 篇說明 = 65 筆 → 聚合成 14 筆補助
    🔴 正好補上我們缺的：勞保老年年金 0 筆、國保老年年金 0 筆

已評估但**不納入**的（寫下來，免得日後又去查一次）：
  · dataset/6509 整合住宅補貼 —— 🔴 欄位是「申請戶數／核准率」，
    是統計表不是補助清單
  · e 政府 7,862 筆裡的中央級 173 筆 —— 多數是「繳納證明」
    「線上建檔」這類行政服務，不是補助
  · 各種「統計表」「初次核付人數」資料集 —— 同上
"""
from __future__ import annotations

import argparse
import collections
import json
import re
import sys
from pathlib import Path

import psycopg2

sys.path.insert(0, str(Path(__file__).parent))
from import_county_opendata import fetch  # noqa: E402

# 保險別 → 主管機關
AGENCY_OF = {
    "勞工保險": "勞動部勞工保險局",
    "勞工職業災害保險": "勞動部勞工保險局",
    "勞工退休金": "勞動部勞工保險局",
    "國民年金保險": "勞動部勞工保險局",
}

MOL_PENSION = ("https://apiservice.mol.gov.tw/OdService/download/"
               "A17000000J-000009-zeh")


def import_mol_pension(cur, apply: bool, refresh: bool = False) -> tuple[int, int]:
    """勞保局年金給付：65 篇說明 → 聚合成 14 筆補助。"""
    rows = fetch(MOL_PENSION)
    print(f"勞保局年金給付：抓到 {len(rows)} 篇說明")

    # 🔴 按「保險別 + 給付種類」聚合 —— 一個給付種類 = 一筆補助
    groups: dict[tuple[str, str], list[dict]] = collections.defaultdict(list)
    for r in rows:
        ins = str(r.get("保險別", "")).strip()
        kind = str(r.get("給付種類", "")).strip()
        if ins and kind:
            groups[(ins, kind)].append(r)
    print(f"  聚合成 {len(groups)} 筆補助（一個給付種類 = 一筆）")

    # 🔴 排除「總論型」的給付種類 —— 它們不是可申請的補助。
    #    實測「勞工保險/勞保年金」那組是簡介、平均月投保薪資計算方式、
    #    保險年資計算方式、申請與核發原則 —— 全是說明而非給付項目。
    #    ⚠️ 照抄會產生一筆叫「勞工保險勞保年金」的假補助，
    #    而它看起來跟其他 15 筆一模一樣。
    OVERVIEW_KINDS = {"勞保年金"}

    cur.execute("""SELECT name FROM benefits
                    WHERE agency = '勞動部勞工保險局'""")
    existing = {re.sub(r"\s+", "", n) for (n,) in cur.fetchall()}

    new = 0
    skipped = 0
    for (ins, kind), items in sorted(groups.items()):
        if kind in OVERVIEW_KINDS:
            print(f"    ⏭ 跳過總論：{ins}{kind}（{len(items)} 篇，非可申請給付）")
            continue
        # 🔴 名稱要含保險別 —— 「失能年金」在勞保與職災保險都有，
        #    只用給付種類會撞名（而且是兩個不同的給付）
        name = f"{ins}{kind}"
        if re.sub(r"\s+", "", name) in existing and not refresh:
            skipped += 1
            continue

        # 🔴 **這批資料是索引不是內容**（2026-09-25 實測）：
        #    「說明」欄只有標題（如「勞工保險老年年金給付請領要件」），
        #    真正的內容在「網址」指向的頁面。
        #    ⚠️ 不可把標題串起來當描述 —— 那會產生
        #    「勞工保險－老年年金。勞工保險老年年金給付請領要件
        #     勞工保險老年年金給付標準」這種**看起來有內容但什麼都沒講**的字串。
        #    ⇒ 誠實寫成「官方頁面清單」，並把每個網址列出來。
        links = []
        for it in items:
            title = str(it.get("說明", "")).strip()
            u = str(it.get("網址", "")).strip()
            if title and u.startswith("http"):
                links.append(f"{title}：{u}")
        description = (
            f"{ins}－{kind}。🔴 本筆為官方頁面索引，"
            f"詳細請領資格與金額請見以下 {len(links)} 個勞保局官方頁面（"
            + "；".join(t.split("：")[0] for t in links) + "）。"
        )[:1500]
        parts = links

        # 🔴 source_url 取第一個有網址的那篇，沒有才退回 dataset 頁
        url = ""
        for it in items:
            u = str(it.get("網址", "")).strip()
            if u.startswith("http"):
                url = u
                break
        url = url or "https://data.gov.tw/dataset/6062"

        excerpt = " ／ ".join(parts)[:900] or f"{ins}{kind}（勞保局開放資料）"

        # 資格條件：🔴 來源**完全沒有**結構化的年齡/收入門檻，
        #    連文字敘述都沒有（「說明」欄只是標題）。
        #    ⇒ 只填 counties=全國 並標明待補，
        #    **絕不可把索引標題塞進 otherConditions 假裝有條件**，
        #    也不可自己猜 ageMin=65（老年年金請領年齡逐年調整）。
        elig = {
            "counties": ["全國"],
            "_note": "資格條件待從官方頁面補齊（本筆來源僅提供頁面索引）",
        }

        print(f"    · {name}（{len(items)} 篇說明）")
        if apply and refresh and re.sub(r"\s+", "", name) in existing:
            # 🔴 refresh：只更新內容，不新增（避免同名兩筆）
            cur.execute("""UPDATE benefits
                              SET description = %s, eligibility_conditions = %s::jsonb,
                                  source_url = %s, source_excerpt = %s,
                                  last_verified_date = CURRENT_DATE
                            WHERE name = %s AND agency = %s""",
                        (description, json.dumps(elig, ensure_ascii=False),
                         url, excerpt, name, AGENCY_OF.get(ins, "勞動部勞工保險局")))
            new += 1
            continue
        if apply:
            cur.execute("""
                INSERT INTO benefits
                  (name, agency, county, description, search_group,
                   application_period, eligibility_conditions, source_url,
                   source_excerpt, last_verified_date, is_active, deadline_type)
                VALUES (%s, %s, %s, %s, %s, %s, %s::jsonb, %s, %s,
                        CURRENT_DATE, true, 'always')
                RETURNING id""",
                (name, AGENCY_OF.get(ins, "勞動部勞工保險局"), "全國",
                 description, "現金與生活補助類",
                 "常態受理",         # 🔴 年金給付確實是常態，非猜測
                 json.dumps(elig, ensure_ascii=False), url, excerpt))
            bid = cur.fetchone()[0]
            cur.execute("""INSERT INTO benefit_locations
                             (benefit_id, name, phone, website)
                           VALUES (%s, %s, %s, %s)""",
                        (bid, "勞動部勞工保險局（各地辦事處）",
                         "02-23961266", "https://www.bli.gov.tw/"))
        new += 1
    return new, skipped


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--refresh", action="store_true",
                    help="重寫已存在的筆（修正描述與資格條件）")
    args = ap.parse_args()

    conn = psycopg2.connect(dbname="welfare_check")
    cur = conn.cursor()

    cur.execute("SELECT count(*) FROM benefits")
    before = cur.fetchone()[0]

    new, skipped = import_mol_pension(cur, args.apply, args.refresh)

    if args.apply:
        conn.commit()
        cur.execute("SELECT count(*) FROM benefits")
        after = cur.fetchone()[0]
        print(f"\n✅ 寫入 {new} 筆（已存在跳過 {skipped}）"
              f"　benefits {before} → {after}")
        # 🔴 驗終點：真的讀回來確認
        if not args.refresh and after - before != new:
            print(f"🔴 筆數不符：預期 +{new}，實際 +{after - before}")
            return 1
    else:
        print(f"\n（dry-run）會新增 {new} 筆，已存在跳過 {skipped}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
