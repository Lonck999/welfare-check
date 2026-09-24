#!/usr/bin/env python3
"""第二輪查證：用「業務領域」生成查詢詞，重查判不出來的機關。

🔴 為什麼需要第二輪：
   第一輪一律用「<機關全名> 補助 申請」，對**名稱與業務不一致**的機關失效：
   · 「新北市政府高齡長期照顧處」→ 搜到財政部的頁面
   · 「新北市政府地政局」→ 地價稅減免其實在**稅捐稽徵處**網站
   · 「新竹縣政府教育局」→ 獎學金公告全在學校網站（已被排除）
   ⇒ 改用「縣市 + 業務關鍵字」（新北市 長照 補助）就立刻找到。

⚠️ 這一輪仍**不會把任何機關標成「沒有補助」** ——
   查不到就留 NULL，因為「查不到」≠「沒有」。

用法：python scripts/agency_verify_round2.py [--limit N] [--dry-run]
"""
from __future__ import annotations

import argparse
import re
import sys
import time

import psycopg2

from agency_verify_run import (SearchUnavailable, judge, mark, web_search)

# 機關名稱裡的業務關鍵字 → 更有效的查詢詞
# 🔴 每一條都來自實測（2026-09-24），不是憑感覺列的
DOMAIN_QUERY = [
    (r"高齡|長期照顧|長照",      "長照 補助 申請 老人"),
    (r"地政",                    "地價稅 減免 土地增值稅 優惠"),
    (r"稅務|稅捐|國稅",          "地方稅 減免 退稅 分期繳納"),
    (r"教育",                    "學生 獎助學金 學雜費 減免 補助"),
    (r"建設|工務",               "住宅 修繕 補助 公寓大廈"),
    (r"都市發展|都更|住宅",      "租金補貼 住宅補助 都市更新 補助"),
    (r"環境保護|環保",           "資源回收 獎勵 補助 電動車"),
    (r"警察",                    "犯罪被害人 補償 協助 申請"),
    (r"消防",                    "災害 救助 慰問金 申請"),
    (r"衛生",                    "醫療補助 健康檢查 補助 申請"),
    (r"社會|社福",               "社會救助 津貼 補助 申請"),
    (r"勞工|勞動",               "勞工 津貼 補助 失業 申請"),
    (r"農業|農林",               "農民 補助 津貼 天然災害 救助"),
    (r"原住民",                  "原住民 補助 獎助學金 申請"),
    (r"客家",                    "客語 獎勵 補助 申請"),
    (r"文化|藝術|博物館|圖書館", "藝文 補助 獎助 申請"),
    (r"體育|運動",               "運動 補助 獎勵金 申請"),
    (r"交通|捷運|運輸",          "交通 補貼 敬老卡 優惠"),
    (r"氣象",                    "天然災害 農業 救助 補助"),
    (r"科學園區|科技",           "園區 補助 獎勵 申請"),
    (r"災害防救|防災",           "災害 救助 慰問金 重建 補助"),
    (r"國防|軍備|後備",          "國軍 官兵 補助 慰問金 申請"),
    (r"太空|研究所|研究中心",    "研究 獎助 計畫 補助 申請"),
    (r"選舉",                    "政黨 競選經費 補助款"),
    (r"發展基金",                "投資 補助 申請 基金"),
]

# 🔴 這些機關的業務性質就是不發補助 —— 但仍**不標 False**，
#    只在報告裡註明，讓人工最後決定。
#    ⚠️ 審計部是查帳的、檢察署是辦案的、工程處是蓋東西的。
UNLIKELY = r"(審計|檢察署|法醫|獸醫|生物多樣性|工程處|秘書處|主計處|" \
           r"研究發展考核|法制局|政風|人事處)"


def county_of(name: str) -> str:
    """抽出縣市名（查詢時比機關全名有效）。"""
    m = re.match(r"^(.{2,3}[市縣])", name)
    return m.group(1) if m else ""


def build_query(name: str) -> str:
    """🔴 用『縣市 + 業務關鍵字』取代『機關全名 + 補助』。

    ⚠️ 只對**地方機關**這樣做。中央機關的名稱常帶上級部會前綴
    （「**交通部**中央氣象署」），拿它去比對業務關鍵字會配錯 ——
    實測氣象署被配到「交通 補貼 敬老卡」。
    ⇒ 中央機關先把上級前綴剝掉再比對。
    """
    county = county_of(name)
    target = name
    if not county:
        # 剝掉中央上級機關前綴：「交通部中央氣象署」→「中央氣象署」
        target = re.sub(r"^(.{2,6}?(?:部|委員會|總處|署|院))(?=.{3,})",
                        "", name) or name
    for pat, kw in DOMAIN_QUERY:
        if re.search(pat, target):
            return f"{county} {kw}".strip() if county else f"{name} {kw}"
    # 沒對到業務類別 → 退回機關全名，但換個角度問
    return f"{name} 民眾 申請 服務"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=100)
    ap.add_argument("--dry-run", action="store_true",
                    help="只印查詢詞與判定結果，不寫資料庫")
    args = ap.parse_args()

    with psycopg2.connect(dbname="welfare_check") as c, c.cursor() as cur:
        cur.execute("""SELECT name, stage FROM agency_verification
                        WHERE has_benefit IS NULL AND stage <= 4
                        ORDER BY stage, name LIMIT %s""", (args.limit,))
        rows = cur.fetchall()

    print(f"第二輪查證：{len(rows)} 個機關"
          f"{'（dry-run，不寫入）' if args.dry_run else ''}\n")
    found = still = 0
    for i, (name, stage) in enumerate(rows, 1):
        q = build_query(name)
        try:
            hb, url, note = judge(name, web_search(q))
        except SearchUnavailable as e:
            print(f"  [{i:>3}] 🔴 後端失敗（保持待查）{name}　{e}")
            time.sleep(3)
            continue

        unlikely = bool(re.search(UNLIKELY, name))
        if hb:
            found += 1
            note = f"第二輪（查詢：{q}）{note}"
            if not args.dry_run:
                mark(name, True, url, note, "web_search 第二輪")
            print(f"  [{i:>3}] ✅ 有　{name}")
            print(f"         查詢：{q}")
            print(f"         {url[:80]}")
        else:
            still += 1
            tag = "（業務性質本就不發補助）" if unlikely else ""
            print(f"  [{i:>3}] ❓ 仍查不到　{name}{tag}")
            print(f"         查詢：{q}")
        time.sleep(0.4)

    print(f"\n第二輪：翻正 {found}　仍待確認 {still}")
    print("🔴 「仍查不到」不等於「沒有補助」 —— 一律留 NULL 不寫 False。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
