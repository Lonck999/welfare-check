#!/usr/bin/env python3
"""補回 opendata 180 筆的逐筆來源網址（新北 148／臺中 25／南投 6／臺南 1）。

🔴 根因與桃園那 26 筆（`fix_tycg_source_urls.py`，W-009）完全同形：
**匯入時丟掉了原始資料本來就有的逐筆網址**，不是「找不到網址」。
但這批的「丟掉方式」有兩種，而且第二種更隱蔽：

| 縣市 | 原始欄位 | 為什麼沒進資料庫 |
|---|---|---|
| 臺中 25 | `詳細資訊連結`／`相關資訊連結`／`網址` | 🔴 **`ALIAS["link"]` 根本沒有這三個名字** —— 只有 `詳細資訊[連結]`（帶方括號，臺南的寫法）與 `詳細資訊網址`／`詳細資訊`。差一個字就 fallback 到 `src["dataset"]`（＝data.gov.tw 目錄頁） |
| 新北 148 | **沒有**逐筆網址欄位 | 它只有 `curl`（**書表下載**頁，77/149 有值）。🔴 但同一個 `itemId` 換成 `CaseData.action` 就是完整案件說明頁 —— 網址要**推導**不是直接讀 |
| 南投 6／臺南 1 | `詳細資訊`／`詳細資訊[連結]` | ✅ 原始資料**真的是空的**（實測逐筆列出來看過）—— 這 7 筆無解，不是 bug |

🔴 **新北那 148 筆的推導鏈（三個來源才拼得出來）**：
① 福利資料集的 `curl` 欄位 `DownloadForm.action?itemId=112074` → 取出 itemId
② itemId 換路徑 → `CaseData.action?itemId=112074` ＝ 案件說明頁
③ `curl` 為空的 70 筆：改用「新北市申辦e服務」資料集（1,505 筆 ITEM_ID＋ITEM_NAME）
   按名稱配對 —— ⚠️ 只接受**唯一命中**，多重命中一律不寫（實測 0 筆多重）

⚠️ **e服務清單的 JSON API 封頂 500 筆**（`?size=3000` 照樣只回 500，
且 `skip` 參數無效 —— 四次分頁拿到完全一樣的 500 筆）。
🔴 **必須用 `/csv/file` 全檔**才拿得到 1,505 筆。
拿 500 筆配對的話名稱命中率從 2 筆變 2 筆（巧合），但**無法證明沒漏**。

🔴 **抓 service.ntpc.gov.tw 必須用 curl 不可用 urllib**：
它不關閉連線 ⇒ `urllib.urlopen(timeout=30)` 每筆都卡滿 30.2 秒
（實測 79 筆 ＝ 40 分鐘，而且背景跑到變 zombie），curl 同一頁 0.8 秒。
⚠️ 症狀是「腳本看起來在跑但永遠不結束」，不是錯誤。

## 驗證方式（逐筆，不抽樣）

比對「頁面標題／正文**含不含該筆補助名稱**」才寫入：
- 新北：`<h2>` 必須與 `name` **完全相等**（該站的 h2 就是案件名稱）
- 臺中：`<title>` 或正文含 `name`（該站標題格式是「社會局全球資訊網-類別-名稱」）

🔴 **這道驗證不是形式** —— 它攔下 3 筆臺中：
- **739 中低收入老人補助裝置假牙** → 那個網址的頁面是「**愛心手鍊**」
  ⚠️ **開放資料自己把逐筆網址填錯了**。沒做名稱比對就會寫進一個
  講別的補助的官方頁面 ＝ 正好製造出 W-001（佐證講別的東西）
- **745 重陽節敬老禮金**／**729 原住民族急難救(補)助** → 頁面已不存在（找不到網頁）
以及 1 筆新北（**686 體育獎學金申請撥付**，itemId 105006 已失效）。

🔴 **negative control 兩道都要**（只有①會讓「全部都通過」的 bug 全綠）：
① 假 id／假 itemId 必須判不通過
② 真頁面配一個不相干的名稱必須判不符

## source_tier

補完網址後 tier 從 `opendata` 升 `official` —— 新網址是
`service.ntpc.gov.tw`／`society.taichung.gov.tw`／`ipd.taichung.gov.tw`，
都是 .gov.tw **原始公告頁**，符合 migration 20260929 對 official 的定義。
⚠️ 驗證不通過、以及南投/臺南那 7 筆**維持 `opendata` 不動**。
"""
from __future__ import annotations

