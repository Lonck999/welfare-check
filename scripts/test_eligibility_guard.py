#!/usr/bin/env python3
"""eligibility_guard 的回歸測試（純 Python，🔴 不連資料庫）。

執行：python3 scripts/test_eligibility_guard.py

三件事：
  ① 合格／不合格案例（每個合格訊號各有一筆**只命中它自己**的案例）
  ② 🔴 負向控制：把判準換成「永遠通過」時，不合格案例的斷言**必須失敗** ——
     否則這組測試在守門整個壞掉時仍然全綠（那就等於沒驗）
  ③ 🔴 一致性：Python 的 ENGINE_CHECKED_KEYS 必須跟 eligibility.ts 的逐字相同
     （直接讀 TS 原始碼比對字串，不需要 node/tsx）
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import eligibility_guard as G  # noqa: E402

TS_PATH = Path(__file__).resolve().parent.parent / "backend/src/logic/eligibility.ts"

# ── 案例 ──────────────────────────────────────────────────────────
# 🔴 每個合格案例只命中一個訊號（CLAUDE.md：「測試案例不可同時命中兩個訊號」——
#    同時有 ageMin 又有 requiredFlags 的案例，白名單少一個鍵也照樣綠）
OK_CASES = [
    ("只有 ageMin", {"counties": ["臺北市"], "ageMin": 65}),
    ("只有 uncheckedConditions", {"counties": ["全國"],
                                  "uncheckedConditions": ["須經社工評估"]}),
    ("只有 openToAll:true", {"counties": ["全國"], "openToAll": True}),
]

BAD_CASES = [
    ("None", None),
    ("空物件", {}),
    ("只有 counties", {"counties": ["苗栗縣"]}),
    ("counties + _note", {"counties": ["彰化縣"],
                          "_note": "資格條件待從官方頁面補齊"}),
    ("counties + referenceData", {"counties": ["全國"],
                                  "referenceData": {"table": "跨縣市對照表"}}),
]


def check_ok_cases() -> list[str]:
    """合格案例：assert_substantive 不可 raise。"""
    fails = []
    for label, cond in OK_CASES:
        try:
            G.assert_substantive(cond, label=label)
        except ValueError as e:
            fails.append(f"合格案例被擋下：{label} —— {e}")
    return fails


def check_bad_cases() -> list[str]:
    """🔴 不合格案例：assert_substantive **必須** raise ValueError，訊息要含 label。

    這個函式被呼叫兩次：正常模式（期待 0 個 fail）與負向控制模式
    （把判準換成永遠通過，期待 len(BAD_CASES) 個 fail）。
    """
    fails = []
    for label, cond in BAD_CASES:
        try:
            G.assert_substantive(cond, label=label)
        except ValueError as e:
            msg = str(e)
            if label not in msg:
                fails.append(f"擋下了但訊息沒有 label：{label} —— {msg}")
            if isinstance(cond, dict) and cond and not all(k in msg for k in cond):
                fails.append(f"擋下了但訊息沒列出現有鍵：{label} —— {msg}")
            continue
        fails.append(f"🔴 不合格案例被放行：{label}（{cond!r}）")
    return fails


def self_check_negative_control() -> list[str]:
    """🔴 負向控制：把判準替成「永遠通過」，check_bad_cases() 必須全數失敗。

    不做這一步的話，「assert_substantive 其實沒在擋」跟「資料都合格」
    在測試輸出裡長得一模一樣（都是綠的）。
    """
    fails = []
    original = G.is_substantive
    try:
        G.is_substantive = lambda cond: True          # 植入：永遠通過
        broken = check_bad_cases()
        if len(broken) != len(BAD_CASES):
            fails.append(
                f"🔴 負向控制沒達成：判準換成永遠通過後，{len(BAD_CASES)} 個不合格案例"
                f"只有 {len(broken)} 個被測出來 ⇒ 這組測試沒有鑑別力"
            )
        # 反方向：還原後必須靜默（植入必須報 → 還原必須不報，兩個方向都測）
    finally:
        G.is_substantive = original
    restored = check_bad_cases()
    if restored:
        fails.append(f"🔴 還原判準後仍有 fail：{restored}")
    return fails


def parse_ts_whitelist() -> set[str]:
    """從 eligibility.ts 撈出 ENGINE_CHECKED_KEYS 的字串字面值。"""
    src = TS_PATH.read_text(encoding="utf-8")
    m = re.search(r"const ENGINE_CHECKED_KEYS = new Set\(\[(.*?)\]\)", src, re.S)
    if not m:
        raise AssertionError(f"🔴 在 {TS_PATH} 找不到 ENGINE_CHECKED_KEYS 的宣告")
    body = re.sub(r"//[^\n]*", "", m.group(1))        # 先剝掉 // 註解，否則註解裡的字會被當成鍵
    return {a or b for a, b in re.findall(r"'([^']+)'|\"([^\"]+)\"", body)}


def check_ts_consistency() -> list[str]:
    """🔴 Python 白名單必須與 TS 逐字一致，且 openToAll 的提早 return 還在。"""
    fails = []
    ts_keys = parse_ts_whitelist()
    py_keys = set(G.ENGINE_CHECKED_KEYS)
    if ts_keys != py_keys:
        fails.append(
            f"🔴 白名單與 eligibility.ts 不一致：\n"
            f"   只在 TS：{sorted(ts_keys - py_keys)}\n"
            f"   只在 Python：{sorted(py_keys - ts_keys)}"
        )
    src = TS_PATH.read_text(encoding="utf-8")
    if "conditions.openToAll === true" not in src:
        fails.append("🔴 eligibility.ts 的 openToAll 提早 return 不見了 ⇒ 判準已變，守門要跟著改")
    if "ENGINE_CHECKED_KEYS.has(k)" not in src:
        fails.append("🔴 eligibility.ts 的 hasUnsortedConditions 不再用白名單 ⇒ 判準已變")
    return fails


def main() -> int:
    groups = [
        ("合格案例不可被擋", check_ok_cases),
        ("不合格案例必須被擋（含訊息內容）", check_bad_cases),
        ("負向控制：判準失效時測試必須變紅", self_check_negative_control),
        ("與 eligibility.ts 白名單一致", check_ts_consistency),
    ]
    all_fails = []
    for name, fn in groups:
        fails = fn()
        print(f"{'✅' if not fails else '❌'} {name}"
              f"（{len(OK_CASES) if fn is check_ok_cases else len(BAD_CASES) if fn is check_bad_cases else 1} 項）")
        for f in fails:
            print(f"    {f}")
        all_fails += fails
    print(f"\n案例：合格 {len(OK_CASES)} 筆、不合格 {len(BAD_CASES)} 筆；"
          f"TS 白名單 {len(parse_ts_whitelist())} 鍵（來源 {TS_PATH.name}）")
    if all_fails:
        print(f"🔴 FAIL {len(all_fails)} 項")
        return 1
    print("✅ 全綠")
    return 0


if __name__ == "__main__":
    sys.exit(main())
