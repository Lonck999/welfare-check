#!/usr/bin/env python3
"""掃全庫：`amount_*` 裡有沒有「資格門檻」被當成「補助金額」。

🔴 起因（2026-09-30，id 854）：
   `amount_min=2308, amount_max=8079, unit=monthly` 看起來完全合理，
   實際是 **109 年台北市第 1 類的收入門檻**
   （全戶平均每人每月總收入介於此區間才「符合資格」），
   真實補助金額是 11,850／6,825／3,008。

   成因：那筆的 source_url 指向「低收入戶**類別條件**一覽表」而不是
   「生活扶助**金額**表」，抽取器照抽數字 ⇒ 門檻進了金額欄位。

🔴 **這比壞連結嚴重**：壞連結點了會發現；`2,308~8,079 元/月`
   看起來完全合理，**沒有任何訊號說它是錯的**。

🔴 為什麼不能用「已知門檻數字清單」當判準：
   ⚠️ 我第一版就是這樣寫的（15,515／14,341／18,682…），全庫只命中 1 筆。
   但那些數字**每年調整、每個縣市不同、每個年度版本都不一樣** ——
   清單永遠列不完，而漏掉時的症狀是「掃描報告很乾淨」。
   ⇒ 改成偵測「**這個數字在描述裡出現時，周圍的字在講什麼**」：
     講「未超過／以下／總收入／最低生活費」＝資格門檻
     講「補助／發給／核發／最高」＝補助金額

⚠️ 這是**偵測**腳本，不改任何資料。
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import psycopg2

# 🔴 這個數字**周圍**出現這些字 ⇒ 它在講資格，不是在講補助
THRESHOLD_CTX = (
    "最低生活費", "未超過", "未逾", "以下者", "低於", "總收入",
    "平均分配", "每人每月在", "動產", "不動產", "存款本金",
    "家庭財產", "一定金額", "資格", "門檻", "審查", "限額",
)
# 🔴 出現這些字 ⇒ 它在講補助金額（可以抵銷上面的訊號）
BENEFIT_CTX = (
    "補助", "發給", "核發", "給付", "津貼", "扶助費", "最高補助",
    "每案", "補貼", "獎勵金", "慰問金", "生活費為", "補助費",
)

WIN = 40          # 數字前後各看幾個字
_num = re.compile(r"[\d,]{3,}")


def ctx_verdict(desc: str, value: int) -> tuple[str, str] | None:
    """這個數字在描述裡出現時，周圍在講什麼。

    回傳 (判定, 證據片段)；**描述裡完全找不到這個數字時回 None**。

    🔴 「找不到」是最強的訊號，不是「不確定」：
       金額欄位有值、但描述裡連提都沒提到它 ⇒ 那個數字來源不明
       （854 就是這樣 —— 2,308／8,079 是從**另一個頁面**抽來的）。
    ⚠️ 第一版在找不到時回 `("unclear", "")`，於是 854 被歸進
       「語境不明」而不是「來源不明」——
       🔴 **最該抓的那一類報告永遠是 0 筆，而 0 筆看起來像「沒問題」**。
       這正是我自己寫過的「統計腳本讀不存在的欄位 → 永遠回報失敗 0」。
    """
    if not desc:
        return None
    found = False
    best: tuple[str, str] | None = None
    for m in _num.finditer(desc):
        try:
            if int(m.group().replace(",", "")) != value:
                continue
        except ValueError:
            continue
        found = True
        lo = max(0, m.start() - WIN)
        seg = desc[lo:m.end() + WIN]

        # 🔴 判準不是「數哪邊的詞多」，是「**這個數字自己前後最近的那個詞**」。
        #    ⚠️ 第一版數詞頻，誤判了 666／735 兩筆正確資料 ——
        #       它們的原句是「家庭總收入…在 26,625 元以下者，
        #       **每月發給 8,329 元**」，同一句裡門檻與金額都有，
        #       而門檻詞剛好比較多 ⇒ 正確的資料被報成錯的。
        #    🔴 誤報比漏報更傷：它會讓人去「修」一筆本來就對的資料。
        near = desc[max(0, m.start() - 12):m.start()]
        if any(k in near for k in ("發給", "補助", "核發", "給付",
                                   "補貼", "最高", "為")):
            return ("benefit", seg.replace("\n", " "))
        after = desc[m.end():m.end() + 14]
        if any(k in after for k in ("以下", "以上", "未超過", "者，",
                                    "元以下", "元以上")):
            if best is None:
                best = ("threshold", seg.replace("\n", " "))
            continue
        t = sum(1 for k in THRESHOLD_CTX if k in seg)
        b = sum(1 for k in BENEFIT_CTX if k in seg)
        if b > t:
            return ("benefit", seg.replace("\n", " "))
        if t > b and best is None:
            best = ("threshold", seg.replace("\n", " "))
    if not found:
        return None          # 🔴 描述裡沒有這個數字 ⇒ 來源不明
    return best or ("unclear", "")


def main() -> int:
    conn = psycopg2.connect(dbname="welfare_check")
    cur = conn.cursor()
    cur.execute("""SELECT id, county, name, amount_min, amount_max,
                          amount_unit, description, source_url
                     FROM benefits
                    WHERE amount_min IS NOT NULL
                    ORDER BY id""")
    rows = cur.fetchall()
    print(f"有金額的 {len(rows)} 筆\n")

    buckets: dict[str, list] = {"threshold": [], "not_in_desc": [],
                                "unclear": [], "benefit": []}
    for bid, county, name, amin, amax, unit, desc, url in rows:
        v_min = ctx_verdict(desc, amin)
        v_max = ctx_verdict(desc, amax) if amax and amax != amin else v_min
        if v_min is None and v_max is None:
            buckets["not_in_desc"].append((bid, county, name, amin, amax,
                                           unit, "", url))
            continue
        verds = {v[0] for v in (v_min, v_max) if v}
        ev = next((v[1] for v in (v_min, v_max) if v and v[1]), "")
        if "threshold" in verds and "benefit" not in verds:
            buckets["threshold"].append((bid, county, name, amin, amax,
                                         unit, ev, url))
        elif "benefit" in verds:
            buckets["benefit"].append((bid, county, name, amin, amax,
                                       unit, ev, url))
        else:
            buckets["unclear"].append((bid, county, name, amin, amax,
                                       unit, ev, url))

    def show(key: str, title: str, limit: int = 40) -> None:
        items = buckets[key]
        print(f"\n{'='*72}\n{title}：{len(items)} 筆")
        for bid, county, name, amin, amax, unit, ev, _u in items[:limit]:
            rng = f"{amin:,}" if amin == amax else f"{amin:,}~{amax:,}"
            print(f"  [{bid}] {county or '－'} {name[:30]}")
            print(f"        {rng} {unit or ''}")
            if ev:
                print(f"        證據：…{ev[:110]}…")
        if len(items) > limit:
            print(f"  （另 {len(items) - limit} 筆，見 JSON）")

    show("threshold", "🔴 疑似『資格門檻被當成補助金額』")
    show("not_in_desc", "⚠️ 金額欄位的數字**在描述裡完全找不到**（來源不明）")
    show("unclear", "🔸 語境兩邊都不明顯（需人工看）", 15)
    print(f"\n{'='*72}\n✅ 語境明確是補助金額：{len(buckets['benefit'])} 筆")

    out = Path("/tmp/wc_backup/amount_threshold_scan.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(
        {k: [{"id": r[0], "county": r[1], "name": r[2], "min": r[3],
              "max": r[4], "unit": r[5], "evidence": r[6], "url": r[7]}
             for r in v] for k, v in buckets.items()},
        ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n完整結果 → {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
