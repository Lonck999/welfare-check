#!/usr/bin/env python3
"""填 effort_level（P2-① 成功率排序）與 quota_limited（名額風險）。

🔴 判準必須從**既有資料**推，不是憑感覺分級（2026-09-25）：
   effort_level  1 = 好申請   2 = 普通   3 = 難/門檻高
   quota_limited True = 有名額或競爭審查（先搶先贏，錯過就沒了）

🔴 **只在有證據時才填，沒證據一律留 NULL**：
   migration 的原始註解就寫了「NULL = 未評估。不可預設 1，
   否則『沒查過』會被當成『很好申請』」。

⚠️ 最重要的一條：**551 筆「應備文件 0 份」不代表不用文件**，
   而是我們沒抓到文件清單 —— 那批**絕不可**因此判成「好申請」。
   這正是「資料缺漏偽裝成好消息」的形狀。
   ⇒ 文件數只在 >=1 時當訊號用，=0 時完全不採信。

判準（依序套用，先命中先決定）：
  3（難）  · 需低收入戶/中低收入/清寒資格 —— 要先取得另一個資格
           · 競爭型（審查會/評選/擇優）
           · 應備文件 >= 6 份
  1（易）  · 免申請/主動發放/逕予核發 —— 根本不用辦
           · 線上申辦 且 應備文件 <= 3 份
  2（普通）· 應備文件 1~5 份且無上述特徵
  NULL     · 其餘（含文件數 0 = 沒抓到）
"""
from __future__ import annotations

import argparse
import re
import sys

import psycopg2

HARD_IDENTITY = re.compile(r"低收入戶|中低收入|清寒|經濟弱勢|特殊境遇")
COMPETITIVE = re.compile(r"審查會|評審|評選|擇優|競爭|甄選|評比")
QUOTA = re.compile(r"名額|限額|額滿|先申請先|經費用罄|預算用罄|依序核給|"
                   r"至用罄為止|逾期不受理")
NO_APPLY = re.compile(r"免申請|主動發放|逕予核發|逕行核發|自動核發|無須申請")
ONLINE = re.compile(r"線上申辦|線上申請|網路申請|線上立即申辦|e 化|網路報名")


def classify(desc: str, n_docs: int) -> tuple[int | None, bool | None]:
    """回傳 (effort_level, quota_limited)。沒證據就回 None。"""
    d = desc or ""
    quota = True if QUOTA.search(d) or COMPETITIVE.search(d) else None

    # 3 = 難
    # 🔴 有名額/額滿為止 也算難（2026-09-25 雙向驗證抓到）：
    #    原本 QUOTA 只設 quota_limited 卻沒影響 effort_level，
    #    於是「名額有限、額滿為止」被判成 NULL（未評估）。
    #    ⚠️ 搶不到就沒了，那本來就是申請難度的一部分。
    if HARD_IDENTITY.search(d) or COMPETITIVE.search(d) or QUOTA.search(d):
        return 3, quota
    if n_docs >= 6:
        return 3, quota

    # 1 = 易
    if NO_APPLY.search(d):
        return 1, quota
    if ONLINE.search(d) and 1 <= n_docs <= 3:
        return 1, quota

    # 2 = 普通（🔴 只在真的知道文件數時）
    if 1 <= n_docs <= 5:
        return 2, quota

    # 🔴 n_docs == 0 一律 NULL —— 那是「沒抓到」不是「不用文件」
    return None, quota


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    conn = psycopg2.connect(dbname="welfare_check")
    cur = conn.cursor()
    cur.execute("""
        SELECT b.id, b.description,
               (SELECT count(*) FROM benefit_documents d
                 WHERE d.benefit_id = b.id)
          FROM benefits b""")
    rows = cur.fetchall()

    tally = {1: 0, 2: 0, 3: 0, None: 0}
    q_count = 0
    for bid, desc, n_docs in rows:
        lvl, quota = classify(desc, n_docs)
        tally[lvl] += 1
        if quota:
            q_count += 1
        if args.apply:
            cur.execute("""UPDATE benefits
                              SET effort_level = %s, quota_limited = %s
                            WHERE id = %s""", (lvl, quota, bid))

    if args.apply:
        conn.commit()

    print("effort_level 分佈")
    print(f"  1 好申請   {tally[1]:>4}")
    print(f"  2 普通     {tally[2]:>4}")
    print(f"  3 難/門檻高 {tally[3]:>4}")
    print(f"  🔴 NULL 未評估 {tally[None]:>4}"
          f"　（其中文件數 0 = 沒抓到，不是不用文件）")
    print(f"\nquota_limited = true　{q_count} 筆（有名額/競爭審查）")

    covered = tally[1] + tally[2] + tally[3]
    print(f"\n可排序覆蓋率 {covered}/{len(rows)}（{covered/len(rows):.0%}）")
    if not args.apply:
        print("\n（dry-run，加 --apply 才寫入）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
