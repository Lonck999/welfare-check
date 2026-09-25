#!/usr/bin/env python3
"""從縣市社會局的「福利補助目錄頁」逐項展開，補齊 gap_vs_mohw_table 的缺口。

🔴 為什麼不用搜尋（2026-09-24 實測）：
   搜尋抓取命中率只有 25%、誤判率 1/3，而且失敗全卡在
   **找不到對的頁**（不是讀不懂頁面）。
   ⇒ 改從各縣市自己的「補助總覽/津貼專區」目錄頁進去，
     那是官方自己維護的列舉，比搜尋猜可靠。

🔴 實測哪些縣市有真正的列舉型目錄頁（2026-09-25）：
   ✅ 彰化「津貼及補助專區」—— 編號式（1-1 生育補助、1-2 特殊境遇…）
   ✅ 新竹市「老人福利」—— 每項都是獨立計畫名
   ⚠️ 雲林/基隆/苗栗 —— 有連結但多半是申請表 PDF 或公告，非項目清單
   🔴 屏東/南投/新竹縣 —— 抽取失敗（需重試或換頁）

⚠️ 本腳本**只抓目錄頁上的項目名稱與連結**，不自動寫入資料庫 ——
   項目名稱要人看過才知道是不是真的補助（實測目錄頁上也有
   「網站導覽」「各科職掌」這類非補助連結）。
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from benefit_keywords import BENEFIT_KW  # noqa: E402
from fetch_local_benefit import extract, is_own_county, strip_noise  # noqa: E402

# 🔴 每個縣市的「福利補助目錄頁」—— 實測過真的列舉得出項目的才放進來
DIRECTORY_PAGES: dict[str, list[str]] = {
    "彰化縣": [
        "https://social.chcg.gov.tw/07other/main.aspx?main_id=2",
    ],
    "新竹市": [
        "https://society.hccg.gov.tw/ch/home.jsp?id=206&parentpath=0%2C5%2C44",
    ],
    "雲林縣": [
        "https://welfare.yunlin.gov.tw/People/Search/64?Q_Dept=490079",
        "https://social.yunlin.gov.tw/News.aspx?n=9454&sms=16138",
    ],
    "基隆市": [
        "https://www.klcg.gov.tw/tw/social/2715.html",
        "https://www.klcg.gov.tw/tw/social/2711.html",
    ],
    "苗栗縣": [
        "https://www.miaoli.gov.tw/social_affairs/News.aspx?n=693&sms=9613",
    ],
    "宜蘭縣": [
        "https://sntroot.e-land.gov.tw/cp.aspx?n=10106",
        "https://sntroot.e-land.gov.tw/cp.aspx?n=10414",
    ],
    "屏東縣": [
        "https://www.pthg.gov.tw/planjdp/Content_List.aspx?n=46F6EFDFE943D834",
    ],
    "南投縣": [
        "https://welfare.nantou.gov.tw/1486/2201",
    ],
    "新竹縣": [
        "https://social.hsinchu.gov.tw/cl.aspx?n=202",
    ],
}

# 🔴 目錄頁上的非補助連結 —— 不排除的話會被當成補助項目
NOT_ITEM = re.compile(
    r"網站導覽|各科職掌|業務簡介|聯絡|回首頁|下載專區|意見信箱|隱私|"
    r"無障礙|facebook|線上申辦$|更多|回上頁|列印|友善列印|RSS|"
    r"^\d+$|^第?\d+頁|常見問答|FAQ|專區$|公告專區")


def harvest(county: str, url: str) -> list[tuple[str, str]]:
    """從一個目錄頁抓出「項目名稱 → 連結」。"""
    text = strip_noise(extract(url))
    if not text:
        return []
    out: list[tuple[str, str]] = []
    # 🔴 markdown 連結常帶 title 屬性：[名稱](網址 "說明")
    #    ⚠️ 用 `\(([^)\s]+)\)` 會因為網址後面那個空格而**整個 match 失敗**，
    #    結果連結數變 0 —— 而 extract 明明抓到 3563 字元，
    #    所以看起來像「頁面沒有連結」而不是「我的 regex 錯了」。
    for m in re.finditer(r'\[([^\]]{4,60})\]\(([^)\s]+)(?:\s+"[^"]*")?\)', text):
        title = re.sub(r"[*\s]+", " ", m.group(1)).strip()
        link = m.group(2)
        if NOT_ITEM.search(title):
            continue
        if not any(k in title for k in BENEFIT_KW):
            continue
        # 🔴 連結必須還在這個縣市自己的網域 —— 目錄頁上常有
        #    中央或別縣市的連結（實測宜蘭頁上有 1966 長照專線）
        if link.startswith("http") and not is_own_county(link, county):
            continue
        out.append((title, link))
    # 去重（同一項目常出現在麵包屑與主列表兩處）
    seen: set[str] = set()
    uniq = []
    for t, u in out:
        k = re.sub(r"\s+", "", t)
        if k not in seen:
            seen.add(k)
            uniq.append((t, u))
    return uniq


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--county", help="只跑單一縣市")
    ap.add_argument("--out", default="/tmp/directory_items.json")
    args = ap.parse_args()

    targets = ({args.county: DIRECTORY_PAGES[args.county]}
               if args.county else DIRECTORY_PAGES)

    result: dict[str, list[dict]] = {}
    total = 0
    for county, pages in targets.items():
        items: list[tuple[str, str]] = []
        failed = 0
        for p in pages:
            got = harvest(county, p)
            if not got:
                failed += 1
            items += got
        # 跨頁去重
        seen: set[str] = set()
        uniq = []
        for t, u in items:
            k = re.sub(r"\s+", "", t)
            if k not in seen:
                seen.add(k)
                uniq.append({"name": t, "url": u})
        result[county] = uniq
        total += len(uniq)
        mark = "✅" if uniq else "🔴"
        note = f"（{failed}/{len(pages)} 頁抽取失敗）" if failed else ""
        print(f"  {mark} {county}　{len(uniq)} 個項目{note}")
        for it in uniq[:6]:
            print(f"       · {it['name'][:44]}")

    Path(args.out).write_text(
        json.dumps(result, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\n共 {total} 個項目 → {args.out}")
    print("🔴 這些只是候選 —— 要人看過確認是補助才可寫入資料庫")
    return 0


if __name__ == "__main__":
    sys.exit(main())
