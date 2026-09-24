#!/usr/bin/env python3
"""從人事行政總處官方名錄，篩出 welfare-check 需要的機關清單。

資料來源：政府資料開放平臺 dataset/7307「行政院所屬中央及地方機關代碼」
          → https://www.dgpa.gov.tw/open/code/orglist.csv
          （人事行政總處維護，17,412 筆，含層級與裁撤註記）

🔴 為什麼不用維基或 regex 抓：
   2026-09-24 實測用 regex 從維基沿革文字抓「XX署／XX局」，
   撈出一堆**已裁撤**的（內政部兒童局、行政院衛生署、交通部電信總局）
   與**不相干**的（地方檢察署、國安局、參謀本部軍醫局）。
   ⚠️ 那份清單看起來很完整，但把死掉的機關寫進文件 = 之後去抓一個不存在的網站。

篩選邏輯：
   · 排除已裁撤（裁撤註記 = 是）
   · 中央：層級 2（部/會）與 3（署/局）
   · 地方：縣市政府本身與其一級局處
   · ⚠️ 不含四級（分署/分局）與鄉鎮市區公所 ——
     它們是**執行/收件**單位，不訂補助辦法，屬於 benefit_locations 的範圍。
"""
from __future__ import annotations

import argparse
import csv
import io
import json
import re
import sys
import urllib.request
from pathlib import Path

CSV_URL = "https://www.dgpa.gov.tw/open/code/orglist.csv"
CACHE = Path.home() / ".hermes/cache/orglist.csv"
OUT = Path(__file__).resolve().parent / "gov_agencies.json"

UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/125.0 Safari/537.36")

# 22 縣市（用來認地方機關）
COUNTIES = [
    "臺北市", "新北市", "桃園市", "臺中市", "臺南市", "高雄市",
    "宜蘭縣", "新竹縣", "苗栗縣", "彰化縣", "南投縣", "雲林縣",
    "嘉義縣", "屏東縣", "臺東縣", "花蓮縣", "澎湖縣",
    "基隆市", "新竹市", "嘉義市", "金門縣", "連江縣",
]

# ⚠️ **這組關鍵字只用來「標記優先看哪些」，絕不用來排除。**
# 🔴 2026-09-24 實測它很不準：把「財政部印刷廠」「農業部獸醫研究所」
#    標成福利相關（因為含「財政」「農業」），
#    而真正發補助的單位名稱裡未必有這些字。
#    **白名單永遠會漏下一種寫法** —— 哪個機關發補助要靠實際查證，不靠猜名字。
WELFARE_HINT = ("社會", "衛生", "勞工", "勞動", "教育", "民政", "環保", "環境",
                "都發", "住宅", "地政", "原住民", "客家", "農業", "文化",
                "青年", "婦幼", "長照", "財政", "稅務", "健康", "保險",
                "福利", "家庭", "退除役", "僑務", "移民", "消防", "警政")


def load_csv(*, refresh: bool = False) -> list[dict]:
    if refresh or not CACHE.exists():
        req = urllib.request.Request(CSV_URL, headers={"User-Agent": UA})
        with urllib.request.urlopen(req, timeout=90) as r:
            CACHE.parent.mkdir(parents=True, exist_ok=True)
            CACHE.write_bytes(r.read())
    raw = CACHE.read_bytes()
    for enc in ("cp950", "big5", "utf-8-sig", "utf-8"):
        try:
            text = raw.decode(enc)
            break
        except UnicodeDecodeError:
            continue
    else:                                        # pragma: no cover
        text = raw.decode("utf-8", errors="replace")
    return list(csv.DictReader(io.StringIO(text)))


def is_alive(row: dict) -> bool:
    """🔴 裁撤註記 = 是 → 這個機關已經不存在。"""
    return (row.get("裁撤註記") or "").strip() != "是"


def classify(row: dict) -> str | None:
    """回傳 central2 / central3 / local_gov / local_dept，不要的回 None。"""
    name = (row.get("機關名稱") or "").strip()
    level = (row.get("機關層級") or "").strip()
    parent = (row.get("主管機關名稱") or "").strip()

    if not name:
        return None

    # 地方：縣市政府本身
    if name in [c + "政府" for c in COUNTIES]:
        return "local_gov"

    # 🔴 名錄涵蓋**五院、議會、學校、公營公司**，不只行政院。
    #   2026-09-24 第一版沒濾，得到 central2=78（預期 33）、
    #   central3=2952，裡面全是世新大學、中華郵政、南投縣議會、中央研究院。
    #   ⚠️ 那些數字「看起來只是偏大」，不像壞掉 —— 要印出內容才看得出來。
    if re.search(r"(大學|學院|學校|高中|國中|國小|醫院|議會|公司|銀行|"
                 r"印製廠|造幣廠|研究院|郵局)$", name):
        return None
    # 只要行政院體系（排除總統府／立法院／司法院／考試院／監察院／國安會）
    NON_EXEC = ("總統府", "立法院", "司法院", "考試院", "監察院",
                "國家安全會議", "中央研究院", "國史館")
    if parent in NON_EXEC or name in NON_EXEC:
        return None

    # 地方一級局處：「○○市政府○○局」且主管機關是該府
    if any(name.startswith(c + "政府") for c in COUNTIES) and name != parent:
        rest = re.sub(r"^.{3}(?:市|縣)政府", "", name)
        # 只取一級局處（不含「科」「股」「所」「隊」「分局」）
        if rest and not re.search(r"(分局|分署|所|隊|科|股|中心|學校|國小|國中|高中)$", rest):
            if re.search(r"(局|處|委員會)$", rest):
                return "local_dept"
        return None

    # 中央
    if level == "2":
        # 🔴 二級必須直屬行政院（議會的主管機關欄也寫「行政院」，要另外擋）
        if parent != "行政院" or name.endswith("議會"):
            return None
        return "central2"
    if level == "3":
        return "central3"
    return None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--refresh", action="store_true", help="重新下載 CSV")
    ap.add_argument("--kind", help="只印某一類（central2/central3/local_gov/local_dept）")
    args = ap.parse_args()

    rows = load_csv(refresh=args.refresh)
    print(f"官方名錄共 {len(rows)} 筆")

    buckets: dict[str, list[dict]] = {
        "central2": [], "central3": [], "local_gov": [], "local_dept": []}
    dropped_dead = 0

    for r in rows:
        if not is_alive(r):
            dropped_dead += 1
            continue
        kind = classify(r)
        if kind is None:
            continue
        buckets[kind].append({
            "code": (r.get("機關代碼") or "").strip(),
            "name": (r.get("機關名稱") or "").strip(),
            "parent": (r.get("主管機關名稱") or "").strip(),
            "level": (r.get("機關層級") or "").strip(),
            "phone": (r.get("機關電話") or "").strip(),
            "address": (r.get("機關地址") or "").strip(),
            "welfare_hint": any(k in (r.get("機關名稱") or "")
                                for k in WELFARE_HINT),
        })

    print(f"🔴 排除已裁撤 {dropped_dead} 筆\n")
    for k, v in buckets.items():
        wf = sum(1 for x in v if x["welfare_related"])
        print(f"  {k:<12} {len(v):>4} 個　（與福利相關 {wf}）")

    if args.kind:
        print()
        for x in sorted(buckets.get(args.kind, []), key=lambda d: d["name"]):
            mark = "★" if x["welfare_related"] else " "
            print(f"  {mark} {x['name']}　←　{x['parent']}")

    OUT.write_text(json.dumps(buckets, ensure_ascii=False, indent=2),
                   encoding="utf-8")
    print(f"\n✅ {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
