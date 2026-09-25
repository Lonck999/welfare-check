#!/usr/bin/env python3
"""把描述裡已經有的金額抽進 amount_min/max（P2「依金額排序」要用）。

🔴 為什麼需要這支（2026-09-25 端到端驗證發現）：
   152 筆的 description 裡**找得到金額**，但只有 7 筆填了 amount_max
   ⇒ P2 的「金額大優先」這個排序維度等於做不到。
   ⚠️ 資料在庫裡，只是沒進到排序用得到的欄位 —— 這種缺口不會報錯。

🔴 抽取判準（沿用 fetch_local_benefit 的教訓，別再踩一次）：
   · 必須是**明確的給付語句**（「補助金額：N 元」「每月發給 N 元」），
     不是「頁面上出現的任何數字」
   · 排除工本費／規費／手續費（那些是使用者要付的，不是領的）
   · 🔴 抽不出來就留 None —— 絕不猜

⚠️ 這支**只讀 description 不上網**，所以不會有「抓到別的補助的金額」
   那種問題（那是跨頁抓取才有的）。但仍要驗：金額必須和
   這筆補助的名稱在同一段文字裡。
"""
from __future__ import annotations

import argparse
import re
import sys

import psycopg2

# 🔴 只抓「明確的給付語句」
PAY_RE = re.compile(
    r"(補助金額|補助標準|給付金額|核發金額|發給|發放|發放|核給|核發|補助|津貼|最高|給付)"
    r"[^。；\n]{0,30}?"
    r"([0-9][0-9,]{2,})\s*元"
)
# 「N 萬元」另外處理（1 萬 = 10000）
# 🔴 必須先處理「X萬Y,Z00元」這種混合寫法（2026-09-25 實測踩到）：
#    「最高補助4萬4,000元」若先跑 PAY_RE 會抓到「4,000」，
#    再跑 WAN_RE 抓到「40,000」→ 變成區間 4,000~40,000，**兩個都錯**
#    （正確是 44,000）。⚠️ 錯得很像對的：區間看起來合理，沒有訊號。
MIXED_RE = re.compile(
    r"(補助金額|補助標準|給付金額|核發金額|發給|發放|發放|核給|核發|補助|津貼|最高|給付)"
    r"[^。；\n]{0,30}?"
    r"([0-9]+)\s*萬\s*([0-9][0-9,]{2,})\s*元"
)
WAN_RE = re.compile(
    r"(補助金額|補助標準|發給|發放|核給|核發|補助|津貼|最高|給付)"
    r"[^。；\n]{0,30}?"
    r"([0-9]+(?:\.[0-9]+)?)\s*萬\s*元?"
)
# 🔴 這些數字不是補助金額
# ⚠️ 「編列預算/公務預算/總經費」是**政府自己的錢**，不是給個人的
#    （2026-09-25 實測踩到：「115年由本府衛生局編列公務預算共計新臺幣
#    1億480萬元」→ 我抓出 4,800,000 當成假牙補助上限，
#    🔴 而它跟正確的 6,600/17,000/39,000 並列，看起來只是「上限比較高」）
NOT_AMOUNT = re.compile(r"工本費|規費|手續費|掛號費|郵資|自付|負擔|罰|"
                        r"收費|費用為|應繳|預算|經費|億")

UNIT_MONTHLY = re.compile(r"每月|按月|月領|每人每月")
# 🔴 「年度預算」「年度結束」是政府自己的會計年度，**不是給付週期**
#    （2026-09-26 踩到：嘉義市生育津貼「每胎三萬元」被判成 yearly，
#      真因是頁尾「由本府編列年度預算支應」）
#    ⚠️ 判錯單位會讓使用者以為每年都能領一次。
UNIT_YEARLY = re.compile(r"每年(?!度預算)|每學年|每一年|按年(?!度)")
UNIT_ONCE = re.compile(r"每胎|每一胎|每名新生兒|每一新生兒|一次性|"
                       r"每人一次|限領一次")

# 🔴 中文數字金額（2026-09-25 發現，影響全部法規頁）：
#    政府**法規條文**一律用中文數字寫金額 ——
#      金門「單胞胎新臺幣二萬元，雙胞胎新臺幣六萬元」
#      連江「第一胎新臺幣三萬元，第二胎六萬元…第四胎十五萬元」
#      嘉義市「每生育一名新生兒補助新臺幣三萬元」
#    ⚠️ 只認阿拉伯數字時，這些頁面會回報「0 個金額」——
#       而那看起來跟「這頁真的沒有補助」一模一樣，**完全沒有訊號**。
#    這正是 5 個縣市裡 4 個抓到官方頁卻抽不到金額的真因。
_CN_DIGIT = {"〇": 0, "零": 0, "一": 1, "二": 2, "兩": 2, "三": 3, "四": 4,
             "五": 5, "六": 6, "七": 7, "八": 8, "九": 9}


