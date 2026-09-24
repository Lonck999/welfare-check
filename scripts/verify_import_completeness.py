#!/usr/bin/env python3
"""驗證每個開放資料來源「抓到幾筆」與「真的進庫幾筆」一致。

🔴 為什麼需要這支（2026-09-25 踩到）：
   批次匯入時臺北市那 10 筆因為 `benefit_locations.phone` 是
   varchar(50) 而我截到 100 → StringDataRightTruncation
   → **整批 rollback**。
   而批次腳本用 `grep -E "抓到|去重|新增|寫入"` 過濾輸出，
   **錯誤訊息被濾掉了** ⇒ 輸出看起來一切正常，資料一筆都沒進。

   ⚠️ 這個失敗沒有任何訊號：
      · 腳本 exit code 0（錯誤被 Python 吃掉前已 print）
      · 總筆數有增加（其他縣市成功了）
      · 驗證器 33/33 全綠（它驗的是「已有資料的品質」，
        不是「該有的資料在不在」）

🔴 判準：**來源有幾筆，庫裡就該有幾筆**。差一筆都要報。

跑法：python3 scripts/verify_import_completeness.py
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

import psycopg2

sys.path.insert(0, str(Path(__file__).parent))
from import_county_opendata import SOURCES, fetch, pick  # noqa: E402


def main() -> int:
    conn = psycopg2.connect(dbname="welfare_check")
    cur = conn.cursor()

    fails: list[str] = []
    unreachable: list[str] = []

    print("=== 每個來源：抓到幾筆 vs 真的進庫幾筆 ===\n")
    for key, src in SOURCES.items():
        county = src.get("county", key)
        try:
            rows = fetch(src["url"])
        except Exception as e:                        # noqa: BLE001
            # 🔴 抓不到 ≠ 匯入失敗 —— 來源網站可能暫時掛了。
            #    分開報，不可混為一談（否則會去「修」一個沒壞的東西）。
            unreachable.append(f"{key}：{str(e)[:60]}")
            print(f"  ⚠️ {key:<18} 來源暫時抓不到（非匯入失敗）")
            continue

        names = {re.sub(r"\s+", "", pick(r, "name"))
                 for r in rows if pick(r, "name")}
        cur.execute("SELECT name FROM benefits WHERE county = %s", (county,))
        have = {re.sub(r"\s+", "", n) for (n,) in cur.fetchall()}
        missing = names - have

        mark = "✅" if not missing else "🔴"
        print(f"  {mark} {key:<18} 來源 {len(names):>3}　"
              f"已入庫 {len(names) - len(missing):>3}　缺 {len(missing)}")
        if missing:
            fails.append(f"{key} 缺 {len(missing)} 筆")
            for m in list(missing)[:4]:
                print(f"       · {m[:40]}")

    print("\n" + "=" * 46)
    if unreachable:
        print(f"⚠️ {len(unreachable)} 個來源暫時抓不到（不算失敗）：")
        for u in unreachable:
            print(f"   {u}")
    if fails:
        print(f"🔴 {len(fails)} 個來源有缺漏：")
        for f in fails:
            print(f"   {f}")
        return 1
    print(f"✅ {len(SOURCES) - len(unreachable)} 個來源全部零缺漏")
    return 0


if __name__ == "__main__":
    sys.exit(main())
