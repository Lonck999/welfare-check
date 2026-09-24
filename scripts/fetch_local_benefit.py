#!/usr/bin/env python3
"""試抓：把「未查得」的地方補助真的查出來（路線一，3 主題試作）。

🔴 為什麼現有 328 筆查不到（實查 2026-09-24）：
   · source_url 指向衛福部首頁 https://www.mohw.gov.tw/
     —— 中央網站當然沒有各縣市的金額
   · 孕產婦那批來源是 yannigo.com（月子中心行銷部落格），根本不是官方
   · 22 縣市描述一字不差只換縣市名 —— 一次性生成的模板，沒有真的查過

   ⇒ 要查到金額必須去**各縣市自己的官網**。

🔴 本腳本只做三件事，且**不寫入資料庫**（--apply 才寫）：
   ① 針對「縣市 + 主題」搜尋，只採信官方網域
   ② 讀該頁全文，抽出金額
   ③ 抽不到就誠實記 no_amount_found，**絕不編造**
"""
from __future__ import annotations

import argparse
import asyncio
import json
import os
import re
import subprocess
import sys
from pathlib import Path

import psycopg2

HERMES = Path.home() / ".hermes" / "hermes-agent"
PY = HERMES / "venv" / "bin" / "python"

sys.path.insert(0, str(Path(__file__).parent))
from benefit_keywords import NOT_BENEFIT_CTX  # noqa: E402

# 🔴 官方網域：gov.tw / gov.taipei（臺北市全台唯一）
OFFICIAL_RE = re.compile(r"^https?://[^/]*\.(gov\.tw|gov\.taipei)(/|$)", re.I)

# 🔴 排除：採購網、法規庫、公報 —— 在官方網域但不是在發補助
EXCLUDE_RE = re.compile(
    r"^https?://[^/]*("
    r"pcc\.gov\.tw|law[s]?\.[^/]*gov\.(tw|taipei)|gazette|"
    r"president\.gov\.tw|ppg\.ly\.gov\.tw"
    r")", re.I)

# 金額：抓「N 元」「N 萬元」「N,NNN 元」
AMOUNT_RE = re.compile(
    r"([0-9][0-9,]{2,})\s*元"
    r"|([0-9]+(?:\.[0-9]+)?)\s*萬\s*元?"
    r"|新臺幣\s*([0-9][0-9,]*)\s*元")


# 🔴 縣市官方網域對照（2026-09-24 建，實測必要）：
#    搜尋「嘉義縣 照顧者津貼」會撈到 social.chiayi.gov.tw —— 那是嘉義**市**。
#    ⚠️ 不驗網域的話，A 縣市的補助會被寫進 B 縣市，**而且完全沒有訊號**
#    （金額看起來很正常，只是屬於別的縣市）。
COUNTY_DOMAIN: dict[str, tuple[str, ...]] = {
    "臺北市": ("gov.taipei",),
    "新北市": ("ntpc.gov.tw",),
    "桃園市": ("tycg.gov.tw", "tyc.gov.tw"),
    "臺中市": ("taichung.gov.tw",),
    "臺南市": ("tainan.gov.tw",),
    "高雄市": ("kcg.gov.tw",),
    "基隆市": ("klcg.gov.tw",),
    "新竹市": ("hccg.gov.tw",),
    "新竹縣": ("hsinchu.gov.tw",),
    "苗栗縣": ("miaoli.gov.tw",),
    "彰化縣": ("chcg.gov.tw",),
    "南投縣": ("nantou.gov.tw",),
    "雲林縣": ("yunlin.gov.tw",),
    "嘉義市": ("chiayi.gov.tw",),
    "嘉義縣": ("cyhg.gov.tw",),          # 🔴 與嘉義市 chiayi 完全不同
    "屏東縣": ("pthg.gov.tw",),
    "宜蘭縣": ("e-land.gov.tw", "ilcg.gov.tw"),
    "花蓮縣": ("hl.gov.tw", "hlcg.gov.tw"),
    "臺東縣": ("taitung.gov.tw",),
    "澎湖縣": ("penghu.gov.tw",),
    "金門縣": ("kinmen.gov.tw",),
    "連江縣": ("matsu.gov.tw", "lienchiang.gov.tw"),
}


def is_own_county(url: str, county: str) -> bool:
    """這個網址是不是**該縣市自己的**官網。

    🔴 中央網域（mohw.gov.tw 等）一律不算 —— 那是現有 328 筆空殼的成因：
       source_url 全指向衛福部首頁，所以永遠查不到地方金額。
    """
    doms = COUNTY_DOMAIN.get(county)
    if not doms:
        return False
    return any(d in url.lower() for d in doms)