def cn_to_int(s: str) -> int | None:
    """把「十五」「二」「一百二十」轉成整數。看不懂回 None。"""
    s = s.strip()
    if not s or any(ch not in _CN_DIGIT and ch not in "十百千" for ch in s):
        return None
    total, section, digit = 0, 0, 0
    for ch in s:
        if ch in _CN_DIGIT:
            digit = _CN_DIGIT[ch]
        elif ch == "十":
            section += (digit or 1) * 10
            digit = 0
        elif ch == "百":
            section += (digit or 1) * 100
            digit = 0
        elif ch == "千":
            section += (digit or 1) * 1000
            digit = 0
    return total + section + digit


# ⚠️ 觸發詞可能離金額很遠（連江：「…申請補助者，以設籍本縣之日後出生之
#    胞胎起算第一胎新臺幣三萬元」—— 中間隔了 20 幾個字）
#    ⇒ 視窗放寬到 40 字，並把「新臺幣」本身也當成觸發詞
CN_AMOUNT_RE = re.compile(
    r"(補助|津貼|發給|發放|核給|核發|給付|獎勵|新臺幣|新台幣|為)"
    r"[^。；\n]{0,40}?"
    r"([〇零一二三四五六七八九十百千兩]{1,8})\s*(萬|千)?\s*元"
)

# 🔴 接續列舉的金額（同一句裡的第 2、3、4 個）：
#    「第一胎新臺幣三萬元，第二胎六萬元，第三胎九萬元，第四胎十五萬元」
#    ⚠️ 只有第一個前面有「補助/新臺幣」，後面全是裸的
#       ⇒ 用 CN_AMOUNT_RE 只會抓到第一個，區間變成 30000~30000，
#          而**那個數字本身是對的**，所以看起來完全正常（沒有訊號）。
#    ⇒ 一句裡已命中過中文金額時，才用這個寬鬆式抓其餘的。
CN_FOLLOW_RE = re.compile(
    r"([〇零一二三四五六七八九十百千兩]{1,8})\s*(萬|千)\s*元"
)


def _near(text: str, start: int, end: int, span: int = 25) -> str:
    """取金額前後的上下文，🔴 **不跨句**。

    ⚠️ 2026-09-26 踩到：嘉義市「每生育一名新生兒補助新臺幣三萬元。
       六、經費來源：由本府編列年度預算支應」——
       固定 25 字視窗跨過句號吃到下一句的「經費/預算」，
       於是 NOT_AMOUNT 把**正確的金額**擋掉了。
    🔴 而擋掉的結果是「這頁沒有金額」，跟真的沒有長得一模一樣。
    """
    left = text[max(0, start - span): start]
    right = text[end: end + span]
    # 只取最後一個句界之後 / 第一個句界之前
    for sep in "。；\n":
        if sep in left:
            left = left.rsplit(sep, 1)[1]
        if sep in right:
            right = right.split(sep, 1)[0]
    return left + text[start:end] + right


