#!/usr/bin/env python3
"""C 案：`official` ＋ 首頁當來源 ＋ 描述空殼 ⇒ 降級 `unknown`（第二批）。

🔴 2026-10-01，Lonck 選「A＋C」：
   · A ＝ 舊判準誤殺的 32 筆不動（錯的是判準，已換掉）
   · C ＝ 處理 `official` ＋ 首頁 ＋ empty 的那幾筆

與 `fix_homepage_source_tier.py`（第一批 22 筆）同一套邏輯，
差別是**判準改用 `description_substance.verdict()`** 而非白名單。

🔴 為什麼要第二批：第一批用白名單（「未查得／查無／待補／尚未」），
   漏掉三種寫法：
     · id 209「金額未在官方頁面列出」—— 不在白名單
     · id 510 只把補助名稱重寫一次 —— 根本沒有宣告
     · id 731「未**含**補助金額…請洽 XXX」—— 「未含」不在白名單，
       且剝掉後剩下的那句只是「去別處問」

一律先 `--dry-run`（預設），`--apply` 才寫；寫前備份整列。
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from urllib.parse import urlparse

import psycopg2

sys.path.insert(0, str(Path(__file__).parent))
from description_substance import verdict             # noqa: E402
from scan_homepage_as_source import is_bare_homepage  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    conn = psycopg2.connect(dbname="welfare_check")
    cur = conn.cursor()
    cur.execute("""SELECT id, county, name, source_url, description
                     FROM benefits
                    WHERE source_tier = 'official'
                      AND source_url IS NOT NULL
                    ORDER BY id""")

    # 🔴 判準現場重算，**不讀掃描報告的 JSON** ——
    #    讀報告等於相信一份可能已過期的檔案，而「資料在我讀報告之後
    #    被改過」不會有任何訊號。
    targets = []
    for bid, county, name, url, desc in cur.fetchall():
        bare, why_url = is_bare_homepage(url)
        if not bare:
            continue
        v, why = verdict(desc or "", name or "")
        if v != "empty":
            continue          # thin / ok 不動（thin 要人看，不是機器判）
        targets.append((bid, county, name, url, why_url, why))

    print(f"official ＋ 首頁當來源 ＋ 描述空殼：{len(targets)} 筆\n")
    if not targets:
        print("沒有要處理的")
        return 0

    ids = [t[0] for t in targets]
    bak = Path("/tmp/wc_backup")
    bak.mkdir(parents=True, exist_ok=True)
    cur.execute("SELECT row_to_json(b)::text FROM benefits b"
                " WHERE b.id = ANY(%s)", (ids,))
    rows = [r[0] for r in cur.fetchall()]
    if len(rows) != len(ids):
        print(f"🔴 備份 {len(rows)} ≠ 目標 {len(ids)}，中止")
        return 1
    out = bak / "tier_downgrade_batch2.jsonl"
    out.write_text("\n".join(rows) + "\n", encoding="utf-8")
    print(f"✅ 已備份 {len(rows)} 筆整列 → {out}\n")

    for bid, county, name, url, why_url, why in targets:
        print(f"  [{bid:>3}] {county or '全國':<4} {name[:30]}")
        print(f"        {urlparse(url).netloc}（{why_url}）")
        print(f"        描述：{why}")
        print(f"        official → unknown")

    if not args.apply:
        print("\n（dry-run，未寫入。確認後加 --apply）")
        return 0

    cur.execute("UPDATE benefits SET source_tier = 'unknown'"
                " WHERE id = ANY(%s)", (ids,))
    conn.commit()

    # 🔴 驗終點：重讀 DB，不信 UPDATE 的回報
    cur.execute("SELECT count(*) FROM benefits"
                " WHERE id = ANY(%s) AND source_tier = 'unknown'", (ids,))
    got = cur.fetchone()
    n = got[0] if got else 0
    if n != len(ids):
        print(f"🔴 驗終點失敗：只有 {n}/{len(ids)} 筆變成 unknown")
        return 1
    print(f"\n✅ 已寫入並驗證：{n} 筆 official → unknown")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
