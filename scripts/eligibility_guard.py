#!/usr/bin/env python3
"""匯入／寫入 benefits 前的資格條件守門（C-6b ③，2026-11-19）。

🔴 **這支的存在理由**：過去的匯入程式把 `eligibility_conditions` 填成
`{"counties": [...], "_note": "資格條件見官方頁"}` 就寫進庫（`import_directory_items.py`
的註解當年甚至明文寫「eligibility_conditions 只填 counties + _note」），
製造了 **241 筆沒有任何實質條件的列**。那種列在引擎裡會被
`hasUnsortedConditions()` 判成 possible ＋「資格條件尚未整理（請見官方頁）」——
也就是對任何人都顯示、誰都篩不掉。那 241 筆已逐筆補完（全庫啟用中只剩 2 筆），
**這支負責讓它不會再長回來**。

🔴 **判準完全照抄** `backend/src/logic/eligibility.ts`：
  · `hasUnsortedConditions()`　eligibility.ts:338-344
  · `ENGINE_CHECKED_KEYS`　　 eligibility.ts:347-352
TS 用的是**白名單**（只認引擎真的會 check 的鍵），不是「排除 counties／
referenceData／`_` 開頭」的黑名單 —— 白名單本來就把 `counties`、`referenceData`、
`_note` 這些排除在外，所以不需要另寫前綴規則；
⚠️ 反過來說，**新增一種條件鍵時只加在 DB 裡不夠**，要同步加進 TS 的
`ENGINE_CHECKED_KEYS`（否則引擎永遠看不到它，而且不會報錯），
這支的清單也要跟著改 —— `test_eligibility_guard.py` 會逐字比對兩邊，不一致就紅。

用法：
    from eligibility_guard import assert_substantive
    assert_substantive(elig, label=f"{county}｜{name}")   # 不合格 → raise ValueError
"""

from __future__ import annotations

from typing import Any

# 🔴 照抄 backend/src/logic/eligibility.ts:347-352 的 ENGINE_CHECKED_KEYS。
#    TS 那邊的註解：「引擎真的會拿來判斷的鍵（新增 check 時要同步加進來，
#    否則那個條件的項目會被當成未整理 → 最高 possible）」
#    ⚠️ TS 刻意**不含** minResidencyMonths／requiredGender：只有設籍或性別
#       的項目仍算「條件未整理」（只寫「設籍滿 1 年」不代表人人可領）。
#       這裡也不可自己加 —— 加了就跟引擎對不上，守門放行而引擎照樣判 possible。
ENGINE_CHECKED_KEYS: frozenset[str] = frozenset({
    "ageMin", "ageMax", "incomeThreshold", "maxPerCapitaAssets", "requiredIdentities",
    "requiresChildUnder", "requiresElderOver", "requiresNoOwnedHome", "requiresOwnedHome",
    "requiredFlags", "uncheckedConditions",
})

# eligibility.ts:339 —— `conditions.openToAll === true` 時直接算整理過
OPEN_TO_ALL_KEY = "openToAll"


def is_substantive(cond: dict[str, Any] | None) -> bool:
    """這份條件在引擎眼中「有實質條件」嗎？（= not hasUnsortedConditions）

    對應 eligibility.ts:338-344：
        if (conditions.openToAll === true) return false
        return !Object.keys(conditions).some((k) => ENGINE_CHECKED_KEYS.has(k))
    """
    if not isinstance(cond, dict):
        return False                       # None／非 dict：連 JSONB 物件都不是
    if cond.get(OPEN_TO_ALL_KEY) is True:  # 🔴 必須是 True 本身，不是 truthy
        return True
    return any(k in ENGINE_CHECKED_KEYS for k in cond)


def assert_substantive(cond: dict[str, Any] | None, *, label: str) -> None:
    """不合格就 raise ValueError（訊息含 label 與現有鍵），讓那一批整批炸掉。

    🔴 刻意 raise 而不是 print 警告再寫下去 —— 警告會被捲走，
       而「只有 counties 的列」在使用者端的症狀跟正常資料長得一樣。
    """
    # 透過模組全域名稱呼叫，才能在測試裡 monkeypatch 成「永遠通過」做負向控制
    if is_substantive(cond):
        return
    keys = sorted(cond.keys()) if isinstance(cond, dict) else None
    raise ValueError(
        f"🔴 資格條件沒有任何引擎認得的條件鍵，拒絕寫入：{label}\n"
        f"   現有鍵：{keys if keys else cond!r}\n"
        f"   引擎認得的鍵（eligibility.ts ENGINE_CHECKED_KEYS）：{sorted(ENGINE_CHECKED_KEYS)}\n"
        f"   或明確標 {OPEN_TO_ALL_KEY}=True（真的人人可領）；"
        f"抓不到條件原文時用 uncheckedConditions=[\"原文…\"]，不要只填 counties。"
    )
