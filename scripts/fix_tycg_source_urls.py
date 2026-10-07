#!/usr/bin/env python3
"""桃園 26 筆 opendata：把逐筆 sourceUrl 補回 benefits.source_url。

🔴 匯入時取錯欄位：`ALIAS["link"]` 把 `sourceUrl`（逐筆申辦頁）
與 `competentAuthorityUrl`（主管機關**首頁**）並列，而 `pick()` 取第一個
非空的 —— 桃園兩個欄位都有值，落到哪一個取決於 ALIAS 的順序。
結果 26 筆全部拿到首頁 ⇒ 「official 但來源是首頁」＝沒來源卻掛官方認證。

🔴 這不是「找不到網址」而是「取錯欄位」—— 原始資料裡逐筆網址一直都在。

驗證方式：渲染每個網址（SPA，`web_extract` 只拿到頁尾），
確認 `<title>` 真的含該筆補助名稱才寫入。
🔴 negative control：假 item_no 渲染後是 0 字無標題（已實測）。
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
import urllib.request
from concurrent.futures import ThreadPoolExecutor

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from render_page import render  # noqa: E402

TY_URL = ("https://opendata.tycg.gov.tw/api/dataset/"
          "b20a8017-2736-448e-86e4-4032211073d7/resource/"
          "80eecbec-9112-4f3b-9b7d-20ace73eb7b3/download")
BACKUP = "/tmp/wc_backup/tycg_sourceurl_fix.jsonl"


def fetch_rows() -> list[dict]:
    req = urllib.request.Request(TY_URL, headers={"User-Agent": "Mozilla/5.0"})
    txt = urllib.request.urlopen(req, timeout=60).read().decode("utf-8-sig", "replace")
    try:
        d = json.loads(txt)
        return d.get("data", d) if isinstance(d, dict) else d
    except json.JSONDecodeError:
        return list(csv.DictReader(io.StringIO(txt)))


def psql(sql: str) -> str:
    p = subprocess.run(["psql", "-d", "welfare_check", "-At", "-F", "\t", "-c", sql],
                       capture_output=True, text=True)
    if p.returncode:
        sys.exit(f"psql 失敗：{p.stderr}")
    return p.stdout


def norm(s: str) -> str:
    """比對標題與名稱時只去掉空白與全半形括號差異，不做模糊比對。"""
    return re.sub(r"[\s　]+", "", s or "").replace("（", "(").replace("）", ")")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--workers", type=int, default=4)
    args = ap.parse_args()

    rows = fetch_rows()
    by_name = {str(r["policyName"]).strip(): r for r in rows}
    print(f"桃園 opendata {len(rows)} 筆，名稱去重後 {len(by_name)}")

    # 只處理「首頁當來源」掃描器列出的 official 那批
    scan_path = "/tmp/wc_backup/homepage_as_source_scan.json"
    if not os.path.exists(scan_path):
        sys.exit(f"先跑 scan_homepage_as_source.py（缺 {scan_path}）")
    targets = [r for r in json.load(open(scan_path)) if r["tier"] == "official"]
    print(f"official ＋ 首頁當來源：{len(targets)} 筆")

    todo, skipped = [], []
    for t in targets:
        src = by_name.get(str(t["name"]).strip())
        if src and str(src.get("sourceUrl", "")).strip():
            todo.append((int(t["id"]), t["name"], t["url"], src["sourceUrl"].strip()))
        else:
            skipped.append((int(t["id"]), t["county"], t["name"], t["url"]))

    print(f"可從 opendata 補回：{len(todo)} 筆；對不上名稱：{len(skipped)} 筆")
    for s in skipped:
        print(f"  ⬜ [{s[0]}] {s[1]} {s[2]}　{s[3]}")

    # 🔴 渲染驗證：標題必須含該筆名稱，否則不寫
    def check(item):
        bid, name, old, new = item
        title, text = render(new, budget=12000, timeout=120)
        ok = norm(name) in norm(title) or norm(name) in norm(text[:800])
        return bid, name, old, new, title, len(text), ok

    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        results = list(ex.map(check, todo))

    good = [r for r in results if r[6]]
    bad = [r for r in results if not r[6]]
    print(f"\n渲染驗證：通過 {len(good)}／{len(results)}")
    for r in bad:
        print(f"  ❌ [{r[0]}] {r[1]}　title={r[4]!r} chars={r[5]}")
    for r in good:
        print(f"  ✅ [{r[0]}] {r[1]}　{r[3]}")

    if not args.apply:
        print("\n（--dry-run 模式，未寫入。加 --apply 才寫）")
        return 0
    if bad:
        sys.exit(f"\n🔴 有 {len(bad)} 筆驗證不通過，整批不寫入（要個別處理）")

    os.makedirs(os.path.dirname(BACKUP), exist_ok=True)
    with open(BACKUP, "w") as f:
        for r in good:
            f.write(json.dumps({"id": r[0], "name": r[1], "old_source_url": r[2],
                                "new_source_url": r[3]}, ensure_ascii=False) + "\n")
    print(f"\n備份 → {BACKUP}")

    for r in good:
        bid, new = r[0], r[3]
        psql("update benefits set source_url = {u}, updated_at = now() "
             "where id = {i}".format(u=f"$${new}$$", i=bid))
    print(f"✅ 已更新 {len(good)} 筆")
    return 0


if __name__ == "__main__":
    sys.exit(main())
