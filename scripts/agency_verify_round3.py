#!/usr/bin/env python3
"""第三輪（人工級）查證：**真的打開該機關的官網讀內容**。

🔴 為什麼需要第三輪 —— 前兩輪的共同缺陷：
   **只讀搜尋結果的標題與摘要，從來沒有打開過任何網頁。**
   · 第一輪查詢用機關全名 → 名稱與業務不符的機關（高齡長期照顧處）搜不到
   · 第二輪查詢用業務關鍵字 → 但 `judge()` 要求「結果必須提到機關名」，
     兩個判準互相矛盾，第二輪的結果幾乎必然被擋掉
   ⇒ 第三輪改成：**先確定該機關自己的官網網域，再抓那個網站的內容**。

🔴 判準（比前兩輪嚴格）：
   ① 先找出該機關**自己的**官網（網域必須在搜尋結果中重複出現且標題含機關名）
   ② 抓該網站首頁 + 搜尋結果頁的**實際文字**
   ③ 在文字裡找補助關鍵字，並記下出現的上下文當證據

⚠️ 仍然**不會把任何機關標成「沒有補助」** ——
   查不到只記 `note`，`has_benefit` 留 NULL。
   「我判斷它不該發」跟「查證過它沒發」是兩回事。

⚠️ 信任邊界（AGENTS.md §8）：本輪用 `web_extract`（有 untrusted 包裝），
   不用 curl。抓回的內容只做關鍵字比對與存檔，不依它改變流程。

用法：
    python scripts/agency_verify_round3.py --dry-run     # 先看判定
    python scripts/agency_verify_round3.py --limit 10
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import time
from collections import Counter

import psycopg2

from agency_verify_round2 import build_query
from agency_verify_run import (EXCLUDE_DOMAIN_RE, OFFICIAL_RE,
                               SearchUnavailable, mark, web_search)
from benefit_keywords import BENEFIT_KW, NOT_BENEFIT_CTX

HERMES = "/Users/lonck/.hermes/hermes-agent"
PY = f"{HERMES}/venv/bin/python"


def own_domain(name: str) -> tuple[str, str]:
    """找出這個機關**自己的**官網網域。

    🔴 判準：搜尋「<機關全名>」，取「標題含機關名」的官方結果中
       出現最多次的網域 —— 那才是它自己的站。
       ⚠️ 不可用「第一筆結果」：實測第一筆常是上級機關或入口網。

    🔴 **教育主管機關是 `.edu.tw` 排除規則的例外**（2026-09-24 實測）：
       `EXCLUDE_DOMAIN_RE` 擋掉所有 `.edu.tw`（因為學校會轉貼各機關公告，
       任何機關都可能命中某間學校的頁面）。
       但**教育局／教育處自己的官網就在 `.edu.tw`**
       （新竹縣教育局＝`doe.hcc.edu.tw`）⇒ 對教育類機關放行。
    """
    is_edu_agency = bool(re.search(r"教育(局|處|署|部)", name))
    try:
        results = web_search(f"{name} 官方網站")
    except SearchUnavailable:
        return "", ""

    def usable(u: str) -> bool:
        if not OFFICIAL_RE.match(u):
            return False
        if not EXCLUDE_DOMAIN_RE.match(u):
            return True
        # 教育機關：只放行 .edu.tw，其餘排除理由（採購網、法規庫…）仍成立
        return is_edu_agency and ".edu.tw" in u and not re.search(
            r"(pcc\.gov|law[s]?\.|gazette|ppg\.ly|president\.gov|data\.gov)", u)

    doms: Counter[str] = Counter()
    url_of: dict[str, str] = {}
    short = re.sub(r"^.{2,3}[市縣]政府", "", name)
    for r in results:
        u = r.get("url", "") or ""
        if not usable(u):
            continue
        title = r.get("title", "") or ""
        if name in title or (len(short) >= 3 and short in title):
            d = re.sub(r"^https?://", "", u).split("/")[0]
            doms[d] += 1
            url_of.setdefault(d, u)
    if doms:
        d = doms.most_common(1)[0][0]
        return d, url_of[d]

    # 🔴 退一步：標題沒提到機關名時，改看**描述**。
    #    實測「新竹縣政府教育局」的某些官網頁標題是「新竹縣政府全球資訊網」，
    #    嚴格比對標題會判成「找不到官網」—— 而它明明有。
    for r in results:
        u = r.get("url", "") or ""
        if not usable(u):
            continue
        blob = (r.get("title", "") or "") + (r.get("description", "") or "")
        if name in blob or (len(short) >= 3 and short in blob):
            return re.sub(r"^https?://", "", u).split("/")[0], u
    return "", ""


def extract(url: str) -> str:
    """用 Hermes 的 web_extract 抓網頁純文字（有 untrusted 包裝）。"""
    code = (
        "import asyncio,json,sys;"
        f"sys.path.insert(0,{HERMES!r});"
        "from tools import web_tools as w;"
        # 🔴 web_extract_tool 是 **async** —— 直接呼叫只會拿到 coroutine，
        #    而 coroutine 沒有內容，會靜默變成「這個機關官網沒有補助字樣」。
        # 🔴 char_limit 要夠大 —— 實測新北衛生局首頁有 33,449 字元，
        #    設 6000 會把「補助」那段截掉 ⇒ 變成假的「官網沒有補助字樣」。
        f"r=asyncio.run(w.web_extract_tool(urls=[{url!r}], char_limit=40000));"
        "print(r if isinstance(r,str) else json.dumps(r,ensure_ascii=False))"
    )
    try:
        # 🔴 必須指定 encoding="utf-8" —— 否則 subprocess 用系統預設編碼
        #    解 stdout，中文會變成 `æ°åå¸` 這種亂碼，
        #    然後關鍵字一個都比對不到 ⇒ 靜默變成「這個機關沒有補助」。
        out = subprocess.run([PY, "-c", code], capture_output=True,
                             text=True, timeout=120,
                             encoding="utf-8", errors="replace",
                             env={**os.environ, "PYTHONIOENCODING": "utf-8"})
    except subprocess.TimeoutExpired:
        return ""
    if out.returncode != 0:
        return ""
    try:
        data = json.loads(out.stdout)
        if isinstance(data, str):
            data = json.loads(data)
    except Exception:
        return out.stdout[:8000]
    parts = []
    for r in (data or {}).get("results", []):
        parts.append(str(r.get("content") or ""))
    return "\n".join(parts)


def find_benefit(text: str) -> tuple[list[str], str]:
    """在網頁內文裡找補助關鍵字，回傳 (命中字, 上下文證據)。

    🔴 **命中關鍵字 ≠ 這個機關在發補助**（2026-09-24 實測，26 筆有 18 筆誤判）。
       「補助」二字在政府網站無所不在，而這些全都不是民眾可申請的福利：

       · 「[是否受機關補助] 否」                  表單欄位
       · 「補助計畫項下財產免填送」               財產申報表說明
       · 「利益衝突迴避暨**補助**交易身分關係」    系統名稱
       · 「中央各部會補助款」                    中央撥給地方的錢
       · 「拆遷補償>人口搬遷補助費」              工程拆遷補償
       · 「差旅費報支暨…講習費用補助要點」        公務員報帳

       ⇒ 先用 `NOT_BENEFIT_CTX` 把這些上下文剔除，再看剩下的有沒有命中。
       ⚠️ 這只降低誤判率，**不保證正確** —— 最終仍需人工讀證據。
    """
    for pat in NOT_BENEFIT_CTX:
        text = re.sub(pat, " ", text)
    hits, ctx = [], ""
    for k in BENEFIT_KW:
        m = re.search(r".{0,28}" + re.escape(k) + r".{0,28}", text)
        if m:
            hits.append(k)
            if not ctx:
                ctx = re.sub(r"\s+", " ", m.group(0)).strip()
    return hits, ctx


def pages_to_read(name: str, dom: str, home: str) -> list[str]:
    """要讀哪些頁 —— 🔴 只讀首頁不夠。

    實測臺中市建設局首頁 10,871 字元**完全沒有「補助」**，
    但它確實有「公寓大廈修繕補助」—— 補助資訊在內頁。
    ⇒ 除了首頁，再用站內限定搜尋（`site:`）找該機關自己的補助頁。
    """
    urls = [home]
    try:
        for r in web_search(f"site:{dom} 補助 申請"):
            u = r.get("url", "") or ""
            if dom in u and u not in urls:
                urls.append(u)
            if len(urls) >= 3:
                break
    except SearchUnavailable:
        pass
    return urls


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=60)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    with psycopg2.connect(dbname="welfare_check") as c, c.cursor() as cur:
        cur.execute("""SELECT name, stage FROM agency_verification
                        WHERE has_benefit IS NULL AND stage <= 4
                        ORDER BY stage, name LIMIT %s""", (args.limit,))
        rows = cur.fetchall()

    print(f"第三輪（讀網頁內容）：{len(rows)} 個機關"
          f"{'　dry-run' if args.dry_run else ''}\n")
    found = nosite = noben = nofetch = 0
    for i, (name, _stage) in enumerate(rows, 1):
        dom, home = own_domain(name)
        if not dom:
            nosite += 1
            print(f"  [{i:>2}] 🔴 找不到自己的官網　{name}")
            if not args.dry_run:
                mark(name, None, "", "第三輪：搜尋不到該機關自己的官網",
                     "web 第三輪（讀內容）")
            time.sleep(0.5)
            continue

        urls = pages_to_read(name, dom, home)
        text, used = "", ""
        for u in urls:
            t = extract(u)
            if len(t) >= 200:
                text += "\n" + t
                used = used or u
            if find_benefit(text)[0]:
                used = u
                break

        # 🔴 抓不到內容 ≠ 官網沒有補助 —— 那是**抽取失敗**。
        #    實測 web_extract_tool 是 async，忘了 await 會回 coroutine，
        #    len()=0 然後靜默變成「這個機關沒有補助字樣」。
        #    ⇒ 內容太短一律視為失敗，不可下任何結論。
        if len(text) < 200:
            nofetch += 1
            print(f"  [{i:>2}] 🔴 官網抓不到內容（{len(text)} 字元）　{name}"
                  f"　{dom}")
            if not args.dry_run:
                mark(name, None, home,
                     f"第三輪：找到官網 {dom} 但內容抽取失敗"
                     f"（{len(text)} 字元）—— 未能判定",
                     "web 第三輪（抽取失敗）")
            time.sleep(0.5)
            continue

        hits, ctx = find_benefit(text)
        if hits:
            found += 1
            note = (f"第三輪讀官網內容：命中「{'／'.join(hits[:4])}」"
                    f"｜證據：{ctx[:70]}")
            print(f"  [{i:>2}] ✅ 有　{name}")
            print(f"       {dom}（讀了 {len(urls)} 頁 / {len(text)} 字元）"
                  f"　命中 {hits[:4]}")
            print(f"       「{ctx[:64]}」")
            if not args.dry_run:
                mark(name, True, used or home, note, "web 第三輪（讀官網內容）")
        else:
            noben += 1
            note = (f"第三輪已讀官網 {dom} 共 {len(urls)} 頁 / {len(text)} 字元，"
                    f"未出現任何補助關鍵字 —— 仍不代表沒有")
            print(f"  [{i:>2}] ❓ 官網無補助字樣　{name}　（{dom}，"
                  f"{len(urls)} 頁 / {len(text)} 字元）")
            if not args.dry_run:
                mark(name, None, home, note, "web 第三輪（讀官網內容）")
        time.sleep(0.5)

    print(f"\n第三輪：翻正 {found}　官網無補助字樣 {noben}　"
          f"找不到官網 {nosite}　🔴 抽取失敗 {nofetch}")
    print("🔴 後兩者一律留 NULL —— 「查不到」不可寫成「沒有」。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
