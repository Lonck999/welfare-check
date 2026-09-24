#!/usr/bin/env python3
"""逐一清查機關有沒有發補助（照中央→地方→其他順序）。

🔴 為什麼需要逐一查：
   e 政府申辦服務資料只能證明「有」，**不能證明「沒有」** ——
   6 個已知在發補助的機關它只收錄 4 個（國健署、能源署掛零）。
   ⇒ 剩下的 482 個必須逐一去查官網。

🔴 進度寫資料庫（`agency_verification`）不寫檔案：
   482 次查證必跨 session，沒落地的進度 = 每次中斷重來。

⚠️ 信任邊界（AGENTS.md §8）：`web_search` 有 untrusted 包裝，
   但本腳本只**記錄搜尋結果的標題與網址**，不依內容改變流程。
   🔴 判定「有沒有補助」由人看過再 `--mark`，腳本只負責蒐證。

用法：
    python scripts/agency_verify_run.py --status
    python scripts/agency_verify_run.py --next 20           # 看下一批
    python scripts/agency_verify_run.py --search 20         # 實際查證一批
    python scripts/agency_verify_run.py --mark "機關名" --has-benefit \\
           --url https://... --note "..."
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
import time

import psycopg2

from benefit_keywords import BENEFIT_KW, OFFICIAL_DOMAIN_RE

DB = "welfare_check"
STAGE_LABEL = {
    1: "中央二級（部／會）",
    2: "中央三級・直屬部會（署／局）★主力",
    3: "縣市政府",
    4: "地方一級局處 ★主力",
    5: "中央三級・其他",
}

# 🔴 關鍵字與官方網域判準來自 benefit_keywords.py（唯一來源）
#    ⚠️ 不可在這裡另外定義一份 —— 2026-09-24 就是因為兩支腳本各自
#    維護，導致同一個機關有兩種答案。
# 🔴 這些官方網域雖然是 gov.tw，但**內容不是福利** ——
#    採信它們會系統性誤判（2026-09-24 實測）：
#    · `web.pcc.gov.tw` 政府電子採購網 —— 招標公告，「補助」只是表格欄位名，
#      害「財政部印刷廠」被判成有發補助。
#      ⚠️ 任何機關都會出現在採購網上，所以這個誤判**對全部 467 筆都成立**。
#    · `law.moj.gov.tw` / `*.law.*` 法規資料庫 —— 法條全文必然提到補助，
#      但那不代表**這個機關**在發。
#    · 🔴 **`*.edu.tw` 學校網站**（2026-09-24 實測 39 筆誤用）——
#      「大陸委員會香港辦事處」的證據是 `hk.edu.tw`、
#      「臺中市研考會」是 `music.thu.edu.tw`（東海大學音樂系）。
#      學校會轉貼各機關的獎助公告，所以**任何機關都可能命中某間學校的頁面**。
#    · 公報／立法院（`gazette.nat`、`ppg.ly.gov.tw`）—— 公報全文會提到
#      各種補助，但那是「立法院的公報」不是該機關的服務頁。
#    · 開放資料平台（`data.gov.tw`）—— 那是資料集目錄，不是申辦頁。
EXCLUDE_DOMAIN_RE = re.compile(
    r"https?://[^/]*("
    r"pcc\.gov\.tw"            # 政府電子採購網（招標公告）
    r"|law[s]?\.[^/]*gov\.tw"  # 各級法規資料庫（含 laws.taipei）
    r"|law\.moj\.gov\.tw|lawbank|edu\.law"
    r"|\.edu\.tw"              # 🔴 所有學校網站
    r"|gazette\.nat\.gov\.tw"  # 政府公報
    r"|ppg\.ly\.gov\.tw|\.ly\.gov\.tw"   # 立法院
    r"|president\.gov\.tw"     # 總統府公報
    r"|data\.gov\.tw|data\.nat\.gov\.tw"  # 開放資料目錄
    r")")

OFFICIAL_RE = re.compile(OFFICIAL_DOMAIN_RE)


class SearchBackendError(RuntimeError):
    """搜尋後端本身失敗（非「查不到」）。

    🔴 這兩件事必須嚴格分開：
       · 後端掛了     → 重試；重試完還是掛 → 標「查不到」並**記下原因**
       · 真的查不到    → 標「查不到」
    合併成同一個值的話，事後永遠分不出哪些機關需要重查。
    """


class SearchUnavailable(RuntimeError):
    """重試用盡，這一筆無法判定。"""


def conn():
    return psycopg2.connect(dbname=DB)


def show_status() -> None:
    with conn() as c, c.cursor() as cur:
        cur.execute("""
            SELECT stage,
                   count(*) FILTER (WHERE status = 'done'),
                   count(*) FILTER (WHERE status = 'pending'),
                   count(*) FILTER (WHERE status = 'done' AND has_benefit),
                   count(*)
              FROM agency_verification GROUP BY 1 ORDER BY 1""")
        print("階段  類別                                已查  待查  有補助  合計")
        tot_d = tot_p = 0
        for s, d, p, hb, t in cur.fetchall():
            tot_d += d
            tot_p += p
            print(f"  {s}   {STAGE_LABEL[s]:<32} {d:>4} {p:>5} {hb:>6} {t:>6}")
        print(f"\n已查 {tot_d}　待查 {tot_p}")
        cur.execute("""SELECT count(*) FROM agency_verification
                        WHERE status = 'pending' AND stage <= 4""")
        print(f"🔴 階段 1-4（實際要查的）待查 {cur.fetchone()[0]}")


def next_batch(n: int) -> list[tuple]:
    """取下一批待查機關 —— 🔴 照階段順序，同階段內 hint 優先。"""
    with conn() as c, c.cursor() as cur:
        cur.execute("""
            SELECT name, kind, stage, org_code FROM agency_verification
             WHERE status = 'pending' AND stage <= 4
             ORDER BY stage, welfare_hint DESC, name
             LIMIT %s""", (n,))
        return cur.fetchall()


def web_search(query: str, *, retries: int = 4) -> list[dict]:
    """呼叫 Hermes 的 web_search（有 untrusted 包裝的那條路）。

    🔴 不用 curl —— AGENTS.md §8：curl 抓外部網頁沒有信任邊界。

    🔴 **後端失敗必須跟「真的查不到」分開**（2026-09-24 血淋淋的教訓）：
       原本用 ddgs 後端，實測 **67%** 的呼叫因為 startpage/yahoo
       連線被拒而失敗，而程式把失敗當成「查不到」寫進資料庫。
       已改用 exa（實測 8/8 穩定），但這道防線要留著 ——
       任何後端都可能掛，而掛掉時「查無」跟「沒有」長得一模一樣。
    """
    backend_errors: list[str] = []
    for attempt in range(retries):
        try:
            hits = _search_once(query)
        except SearchBackendError as e:
            backend_errors.append(str(e))
        else:
            if hits:
                return hits
            # 後端正常但真的沒結果 —— 這才是「查不到」
            return []
        if attempt < retries - 1:
            time.sleep(2.0 * (attempt + 1))
    raise SearchUnavailable(
        f"後端連續失敗 {retries} 次：{backend_errors[-1][:120]}")


def _search_once(query: str) -> list[dict]:
    """呼叫 Hermes 的 web_search（有 untrusted 包裝的那條路）。

    🔴 不用 curl —— AGENTS.md §8：curl 抓外部網頁沒有信任邊界。
    """
    code = (
        "import json,sys;"
        "sys.path.insert(0,'/Users/lonck/.hermes/hermes-agent');"
        "from tools import web_tools as w;"
        f"r=w.web_search_tool({query!r}, limit=8);"
        "print(json.dumps(r,ensure_ascii=False))"
    )
    out = subprocess.run(
        ["/Users/lonck/.hermes/hermes-agent/venv/bin/python", "-c", code],
        capture_output=True, text=True, timeout=90)
    if out.returncode != 0:
        # 🔴 不可靜默回空 —— 那會讓整批被標成「查不到」，
        #    而「查不到」跟「真的沒有」在資料上長得一模一樣。
        raise RuntimeError(
            f"web_search 失敗（exit {out.returncode}）：{out.stderr[-300:]}")
    import json as _j
    try:
        data = _j.loads(out.stdout)
        # ⚠️ web_search_tool 回的是 **JSON 字串**，不是 dict ——
        #    第一版直接 .get() 炸掉。可能要解兩層。
        if isinstance(data, str):
            data = _j.loads(data)
    except Exception as e:
        raise RuntimeError(f"web_search 回傳非 JSON：{out.stdout[:200]}") from e

    data = data or {}
    # 🔴 **最重要的一段**：後端失敗時回的是 `success: false` + error，
    #    而不是空結果。2026-09-24 實測 ddgs 後端 67% 的呼叫長這樣
    #    （startpage / yahoo Connection refused），
    #    而第一版把它當成「搜尋不到」寫進資料庫 ——
    #    **「後端掛了」和「真的沒有」在資料上完全分不出來**。
    #    ⇒ 失敗必須拋出來，讓重試接手；重試後仍失敗要標成「查不到」。
    if data.get("success") is False:
        raise SearchBackendError(str(data.get("error", ""))[:200])
    return data.get("data", {}).get("web", []) or []


def judge(name: str, results: list[dict]) -> tuple[bool | None, str, str]:
    """從搜尋結果判定 —— 🔴 只採信官方網域，且結果必須真的在講這個機關。

    回傳 (has_benefit, url, note)。
    has_benefit=None 代表**查不到，不是沒有** ——
    這個區別是整個專案最重要的一條。

    🔴 2026-09-24 實測的兩個誤判（都會安靜產生錯資料）：
       ① 「財政部印刷廠」被判成有補助 ——
          因為搜尋回了 `service.moea.gov.tw`（經濟部的網站，
          **不是印刷廠的**），而那頁當然提到「補助」。
          ⇒ 光看「官方網域 + 有補助字樣」不夠，
             **標題或描述必須真的提到這個機關**。
       ② 搜尋偶發回空 → 被判「查無」（已由 web_search 重試處理）。
    """
    official = [r for r in results
                if OFFICIAL_RE.match(r.get("url", "") or "")
                and not EXCLUDE_DOMAIN_RE.match(r.get("url", "") or "")]

    # 🔴 機關名稱的可辨識片段：去掉上級機關前綴後的本名
    #    「財政部印刷廠」→「印刷廠」；「衛生福利部國民健康署」→「國民健康署」
    short = re.sub(r"^.*?(部|會|委員會|總處|署|政府)(?=[^部會署]{2,})", "", name)
    short = short or name

    about_this = []
    for r in official:
        blob = (r.get("title", "") or "") + (r.get("description", "") or "")
        if name in blob or (len(short) >= 3 and short in blob):
            about_this.append((r, blob))

    for r, blob in about_this:
        hits = [k for k in BENEFIT_KW if k in blob]
        if hits:
            return True, r["url"], f"官方頁面提到：{'／'.join(hits[:3])}"

    if about_this:
        return None, about_this[0][0]["url"], (
            "🔴 找到該機關官方頁面但沒看到補助字樣 —— 待人工確認")
    if official:
        return None, official[0]["url"], (
            f"🔴 官方結果沒有提到「{short}」—— 可能是上級機關的頁面，待人工確認")
    if not results:
        return None, "", "🔴 搜尋回空（已重試 3 次）—— 待人工確認"
    return None, "", "🔴 搜尋不到官方頁面 —— 待人工確認"


def mark(name: str, has_benefit: bool | None, url: str, note: str,
         source: str = "web_search 查證") -> None:
    with conn() as c, c.cursor() as cur:
        cur.execute("""
            UPDATE agency_verification
               SET status = 'done', has_benefit = %s, evidence_url = %s,
                   evidence_source = %s, note = %s, verified_at = now()
             WHERE name = %s""", (has_benefit, url, source, note, name))
        if cur.rowcount == 0:
            print(f"🔴 找不到機關「{name}」")
            sys.exit(1)
        c.commit()


def run_search(n: int) -> None:
    batch = next_batch(n)
    if not batch:
        print("✅ 階段 1-4 全部查完")
        return
    print(f"開始查證 {len(batch)} 個機關\n")
    stats = {"yes": 0, "unknown": 0, "failed": 0}
    for i, (name, kind, stage, _code) in enumerate(batch, 1):
        try:
            results = web_search(f"{name} 補助 申請")
            hb, url, note = judge(name, results)
            # ⚠️ 判不出來時再搜一次，換用詞（很多機關只寫「減免」「退稅」）
            if hb is None:
                time.sleep(1)
                hb, url, note = judge(
                    name, web_search(f"{name} 津貼 減免 退稅 申請資格"))
        except SearchUnavailable as e:
            # 🔴 **不可標成 done** —— 後端掛掉不是「這個機關沒有補助」。
            #    留在 pending，下次重跑會再查到它。
            stats["failed"] += 1
            print(f"  [{i:>3}/{len(batch)}] 🔴 後端失敗（保持待查）　{name}")
            print(f"          {e}")
            time.sleep(3)
            continue
        mark(name, hb, url, note)
        flag = "✅ 有" if hb else "❓ 待確認"
        stats["yes" if hb else "unknown"] += 1
        print(f"  [{i:>3}/{len(batch)}] {flag}　{name}")
        print(f"          {note}")
        if url:
            print(f"          {url[:88]}")
        time.sleep(0.4)
    print(f"\n本批：有補助 {stats['yes']}　待人工確認 {stats['unknown']}"
          f"　🔴 後端失敗未判定 {stats['failed']}")
    print("🔴 「待人工確認」不等於「沒有補助」 —— "
          "只代表搜尋沒找到官方證據。")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--status", action="store_true")
    ap.add_argument("--next", type=int, metavar="N", help="預覽下一批")
    ap.add_argument("--search", type=int, metavar="N", help="實際查證一批")
    ap.add_argument("--mark", metavar="NAME")
    ap.add_argument("--has-benefit", action="store_true")
    ap.add_argument("--no-benefit", action="store_true")
    ap.add_argument("--url", default="")
    ap.add_argument("--note", default="")
    args = ap.parse_args()

    if args.status:
        show_status()
    elif args.next:
        for name, kind, stage, code in next_batch(args.next):
            print(f"  [{stage}] {name}　{code}")
    elif args.search:
        run_search(args.search)
    elif args.mark:
        hb = True if args.has_benefit else (False if args.no_benefit else None)
        mark(args.mark, hb, args.url, args.note, "人工查證")
        print(f"✅ 已標記 {args.mark}")
    else:
        show_status()
    return 0


if __name__ == "__main__":
    sys.exit(main())
