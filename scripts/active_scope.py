#!/usr/bin/env python3
"""共用：`is_active` 範圍判準（偵測器的範圍要跟「使用者看得到什麼」一致）。

🔴 起因（2026-10-08，W-010）：id 34 拆成三筆後標 `is_active=false`
（**刻意保留不刪** —— 刪掉月更比對會把它當新缺口再抓一次），
但多支偵測器仍把它算進結果 ⇒ 看起來「修了卻沒變少」。
**報一筆不會被使用者看到的資料，只會讓人去修一個不影響任何人的東西。**

🔴 判準分三類，不可一律套用（`grep -c is_active == 0` 不是判準）：

| 類型 | 要不要濾 | 為什麼 |
|---|---|---|
| **偵測器／填值器**（找出有問題的資料、補欄位） | ✅ **濾** | 範圍要等於使用者看得到的 |
| **月更比對／完整性稽核**（來源 vs 庫裡有沒有） | 🔴 **不可濾** | 濾掉停用筆 ⇒ 誤報 missing ⇒ **月更會把它當新缺口再抓一次**，那正是當初保留它的理由 |
| **指定 id 的修復腳本** | ⬜ 不適用 | 範圍已由 id 決定 |

用法（偵測器／填值器）：

```python
from active_scope import add_scope_arg, scope_sql, scope_label

ap = argparse.ArgumentParser()
add_scope_arg(ap)
args = ap.parse_args()

cur.execute(f"SELECT ... FROM benefits WHERE foo {scope_sql(args)}")
print(f"共 N 筆（{scope_label(args)}）")
```

🔴 `scope_sql()` 回傳的是 **` AND is_active`**（前面帶 AND）——
所以呼叫端的 WHERE 必須已經有條件。沒有條件時用 `scope_where(args)`。
⚠️ 兩個函式刻意分開：合成一個「自己判斷要不要加 AND」的版本，
會在 SQL 長得稍微不一樣時默默產生語法錯或**條件被吃掉**。
"""
from __future__ import annotations

import argparse

FLAG = "--include-inactive"
HELP = "連已停用（is_active=false）的也算（查歷史用，預設不算）"


def add_scope_arg(ap: argparse.ArgumentParser) -> None:
    ap.add_argument(FLAG, action="store_true", help=HELP)


def include_inactive(args: argparse.Namespace) -> bool:
    return bool(getattr(args, "include_inactive", False))


def scope_sql(args: argparse.Namespace) -> str:
    """接在既有 WHERE 條件後面（回傳值前面帶 AND，或空字串）。"""
    return "" if include_inactive(args) else " AND is_active"


def scope_where(args: argparse.Namespace) -> str:
    """當 SQL 還沒有 WHERE 時用（回傳 `WHERE is_active`，或空字串）。"""
    return "" if include_inactive(args) else " WHERE is_active"


def scope_label(args: argparse.Namespace) -> str:
    return "含已停用" if include_inactive(args) else "僅生效中"