import argparse
import csv
import io
import json
import os
import re
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import psycopg2  # noqa: E402

from import_county_opendata import SOURCES, fetch, pick  # noqa: E402

BACKUP = Path("/tmp/wc_backup/opendata_percase_url_fix.jsonl")

# 🔴 新北 e服務項目清單：必須用 /csv/file（JSON API 封頂 500 筆，見 docstring）
NTPC_ITEMS_CSV = ("https://data.ntpc.gov.tw/api/datasets/"
                  "394d1632-69fc-4792-a74d-88f5b1b46036/csv/file")
NTPC_CASE = "https://service.ntpc.gov.tw/eservice/CaseData.action?itemId={}"

# 🔴 臺中三個資料集各自用不同欄位名放同一件事 —— 一個都不能漏
TC_LINK_FIELDS = ("詳細資訊連結", "相關資訊連結", "網址")
TC_SOURCES = ["臺中市-112090", "臺中市-112084", "臺中市-138591",
              "臺中市-138588", "臺中市-138589"]


def norm(s: str) -> str:
    """只去空白與全半形括號差異，不做模糊比對。"""
    return re.sub(r"[\s　]+", "", s or "").replace("（", "(").replace("）", ")")


def curl(url: str, timeout: int = 30) -> str:
    """🔴 必須用 curl，不可用 urllib（見 docstring）。"""
    p = subprocess.run(
        ["curl", "-s", "-L", "--max-time", str(timeout), "-A", "Mozilla/5.0", url],
        capture_output=True, text=True,
    )
    return p.stdout


def ntpc_h2(item_id: str) -> tuple[str | None, str]:
    """新北案件說明頁的 <h2> ＝ 案件名稱。回傳 (正規化標題, 錯誤原因)。"""
    raw = curl(NTPC_CASE.format(item_id))
    if not raw:
        return None, "抓取失敗（空回應）"
    if "網頁不存在" in raw or "Page Not Available" in raw:
        return None, "404 頁"
    m = re.search(r"<h2>(.*?)</h2>", raw, re.S)
    return (norm(m.group(1)), "") if m else (None, "無 <h2>")


def page_has_name(url: str, name: str) -> tuple[bool, str]:
    """頁面標題或正文含不含該筆名稱。"""
    raw = curl(url)
    if not raw:
        return False, "抓取失敗"
    m = re.search(r"<title[^>]*>(.*?)</title>", raw, re.S | re.I)
    title = m.group(1).strip() if m else ""
    body = re.sub(r"<script.*?</script>", " ", raw, flags=re.S | re.I)
    body = re.sub(r"<style.*?</style>", " ", body, flags=re.S | re.I)
    body = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", body))
    if norm(name) in norm(title):
        return True, "title"
    if norm(name) in norm(body):
        return True, "body"
    return False, f"名稱不在頁面內 title={title[:40]!r}"


def db_rows(cur, county: str) -> dict[str, tuple[int, str, str]]:
    cur.execute(
        "SELECT id, name, source_url, source_tier FROM benefits "
        "WHERE county = %s AND source_url LIKE %s",
        (county, "%data.gov.tw%"))
    return {norm(n): (i, u, t) for i, n, u, t in cur.fetchall()}


