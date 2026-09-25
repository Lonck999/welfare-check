#!/usr/bin/env python3
"""端到端驗證：857 筆資料能不能真的交付 P1~P4。

🔴 判準不是「資料有幾筆」，是**拿一個真實的使用者輪廓跑完整比對，
   看四個承諾各自交付得出來嗎**。

   P1 分析能領什麼   → 比對後有結果，且結果合理
   P2 依重要性＋時效排序 → 排序欄位（成功率/期限/金額）有值可排
   P3 告知文件與地點  → benefit_documents / benefit_locations 有資料
   P4 自身>配偶>家人  → benefit_applicants 有資料

⚠️ 這支不是單元測試 —— 它讀真實資料庫，所以會反映真實缺口。
"""
from __future__ import annotations

import json
import sys
from datetime import date

import psycopg2

PASS: list[str] = []
FAIL: list[str] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    (PASS if ok else FAIL).append(name)
    print(f"  {'✅' if ok else '🔴'} {name}" + (f"　{detail}" if detail else ""))


# 🔴 用 Lonck 的真實輪廓（男、已婚、新北、受僱有勞保、租屋）
PROFILE = {
    "county": "新北市",
    "age": 33,
    "married": True,
    "employed_insured": True,
    "renting": True,
    "income_level": None,      # 非低收/中低收
}


def main() -> int:
    conn = psycopg2.connect(dbname="welfare_check")
    cur = conn.cursor()

    print("=== P1：能不能分析出「可以領什麼」 ===")
    # 模擬比對：縣市符合（含全國）＋ 年齡符合 ＋ 不要求低收入身分
    cur.execute("""
        SELECT count(*) FROM benefits
         WHERE is_active
           AND (NOT jsonb_exists(eligibility_conditions, 'counties')
                OR eligibility_conditions->'counties' @> '["全國"]'
                OR eligibility_conditions->'counties' @> %s)
           AND ((eligibility_conditions->>'ageMin') IS NULL
                OR (eligibility_conditions->>'ageMin')::int <= %s)
           AND ((eligibility_conditions->>'ageMax') IS NULL
                OR (eligibility_conditions->>'ageMax')::int >= %s)
    """, (json.dumps([PROFILE["county"]]), PROFILE["age"], PROFILE["age"]))
    matched = cur.fetchone()[0]
    check("比對得出候選項目", matched > 0, f"{matched} 筆")
    check("候選數合理（不是全部也不是 0）",
          10 <= matched <= 500, f"{matched}/857")

    # 🔴 全國層級必須進得來 —— 那是最多人能領的
    cur.execute("""
        SELECT count(*) FROM benefits
         WHERE is_active AND eligibility_conditions->'counties' @> '["全國"]'
    """)
    natl = cur.fetchone()[0]
    check("全國層級項目存在", natl > 0, f"{natl} 筆")

    print("\n=== P2：排序欄位有沒有值可排 ===")
    cur.execute("SELECT count(*) FROM benefits WHERE amount_max IS NOT NULL")
    has_amt = cur.fetchone()[0]
    check("有金額可排序的筆數", has_amt > 0, f"{has_amt}/857")

    cur.execute("""SELECT deadline_type, count(*) FROM benefits
                    GROUP BY 1 ORDER BY 2 DESC""")
    dl = dict(cur.fetchall())
    check("deadline_type 全部有值", dl.get(None, 0) == 0,
          " ".join(f"{k}:{v}" for k, v in dl.items() if k))

    # 🔴 事件觸發型是「錯過就沒了」的那批 —— 必須排得出來
    cur.execute("""SELECT count(*) FROM benefits
                    WHERE deadline_type = 'event'
                      AND deadline_rule->>'trigger' IS NOT NULL""")
    ev = cur.fetchone()[0]
    check("事件觸發型有 trigger 可推算期限", ev > 0, f"{ev} 筆")

    cur.execute("SELECT count(*) FROM benefits WHERE effort_level IS NOT NULL")
    eff = cur.fetchone()[0]
    check("🔴 P2-① 成功率：effort_level 有值", eff > 0,
          f"{eff}/857（0 = 這個排序維度做不出來）")

    print("\n=== P3：文件與申請地點 ===")
    cur.execute("""SELECT count(DISTINCT benefit_id) FROM benefit_documents""")
    d = cur.fetchone()[0]
    check("有應備文件的補助數", d > 0, f"{d}/857（{d/857:.0%}）")
    cur.execute("""SELECT count(DISTINCT benefit_id) FROM benefit_locations""")
    lo = cur.fetchone()[0]
    check("有申請地點的補助數", lo > 0, f"{lo}/857（{lo/857:.0%}）")

    print("\n=== P4：申請對象（自身>配偶>家人）===")
    cur.execute("SELECT count(*) FROM benefit_applicants")
    ap = cur.fetchone()[0]
    check("🔴 benefit_applicants 有資料", ap > 0,
          f"{ap} 筆（0 = P4 完全做不出來）")

    print("\n=== 🔴 資料品質：會不會給出錯的答案 ===")
    cur.execute("""SELECT count(*) FROM benefits
                    WHERE amount_min IS NOT NULL AND amount_max IS NOT NULL
                      AND amount_min > amount_max""")
    check("沒有金額區間顛倒", cur.fetchone()[0] == 0)

    cur.execute("""SELECT count(*) FROM benefits
                    WHERE source_url IS NULL OR source_url !~ '^https?://'""")
    check("每筆都有可點的來源網址", cur.fetchone()[0] == 0)

    cur.execute("""SELECT count(*) FROM benefits
                    WHERE description IS NULL OR length(description) < 10""")
    check("沒有空描述", cur.fetchone()[0] == 0)

    # 🔴 過期資料：last_verified_date 太舊的會給出過時金額
    cur.execute("""SELECT count(*) FROM benefits
                    WHERE last_verified_date < CURRENT_DATE - 180""")
    stale = cur.fetchone()[0]
    check("沒有超過半年沒查證的", stale == 0, f"{stale} 筆過期")

    print("\n" + "=" * 46)
    print(f"通過 {len(PASS)}　失敗 {len(FAIL)}")
    if FAIL:
        print("\n🔴 做不到的承諾：")
        for f in FAIL:
            print(f"   · {f}")
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
