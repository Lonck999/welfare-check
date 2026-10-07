#!/usr/bin/env python3
"""回歸：opendata 匯入的 `link` 別名，逐筆網址必須贏過機關首頁。

🔴 為什麼要有這支（2026-10-07，W-009）：
`ALIAS["link"]` 原本漏了 `sourceUrl`，於是桃園 26 筆全部 fallback 到
`competentAuthorityUrl`（局處首頁）—— **不報錯，只是來源變成首頁**，
而 `source_tier` 仍是 `official` ⇒ 「沒來源卻掛官方認證」27 筆。

這支測三件事：
 ① `sourceUrl` 必須在別名清單裡
 ② 兩個欄位都有值時，`pick()` 必須回逐筆那個（**順序**）
 ③ 只有首頁欄位時仍要回首頁（不可因為①②而退化成空）

🔴 negative control：把別名順序改回舊版 ⇒ ②必須變紅。
（只測「現在是對的」會讓「順序被改掉」這個真 bug 完全通過。）
"""
from __future__ import annotations

import importlib.util
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
TARGET = os.path.join(HERE, "import_county_opendata.py")

# 🔴 先刪 .pyc：還原後的 mtime 可能與植入版 bytecode 相符
_pyc = os.path.join(HERE, "__pycache__")
if os.path.isdir(_pyc):
    for f in os.listdir(_pyc):
        if f.startswith("import_county_opendata"):
            os.remove(os.path.join(_pyc, f))


def load():
    spec = importlib.util.spec_from_file_location("_icd", TARGET)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


HOME = "https://lhrb.tycg.gov.tw/"
ITEM = ("https://e-services.tycg.gov.tw/eservice/app/customize/"
        "item/detail?item_no=W0199")

CASES = [
    # (說明, row, 期望)
    ("兩個都有值 → 必須取逐筆申辦頁",
     {"sourceUrl": ITEM, "competentAuthorityUrl": HOME}, ITEM),
    ("只有首頁欄位 → 仍回首頁（不可變空）",
     {"competentAuthorityUrl": HOME}, HOME),
    ("只有逐筆 → 回逐筆",
     {"sourceUrl": ITEM}, ITEM),
    ("逐筆是空白字串 → 退回首頁",
     {"sourceUrl": "   ", "competentAuthorityUrl": HOME}, HOME),
    ("中文欄位優先於兩者（既有行為不可被破壞）",
     {"詳細資訊網址": "https://example.tw/a", "sourceUrl": ITEM,
      "competentAuthorityUrl": HOME}, "https://example.tw/a"),
    ("兩者皆無 → 空字串",
     {"policyName": "x"}, ""),
]


def main() -> int:
    m = load()
    fails: list[str] = []

    alias = m.ALIAS["link"]
    if "sourceUrl" not in alias:
        fails.append("① `sourceUrl` 不在 ALIAS['link'] 裡")
    elif "competentAuthorityUrl" in alias and \
            alias.index("sourceUrl") > alias.index("competentAuthorityUrl"):
        fails.append("① `sourceUrl` 排在 `competentAuthorityUrl` 之後"
                     "（首頁會贏，等於 W-009 復活）")

    for desc, row, want in CASES:
        got = m.pick(row, "link")
        if got != want:
            fails.append(f"② {desc}：得到 {got!r} 期望 {want!r}")

    total = 1 + len(CASES)
    print(f"{total - len(fails)}/{total} 通過")
    for f in fails:
        print("  ❌", f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