def plan_taichung(cur) -> list[tuple[int, str, str, str]]:
    """回傳 [(id, name, old_url, new_url)]。"""
    db = db_rows(cur, "臺中市")
    out, seen = [], set()
    for key in TC_SOURCES:
        for r in fetch(SOURCES[key]["url"]):
            nm = norm(pick(r, "name"))
            if nm not in db or nm in seen:
                continue
            new = next((str(r.get(k, "")).strip() for k in TC_LINK_FIELDS
                        if str(r.get(k, "")).strip().startswith("http")), "")
            if new:
                seen.add(nm)
                bid, old, _ = db[nm]
                out.append((bid, pick(r, "name"), old, new))
    return out


def plan_ntpc(cur) -> tuple[list[tuple[int, str, str, str]], list[tuple]]:
    """回傳 (可推導的清單, 推不出 itemId 的清單)。"""
    db = db_rows(cur, "新北市")
    # e服務項目清單（1,505 筆）
    items = list(csv.DictReader(io.StringIO(
        curl(NTPC_ITEMS_CSV, timeout=60).lstrip("\ufeff"))))
    by_name: dict[str, list[dict]] = {}
    for it in items:
        by_name.setdefault(norm(it["ITEM_NAME"]), []).append(it)
    print(f"  新北 e服務清單 {len(items)} 筆（唯一名稱 {len(by_name)}）")
    # 🔴 封頂偵測：JSON API 只回 500，CSV 應該遠多於此
    if len(items) <= 500:
        sys.exit("🔴 e服務清單只有 %d 筆 —— 疑似被 API 封頂，"
                 "無法證明沒漏，整批不處理" % len(items))

    out, unresolved = [], []
    for r in fetch(SOURCES["新北市"]["url"]):
        nm = norm(pick(r, "name"))
        if nm not in db:
            continue
        bid, old, _ = db[nm]
        m = re.search(r"itemId=(\d+)", str(r.get("curl", "")))
        if m:
            out.append((bid, pick(r, "name"), old,
                        NTPC_CASE.format(m.group(1))))
            continue
        cands = by_name.get(nm, [])
        if len(cands) == 1:
            out.append((bid, pick(r, "name"), old,
                        NTPC_CASE.format(cands[0]["ITEM_ID"])))
        else:
            # 🔴 多重命名一律不寫 —— 猜錯會寫進講別的補助的頁面
            unresolved.append((bid, pick(r, "name"),
                               f"{len(cands)} 筆同名" if cands else "清單無此名"))
    return out, unresolved


def verify(todo: list[tuple[int, str, str, str]], workers: int):
    """逐筆驗證，回傳 (通過, 不通過)。"""
    def one(t):
        bid, name, old, new = t
        if "service.ntpc.gov.tw" in new:
            iid = re.search(r"itemId=(\d+)", new).group(1)
            title, err = ntpc_h2(iid)
            if title is None:
                return ("bad", bid, name, old, new, err)
            # 🔴 新北用「完全相等」—— 該站 h2 就是案件名稱，不該放寬
            if title == norm(name):
                return ("ok", bid, name, old, new, "h2")
            return ("bad", bid, name, old, new, f"h2 不符: {title[:40]}")
        ok, why = page_has_name(new, name)
        return (("ok" if ok else "bad"), bid, name, old, new, why)

    with ThreadPoolExecutor(max_workers=workers) as ex:
        out = list(ex.map(one, todo))
    return ([x[1:] for x in out if x[0] == "ok"],
            [x[1:] for x in out if x[0] == "bad"])


