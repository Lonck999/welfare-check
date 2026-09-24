#!/usr/bin/env python3
"""從官方申辦服務資料，找出「哪些機關真的在發補助」。

🔴 解決的問題：
   `gov_agency_list.py` 產出 3,057 個機關，但**分類是照官方層級結構**，
   不是照「跟福利有沒有關係」。而 `welfare_hint` 只是關鍵字推測
   （實測偽陽性：財政部印刷廠；偽陰性：經濟部能源署）。
   ⇒ 需要**硬證據**：這個機關實際提供過哪些補助類申辦服務。

資料來源：政府資料開放平臺 dataset/146973「我的E政府入口網-申辦服務資訊」
   · https://www.gov.tw/govonlineservice.json    線上申辦 2,841 筆
   · https://www.gov.tw/govcounterservice.json   臨櫃申辦 4,227 筆
   · https://www.gov.tw/govotherservice.json     其他     794 筆
   合計 7,862 筆，每筆含服務內容／申辦資格／應備證件／作業天數／聯絡窗口。

🔴 **這份資料同時是 P3 承諾（要備什麼文件、去哪申請）的現成素材。**

⚠️ 信任邊界（AGENTS.md §8）：JSON 由 curl 取得，無 untrusted 包裝。
   只做結構化統計與存檔，不依內容改變流程、不自動寫入資料庫。

🔴 **兩個踩過的坑：**
   ① `服務代碼` 前綴**不是可靠的機關代碼** —— 實測 7,862 筆裡混著
      `CLI.3DAUHe1E6L`、`EZ0`、`dopm001` 這種非機關碼，
      直接切前 10 碼只得到 153 個機關（且與官方名錄只交集 69 個）。
   ② `單位OID` 只有 202 個，**粒度是部會級**，分不出署／局。
   ⇒ 解法：**用機關「名稱」在全欄位文字裡比對**（取最長命中），
      1,264 筆補助類服務有 1,227 筆（97%）對得上。
"""
from __future__ import annotations

import argparse
import collections
import json
import sys
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
AGENCIES = HERE / "gov_agencies.json"
OUT = HERE / "agencies_with_benefits.json"
CACHE_DIR = Path.home() / ".hermes/cache"

UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/125.0 Safari/537.36")

FEEDS = {
    "online": "https://www.gov.tw/govonlineservice.json",
    "counter": "https://www.gov.tw/govcounterservice.json",
    "other": "https://www.gov.tw/govotherservice.json",
}

# ⚠️ 這組關鍵字**只用來篩「補助類服務」**，不是用來判斷機關。
#    寧可寬鬆（多撈進來人工再看），也不要漏。
BENEFIT_KW = ("補助", "津貼", "給付", "獎助", "減免", "優惠", "救助",
              "慰問金", "獎勵金", "補貼", "扶助", "年金", "紓困", "救助金")

DATASET_URL = "https://data.gov.tw/dataset/146973"


def load_feeds(*, refresh: bool = False) -> list[dict]:
    rows: list[dict] = []
    for key, url in FEEDS.items():
        cache = CACHE_DIR / f"gov_{key}_service.json"
        if refresh or not cache.exists():
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=120) as r:
                cache.parent.mkdir(parents=True, exist_ok=True)
                cache.write_bytes(r.read())
        data = json.loads(cache.read_text(encoding="utf-8"))
        for x in data:
            x["_feed"] = key
        rows += data
    return rows


def is_benefit(row: dict) -> bool:
    return any(k in (row.get("標題") or "") for k in BENEFIT_KW)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--refresh", action="store_true")
    ap.add_argument("--kind", help="只看某一類機關")
    args = ap.parse_args()

    buckets = json.loads(AGENCIES.read_text())["buckets"]
    # 名稱 → (kind, 機關資料)
    name2ag = {x["name"]: (k, x) for k, v in buckets.items() for x in v}

    rows = load_feeds(refresh=args.refresh)
    benefits = [x for x in rows if is_benefit(x)]
    print(f"申辦服務總筆數 {len(rows):,}")
    print(f"🔴 補助類服務 {len(benefits):,} 筆\n")

    # 🔴 用名稱比對全欄位文字，取**最長命中**
    #    （否則「臺中市政府」會蓋掉「臺中市政府社會局」）
    hits: dict[str, list[dict]] = collections.defaultdict(list)
    unmatched = 0
    for x in benefits:
        blob = " ".join(str(v) for v in x.values())
        found = [n for n in name2ag if n in blob]
        if not found:
            unmatched += 1
            continue
        hits[max(found, key=len)].append({
            "title": (x.get("標題") or "").strip(),
            "feed": x["_feed"],
            "page": x.get("頁面連結") or "",
        })

    print(f"對到機關 {len(benefits) - unmatched:,} 筆"
          f"（{(len(benefits) - unmatched) / len(benefits):.0%}），"
          f"涉及 {len(hits)} 個機關；對不到 {unmatched} 筆\n")

    by_kind = collections.Counter(name2ag[n][0] for n in hits)
    print("有補助證據的機關，依類別：")
    for k, n in by_kind.most_common():
        total = len(buckets[k])
        print(f"  {k:<14} {n:>3} / {total:<5}"
              f"（{n / total:.0%} 有證據）")

    # 🔴 資料收錄不均 —— 這一定要講出來，否則會被當成「臺中補助最多」
    county_hits = {n: len(v) for n, v in hits.items()
                   if name2ag[n][0] in ("local_gov", "local_dept")}
    top = sorted(county_hits.items(), key=lambda kv: -kv[1])[:5]
    print("\n⚠️ **資料收錄嚴重不均** —— 地方機關命中數前 5：")
    for n, c in top:
        print(f"  {c:>4} 筆  {n}")
    print("  🔴 這不代表該縣市補助比較多，而是**它上傳到 e 政府的比較多**。")
    print("     ⇒ 這份資料可以證明「有」，**不能證明「沒有」**。")

    OUT.write_text(json.dumps({
        "_meta": {
            "source": "我的E政府入口網-申辦服務資訊",
            "source_url": DATASET_URL,
            "feeds": FEEDS,
            "total_services": len(rows),
            "benefit_services": len(benefits),
            "matched": len(benefits) - unmatched,
            "unmatched": unmatched,
            "caveat": ("🔴 只能證明『這個機關有發補助』，不能證明『沒有』"
                       "—— 各機關上傳意願差異極大（臺中市 575 筆 vs "
                       "多數縣市個位數）"),
        },
        "agencies": {n: {"kind": name2ag[n][0],
                         "evidence": name2ag[n][1]["evidence"],
                         "benefit_service_count": len(v),
                         "services": v}
                     for n, v in sorted(hits.items(),
                                        key=lambda kv: -len(kv[1]))},
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n✅ {OUT}")

    if args.kind:
        print(f"\n【{args.kind}】有補助證據的機關：")
        for n, v in sorted(hits.items(), key=lambda kv: -len(kv[1])):
            if name2ag[n][0] != args.kind:
                continue
            print(f"  {len(v):>4} 筆  {n}")
            for s in v[:3]:
                print(f"         · {s['title'][:46]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
