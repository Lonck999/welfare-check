#!/usr/bin/env python3
"""回歸：偵測「原始資料有網址欄位但匯入沒用到」—— 判準測試（離線）。

🔴 為什麼不直接跑 `scan_opendata_unused_link_fields.py`：
那支要連 12 個政府網站（實測 126 秒），而且會因對方掛掉而紅
—— 那時紅的理由跟它要測的事無關（§ scripts/AGENTS.md「別把當下的資料
狀態寫進斷言」）。這支用**假 row** 測判準本身。

測的是 `ALIAS["link"]` 對三種真實存在的欄位寫法都有效：
 ① 臺南 `詳細資訊[連結]`（有方括號）
 ② 臺中 `詳細資訊連結`（無方括號）／`相關資訊連結`／`網址`
 ③ 桃園 `sourceUrl` 必須贏過 `competentAuthorityUrl`（W-009）

🔴 negative control（三道，缺任一就測不出真 bug）：
 ① 移掉臺中那三個別名 ⇒ 它們必須變紅（＝W-010 復活）
 ② 把 `sourceUrl` 移到首頁欄位之後 ⇒ 順序案例必須變紅（＝W-009 復活）
 ③ 清空整個 `link` 別名 ⇒ 全部必須變紅（擋「判準整支失效」）
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
    spec = importlib.util.spec_from_file_location("_icd_alias", TARGET)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


ITEM = "https://e-services.tycg.gov.tw/eservice/app/customize/item/detail?item_no=W0199"
HOME = "https://lhrb.tycg.gov.tw/"
TC_SOC = "https://www.society.taichung.gov.tw/461550/post"
TC_IPD = "https://www.ipd.taichung.gov.tw/323054/post"
TN = "http://social.tainan.gov.tw/social/cenpage.asp?id={ABC}"

# (說明, row, 期望)　—— 每個欄位寫法各有一筆**只命中它自己**的案例
CASES = [
    ("臺南 `詳細資訊[連結]`（方括號）", {"詳細資訊[連結]": TN}, TN),
    ("臺中 `詳細資訊連結`（無方括號，W-010）",
     {"詳細資訊連結": TC_SOC}, TC_SOC),
    ("臺中 `相關資訊連結`（W-010）", {"相關資訊連結": TC_SOC}, TC_SOC),
    ("臺中 `網址`（W-010）", {"網址": TC_IPD}, TC_IPD),
    ("桃園 兩個都有 → 逐筆贏（W-009）",
     {"sourceUrl": ITEM, "competentAuthorityUrl": HOME}, ITEM),
    ("只有首頁欄位 → 仍回首頁（不可退化成空）",
     {"competentAuthorityUrl": HOME}, HOME),
    ("空白字串不算有值 → 退回首頁",
     {"sourceUrl": "   ", "competentAuthorityUrl": HOME}, HOME),
    ("都沒有 → 空字串", {"policyName": "x"}, ""),
]

W010_FIELDS = ("詳細資訊連結", "相關資訊連結", "網址")


def run(m) -> list[str]:
    fails = []
    for desc, row, want in CASES:
        got = m.pick(row, "link")
        if got != want:
            fails.append(f"{desc}：得到 {got!r} 期望 {want!r}")
    return fails


def main() -> int:
    m = load()
    fails = run(m)
    total = len(CASES)
    print(f"{total - len(fails)}/{total} 通過")
    for f in fails:
        print("  ❌", f)
    if fails:
        return 1

    # ── negative control：在記憶體裡動 ALIAS，不改檔案 ──
    print("\nnegative control：")
    orig = m.ALIAS["link"]

    m.ALIAS["link"] = tuple(k for k in orig if k not in W010_FIELDS)
    nc1 = run(m)
    hit1 = [f for f in nc1 if "W-010" in f]
    print(f"  ① 移掉臺中三個別名 → {len(nc1)} 項失敗"
          f"（其中 W-010 相關 {len(hit1)}/3）")
    assert len(hit1) == 3, "🔴 NC① 移掉別名後臺中案例竟然還過 —— 判準無鑑別力"

    m.ALIAS["link"] = tuple(
        [k for k in orig if k != "sourceUrl"] + ["sourceUrl"])
    nc2 = run(m)
    hit2 = [f for f in nc2 if "W-009" in f]
    print(f"  ② sourceUrl 移到首頁之後 → W-009 案例失敗 {len(hit2)}/1")
    assert len(hit2) == 1, "🔴 NC② 順序被改掉竟然沒變紅"

    m.ALIAS["link"] = ()
    nc3 = run(m)
    # 「都沒有 → 空字串」那筆本來就期望空，清空別名後它仍會過
    print(f"  ③ 清空整個 link 別名 → {len(nc3)}/{total - 1} 個有期望值的案例失敗")
    assert len(nc3) == total - 1, \
        f"🔴 NC③ 別名全空竟只有 {len(nc3)} 項失敗 —— 判準整支失效也測不出來"

    m.ALIAS["link"] = orig
    assert not run(m), "🔴 還原後竟不是全綠 —— NC 汙染了狀態"
    print("  還原 → 全綠 ✅")
    return 0


if __name__ == "__main__":
    sys.exit(main())
