#!/usr/bin/env python3
"""驗證 benefits schema 擴充（P1~P4）真的能用。

🔴 判準不是「欄位存在」，是**約束真的會擋、合法值真的放行**。
   只驗欄位存在的話，CHECK 打錯字也會全綠。

跑法：python3 scripts/verify_benefits_schema.py
"""
from __future__ import annotations

import sys

import psycopg2
from psycopg2 import errors

PASS: list[str] = []
FAIL: list[str] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    (PASS if ok else FAIL).append(name)
    mark = "  ✅" if ok else "  🔴"
    print(f"{mark} {name}" + (f"　{detail}" if detail else ""))


def main() -> int:
    conn = psycopg2.connect(dbname="welfare_check")

    print("── ① 新欄位存在且型別正確 ──")
    want = {
        "amount_min": "integer", "amount_max": "integer",
        "amount_unit": "text", "amount_note": "text",
        "deadline_type": "text", "deadline_date": "date",
        "deadline_rule": "jsonb", "effort_level": "smallint",
        "quota_limited": "boolean",
    }
    cur = conn.cursor()
    cur.execute("""SELECT column_name, data_type FROM information_schema.columns
                    WHERE table_name = 'benefits'""")
    have = dict(cur.fetchall())
    for col, typ in want.items():
        got = have.get(col)
        check(f"benefits.{col} 是 {typ}", got == typ, f"實際 {got}")

    print("\n── ② benefit_applicants 表（P4）──")
    cur.execute("""SELECT count(*) FROM information_schema.tables
                    WHERE table_name = 'benefit_applicants'""")
    check("benefit_applicants 表存在", cur.fetchone()[0] == 1)
    cur.execute("""SELECT count(*) FROM information_schema.columns
                    WHERE table_name = 'benefit_applicants'
                      AND column_name IN ('benefit_id','role','relation','note')""")
    check("四個必要欄位都在", cur.fetchone()[0] == 4)

    print("\n── ③ 🔴 CHECK 約束真的會擋（植入非法值）──")
    bad = [
        ("非法 amount_unit",
         "UPDATE benefits SET amount_unit='每個月' WHERE id=(SELECT min(id) FROM benefits)"),
        ("amount_min > amount_max",
         "UPDATE benefits SET amount_min=9000, amount_max=100 "
         "WHERE id=(SELECT min(id) FROM benefits)"),
        ("非法 deadline_type",
         "UPDATE benefits SET deadline_type='常態' WHERE id=(SELECT min(id) FROM benefits)"),
        ("always 卻塞 deadline_date",
         "UPDATE benefits SET deadline_type='always', deadline_date='2026-12-31' "
         "WHERE id=(SELECT min(id) FROM benefits)"),
        ("effort_level=0",
         "UPDATE benefits SET effort_level=0 WHERE id=(SELECT min(id) FROM benefits)"),
        ("非法 applicant role",
         "INSERT INTO benefit_applicants(benefit_id, role) "
         "SELECT min(id), '朋友' FROM benefits"),
        ("非法 relation",
         "INSERT INTO benefit_applicants(benefit_id, role, relation) "
         "SELECT min(id), 'family', '鄰居' FROM benefits"),
    ]
    for name, sql in bad:
        c = conn.cursor()
        try:
            c.execute(sql)
            conn.rollback()
            check(f"擋下：{name}", False, "🔴 沒擋住！")
        except errors.CheckViolation:
            conn.rollback()
            check(f"擋下：{name}", True)
        except Exception as e:                       # noqa: BLE001
            conn.rollback()
            check(f"擋下：{name}", False, f"其他錯誤 {type(e).__name__}")

    print("\n── ④ 🔴 合法值必須放行（negative control）──")
    # 沒有這節的話，「全部都擋」也會讓上一節全綠
    good = [
        ("fixed + deadline_date",
         "UPDATE benefits SET deadline_type='fixed', deadline_date='2026-12-31' "
         "WHERE id=(SELECT min(id) FROM benefits)"),
        ("event + deadline_rule",
         "UPDATE benefits SET deadline_type='event', deadline_date=NULL, "
         """deadline_rule='{"trigger":"childbirth","within_months":6}' """
         "WHERE id=(SELECT min(id) FROM benefits)"),
        ("合法 applicant",
         "INSERT INTO benefit_applicants(benefit_id, role, relation) "
         "SELECT min(id), 'family', 'child' FROM benefits"),
    ]
    for name, sql in good:
        c = conn.cursor()
        try:
            c.execute(sql)
            conn.rollback()
            check(f"放行：{name}", True)
        except Exception as e:                       # noqa: BLE001
            conn.rollback()
            check(f"放行：{name}", False, f"🔴 誤擋 {e}")

    print("\n── ⑤ deadline_type 回填覆蓋率 ──")
    cur.execute("SELECT count(*) FROM benefits WHERE deadline_type IS NULL")
    check("沒有任何 benefits 缺 deadline_type", cur.fetchone()[0] == 0)
    cur.execute("SELECT count(*) FROM benefits WHERE deadline_type='unknown'")
    unk = cur.fetchone()[0]
    cur.execute("SELECT count(*) FROM benefits")
    total = cur.fetchone()[0]
    check(f"unknown 不超過 10%", unk / total <= 0.10, f"{unk}/{total}")

    # 🔴 事件觸發型必須有 trigger —— 沒有的話「錯過就沒了」的提醒發不出來
    cur.execute("""SELECT count(*) FROM benefits
                    WHERE deadline_type='event'
                      AND (deadline_rule IS NULL
                           OR deadline_rule->>'trigger' IS NULL)""")
    no_trig = cur.fetchone()[0]
    cur.execute("SELECT count(*) FROM benefits WHERE deadline_type='event'")
    ev = cur.fetchone()[0]
    check("event 型九成以上解得出 trigger",
          ev > 0 and no_trig / ev <= 0.10, f"缺 trigger {no_trig}/{ev}")

    print("\n── ⑥ 既有資料未受損 ──")
    cur.execute("SELECT count(*) FROM benefits")
    check("benefits 仍有 499 筆", cur.fetchone()[0] == 499)
    cur.execute("""SELECT count(*) FROM benefits
                    WHERE description IS NOT NULL AND length(description) > 50""")
    check("有實質內容的筆數未減少", cur.fetchone()[0] >= 157)

    print("\n" + "=" * 46)
    print(f"通過 {len(PASS)}　失敗 {len(FAIL)}")
    conn.rollback()
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
