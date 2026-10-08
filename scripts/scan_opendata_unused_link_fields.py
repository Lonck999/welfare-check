#!/usr/bin/env python3
"""偵測：opendata 原始資料裡「有網址但匯入沒用到」的欄位。

🔴 為什麼需要它（2026-10-08，W-010）：
`ALIAS["link"]` 是白名單，而白名單**不會在新寫法出現時失敗** ——
它只是讓次好的選項贏（fallback 到 `src["dataset"]` 或機關首頁），
而次好的選項有值 ⇒ 匯入成功、欄位非空、`source_tier` 算得出來、
**看起來完全正常**。

同一個 bug 已經踩兩次：
- 2026-10-07 W-009：漏 `sourceUrl` ⇒ 桃園 26 筆變局處首頁
- 2026-10-08 W-010：漏 `詳細資訊連結`／`相關資訊連結`／`網址`
  ⇒ 臺中 25 筆變 data.gov.tw 目錄頁

🔴 補白名單只修掉當天那一批，並替下一種寫法重新安裝同一個 bug。
這支改成偵測**後果**：「原始資料有 http 欄位，但 `pick(row,'link')` 沒用到它」。
對未知的欄位名也有效 —— 它不需要事先知道那個欄位叫什麼。

⚠️ 這是**偵測**腳本，不改任何資料。要網路（抓各縣市開放資料）。
exit 1 = 有未使用的網址欄位（給人去決定該不該收）。
🔴 「發現未使用欄位」不等於「該收」—— 桃園的 `tyeserviceurl` 全部都是首頁，
收了就是製造 W-009 本身。**判準是那個欄位裡實際裝什麼，不是名字像不像。**
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from import_county_opendata import ALIAS, SOURCES, fetch, pick  # noqa: E402

# 🔴 已經人工判斷過「不該收」的欄位 —— 收了會製造 W-009
#    （格式：(來源 key, 欄位名): 理由）
KNOWN_REJECT = {
    ("桃園市", "tyeserviceurl"): "全部都是 e-services 首頁，不指向任何單一補助"
                                 "（收了就是 W-009 本身）",
    ("新北市", "curl"): "書表下載頁不是說明頁；逐筆說明頁由 itemId 推導"
                        "（見 fix_opendata_percase_urls.py）",
}

ALL_ALIASES = {k for names in ALIAS.values() for k in names}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", help="把結果寫成 JSON")
    ap.add_argument("--only", nargs="*", help="只掃這幾個來源 key")
    args = ap.parse_args()

    keys = args.only or list(SOURCES)
    findings: list[dict] = []

    for key in keys:
        src = SOURCES[key]
        try:
            rows = fetch(src["url"])
        except Exception as e:  # noqa: BLE001
            print(f"⚠️ {key}：抓不到（{e}）—— 跳過，不當成通過")
            findings.append({"source": key, "error": str(e)})
            continue
        if not rows:
            print(f"⚠️ {key}：0 筆")
            continue

        # 每個欄位有多少筆是 http
        http_count: dict[str, int] = defaultdict(int)
        sample: dict[str, str] = {}
        for r in rows:
            for k, v in r.items():
                s = str(v).strip()
                if s.startswith("http"):
                    http_count[k] += 1
                    sample.setdefault(k, s)

        # 匯入實際用到的 link 欄位（逐筆算，因為 pick 取第一個非空的）
        used: set[str] = set()
        for r in rows:
            got = pick(r, "link")
            if not got:
                continue
            for k in ALIAS["link"]:
                if k in r and str(r[k]).strip() == got:
                    used.add(k)
                    break

        unused = {k: n for k, n in http_count.items()
                  if k not in used and k not in ALL_ALIASES}
        rejected = {k: n for k, n in unused.items()
                    if (key, k) in KNOWN_REJECT}
        new = {k: n for k, n in unused.items() if (key, k) not in KNOWN_REJECT}

        status = "🔴" if new else "✅"
        print(f"{status} {key}（{len(rows)} 筆）"
              f"　匯入用到：{sorted(used) or '無'}")
        for k, n in sorted(new.items(), key=lambda x: -x[1]):
            print(f"    🔴 未使用的網址欄位 `{k}`：{n}/{len(rows)} 筆有 http")
            print(f"        樣本 {sample[k][:95]}")
            findings.append({"source": key, "field": k, "http_rows": n,
                             "total": len(rows), "sample": sample[k]})
        for k, n in sorted(rejected.items()):
            print(f"    ⬜ `{k}`：{n} 筆（已判定不收 —— "
                  f"{KNOWN_REJECT[(key, k)]}）")

    real = [f for f in findings if "field" in f]
    errs = [f for f in findings if "error" in f]
    print(f"\n未使用的網址欄位：{len(real)} 個"
          f"{f'；抓取失敗 {len(errs)} 個來源' if errs else ''}")
    if args.json:
        with open(args.json, "w") as f:
            json.dump(findings, f, ensure_ascii=False, indent=1)
        print(f"→ {args.json}")
    # 🔴 抓取失敗也要回非零 —— 否則「掃不到」跟「沒問題」長得一樣
    return 1 if (real or errs) else 0


if __name__ == "__main__":
    sys.exit(main())