def extract_amounts(text: str) -> tuple[int | None, int | None, str | None,
                                        list[str]]:
    """回傳 (min, max, unit, 證據片段)。抽不到回 (None, None, None, [])。"""
    found: list[tuple[int, str]] = []
    # 🔴 順序很重要：先把「X萬Y,Z00元」整段吃掉並從文字中移除，
    #    否則後面兩個 regex 會把它拆成兩個錯誤的數字。
    for m in MIXED_RE.finditer(text):
        near = _near(text, m.start(2), m.end(3))
        if NOT_AMOUNT.search(near):
            continue
        try:
            v = int(m.group(2)) * 10_000 + int(m.group(3).replace(",", ""))
        except ValueError:
            continue
        if not (100 <= v <= 50_000_000):
            continue
        found.append((v, re.sub(r"\s+", " ", m.group(0))[:80]))
    text = MIXED_RE.sub(" ", text)

    for m in PAY_RE.finditer(text):
        near = _near(text, m.start(2), m.end(2))
        if NOT_AMOUNT.search(near):
            continue
        try:
            v = int(m.group(2).replace(",", ""))
        except ValueError:
            continue
        # 🔴 排除明顯不是金額的數字（電話、身分證）
        if v < 100 or v > 50_000_000:
            continue
        # ⚠️ 年份排除**只在沒有「元」以外的金額語境時**才套用。
        #    2026-09-26 踩到：「每人每胎次補助新臺幣2,000元」被
        #    `1900 <= v <= 2100` 當成年份擋掉 ——
        #    🔴 那條規則會誤殺**所有 2,000 元的補助**，
        #       而結果是「這頁沒有金額」，跟真的沒有長得一模一樣。
        #    正確判準：帶千分位逗號的（2,000）一定是金額，年份不會這樣寫；
        #    裸數字 2026 才可能是年份。
        if 1900 <= v <= 2100 and "," not in m.group(2):
            continue
        found.append((v, re.sub(r"\s+", " ", m.group(0))[:80]))

    for m in WAN_RE.finditer(text):
        near = _near(text, m.start(2), m.end(2))
        if NOT_AMOUNT.search(near):
            continue
        try:
            v = int(float(m.group(2)) * 10_000)
        except ValueError:
            continue
        if v < 100 or v > 50_000_000:
            continue
        found.append((v, re.sub(r"\s+", " ", m.group(0))[:80]))

    # 🔴 中文數字金額（法規條文專用寫法）
    cn_hit = False
    for m in CN_AMOUNT_RE.finditer(text):
        near = _near(text, m.start(2), m.end(2))
        if NOT_AMOUNT.search(near):
            continue
        base = cn_to_int(m.group(2))
        if base is None or base == 0:
            continue
        mult = {"萬": 10_000, "千": 1_000}.get(m.group(3) or "", 1)
        v = base * mult
        # ⚠️ 沒有單位詞時（「五千元」以外的裸中文數字）多半是條號、期數，
        #    例如「第三條」「三個月內」—— 要求至少 100 元才採信
        if not (100 <= v <= 50_000_000):
            continue
        found.append((v, re.sub(r"\s+", " ", m.group(0))[:80]))
        cn_hit = True

    # 🔴 同句裡已命中中文金額 ⇒ 用寬鬆式補抓接續列舉的
    #    （必須帶「萬/千」單位詞，否則「三個月」「二款」會被誤抓）
    if cn_hit:
        for m in CN_FOLLOW_RE.finditer(text):
            near = _near(text, m.start(1), m.end(1))
            if NOT_AMOUNT.search(near):
                continue
            base = cn_to_int(m.group(1))
            if base is None or base == 0:
                continue
            v = base * {"萬": 10_000, "千": 1_000}[m.group(2)]
            if not (100 <= v <= 50_000_000):
                continue
            ev = re.sub(r"\s+", " ", m.group(0))[:80]
            if all(v != x for x, _ in found):
                found.append((v, ev))

    if not found:
        return None, None, None, []
    vals = [v for v, _ in found]
    # 🔴 順序有意義：「每胎」這類一次性語句最明確，要先判
    unit = ("one_time" if UNIT_ONCE.search(text)
            else "monthly" if UNIT_MONTHLY.search(text)
            else "yearly" if UNIT_YEARLY.search(text)
            else "one_time")
    return min(vals), max(vals), unit, [e for _, e in found[:3]]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--show", type=int, default=12)
    args = ap.parse_args()

    conn = psycopg2.connect(dbname="welfare_check")
    cur = conn.cursor()
    cur.execute("""SELECT id, name, description FROM benefits
                    WHERE amount_max IS NULL
                      AND description ~ '[0-9][0-9,]{2,}\\s*元'""")
    rows = cur.fetchall()
    print(f"候選（描述含金額但 amount_max 為空）：{len(rows)} 筆\n")

    hit = 0
    shown = 0
    for bid, name, desc in rows:
        amin, amax, unit, ev = extract_amounts(desc or "")
        if amin is None:
            continue
        hit += 1
        if shown < args.show:
            shown += 1
            print(f"  · {name[:34]}")
            print(f"      {amin:,}~{amax:,} {unit}　「{ev[0][:60]}」")
        if args.apply:
            cur.execute("""UPDATE benefits
                              SET amount_min = %s, amount_max = %s,
                                  amount_unit = %s,
                                  amount_note = %s
                            WHERE id = %s""",
                        (amin, amax, unit,
                         "自描述原文抽取：" + "；".join(ev), bid))

    if args.apply:
        conn.commit()
        cur.execute("SELECT count(*) FROM benefits WHERE amount_max IS NOT NULL")
        print(f"\n✅ 抽出 {hit} 筆　現在有金額的共 {cur.fetchone()[0]} 筆")
    else:
        print(f"\n（dry-run）可抽出 {hit}/{len(rows)} 筆")
    return 0


if __name__ == "__main__":
    sys.exit(main())
