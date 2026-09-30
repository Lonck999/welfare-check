#!/usr/bin/env python3
"""A 類修正：`official` ＋ 首頁當來源 ＋ 描述空殼 ⇒ 降級為 `unknown`。

🔴 Lonck 2026-09-30 選 B（A 類做掉，B 類換搜尋後端後再處理）。

**這不是「資料不完整」，是「標記錯誤」** ——
`source_tier = 'official'` 在這個系統裡的意思是
「**這筆資料有官方頁面佐證**」。而這 22 筆：
  · source_url 是機關**首頁**（`mohw.gov.tw/`、`wda.gov.tw/`…）
  · description 自己寫著「本次搜尋未查得…」

🔴 首頁對**每一筆**補助都同樣「成立」⇒ 它不構成任何一筆的佐證。
⚠️ 而看到 `official` 的人（包括未來的我）就不會再去查 ——
   **錯誤的 `official` 比 `unknown` 危險，因為它會終止查證。**

🔴 為什麼只降 tier、不動 description／source_url：
   描述已經誠實寫著「未查得」（那是對的，不用改）；
   網址雖然是首頁，但**留著比清空有用** —— 至少指出主管機關是誰。
   真正錯的只有 tier 那一格。

🔴 為什麼不順手清掉這 22 筆：
   「這個縣市有沒有這項補助」**還沒查證**（搜尋額度 402 用盡）。
   刪掉＝把「我沒查到」變成「它不存在」，那是兩件事。
   ⇒ 只修標記，內容等查得動的時候再說。

一律先 `--dry-run`（預設），`--apply` 才寫；寫前備份整列。
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from urllib.parse import urlparse

import psycopg2

sys.path.insert(0, str(Path(__file__).parent))
from scan_homepage_as_source import is_bare_homepage  # noqa: E402

EMPTY_MARKS = ("未查得", "查無", "待補", "尚未")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    conn = psycopg2.connect(dbname="welfare_check")
    cur = conn.cursor()
    cur.execute("""SELECT id, county, name, source_url, source_tier,
                          description
                     FROM benefits
                    WHERE source_tier = 'official'
                      AND source_url IS NOT NULL
                    ORDER BY id""")

    # 🔴 判準在這裡重算，**不讀掃描報告的 JSON** ——
    #    讀報告等於相信一份可能已經過期的檔案，
    #    而「資料在我讀報告之後被改過」不會有任何訊號。
    targets = []
    for bid, county, name, url, tier, desc in cur.fetchall():
        bare, why = is_bare_homepage(url)
        if not bare:
            continue
        if not (desc and any(k in desc for k in EMPTY_MARKS)):
            continue          # B 類：描述有實質內容 ⇒ 這支不處理
        targets.append((bid, county, name, url, why))

    print(f"A 類（official ＋ 首頁 ＋ 描述空殼）：{len(targets)} 筆\n")
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
    (bak / "tier_downgrade_before.jsonl").write_text(
        "\n".join(rows) + "\n", encoding="utf-8")
    print(f"✅ 已備份 {len(rows)} 筆整列"
          f" → /tmp/wc_backup/tier_downgrade_before.jsonl\n")

    for bid, county, name, url, why in targets:
        print(f"  [{bid:>3}] {county or '全國':<4} {name[:28]:<30}")
        print(f"        {urlparse(url).netloc}（{why}）"
              f"　official → unknown")

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
