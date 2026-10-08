#!/usr/bin/env python3
"""回歸：偵測器／填值器的範圍必須等於「使用者看得到什麼」（is_active）。

🔴 起因（2026-10-08，W-010）：id 34 拆成三筆後標 `is_active=false`
（刻意保留不刪 —— 刪了月更會把它當新缺口再抓一次），
但多支偵測器仍把它算進結果 ⇒ 看起來「修了卻沒變少」。

🔴 三類腳本的要求相反，所以這支**兩個方向都測**：
 ① 偵測器／填值器 → 必須有 `--include-inactive`，且預設**不含**停用筆
 ② 月更比對／完整性稽核 → 必須**沒有**那個旗標，且程式裡有「刻意不濾」的註解
 ③ 指定 id 的修復腳本 → 不適用，不列入

⚠️ 這支只驗**介面與靜態結構**（不連資料庫）：
- `--help` 裡有沒有旗標
- SQL 字串有沒有用到 `scope_sql`／`scope_where`
🔴 「有旗標」不等於「真的生效」—— 行為驗證在 `verify_active_scope_behavior`
（要資料庫，見下面 main 裡的 `--with-db`）。
"""
from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
PY = sys.executable

# ① 必須濾（偵測器／填值器）
MUST_FILTER = [
    "backfill_deadline_type.py",
    "derive_applicants.py",
    "extract_amounts_from_desc.py",
    "fetch_local_benefit.py",
    "fill_effort_level.py",
    "scan_amount_vs_threshold.py",
    "rescan_description_substance.py",
    "refetch_empty_shells.py",
    "scan_homepage_as_source.py",
]

# ② 不可濾（月更比對／完整性稽核）—— 必須有「刻意不濾」的註解
MUST_NOT_FILTER = {
    "gap_vs_mohw_table.py": "刻意不濾",
    "verify_import_completeness.py": "刻意不濾",
}


def has_flag(script: str) -> bool:
    """🔴 用靜態檢查不跑 `--help`。

    ⚠️ 沒有 argparse 的腳本（如 `verify_import_completeness.py`）
    看到 `--help` 不會印用法，而是**直接開始抓 12 個政府網站** ——
    第一版就這樣逾時（60 秒不夠而且理由跟它要測的事無關）。
    """
    t = (HERE / script).read_text(encoding="utf-8")
    return "--include-inactive" in t or "add_scope_arg" in t


def uses_scope_helper(script: str) -> bool:
    t = (HERE / script).read_text(encoding="utf-8")
    # scan_homepage_as_source 比 active_scope 更早寫，用自己的寫法
    return bool(re.search(r"scope_sql\(|scope_where\(|AND is_active", t))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--with-db", action="store_true",
                    help="連資料庫跑行為驗證（預設只驗介面）")
    args = ap.parse_args()

    fails: list[str] = []
    checks = 0

    print("── ① 偵測器／填值器：必須有旗標且用到範圍判準 ──")
    for s in MUST_FILTER:
        if not (HERE / s).exists():
            fails.append(f"① {s} 不存在（清單過期？）")
            checks += 1
            continue
        checks += 2
        if not has_flag(s):
            fails.append(f"① {s} 的 --help 沒有 --include-inactive")
        if not uses_scope_helper(s):
            fails.append(f"① {s} 沒有用到 scope_sql/scope_where/AND is_active"
                         f"（旗標存在但可能沒生效）")
        print(f"  {'✅' if has_flag(s) and uses_scope_helper(s) else '❌'} {s}")

    print("\n── ② 月更比對：不可有旗標，且要有「刻意不濾」註解 ──")
    for s, mark in MUST_NOT_FILTER.items():
        checks += 2
        t = (HERE / s).read_text(encoding="utf-8")
        if has_flag(s):
            fails.append(f"② {s} 竟有 --include-inactive —— "
                         f"月更比對濾掉停用筆會把它報成新缺口")
        if mark not in t:
            fails.append(f"② {s} 缺少「{mark}」註解 —— "
                         f"下一個人會以為是忘了濾而加上去")
        print(f"  {'✅' if not has_flag(s) and mark in t else '❌'} {s}")

    # 🔴 negative control：確認判準真的有鑑別力
    print("\n── negative control ──")
    checks += 2
    # NC①：月更型腳本若長出旗標，② 的判準必須抓到（已在上面迴圈驗過）
    #   ⚠️ 這裡不可寫 `assert not has_flag(...)` —— 植入「給月更加旗標」時
    #   那個 assert 會先炸，訊息變成「NC 前提壞了」而不是真正的原因
    #   （實測：植入② 時只看到 AssertionError，看不到該報的那條 ❌）。
    gap_flagged = [s for s in MUST_NOT_FILTER if has_flag(s)]
    print(f"  NC① 月更型腳本帶旗標的：{len(gap_flagged)} 支"
          f"（應為 0，② 的判準會抓到）{'✅' if not gap_flagged else '❌'}")
    if gap_flagged:
        fails.append(f"NC① 月更型腳本竟有旗標：{gap_flagged}")
    # NC②：active_scope 的兩個函式語意不可互換
    sys.path.insert(0, str(HERE))
    import active_scope as sc
    ns_off = argparse.Namespace(include_inactive=False)
    ns_on = argparse.Namespace(include_inactive=True)
    assert sc.scope_sql(ns_off).strip().startswith("AND"), \
        "🔴 scope_sql 必須帶 AND（接在既有條件後）"
    assert sc.scope_where(ns_off).strip().startswith("WHERE"), \
        "🔴 scope_where 必須帶 WHERE（SQL 還沒有條件時）"
    assert sc.scope_sql(ns_on) == "" and sc.scope_where(ns_on) == "", \
        "🔴 --include-inactive 時必須完全不加條件"
    assert sc.scope_label(ns_off) != sc.scope_label(ns_on), \
        "🔴 兩種範圍的標籤必須不同，否則輸出看不出範圍"
    print("  NC② scope_sql/scope_where 語意不可互換 ✅")

    if args.with_db:
        print("\n── 行為驗證（連資料庫）──")
        checks += 2
        import json
        out = Path("/tmp/wc_backup/substance_rescan.json")
        for flag, want_34 in ((None, False), ("--include-inactive", True)):
            cmd = [PY, str(HERE / "rescan_description_substance.py")]
            if flag:
                cmd.append(flag)
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
            if r.returncode not in (0, 1):
                fails.append(f"行為驗證：{flag or '預設'} rc={r.returncode}")
                continue
            recs = json.loads(out.read_text())
            got = any(x["id"] == 34 for x in recs)
            ok = got == want_34
            if not ok:
                fails.append(f"行為驗證：{flag or '預設'} 時 id34 在結果裡="
                             f"{got}，期望 {want_34}")
            print(f"  {'✅' if ok else '❌'} {flag or '預設'}："
                  f"id34 {'在' if got else '不在'}結果裡（{len(recs)} 筆）")

    print(f"\n{checks - len(fails)}/{checks} 通過")
    for f in fails:
        print("  ❌", f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
