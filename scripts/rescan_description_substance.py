#!/usr/bin/env python3
"""用 description_substance 重掃全庫，取代前一版的白名單分類。

🔴 2026-10-01。前一版 `scan_homepage_as_source.py` 用白名單
   （「未查得／查無／待補／尚未」）判斷描述是不是空殼，實測漏兩種：
   · id 209 自我宣告「金額未在官方頁面列出」—— 不在白名單裡
   · id 510 只是把補助名稱重寫一次 —— 根本沒有宣告，就是沒內容

⚠️ 這支**不改任何資料**，只重算分類並印出差異。

輸出三類（這是下游動作的依據）：
  · empty —— 沒有內容 ⇒ source_tier 不該是 official
  · thin  —— 有字但無金額無細節 ⇒ 要人看一眼
  · ok    —— 內容可用 ⇒ 問題只在 source_url 指向首頁
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path
from urllib.parse import urlparse

import psycopg2

sys.path.insert(0, str(Path(__file__).parent))
from active_scope import (add_scope_arg, scope_label,  # noqa: E402
                          scope_sql)
from description_substance import verdict          # noqa: E402
from scan_homepage_as_source import is_bare_homepage  # noqa: E402

# 舊版的白名單（只用來對照「新偵測多抓到幾筆」）
OLD_WHITELIST = ("未查得", "查無", "待補", "尚未")


def main() -> int:
    ap = argparse.ArgumentParser()
    add_scope_arg(ap)
    args = ap.parse_args()

    conn = psycopg2.connect(dbname="welfare_check")
    cur = conn.cursor()
    cur.execute(f"""SELECT id, county, name, source_url, source_tier,
                          description
                     FROM benefits
                    WHERE true {scope_sql(args)}
                    ORDER BY id""")
    rows = cur.fetchall()
    print(f"全庫 {len(rows)} 筆（{scope_label(args)}）\n")

    recs = []
    for bid, county, name, url, tier, desc in rows:
        v, why = verdict(desc or "", name or "")
        bare, bare_why = is_bare_homepage(url or "")
        old_empty = bool(desc and
                         any(k in desc for k in OLD_WHITELIST))
        recs.append({
            "id": bid, "county": county or "全國", "name": name,
            "url": url or "", "tier": tier,
            "verdict": v, "why": why,
            "bare_url": bare, "bare_why": bare_why,
            "old_empty": old_empty,
            "desc_len": len(desc or ""),
        })

    print("=" * 68)
    print("① 描述實質度（全庫）")
    for v, n in Counter(r["verdict"] for r in recs).most_common():
        mark = {"empty": "🔴", "thin": "🔸", "ok": "✅"}[v]
        print(f"  {mark} {v:<6} {n:>4} 筆")

    # 🔴 新偵測比舊白名單多抓到的 —— 這是這支腳本的存在理由
    newly = [r for r in recs if r["verdict"] == "empty"
             and not r["old_empty"]]
    print(f"\n{'='*68}")
    print(f"🔴 ② 新偵測多抓到的空殼：{len(newly)} 筆"
          f"（舊白名單看不到）")
    for r in newly[:40]:
        print(f"  [{r['id']:>3}] {r['county']:<4} {r['name'][:26]:<28}"
              f" {r['desc_len']:>4}字  {r['why']}")
    if len(newly) > 40:
        print(f"  （另 {len(newly)-40} 筆）")

    # 反向：舊白名單抓到但新偵測放行的（應為 0，否則是退步）
    lost = [r for r in recs if r["old_empty"]
            and r["verdict"] != "empty"]
    print(f"\n🔴 ③ 舊白名單抓到但新偵測放行：{len(lost)} 筆"
          f"（**應為 0**，否則新判準是退步）")
    for r in lost[:10]:
        print(f"  [{r['id']:>3}] {r['name'][:28]}　{r['verdict']}"
              f"　{r['why']}")

    # 下游動作：official ＋ 首頁網址，按描述實質度分
    print(f"\n{'='*68}")
    print("④ `official` ＋ 首頁當來源 —— 按描述實質度分類")
    target = [r for r in recs
              if r["tier"] == "official" and r["bare_url"]]
    for v, n in Counter(r["verdict"] for r in target).most_common():
        mark = {"empty": "🔴 降 tier", "thin": "🔸 要人看",
                "ok": "✅ 只缺網址"}[v]
        print(f"  {mark:<12} {v:<6} {n:>3} 筆")
    for v in ("empty", "thin"):
        grp = [r for r in target if r["verdict"] == v]
        if not grp:
            continue
        print(f"\n  ── {v}（{len(grp)} 筆）")
        for r in grp:
            print(f"     [{r['id']:>3}] {r['county']:<4}"
                  f" {r['name'][:24]:<26} {r['why']}")

    # ok 那批按網域分組（之後要逐站找頁面）
    ok = [r for r in target if r["verdict"] == "ok"]
    if ok:
        print(f"\n  ── ok（{len(ok)} 筆，只缺 source_url）按網域：")
        for d, n in Counter(urlparse(r["url"]).netloc
                            for r in ok).most_common():
            print(f"     {d:<30} {n:>2} 筆")

    out = Path("/tmp/wc_backup/substance_rescan.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(recs, ensure_ascii=False, indent=2),
                   encoding="utf-8")
    print(f"\n完整結果 → {out}")

    # 🔴 ③ 不為 0 就是退步，exit 1
    return 1 if lost else 0


if __name__ == "__main__":
    sys.exit(main())
