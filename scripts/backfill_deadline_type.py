#!/usr/bin/env python3
"""從 application_period 自由文字反解 deadline_type / deadline_rule。

🔴 這支只填 **解析得出來** 的，解析不出來一律填 'unknown' ——
   **不可預設成 'always'**，否則「沒查過」會被當成「隨時可申請」，
   而那正是使用者最不會發現的錯（它看起來很正常）。

實測 499 筆：常態 370(74%)／依公告 94／事件 30／每年 7／固定迄日 5／解析不出 26
"""
from __future__ import annotations

import argparse
import json
import re
import sys

import psycopg2

S = r"\s*"

# 🔴 順序有意義：由「最具體」排到「最籠統」，第一個命中就採用。
#    例：「2026/1/1～2026/12/31，隨到隨辦」同時含固定日期與「隨到隨辦」，
#    應判 fixed（有明確迄日）而不是 always。
RULES: list[tuple[str, str]] = [
    ("fixed", rf"20\d\d{S}年?{S}[/\-]?{S}\d{{1,2}}{S}月?{S}[/\-]?{S}\d{{1,2}}{S}日?"
              rf"|1[0-9]\d{S}年{S}\d{{1,2}}{S}月{S}\d{{1,2}}{S}日"),
    # 🔴 「之日起 N 年內」漏掉會很嚴重：喪葬給付、生育給付都是這種寫法，
    #    而它們**過期就真的領不到**。實測「死亡之日起 5 年內」原本判 unknown。
    ("event", r"後\s*\d+\s*[~～\-至]?\s*\d*\s*(年|個月|日|天)內|發生後|離職後"
              r"|購買後|到期前|出生後|年滿\s*\d+\s*歲|產前|產後|懷孕期間"
              r"|之日起\s*\d+\s*(年|個月|日|天)內|起\s*\d+\s*(年|個月|日)內"
              r"|死亡|喪葬|身故|逾期(視同放棄|不給付|不予受理)"
              # 2026-09-25 匯入新來源後補：中文數字、「之次日起」
              r"|之次日起|次日起\s*[一二三四五六七八九十百零\d]+\s*日內"
              r"|滿\s*[一二三四五六七八九十百零\d]+\s*日之|流產|接種期間"),
    ("annual", rf"每年{S}\d{{1,2}}{S}[~～\-至]?{S}\d{{0,2}}{S}月|每學年|每學期"
               r"|就讀學校所定期限|學校所定期限"),
    ("announced", r"依.{0,8}公告|另行公告|視.{0,6}公告|逐案|依.{0,8}規定"
                  r"|依本局公文|按月統一辦理"),
    # 🔴 「全年受理」「線上立即申辦」都是常態，漏掉會變 unknown
    ("always", r"常態|隨到隨辦|隨時|全年受理|全年皆可|線上立即|即時受理"
               r"|^無$|^\d+\s*天$|^\d+\s*個?工作天$"),
]

# event 的觸發事件 → deadline_rule
EVENT_TRIGGER: list[tuple[str, str]] = [
    ("childbirth", r"出生後|新生兒|生育"),
    ("pregnancy", r"懷孕|產前|產後|流產|小產"),
    ("unemployment", r"離職後|失業|非自願"),
    ("death", r"死亡|喪葬|身故"),
    ("purchase", r"購買後|購置後"),
    ("age", r"年滿\s*\d+\s*歲"),
    ("expiry", r"到期前|證明到期"),
]


def parse(text: str) -> tuple[str, dict | None]:
    """回傳 (deadline_type, deadline_rule)。"""
    for dtype, pat in RULES:
        if not re.search(pat, text):
            continue
        if dtype == "event":
            rule: dict = {}
            for trig, tpat in EVENT_TRIGGER:
                if re.search(tpat, text):
                    rule["trigger"] = trig
                    break
            m = re.search(rf"(\d+){S}[~～\-至]{S}(\d+){S}個月內", text)
            if m:
                rule["within_months"] = int(m.group(2))
            else:
                m = re.search(rf"(\d+){S}個月內", text)
                if m:
                    rule["within_months"] = int(m.group(1))
                else:
                    m = re.search(rf"(\d+){S}年內", text)
                    if m:
                        rule["within_months"] = int(m.group(1)) * 12
            return dtype, (rule or None)
        if dtype == "annual":
            months = [int(x) for x in re.findall(r"(\d{1,2})\s*[~～\-至月]", text)
                      if 1 <= int(x) <= 12]
            return dtype, ({"months": sorted(set(months))} if months else None)
        return dtype, None
    return "unknown", None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true",
                    help="真的寫入（預設只 dry-run）")
    args = ap.parse_args()

    conn = psycopg2.connect(dbname="welfare_check")
    cur = conn.cursor()
    cur.execute("""SELECT id, application_period FROM benefits
                    WHERE application_period IS NOT NULL
                      AND application_period <> ''""")
    rows = cur.fetchall()

    tally: dict[str, int] = {}
    updates: list[tuple[int, str, str | None]] = []
    for bid, text in rows:
        dtype, rule = parse(text)
        tally[dtype] = tally.get(dtype, 0) + 1
        updates.append((bid, dtype, json.dumps(rule, ensure_ascii=False)
                        if rule else None))

    print(f"解析 {len(rows)} 筆：")
    for k in ("always", "announced", "event", "annual", "fixed", "unknown"):
        n = tally.get(k, 0)
        mark = "🔴 " if k == "unknown" and n else "   "
        print(f"  {mark}{k:<10} {n:>4} 筆")

    # 🔴 sanity check：unknown 不該超過一成，超過代表 regex 退化了
    unknown_ratio = tally.get("unknown", 0) / max(len(rows), 1)
    if unknown_ratio > 0.10:
        print(f"\n🔴 unknown 佔 {unknown_ratio:.0%}（>10%）—— regex 可能退化，"
              f"先檢查再寫入")
        return 1

    if not args.apply:
        print("\n（dry-run，未寫入。加 --apply 才會真的寫）")
        return 0

    for bid, dtype, rule in updates:
        cur.execute("""UPDATE benefits
                          SET deadline_type = %s, deadline_rule = %s::jsonb
                        WHERE id = %s""", (dtype, rule, bid))
    conn.commit()
    print(f"\n✅ 已寫入 {len(updates)} 筆")

    cur.execute("""SELECT deadline_type, count(*) FROM benefits
                    GROUP BY 1 ORDER BY 2 DESC""")
    for t, n in cur.fetchall():
        print(f"  {t or '(NULL)':<12} {n:>4}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
