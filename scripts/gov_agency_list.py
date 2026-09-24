#!/usr/bin/env python3
"""從人事行政總處官方名錄，篩出 welfare-check 需要的機關清單。

資料來源：政府資料開放平臺 dataset/7307「行政院所屬中央及地方機關代碼」
          → https://www.dgpa.gov.tw/open/code/orglist.csv
          （人事行政總處維護，17,410 筆，含層級、裁撤註記、生效日期）

🔴 為什麼不用維基或 regex 抓：
   2026-09-24 實測用 regex 從維基沿革文字抓「XX署／XX局」，
   撈出一堆**已裁撤**的（內政部兒童局、行政院衛生署、交通部電信總局）
   與**不相干**的（地方檢察署、國安局、參謀本部軍醫局）。
   ⚠️ 那份清單看起來很完整，但把死掉的機關寫進文件 = 之後去抓一個不存在的網站。

🔴 **每一筆都帶「存在證明」**（2026-09-24 使用者要求）：
   官方名錄沒有網址欄位，但有更硬的東西 ——
   · 機關代碼（人事總處編配的正式編碼）
   · 機關生效日期（民國年，如 0910102）
   · 地址／電話（幾乎 100% 覆蓋）
   ⇒ `evidence` 欄把這些組起來，**任何一筆都可以回溯驗證**。

⚠️ 分類與「是否與福利相關」是兩件事：
   分類（central2/central3/...）是結構，**照官方層級**；
   福利相關是**推測**，只用來排優先序，絕不用來排除。
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
#    **哪個機關發補助要靠實際查證，不靠猜名字。**
WELFARE_HINT = ("社會", "衛生", "勞工", "勞動", "教育", "民政", "環保", "環境",
                "都發", "住宅", "地政", "原住民", "客家", "農業", "文化",
                "青年", "婦幼", "長照", "財政", "稅務", "健康", "保險",
                "福利", "家庭", "退除役", "僑務", "移民", "國民年金")

# 🔴 直屬部會 = 主管機關是「○○部」「○○委員會」「○○總處」。
#    這是「署／局」那一層，補助的主力。
#    ⚠️ 2026-09-24 踩過：文件寫「中央三級 216（直屬部會）」，
#    但 JSON 存的是全部 2739 筆未篩的 —— **文件與檔案對不起來**。
#    現在篩選寫進腳本，數字只有一個來源。
TOP_PARENT_SUFFIX = ("部", "委員會", "總處", "總署")


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


def roc_to_ad(roc: str) -> str | None:
    """民國年 0910102 → 2002-01-02。0000000 代表沒填。"""
    roc = (roc or "").strip()
    if not roc.isdigit() or len(roc) != 7 or roc == "0000000":
        return None
    y, m, d = int(roc[:3]) + 1911, roc[3:5], roc[5:7]
    if m == "00" or d == "00":
        return f"{y}"
    return f"{y}-{m}-{d}"


def build_evidence(row: dict) -> dict:
    """存在證明：官方名錄裡可回溯驗證的欄位。

    🔴 使用者 2026-09-24：「有可以證明他是真的就好，不一定要有網址」。
    官方名錄沒有網址欄，但機關代碼＋生效日期＋地址電話足以證明存在，
    而且比網址穩定（網址會改版，機關代碼不會）。
    """
    return {
        "org_code": (row.get("機關代碼") or "").strip(),
        "effective_date": roc_to_ad(row.get("機關生效日期", "")),
        "address": (row.get("機關地址") or "").strip(),
        "phone": re.sub(r"-+$", "", (row.get("機關電話") or "").strip()),
        "source": "人事行政總處「行政院所屬中央及地方機關代碼」",
        "source_url": "https://data.gov.tw/dataset/7307",
    }


def classify(row: dict) -> str | None:
    """回傳 central2 / central3 / central3_top / local_gov / local_dept。"""
    name = (row.get("機關名稱") or "").strip()
    level = (row.get("機關層級") or "").strip()
    parent = (row.get("主管機關名稱") or "").strip()

    if not name:
        return None

    if name in [c + "政府" for c in COUNTIES]:
        return "local_gov"

    # 🔴 名錄涵蓋**五院、議會、學校、公營公司**，不只行政院。
    #   2026-09-24 第一版沒濾，得到 central2=78（預期 33）、
    #   central3=2952，裡面全是世新大學、中央研究院。
    #   ⚠️ 那些數字「看起來只是偏大」，不像壞掉 —— 要印出內容才看得出來。
    #
    # 🔴 **第二次踩同一個坑（同日稍晚）**：上面那版寫 `學校$`／`高中$`，
    #   但學校的正式名稱是「國立岡山高級中**學**」「○○高級工業職業學校」
    #   —— `高中$` 一個都不match。結果 **55 所高中混進 central3_top**
    #   （「補助主力 216 個」裡 25% 是學校），39 所還被判成「有發補助」。
    #   ⇒ 判準改成**出現即排除**（不綁結尾），並涵蓋「中學／職業學校」等寫法。
    #   ⚠️ 學校確實會發獎助學金，但那是**校內學生**的事，
    #      不是民眾可申請的福利 —— 收進來會讓查詢結果充滿各地高中。
    if re.search(r"(大學|學院|科技大學|專科|中學|學校|高中|高職|國小|國中|"
                 r"幼兒園|附幼|醫院|議會|公司|銀行|印製廠|造幣廠|"
                 r"研究院|郵局|農會|漁會)", name):
        return None
    NON_EXEC = ("總統府", "立法院", "司法院", "考試院", "監察院",
                "國家安全會議", "中央研究院", "國史館")
    if parent in NON_EXEC or name in NON_EXEC:
        return None

    if any(name.startswith(c + "政府") for c in COUNTIES) and name != parent:
        rest = re.sub(r"^.{3}(?:市|縣)政府", "", name)
        if rest and not re.search(
                r"(分局|分署|所|隊|科|股|中心|學校|國小|國中|高中)$", rest):
            if re.search(r"(局|處|委員會)$", rest):
                return "local_dept"
        return None

    if level == "2":
        # 🔴 二級必須直屬行政院（議會的主管機關欄也寫「行政院」，要另外擋）
        if parent != "行政院" or name.endswith("議會"):
            return None
        return "central2"
    if level == "3":
        # 直屬部會的才是「署／局」那一層（補助主力）
        if parent.endswith(TOP_PARENT_SUFFIX):
            return "central3_top"
        return "central3"
    return None


KIND_LABEL = {
    "central2": "中央二級（部／會）",
    "central3_top": "中央三級・直屬部會（署／局）★補助主力",
    "central3": "中央三級・其他",
    "local_gov": "縣市政府",
    "local_dept": "地方一級局處　★補助主力",
}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--refresh", action="store_true", help="重新下載 CSV")
    ap.add_argument("--kind", help="只印某一類")
    ap.add_argument("--hint-only", action="store_true",
                    help="只印 welfare_hint=True 的（⚠️ 那只是推測）")
    args = ap.parse_args()

    rows = load_csv(refresh=args.refresh)
    print(f"官方名錄共 {len(rows)} 筆")

    buckets: dict[str, list[dict]] = {k: [] for k in KIND_LABEL}
    dropped_dead = 0

    for r in rows:
        if not is_alive(r):
            dropped_dead += 1
            continue
        kind = classify(r)
        if kind is None:
            continue
        name = (r.get("機關名稱") or "").strip()
        buckets[kind].append({
            "name": name,
            "parent": (r.get("主管機關名稱") or "").strip(),
            "level": (r.get("機關層級") or "").strip(),
            # ⚠️ 推測欄位，只排優先序，不可用來排除
            "welfare_hint": any(k in name for k in WELFARE_HINT),
            "evidence": build_evidence(r),
        })

    print(f"🔴 排除已裁撤 {dropped_dead} 筆\n")
    total = 0
    for k, v in buckets.items():
        total += len(v)
        hint = sum(1 for x in v if x["welfare_hint"])
        ev = sum(1 for x in v
                 if x["evidence"]["org_code"] and x["evidence"]["address"])
        print(f"  {KIND_LABEL[k]:<34} {len(v):>4} 個"
              f"　hint {hint:>3}　有代碼+地址 {ev}/{len(v)}")
    print(f"  {'合計':<34} {total:>4} 個")

    if args.kind:
        print()
        items = buckets.get(args.kind, [])
        if args.hint_only:
            items = [x for x in items if x["welfare_hint"]]
        for x in sorted(items, key=lambda d: (d["parent"], d["name"])):
            mark = "★" if x["welfare_hint"] else " "
            ev = x["evidence"]
            print(f"  {mark} {x['name']}　←　{x['parent']}")
            print(f"      代碼 {ev['org_code']}　生效 {ev['effective_date']}"
                  f"　{ev['phone']}")

    OUT.write_text(json.dumps(
        {"_meta": {
            "source": "人事行政總處「行政院所屬中央及地方機關代碼」",
            "source_url": "https://data.gov.tw/dataset/7307",
            "csv_url": CSV_URL,
            "total_rows_in_source": len(rows),
            "dropped_dissolved": dropped_dead,
            "note": "🔴 welfare_hint 只是關鍵字推測，不可當成「這個機關發補助」的判準",
        }, "buckets": buckets}, ensure_ascii=False, indent=2),
        encoding="utf-8")
    print(f"\n✅ {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
