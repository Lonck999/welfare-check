#!/usr/bin/env python3
"""驗證機關清單的正確性與「存在證明」完整性。

🔴 為什麼需要這支：2026-09-24 第一版的錯誤是
   **文件數字與 JSON 內容對不起來、welfare_hint 全 0**
   —— 兩邊都「看起來正常」，只有比對才發現。

用法：python scripts/verify_gov_agencies.py
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
DOC = HERE.parent / "福利發放單位清查.md"

ok = fail = 0


def check(label: str, cond: bool, detail: str = "") -> None:
    global ok, fail
    if cond:
        ok += 1
        print(f"  ✅ {label}")
    else:
        fail += 1
        print(f"  🔴 {label}　{detail}")


def main() -> int:
    gov = json.loads((HERE / "gov_agencies.json").read_text())
    ngo = json.loads((HERE / "ngo_welfare_orgs.json").read_text())
    doc = DOC.read_text()
    b = gov["buckets"]

    print("① 分類結果符合官方定義")
    check("中央二級 = 35（15部+9會+3獨立+主計/人事/央行/故宮+省府等）",
          len(b["central2"]) == 35, f"實際 {len(b['central2'])}")
    check("縣市政府 = 22", len(b["local_gov"]) == 22,
          f"實際 {len(b['local_gov'])}")
    check("二級全部直屬行政院",
          all(x["parent"] == "行政院" for x in b["central2"]))
    check("三級直屬部會的 parent 以 部/委員會/總處/總署 結尾",
          all(x["parent"].endswith(("部", "委員會", "總處", "總署"))
              for x in b["central3_top"]))

    print("\n② 🔴 已裁撤機關不可出現（第一版用維基 regex 撈到一堆）")
    allnames = {x["name"] for v in b.values() for x in v}
    for dead in ("內政部兒童局", "行政院衛生署", "交通部電信總局",
                 "行政院勞工委員會", "行政院青年輔導委員會"):
        check(f"不含已裁撤「{dead}」", dead not in allnames)
    check("排除筆數有記錄且 > 0",
          gov["_meta"]["dropped_dissolved"] > 0)

    print("\n③ 🔴 非行政院體系不可出現（第一版 central2=78 的原因）")
    for bad in ("世新大學", "中華郵政股份有限公司", "南投縣議會",
                "中央研究院", "國史館"):
        check(f"不含「{bad}」", bad not in allnames)
    check("無任何名稱以 大學/議會/公司 結尾",
          not [n for n in allnames
               if re.search(r"(大學|議會|公司|銀行|醫院)$", n)])

    print("\n④ 存在證明（使用者要求：能證明它真的存在）")
    flat = [x for v in b.values() for x in v]
    withcode = [x for x in flat if x["evidence"]["org_code"]]
    withaddr = [x for x in flat if x["evidence"]["address"]]
    check(f"全部 {len(flat)} 筆都有機關代碼", len(withcode) == len(flat),
          f"缺 {len(flat) - len(withcode)}")
    check("有地址的 ≥ 99%", len(withaddr) / len(flat) >= 0.99,
          f"{len(withaddr)}/{len(flat)}")
    check("每筆 evidence 都帶 source_url",
          all(x["evidence"].get("source_url") for x in flat))
    check("機關代碼格式正確（10 碼英數）",
          all(re.fullmatch(r"[A-Z0-9]{10}", x["evidence"]["org_code"])
              for x in withcode))

    print("\n⑤ 🔴 welfare_hint 必須真的有作用（第一版全是 0）")
    hint_n = sum(1 for x in flat if x["welfare_hint"])
    check("hint 數量 > 0", hint_n > 0, f"實際 {hint_n}")
    check("hint 不是全部（否則等於沒篩）", hint_n < len(flat))
    check("衛福部社會及家庭署 hint=True",
          any(x["name"] == "衛生福利部社會及家庭署" and x["welfare_hint"]
              for x in flat))
    # 🔴 negative control：hint 不可靠這件事必須是真的
    energy = [x for x in flat if x["name"] == "經濟部能源署"]
    check("經濟部能源署存在", bool(energy))
    check("🔴 能源署 hint=False（證明 hint 會漏掉真的發補助的機關）",
          bool(energy) and not energy[0]["welfare_hint"],
          "若這條變綠代表 hint 改過，文件的警告要一起更新")

    print("\n⑥ 實際發過補助的機關都在 central3_top")
    top = {x["name"] for x in b["central3_top"]}
    for a in ("勞動部勞動力發展署", "勞動部勞工保險局",
              "衛生福利部國民健康署", "衛生福利部社會及家庭署",
              "衛生福利部中央健康保險署", "經濟部能源署"):
        check(f"{a}", a in top)

    print("\n⑦ 民間單位清單完整")
    orgs = ngo["ngo_from_mohw_pdf"]
    check("21 筆", len(orgs) == 21, f"實際 {len(orgs)}")
    check("項次 1~21 連續無缺",
          sorted(x["idx"] for x in orgs) == list(range(1, 22)))
    check("🔴 無幽靈機構（地址欄誤判產生的）",
          not [x for x in orgs if x["org"].startswith("樓")])
    check("名稱無重複", len({x["org"] for x in orgs}) == len(orgs))
    check("每筆都有 source_url",
          all(x.get("source_url") for x in orgs))
    check("慈濟在清單裡（第一版被表頭吃掉）",
          any("慈濟" in x["org"] for x in orgs))
    check("萬海名稱完整（非斷行殘片）",
          any(x["org"] == "財團法人萬海航運社會福利慈善事業基金會"
              for x in orgs))

    print("\n⑧ 🔴 文件數字必須與 JSON 一致（第一版就是這裡錯）")
    for label, n in (("中央二級", len(b["central2"])),
                     ("三級直屬部會", len(b["central3_top"])),
                     ("地方一級局處", len(b["local_dept"])),
                     ("民間單位", len(orgs))):
        check(f"文件提到 {label} = {n}", f"**{n}**" in doc or f"| {n} |" in doc,
              "文件與 JSON 對不起來 —— 重跑腳本並更新文件")
    total = sum(len(v) for v in b.values())
    check(f"文件合計 = {total}", f"**{total:,}**" in doc or f"{total:,}" in doc,
          f"實際合計 {total}")

    print(f"\n{'=' * 46}\n通過 {ok}　失敗 {fail}")
    return 1 if fail else 0


if __name__ == "__main__":
    sys.exit(main())