def negative_controls(sample_ntpc: str | None, sample_tc: str | None) -> None:
    """🔴 兩道都要：①假 id 判不通過 ②真頁面配錯名稱判不符。"""
    t, err = ntpc_h2("99999999")
    assert t is None, f"🔴 NC① 假 itemId 竟抓到標題 {t!r} —— 判準無鑑別力"
    print(f"  NC① 新北假 itemId → 不通過（{err}）✅")

    if sample_ntpc:
        iid = re.search(r"itemId=(\d+)", sample_ntpc).group(1)
        real, _ = ntpc_h2(iid)
        assert real is not None, "🔴 NC② 前提壞了：真 itemId 抓不到 h2"
        assert real != norm("完全不相干的補助名稱"), "🔴 NC② 名稱比對無效"
        print("  NC② 新北真頁面配錯名稱 → 判不符 ✅")

    if sample_tc:
        fake = sample_tc.rsplit("/", 2)[0] + "/99999999/post"
        ok, _ = page_has_name(fake, "中低收入老人生活津貼")
        assert not ok, "🔴 NC① 臺中假網址竟通過 —— 判準無鑑別力"
        print("  NC① 臺中假網址 → 不通過 ✅")
        ok2, _ = page_has_name(sample_tc, "完全不相干的補助名稱")
        assert not ok2, "🔴 NC② 臺中名稱比對無效"
        print("  NC② 臺中真頁面配錯名稱 → 判不符 ✅")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--workers", type=int, default=6)
    ap.add_argument("--only", choices=["ntpc", "taichung"])
    args = ap.parse_args()

    env = Path(__file__).resolve().parent.parent / "backend" / ".env"
    for line in env.read_text().splitlines():
        if line.startswith("DATABASE_URL="):
            os.environ.setdefault("DATABASE_URL", line.split("=", 1)[1])
    conn = psycopg2.connect(os.environ["DATABASE_URL"])
    cur = conn.cursor()

    todo: list[tuple[int, str, str, str]] = []
    unresolved: list[tuple] = []
    if args.only != "taichung":
        print("【新北市】")
        a, u = plan_ntpc(cur)
        todo += a
        unresolved += u
        print(f"  可推導逐筆網址 {len(a)} 筆；推不出 {len(u)} 筆")
    if args.only != "ntpc":
        print("【臺中市】")
        b = plan_taichung(cur)
        todo += b
        print(f"  原始資料有逐筆網址 {len(b)} 筆")

    print(f"\n待驗證合計 {len(todo)} 筆")
    ok, bad = verify(todo, args.workers)
    print(f"\n✅ 驗證通過 {len(ok)}　❌ 不通過 {len(bad)}")
    for x in bad:
        print(f"  ❌ [{x[0]}] {x[1]}　{x[3]}　← {x[4]}")

    print("\nnegative control：")
    negative_controls(
        next((x[3] for x in ok if "ntpc" in x[3]), None),
        next((x[3] for x in ok if "taichung" in x[3]), None))

    if unresolved:
        print(f"\n⬜ 推不出網址（維持 opendata 不動）{len(unresolved)} 筆：")
        for x in unresolved[:10]:
            print(f"    [{x[0]}] {x[1]}　{x[2]}")
        if len(unresolved) > 10:
            print(f"    …另 {len(unresolved) - 10} 筆")

    if not args.apply:
        print("\n（dry-run，未寫入。加 --apply 才寫）")
        return 0
    if not ok:
        sys.exit("🔴 沒有任何一筆通過驗證，不寫入")

    BACKUP.parent.mkdir(parents=True, exist_ok=True)
    cur.execute("SELECT id, source_url, source_tier FROM benefits "
                "WHERE id = ANY(%s)", ([x[0] for x in ok],))
    snap = {i: (u, t) for i, u, t in cur.fetchall()}
    with BACKUP.open("w") as f:
        for x in ok:
            f.write(json.dumps(
                {"id": x[0], "name": x[1],
                 "old_source_url": snap[x[0]][0],
                 "old_source_tier": snap[x[0]][1],
                 "new_source_url": x[3], "new_source_tier": "official"},
                ensure_ascii=False) + "\n")
    print(f"\n逐筆快照 → {BACKUP}")

    for x in ok:
        cur.execute(
            "UPDATE benefits SET source_url = %s, source_tier = 'official', "
            "last_verified_date = CURRENT_DATE, updated_at = now() WHERE id = %s",
            (x[3], x[0]))
    conn.commit()
    print(f"✅ 已更新 {len(ok)} 筆（source_url ＋ tier → official）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
