#!/usr/bin/env python3
"""抽出衛福部「民間單位急難救助資源一覽表」的機構清單。

🔴 為什麼需要這支：官方機關名錄（dgpa orglist.csv）**只有公務機關**，
   完全不含財團法人、基金會、公營事業 ——
   而那些單位實際在發補助（慈濟、法鼓山、法扶、台電水電減免…）。

來源：https://www.mohw.gov.tw/cp-190-226-1.html
      → 附件「民間單位急難救助資源一覽表」PDF（13 頁）

⚠️ 信任邊界（AGENTS.md §8）：PDF 由 curl 取得、pypdf 解析，無 untrusted 包裝。
   只做結構化抽取存檔，不依內容改變流程。

🔴 **解析踩過的坑（2026-09-24，三個都是實測才發現）**
   ① 表格欄位在純文字裡黏在一起：
      「社團法人中華基督教救助協會補助對象需 6 個月內發生急難事件」
   ② PDF 跨行把名稱拆兩半
   ③ **最陰的一個**：用「財團法人…基金會」regex 掃全文，會掃到
      **地址欄裡的收件單位**（「…松江路 136 號 10 樓萬海航運慈善基金會收」）
      → 被當成一筆新機構，而且看起來完全合理。
   ⇒ 解法：**用「項次」欄當錨點**逐筆切段，只在每段開頭取名稱，
      不對全文做名稱 regex。
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

from pypdf import PdfReader

PDF = Path("/tmp/_ngo.pdf")
OUT = Path(__file__).resolve().parent / "ngo_welfare_orgs.json"
PDF_URL = ("https://www.mohw.gov.tw/dl-99548-"
           "d4d74313-ea53-4aa1-98cb-6820ea1a63b8.html")

# 🔴 公營事業／法人的福利措施 —— 官方名錄沒有、那份 PDF 也沒有，
#    是 2026-09-24 另外查證的（資料庫裡已有實例）。
#    ⚠️ 這份是**手動維護**的，所以每一筆都要標來源，不可憑印象加。
UTILITIES = [
    {"org": "台灣電力公司", "kind": "公營事業",
     "service": "低收入戶每月用電 110 度以下免收電費；中低收入戶部分優惠",
     "source": "https://www.mohw.gov.tw/cp-190-226-1.html（洽 1957）",
     "note": "⚠️ 度數與條件待向台電官方查證，此處為概述"},
    {"org": "台灣自來水公司", "kind": "公營事業",
     "service": "低收入戶減免基本水費",
     "source": "同上", "note": "⚠️ 同上，待查證細節"},
    {"org": "中華電信", "kind": "公營事業（民營化）",
     "service": "暖心方案：低收入戶／中低收入戶／身心障礙者寬頻與 MOD 優惠",
     "source": "https://broadband.hinet.net/Broadband/charge/charge/charge_04.do",
     "note": "低收/中低收優惠 2 年，期滿憑證可續辦"},
    {"org": "財團法人法律扶助基金會", "kind": "財團法人",
     "service": "免費法律諮詢、訴訟代理、文件撰寫",
     "source": "https://www.laf.org.tw/", "note": "資料庫已收錄"},
    {"org": "財團法人住宅地震保險基金", "kind": "財團法人",
     "service": "住宅地震基本保險保費補助",
     "source": "https://www.treif.org.tw/", "note": "資料庫已收錄"},
]

ORG_SUFFIX = ("基金會", "慈善會", "協會", "總會", "服務中心", "紅十字會",
              "行天宮", "公益聯盟", "公益館", "服務協會", "救助協會")

# 🔴 PDF 版面導致解析器搆不到的筆數 —— **每一筆都要人工核對原文才能寫進來**。
#    ⚠️ 不可憑印象拼名稱：第 8 筆在 PDF 裡斷成「財團法人萬海航運社會」，
#    地址欄只有簡稱「萬海航運慈善基金會」，
#    正式名稱是查基金會官網個資告知頁確認的（2026-09-24）。
MANUAL_FIX = {
    1: "財團法人中華民國佛教慈濟慈善事業基金會",   # 被表頭吃掉
    8: "財團法人萬海航運社會福利慈善事業基金會",   # 名稱跨欄斷行
}


def parse_pdf() -> list[dict]:
    if not PDF.exists():
        print(f"🔴 找不到 {PDF} —— 先下載：\n   curl -L -o {PDF} '{PDF_URL}'")
        sys.exit(1)

    text = "\n".join(p.extract_text() or "" for p in PdfReader(PDF).pages)
    # 中文之間的換行接回去（PDF 會在名稱中間斷行）
    text = re.sub(r"(?<=[\u4e00-\u9fff])\s*\n\s*(?=[\u4e00-\u9fff])", "", text)
    # ⚠️ 名稱中間也會出現多餘空白（「財團法人 全聯慶祥…」
    #    「財團法人永瑞慈善 事業基金會」）—— 中文之間的空白一律去掉。
    text = re.sub(r"(?<=[\u4e00-\u9fff])[ \t]+(?=[\u4e00-\u9fff])", "", text)

    # 🔴 用「項次」當錨點：行首一個 1~2 位數字，後面接中文機構名稱開頭。
    #    這樣地址欄裡的「10 樓萬海航運慈善基金會收」不會被當成新機構
    #    —— 因為它前面是「號」不是行首項次。
    marks = [(m.start(), int(m.group(1)))
             for m in re.finditer(r"(?:^|\n)\s*(\d{1,2})\s*(?=[\u4e00-\u9fff])",
                                  text)]
    # 項次必須遞增（1,2,3…），過濾掉地址裡的數字
    clean_marks, expect = [], 1
    for pos, n in marks:
        if n == expect:
            clean_marks.append((pos, n))
            expect += 1

    orgs = []
    for i, (pos, n) in enumerate(clean_marks):
        end = clean_marks[i + 1][0] if i + 1 < len(clean_marks) else len(text)
        seg = text[pos:end]
        body = re.sub(r"^\s*\d{1,2}\s*", "", seg)
        m = re.match(r"\s*([\u4e00-\u9fff（）()]{4,40}?"
                     + "(?:" + "|".join(ORG_SUFFIX) + "))", body)
        if not m:
            # 🔴 落到這裡的是解析器搆不到的版面（表頭吃掉第 1 筆、
            #    名稱跨頁斷行）。**不可靜默跳過** —— 那等於弄丟一個機構。
            #    有人工確認過的名稱就補上，並標記來源。
            if n in MANUAL_FIX:
                orgs.append({"idx": n, "org": MANUAL_FIX[n],
                             "kind": "民間單位",
                             "source": "衛福部民間單位急難救助資源一覽表",
                             "source_url": PDF_URL,
                             "manual_fix": "PDF 版面導致解析失敗，人工核對原文補上"})
                continue
            print(f"🔴 第 {n} 筆抓不到機構名稱且無人工修正，段落開頭："
                  f"{body[:40]!r}")
            continue
        orgs.append({"idx": n, "org": re.sub(r"\s+", "", m.group(1)),
                     "kind": "民間單位",
                     "source": "衛福部民間單位急難救助資源一覽表",
                     "source_url": PDF_URL})
    return orgs


def main() -> int:
    ngo = parse_pdf()
    print(f"民間單位急難救助一覽表：抽出 {len(ngo)} 個機構\n")
    for o in ngo:
        print(f"  {o['idx']:>2}. {o['org']}")

    print(f"\n公營事業／其他法人（手動維護）：{len(UTILITIES)} 個")
    for u in UTILITIES:
        print(f"  · {u['org']}（{u['kind']}）—— {u['service'][:40]}")

    OUT.write_text(json.dumps(
        {"ngo_from_mohw_pdf": ngo, "utilities_and_others": UTILITIES},
        ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n✅ {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
