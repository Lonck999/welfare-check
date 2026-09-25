#!/usr/bin/env python3
"""把一頁裡的多個補助項目拆開（C 方案）。

🔴 我曾說「無法自動判斷邊界」—— **那是沒讀原文就下的結論，Lonck 當場駁回。**
   實際讀宜蘭那頁才發現，邊界不但存在，而且是官方**編號列出來的**：

       二、符合規定之婦女，可申請生育津貼及產檢交通費補助：
       114年出生新生兒                      ← 適用年度（分組標題）
         1.生育津貼：每一新生兒補助新臺幣1萬8,000元。
         2.產檢交通費：每人每胎次補助新臺幣2,000元。
       115年出生新生兒
         1.生育津貼：每一新生兒補助新臺幣2萬元。
         2.產檢交通費：每人每胎次補助新臺幣3,000元。

   ⚠️ 而 A 方案把它壓成「3,000~20,000 元」——
      下限 3,000 是**115 年的產檢交通費**，連年度都不是同一個。

🔴 兩個判斷依據（都來自原文，不是猜的）：
   ① 項目邊界 = 「N.項目名：…金額」的編號行
   ② 適用年度 = 「NNN年出生新生兒」這類分組標題，往下套用到下一個標題為止
      ⚠️ 政府公告用**民國年**（114 = 2025），要換算才知道哪筆是現行的。

輸出：每個項目一筆 dict，含 name / amount / unit / period / raw。
🔴 拆不出來就回空 list —— 由呼叫端 fallback 回 A 方案（整頁一筆）。
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

SP = re.compile(r"\s+")

# ① 編號項目行：「1.生育津貼：每一新生兒補助新臺幣1萬8,000元」
#    分隔符號含「：:、.」，項目名不含冒號與數字開頭
ITEM_RE = re.compile(
    r"^\s*(?:\(|（)?(\d{1,2})(?:\)|）|[.、])\s*"      # 編號
    r"([^：:\n0-9]{2,20})\s*[：:]\s*"                  # 項目名
    r"([^\n]{2,160})",                                 # 內容（含金額）
    re.M,
)

# ② 分組標題：「114年出生新生兒」「一百十四年起」「自115年1月1日起」
GROUP_RE = re.compile(
    r"^\s*(?:自)?\s*(\d{3})\s*年(?:度)?"
    r"(?:[0-9月日至起]{0,12})?"
    r"\s*([^\n：:]{0,14})\s*$",
    re.M,
)


@dataclass
class SubsidyItem:
    """一頁裡的單一補助項目。"""
    name: str
    raw: str
    amount_min: int | None = None
    amount_max: int | None = None
    amount_unit: str | None = None
    period: str | None = None          # 適用年度（西元），如 "2025"
    evidence: list[str] = field(default_factory=list)


def roc_to_ad(roc: str) -> str | None:
    """民國年 → 西元年。🔴 政府公告一律民國年，不換算會比錯現行版本。"""
    try:
        n = int(roc)
    except ValueError:
        return None
    # 合理範圍：民國 100~130（2011~2041）
    if not (100 <= n <= 130):
        return None
    return str(n + 1911)


def split_items(text: str) -> list[SubsidyItem]:
    """把整頁拆成多個補助項目。拆不出來回 []。"""
    # 延後 import：避免 circular（extract_amounts 不依賴本模組）
    from extract_amounts_from_desc import extract_amounts

    lines = text.split("\n")
    cur_period: str | None = None
    period_at: dict[int, str | None] = {}
    for i, ln in enumerate(lines):
        g = GROUP_RE.match(ln)
        if g:
            ad = roc_to_ad(g.group(1))
            if ad:
                cur_period = ad
        period_at[i] = cur_period

    items: list[SubsidyItem] = []
    for i, ln in enumerate(lines):
        m = ITEM_RE.match(ln)
        if not m:
            continue
        name = SP.sub("", m.group(2))
        body = m.group(3)
        amin, amax, unit, ev = extract_amounts(body)
        # 🔴 沒有金額的編號行多半是「應備文件」「申請地點」那種 —— 不收
        if amin is None:
            continue
        items.append(SubsidyItem(
            name=name,
            raw=SP.sub(" ", ln.strip())[:200],
            amount_min=amin, amount_max=amax, amount_unit=unit,
            period=period_at.get(i),
            evidence=ev,
        ))
    return items


def latest_only(items: list[SubsidyItem]) -> list[SubsidyItem]:
    """同名項目有多個年度版本時，只留最新的那個。

    🔴 宜蘭的「生育津貼」有 114 年 18,000 與 115 年 20,000 兩版 ——
       給使用者看舊版等於少報 2,000 元。
    ⚠️ 沒有 period 的項目一律保留（不能因為缺年度就丟掉）。
    """
    best: dict[str, SubsidyItem] = {}
    out: list[SubsidyItem] = []
    for it in items:
        if not it.period:
            out.append(it)
            continue
        old = best.get(it.name)
        if old is None or (old.period or "") < it.period:
            best[it.name] = it
    return out + list(best.values())


if __name__ == "__main__":
    import sys
    sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent))
    sample = sys.stdin.read()
    for it in latest_only(split_items(sample)):
        print(f"{it.name}　{it.amount_min}~{it.amount_max} {it.amount_unit}"
              f"　期間={it.period}")
        print(f"   {it.raw[:90]}")
