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
        # 🔴 **刻意不濾 `is_active`** —— 這支比「來源有的 vs 庫裡有的」。
        #    停用但保留的筆仍代表「已匯入過」；濾掉會報成 missing，
        #    而下一步就是去重抓一次（判準見 `active_scope.py`）。
        have = {re.sub(r"\s+", "", n) for (n,) in cur.fetchall()}
        missing = names - have
        # 🔴 2026-11-04：已進「新福利候選」待審／已駁回的不算靜默漏掉 ——
        #    這支要抓的是「匯入失敗而沒人知道」（9/25 rollback 那種），
        #    而候選佇列裡的那幾筆是**已知、等人工決定**。
        #    不分開的話：每次月更寫入候選，這支就紅到有人核准為止（10-21 起天天紅），
        #    真正的靜默漏掉會混在裡面看不出來。
        #    ⚠️ 只有「名字在 benefit_change_log new_candidate 裡」才放行，不是放寬判準。
        cur.execute("""SELECT new_value, approved_at IS NOT NULL, rejected_at IS NOT NULL
                       FROM benefit_change_log
                       WHERE change_type = 'new_candidate' AND new_value LIKE %s""",
                    (f"{county}｜%",))
        queued = {re.sub(r"\s+", "", v.split("｜", 1)[1]): ("核准未入庫" if a else "已駁回" if rj else "待審")
                  for v, a, rj in cur.fetchall() if "｜" in v}
        known = {m: queued[m] for m in missing if m in queued and queued[m] != "核准未入庫"}
        missing = missing - set(known)

        mark = "✅" if not missing else "🔴"
        print(f"  {mark} {key:<18} 來源 {len(names):>3}　"
              f"已入庫 {len(names) - len(missing) - len(known):>3}　缺 {len(missing)}"
              + (f"　⏳ 候選 {len(known)}" if known else ""))
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
