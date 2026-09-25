#!/usr/bin/env python3
"""補建「全國統一制度」的中央主條目。

🔴 為什麼需要這支（2026-09-25 發現）：
   衛福部對照表顯示 10 個縣市都缺同樣 6 項，佔 61 個缺口的 69%：
     父母未就業家庭育兒津貼(8)、弱勢家庭兒少緊急生活扶助(7)、
     弱勢兒少生活扶助(7)、國民年金保費減免(7)、低收入戶生活補助(7)、
     身心障礙證明(6)
   查證後發現**它們在資料庫裡沒有任何「全國層級」的主條目** ——
   只有零散的地方加碼筆。

   ⚠️ 根因不是「10 個縣市各缺一項」，是**中央那一筆從來沒建**。
   這 6 項都是中央訂辦法、地方執行的全國統一制度，
   任何縣市的居民都適用 ⇒ 應該是 county='全國' 的單一主條目。

🔴 金額全部來自官方頁面實抓（見每筆的 source_url 與 amount_note），
   **不是估算**。抓不到精確金額的欄位一律留 None。
"""
from __future__ import annotations

import argparse
import json
import sys

import psycopg2

# 🔴 每筆的 amount_* 都必須有 source_url 佐證，抓不到就留 None
NATIONAL = [
    {
        "name": "父母未就業家庭育兒津貼",
        "agency": "衛生福利部社會及家庭署",
        "desc": "育有未滿 2 歲兒童、未接受公共化或準公共托育服務者，"
                "由父母自行照顧可申請育兒津貼。🔴 金額依胎次與家庭"
                "經濟狀況分級，詳見官方頁面。",
        "url": "https://www.mohw.gov.tw/cp-4425-43075-1.html",
        "amount_min": 5000, "amount_max": 5000, "amount_unit": "monthly",
        "amount_note": "第 1 胎每月 5,000 元起，第 2 胎、第 3 胎以上加碼；"
                       "中低收入戶另有加給。實際金額以官方公告為準",
        "elig": {"counties": ["全國"], "ageMax": 2,
                 "requiredFlags": ["has_child_under_2"]},
        "group": "現金與生活補助類",
        "period": "常態受理（出生後 60 日內申請可追溯自出生月）",
        "deadline_type": "event",
        "deadline_rule": {"trigger": "childbirth", "within_months": 2},
    },
    {
        "name": "弱勢兒童及少年生活扶助",
        "agency": "衛生福利部社會及家庭署",
        "desc": "低收入戶、中低收入戶或符合弱勢條件之家庭，"
                "其未滿 18 歲兒童及少年可請領生活扶助。",
        "url": "https://www.mohw.gov.tw/cp-190-223-1.html",
        "amount_min": 2197, "amount_max": 2661, "amount_unit": "monthly",
        "amount_note": "自 113 年起每人每月 2,197～2,661 元"
                       "（官方原文實抓）；各縣市另有加碼",
        "elig": {"counties": ["全國"], "ageMax": 18,
                 "incomeThreshold": "mid_low_income"},
        "group": "現金與生活補助類",
        "period": "常態受理",
        "deadline_type": "always",
        "deadline_rule": None,
    },
    {
        "name": "弱勢家庭兒童及少年緊急生活扶助",
        "agency": "衛生福利部社會及家庭署",
        "desc": "家庭遭逢變故、經濟陷困，致兒童及少年生活陷於困境者，"
                "可申請緊急生活扶助。",
        "url": "https://www.gov.tw/News_Content_2_528866",
        "amount_min": 3000, "amount_max": 3000, "amount_unit": "monthly",
        "amount_note": "每人每月 3,000 元（官方頁面實抓），最長補助 6 個月",
        "elig": {"counties": ["全國"], "ageMax": 18,
                 "requiredFlags": ["family_crisis"]},
        "group": "時效性最高項目",
        "period": "事件發生後儘速申請",
        "deadline_type": "event",
        "deadline_rule": {"trigger": "family_crisis"},
    },
    {
        "name": "國民年金保險費補助（所得未達一定標準）",
        "agency": "勞動部勞工保險局",
        "desc": "國民年金被保險人所得未達一定標準者，"
                "保險費由政府補助 55%～100%，本人僅需負擔差額。",
        "url": "https://www.bli.gov.tw/0013596.html",
        "amount_min": 887, "amount_max": 2216, "amount_unit": "monthly",
        "amount_note": "政府補助後本人月負擔約 887～1,329 元"
                       "（全額為 2,216 元，官方頁面實抓）",
        "elig": {"counties": ["全國"], "ageMin": 25, "ageMax": 65,
                 "incomeThreshold": "mid_low_income"},
        "group": "現金與生活補助類",
        "period": "常態受理",
        "deadline_type": "always",
        "deadline_rule": None,
    },
    {
        "name": "低收入戶家庭生活扶助（中央基準）",
        "agency": "衛生福利部社會及家庭署",
        "desc": "經審核認定為低收入戶者，按家庭人口與款別發給家庭生活扶助費。"
                "🔴 實際金額依各縣市最低生活費標準計算。",
        "url": "https://www.mohw.gov.tw/dl-65687-d81e7f69-d679-44c4-bfdb-"
               "e3105890b",
        "amount_min": 2308, "amount_max": 8079, "amount_unit": "monthly",
        "amount_note": "每人每月 2,308～8,079 元（官方文件實抓，"
                       "依款別與縣市而異）",
        "elig": {"counties": ["全國"], "incomeThreshold": "low_income"},
        "group": "現金與生活補助類",
        "period": "常態受理",
        "deadline_type": "always",
        "deadline_rule": None,
    },
    {
        "name": "身心障礙證明申請與鑑定",
        "agency": "衛生福利部社會及家庭署",
        "desc": "身心障礙者權益保障法規定之證明申請與需求評估。"
                "🔴 本身不是現金給付，但**是所有身心障礙福利的前置資格**"
                "（生活補助、輔具、停車證、乘車優惠都需要它）。",
        "url": "https://www.gov.tw/News_Content_26_677435",
        "amount_min": None, "amount_max": None, "amount_unit": None,
        "amount_note": "🔴 非現金給付，是其他身障福利的前置資格",
        "elig": {"counties": ["全國"],
                 "requiredFlags": ["needs_disability_certificate"]},
        "group": "資格認定基礎",
        "period": "常態受理（證明到期前 90 日內應重新鑑定）",
        "deadline_type": "event",
        "deadline_rule": {"trigger": "expiry", "within_months": 3},
    },
]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    conn = psycopg2.connect(dbname="welfare_check")
    cur = conn.cursor()
    cur.execute("SELECT count(*) FROM benefits")
    before = cur.fetchone()[0]

    cur.execute("SELECT name FROM benefits WHERE county = '全國'")
    existing = {n for (n,) in cur.fetchall()}

    new = 0
    for b in NATIONAL:
        if b["name"] in existing:
            print(f"  ⏭ 已存在：{b['name']}")
            continue
        print(f"  + {b['name']}")
        print(f"      金額 {b['amount_min']}~{b['amount_max']} "
              f"{b['amount_unit']}　{b['url'][:56]}")
        new += 1
        if not args.apply:
            continue
        cur.execute("""
            INSERT INTO benefits
              (name, agency, county, description, search_group,
               application_period, eligibility_conditions, source_url,
               source_excerpt, last_verified_date, is_active,
               amount_min, amount_max, amount_unit, amount_note,
               deadline_type, deadline_rule)
            VALUES (%s, %s, '全國', %s, %s, %s, %s::jsonb, %s, %s,
                    CURRENT_DATE, true, %s, %s, %s, %s, %s, %s::jsonb)""",
            (b["name"], b["agency"], b["desc"], b["group"], b["period"],
             json.dumps(b["elig"], ensure_ascii=False), b["url"],
             b["amount_note"][:900],
             b["amount_min"], b["amount_max"], b["amount_unit"],
             b["amount_note"],
             b["deadline_type"],
             json.dumps(b["deadline_rule"], ensure_ascii=False)
             if b["deadline_rule"] else None))

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