def _run_tool(func: str, payload: dict) -> object:
    """在 hermes venv 裡呼叫工具（web_search_tool / web_extract_tool）。

    🔴 web_extract_tool 是 async，必須 asyncio.run —— 忘了 await 會拿到
       coroutine，len()=0，然後靜默變成「這個縣市沒有補助」。
    """
    code = f"""
import json, sys, asyncio
sys.path.insert(0, {str(HERMES)!r})
from tools.web_tools import {func}
payload = {payload!r}
r = {func}(**payload)
if asyncio.iscoroutine(r):
    r = asyncio.run(r)
print(json.dumps(r, ensure_ascii=False) if not isinstance(r, str) else r)
"""
    out = subprocess.run([str(PY), "-c", code], capture_output=True,
                         text=True, encoding="utf-8", timeout=180)
    if out.returncode != 0:
        raise RuntimeError(out.stderr[-400:])
    return json.loads(out.stdout)


def search(query: str, limit: int = 6) -> list[dict]:
    r = _run_tool("web_search_tool", {"query": query, "limit": limit})
    if isinstance(r, str):
        r = json.loads(r)
    if isinstance(r, dict) and r.get("success") is False:
        raise RuntimeError(f"搜尋後端失敗：{r.get('error')}")
    data = r.get("data", r) if isinstance(r, dict) else r
    return (data.get("web", []) if isinstance(data, dict) else data) or []


def extract(url: str, char_limit: int = 40000, retries: int = 3) -> str:
    """🔴 內容 <200 字元一律視為抽取失敗，不可當成「這頁沒有補助」。

    🔴 必須重試：實測 Firecrawl 會回 ERR_TUNNEL_CONNECTION_FAILED
       （它自己的 proxy 暫時性錯誤）—— 不重試的話，
       **一次偶發失敗會被永久記成「這個縣市沒有補助」**。
    """
    import time
    for attempt in range(retries):
        try:
            r = _run_tool("web_extract_tool",
                          {"urls": [url], "char_limit": char_limit})
        except Exception:                             # noqa: BLE001
            time.sleep(2 * (attempt + 1))
            continue
        if isinstance(r, str):
            r = json.loads(r)
        results = r.get("results", []) if isinstance(r, dict) else []
        text = "".join(x.get("content", "") or "" for x in results)
        if len(text) >= 200:
            return text
        # 🔴 只有「暫時性錯誤」才重試；真的是空頁就不必浪費配額
        err = " ".join(str(x.get("error") or "") for x in results)
        if not re.search(r"TUNNEL|timeout|proxy|Internal Server|502|503|429",
                         err, re.I):
            return ""
        time.sleep(2 * (attempt + 1))
    return ""


def strip_noise(text: str) -> str:
    """🔴 剔除「補助」二字出現但不是在發補助的上下文。

    實測 26 筆有 18 筆誤判（表單欄位、招標公告、詐騙提醒…）。
    """
    for pat in NOT_BENEFIT_CTX:
        text = re.sub(pat, "", text)
    return text


