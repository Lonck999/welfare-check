#!/usr/bin/env python3
"""從描述推導「這筆補助可以為誰申請」，填 benefit_applicants（P4）。

🔴 Lonck 2026-09-24 明訂 P4：
   「需增設問法有沒有要幫家人申請？有才有其他問法，
     給他除了自己的還有其他人的，沒有只想找自身就只給自身」
   ⇒ 問卷已改（applyFor / applyForRoles），但**沒有一筆補助標註誰能申請**
      ⇒ 使用者勾了「要幫爸媽找」也篩不出東西。

role 定義（見 migration）：
  self      本人
  spouse    配偶
  household 與配偶／全戶共同（全戶型：所得合計、家庭為單位）
  family    為家人申請（relation 再細分 parent/child/...）

🔴 判準只在**描述明確指向某個對象**時才填，不猜：
   · 兒少/就學/托育/育兒 → family(child)
   · 老人/長者/敬老/65歲  → family(parent) ＋ self（自己也會老）
   · 身心障礙/失能        → self ＋ family(other)
   · 孕產/生育/坐月        → self ＋ spouse
   · 喪葬/遺屬/死亡        → family(other)（為過世家人辦）
   · 全戶/家庭/戶內        → household
   · 明示「配偶」          → spouse

⚠️ **每一筆都至少有 self** —— 除非它明確只為別人辦（喪葬、托育）。
   理由：Lonck 說「沒有(要幫家人)只想找自身就只給自身」，
   所以 self 是預設可見的那一層，漏掉 self 會讓補助整個消失。
"""
from __future__ import annotations

import argparse
import re
import sys

import psycopg2

PAT = {
    "child": re.compile(r"兒童|幼兒|嬰兒|新生兒|學童|子女|就學|托育|育兒|"
                        r"少年|學生|國小|國中|高中"),
    "elder": re.compile(r"老人|長者|長輩|高齡|敬老|65\s*歲|六十五歲|"
                        r"中低收入老人"),
    "disab": re.compile(r"身心障礙|身障|失能|重症|植物人"),
    "birth": re.compile(r"孕|產婦|生育|分娩|坐月|哺乳|懷孕"),
    "spouse": re.compile(r"配偶|夫妻|另一半|未婚妻|未婚夫"),
    "house": re.compile(r"全戶|家庭|戶內|同一戶|家戶|家庭總收入|家庭成員"),
    "death": re.compile(r"喪葬|殮葬|死亡|遺屬|亡故|往生"),
}
# 🔴 這些是「只為別人辦」的，不給 self
ONLY_FOR_OTHERS = ("death",)


def derive(desc: str) -> list[tuple[str, str | None]]:
    """回傳 [(role, relation), ...]。"""
    d = desc or ""
    hits = {k: bool(p.search(d)) for k, p in PAT.items()}
    roles: set[tuple[str, str | None]] = set()

    if hits["child"]:
        roles.add(("family", "child"))
    if hits["elder"]:
        roles.add(("family", "parent"))
        roles.add(("self", None))
    if hits["disab"]:
        roles.add(("self", None))
        roles.add(("family", "other"))
    if hits["birth"]:
        roles.add(("self", None))
        roles.add(("spouse", None))
    if hits["spouse"]:
        roles.add(("spouse", None))
    if hits["house"]:
        roles.add(("household", None))
    if hits["death"]:
        roles.add(("family", "other"))

    if not roles:
        return []

    # 🔴 預設補上 self —— 除非它「只為別人辦」且沒有其他指向本人的訊號
    only_others = (hits["death"] or hits["child"]) and not (
        hits["elder"] or hits["disab"] or hits["birth"] or hits["house"])
    if not only_others:
        roles.add(("self", None))
    return sorted(roles)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    conn = psycopg2.connect(dbname="welfare_check")
    cur = conn.cursor()
    cur.execute("SELECT id, description FROM benefits")
    rows = cur.fetchall()

    tally: dict[str, int] = {}
    covered = 0
    for bid, desc in rows:
        roles = derive(desc)
        if not roles:
            continue
        covered += 1
        for role, rel in roles:
            key = f"{role}/{rel}" if rel else role
            tally[key] = tally.get(key, 0) + 1
            if args.apply:
                cur.execute("""
                    INSERT INTO benefit_applicants (benefit_id, role, relation)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (benefit_id, role, relation) DO NOTHING""",
                    (bid, role, rel))

    if args.apply:
        conn.commit()
        cur.execute("SELECT count(*) FROM benefit_applicants")
        print(f"✅ benefit_applicants 現有 {cur.fetchone()[0]} 筆\n")

    print("role 分佈")
    for k, v in sorted(tally.items(), key=lambda x: -x[1]):
        print(f"  {k:<18} {v:>4}")
    print(f"\n有標註申請對象的補助 {covered}/{len(rows)}"
          f"（{covered/len(rows):.0%}）")
    print(f"🔴 其餘 {len(rows)-covered} 筆描述無明確對象指向 → 不猜，留空")
    if not args.apply:
        print("\n（dry-run）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
