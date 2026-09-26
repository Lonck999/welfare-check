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

# 🔴 第二種格式：政府公文常用「(N)項目名：金額」或「a.條件，金額」
#    且**同一行內**用 <br> 分隔多個項目（2026-09-26 從高雄實查）：
#
#      求職交通補助金：每人每次得發給新臺幣500元
#      <br>a.就業地點…30公里以上未滿50公里，每月發給新臺幣一千元
#      <br>b.…50公里以上未滿70公里，每月發給新臺幣二千元
#      <br>(2)搬遷補助金：以搬遷費用收據所列總額核實發給，最高發給新臺幣三萬元
#
#    ⚠️ ITEM_RE 對這頁**拆出 0 項** ⇒ fallback 回整頁一筆
#       → 區間變成 500~30,000（60 倍），而 500 是求職交通、
#         30,000 是搬遷補助 —— **兩種完全不同的補助**
#    🔴 而那個區間看起來完全合理，使用者無從分辨。
#
# 判準：①「名稱：…金額」的具名項目（名稱不含數字、長度 3~18）
#      ② a./b./c. 這種**同一項目的分級**要合併，不是拆開
NAMED_RE = re.compile(
    # 前綴：行首／<br>／全形空白／標點，後面可跟「(N)」「N.」「a.」等編號
    r"(?:^|<br>|　|[\s、，。；])"
    r"\s*(?:[(（]\s*(?:\d{1,2}|[a-z])\s*[)）]|(?:\d{1,2}|[a-z])[.、])?\s*"
    # 項目名：不含冒號、標籤、數字、括號
    # 🔴 必須非貪婪（{3,18}?）—— 貪婪會吃掉「搬遷補助金」全部，
    #    後面的 (?:補助金|補助|…) 就沒東西可配 ⇒ 整條 regex 失敗
    #    ⚠️ 症狀是「只命中第一個項目」，看起來像格式不支援
    r"([^：:<>\n0-9()（）]{2,16}?(?:補助金|補助費|補助|津貼|獎勵金|給付|費))"
    r"\s*[：:]",
    re.M,
)

# ③ 分級條件行（a./b./c. 或「…以上未滿…」）—— 同一項目的級距，不可拆成不同項目
TIER_RE = re.compile(r"(?:^|<br>)\s*(?:[a-z]|\([a-z]\))[.、]|以上未滿|"
                     r"級距|依.{0,8}距離|按.{0,6}年資")

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


# 🔴 政府給付類型的固定變體（2026-09-26 從資料庫實查，不是憑印象列）
#    實際尾字分佈：補助 125／救助 24／扶助 19／津貼 17／補助費 5／
#                  減免 3／補助金 3／禮金 2／慰問金 2／獎勵金 2／優惠 1／給付 1
#
# ⚠️ 為什麼需要它：這批 363 筆的主題名是**我們自己取的**，
#    跟官方用語系統性不一致。已撞到三次：
#      我們「生育獎勵金」  官方「生育津貼」
#      我們「房屋修繕補助」官方「改善低收入戶住宅設施設備補助」
#      我們「中低醫療看護」官方「中低收入老人傷病醫療暨看護費用補助」
# 🔴 名稱對不上時原本 fallback 成「取金額最大」——
#    這次剛好對（20,000 > 3,000），但主項目金額**不保證**比附屬項目大。
PAYOUT_SUFFIX = re.compile(
    r"(津貼|獎勵金|獎助金|補助金|補助費|補助款|補助|慰問金|禮金|"
    r"給付|代金|扶助|救助|優惠|減免|點數|費用)+$"
)


def core_name(name: str) -> str:
    """剝掉給付類型尾字，只留主題核心。

    「生育獎勵金」→「生育」；「生育津貼」→「生育」⇒ 兩者可比對。
    🔴 剝到空字串就回原字串 —— 否則「津貼」這種純類型名會變成 ""，
       而空字串會命中**任何**名稱（`"" in x` 永遠 True），
       ⚠️ 那會讓第一個項目永遠被當成主項目，且完全沒有訊號。
    """
    s = re.sub(r"[（(].*?[)）]", "", name).strip()
    s = re.sub(r"^(地方|中央|全國|本市|本縣)", "", s)
    stripped = PAYOUT_SUFFIX.sub("", s).strip()
    return stripped or s


def same_topic(a: str, b: str) -> bool:
    """兩個名稱是否指同一個補助主題（過同義詞後比對）。

    🔴 三層判準，由嚴到寬（2026-09-26 雙向驗證後定案）：
      ① 核心名互為子字串 —— 「生育」⊂「生育」✅
      ② 🔴 **字元交集比例** —— 詞序不同時用（「老人重陽禮金」↔
         「重陽敬老禮金」核心名是「老人重陽」vs「重陽敬老」，
         互不為子字串但共用「重陽」）
      ③ 都不成立 → False

    ⚠️ ②的門檻設 0.5 是因為 negative control 逼出來的：
       「房屋修繕」vs「房屋租金」共用「房屋」= 0.5，**必須擋掉**
       （那是兩種完全不同的補助），所以門檻要 **> 0.5** 而非 >=。
    """
    ca, cb = core_name(a), core_name(b)
    if not ca or not cb:
        return False
    if ca in cb or cb in ca:
        return True
    # ② 字元交集（短的那邊有幾成字出現在長的那邊）
    short, long = (ca, cb) if len(ca) <= len(cb) else (cb, ca)
    if len(short) < 2:
        return False
    hit = sum(1 for ch in short if ch in long)
    return hit / len(short) > 0.5


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
    if items:
        return items

    # 🔴 第二種格式（ITEM_RE 拆不出來才用）：
    #    「項目名：…」用 NAMED_RE 找具名項目，以它們的位置切段落
    #    ⚠️ 必須以**位置**切，不能逐行 —— 高雄那頁整段擠在同一行用 <br> 分隔
    marks = [(m.start(1), SP.sub("", m.group(1)))
             for m in NAMED_RE.finditer(text)]
    if len(marks) < 2:
        return []
    for idx, (pos, nm) in enumerate(marks):
        end = marks[idx + 1][0] if idx + 1 < len(marks) else len(text)
        seg = text[pos:end]
        # ⚠️ 段落過長多半是抓錯邊界（整頁被當成一段）
        if len(seg) > 1200:
            seg = seg[:1200]
        amin, amax, unit, ev = extract_amounts(seg)
        if amin is None:
            continue
        items.append(SubsidyItem(
            name=nm,
            raw=SP.sub(" ", seg[:200]),
            amount_min=amin, amount_max=amax, amount_unit=unit,
            period=None,
            evidence=ev,
        ))
    # 🔴 只拆出 1 項等於沒拆 —— 回空讓呼叫端 fallback，別假裝成功
    return items if len(items) >= 2 else []


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