def find_amounts(text: str, keywords: list[str]) -> list[tuple[str, str]]:
    """找補助金額，回傳 [(金額原文, 上下文)]。

    🔴 **判準是「這一頁在講什麼」，不是「關鍵字離金額多近」**
       （2026-09-24 連續兩次修錯才想通）：

       · 基隆那頁：關鍵字只出現在最下方的 PDF 檔名，金額在它**上面**
         ⇒ 「命中段 + 後兩段」方向剛好相反，抓不到
       · 宜蘭那頁：是「服務項目總覽」，關鍵字只是選單裡的一個連結，
         同頁有一堆別的補助金額
         ⇒ 任何「就近取」的做法都會抓到別人的金額

       ⇒ 正確做法：先判斷**整頁主題**（關鍵字密度足夠才算），
         再抓「補助金額：…」這類**明確的給付語句**。
    """
    # ① 整頁主題檢查：關鍵字至少出現 2 次，或出現在標題行
    kw_count = sum(text.count(kw) for kw in keywords)
    in_heading = any(
        re.search(rf"^#{{1,4}}\s*.*{re.escape(kw)}", text, re.M)
        for kw in keywords)
    if kw_count < 2 and not in_heading:
        return []

    # ② 只抓「明確的給付語句」—— 必須有動詞或「金額：」這類標記
    PAY_RE = re.compile(
        r"(補助金額|補助標準|給付金額|核發金額|發給|核給|補助)"
        r"[^。\n]{0,40}?"
        r"([0-9][0-9,]{2,}\s*元|[0-9]+(?:\.[0-9]+)?\s*萬\s*元?)")
    found: list[tuple[str, str]] = []
    for m in PAY_RE.finditer(text):
        # 🔴 排除詞只看**金額緊鄰處**（前後 20 字元），不可用整個上下文。
        #    實測基隆那筆正確金額被擋掉，原因是 60 字元外的「檢附文件：
        #    身分證正反面影本」——「影本」跟金額根本無關，卻否決了它。
        tight = text[max(0, m.start(2) - 20): m.end(2) + 20]
        if re.search(r"工本費|規費|手續費|掛號費|郵資", tight):
            continue
        lo = max(0, m.start() - 60)
        near = re.sub(r"\s+", " ", text[lo: m.end() + 60]).strip()
        found.append((m.group(2).strip(), near[:200]))
    return found


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--topic", required=True, help="benefits.name 完全比對")
    ap.add_argument("--keyword", required=True,
                    help="主題詞（可用 / 分隔多個同義詞）")
    ap.add_argument("--counties", type=int, default=3, help="試抓幾個縣市")
    ap.add_argument("--apply", action="store_true", help="真的寫入資料庫")
    args = ap.parse_args()

    conn = psycopg2.connect(dbname="welfare_check")
    cur = conn.cursor()
    cur.execute("""SELECT id, county FROM benefits
                    WHERE name = %s AND description LIKE '%%未查得%%'
                    ORDER BY county LIMIT %s""",
                (args.topic, args.counties))
    rows = cur.fetchall()
    if not rows:
        print(f"🔴 找不到主題「{args.topic}」的未查得項目")
        return 1

    kws = [k.strip() for k in args.keyword.split("/") if k.strip()]
    print(f"主題：{args.topic}")
    print(f"關鍵字：{' / '.join(kws)}　試抓 {len(rows)} 個縣市\n")

    hit = miss = 0
    for bid, county in rows:
        print(f"── {county} ──")
        # 🔴 多組查詢詞：單一查詢常只回 1~2 個該縣市的頁，
        #    而第一頁未必是對的主題（實測嘉義市第一筆是別的補助）。
        results = []
        for kw in kws[:2]:
            for tail in ("補助 金額 申請", "申請資格 每月"):
                try:
                    results += search(f"{county} {kw} {tail}", limit=6)
                except Exception as e:                # noqa: BLE001
                    print(f"  🔴 搜尋失敗：{str(e)[:60]}")
            if len(results) >= 12:
                break

        # 🔴 不可只取第一個命中 —— 實測嘉義市第一筆是「重病住院看護費補助」，
        #    整頁「照顧者」0 次。搜尋排序不保證主題正確。
        #    ⇒ 蒐集**所有**該縣市自己的官網結果，逐一讀到找到金額為止。
        candidates: list[str] = []
        rejected: list[str] = []
        for r in results:
            url = r.get("url", "") or ""
            if not OFFICIAL_RE.match(url) or EXCLUDE_RE.match(url):
                continue
            if not is_own_county(url, county):
                rejected.append(url.split("/")[2])
                continue
            candidates.append(url)
        # 🔴 多組查詢詞會回重複網址 —— 不去重會把同一頁讀 4 次，浪費配額
        seen: set[str] = set()
        candidates = [u for u in candidates
                      if not (u in seen or seen.add(u))]
        if not candidates:
            note = f"　（排除他縣市官網：{', '.join(rejected[:2])}）" if rejected else ""
            print(f"  ❓ 找不到 {county} 自己的官網結果{note}")
            miss += 1
            continue

        picked_url = ""
        amounts: list[tuple[str, str]] = []
        read_fail = 0
        for url in candidates[:4]:
            text = strip_noise(extract(url))
            if not text:
                read_fail += 1
                continue
            got = find_amounts(text, kws)
            if got:
                picked_url, amounts = url, got
                break
        if not amounts:
            if read_fail == len(candidates[:4]):
                print(f"  🔴 {len(candidates[:4])} 頁全部抽取失敗（非「沒有補助」）")
            else:
                print(f"  ❓ 讀了 {len(candidates[:4])} 頁，主題附近都沒有金額")
            miss += 1
            continue

        hit += 1
        raw, ctx = amounts[0]
        print(f"  ✅ {raw}　{picked_url[:54]}")
        print(f"     「{ctx[:92]}」")

        if args.apply:
            cur.execute("""UPDATE benefits
                              SET source_url = %s, source_excerpt = %s,
                                  last_verified_date = CURRENT_DATE
                            WHERE id = %s""", (picked_url, ctx[:500], bid))
    if args.apply:
        conn.commit()
        print("\n✅ 已寫入")
    else:
        print("\n（dry-run，未寫入。加 --apply 才會真的寫）")

    print(f"\n查到金額 {hit}／查不到 {miss}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
