#!/usr/bin/env python3
"""把 748/750/752/854/858 的金額欄位改成 Lonck 定案的寫法（W-007 收尾）。

🔴 Lonck 2026-09-30 的兩個決定（第二個推翻了第一個的一部分）：

   ① 第 5 題選 A：「只有單一金額才填」 ⇒ 748 被清成 null
   ② 第 8 題選 B ＋ **通則**：「有類似的問題就是改寫範圍 3,008~11,850」
      ⇒ ①作廢，748 要改回範圍；854 的錯誤門檻值也換成同一組
   ③ 第 9 題選 A：核實補助（只有上限）⇒ `min = NULL, max = 上限`

🔴 **這三筆的金額性質完全不同，不可用同一條規則處理**：

   | 類型 | 例子 | 原文寫法 | 填法 |
   |---|---|---|---|
   | **固定發給** | 748/854 | 「家庭生活費**為**每月 11,850 元」 | 🔴 **範圍** 3,008~11,850 |
   | **核實補助** | 750 | 「每人每日**最高**補助 2,000 元」 | 🔴 **min=NULL, max=2,000** |
   | **比率補助** | 752 | 「補助 80%／70%／全額」 | 不填（那是比率不是金額）|

⚠️ 750 那個 2,000 **不是「你會領到 2,000」** ——
   官方申請表（dep-e-district.hccg.gov.tw）實際填的單價是
   **全日 1,000 元**，且表上有「全日／半日」兩欄、要附看護收據
   ⇒ **實付多少補多少，2,000 只是天花板**。
   🔴 填 `amount_min = 2000` 會是錯的（可能只領 800）。

🔴 全庫 857 筆從來沒有「只有 max」的先例，這是第一筆。
   已查證：schema CHECK 明確允許
   （`amount_min IS NULL OR amount_max IS NULL OR amount_min <= amount_max`），
   且下游只有 `schema.ts` 的 `integer()` 宣告，沒有任何地方假設 min 有值。

⚠️ `amount_note` 欄位全庫已有 174 筆在用 ⇒ 用它說明「這個數字是什麼」，
   不要把說明塞進 description。

一律先 `--dry-run`（預設），`--apply` 才寫；寫前備份整列。
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import psycopg2

# (id, min, max, unit, note, 為什麼)
PLAN = [
    (748, 3008, 11850, "monthly",
     "依款別與身分別固定發給：第 1 款家庭生活費每月 11,850 元；"
     "第 2 款每戶每月 6,825 元；第 2、3 款兒童生活補助每人每月 3,008 元；"
     "高中職以上就學生活補助每人每月 6,825 元。非連續區間。",
     "固定發給 —— 範圍照填（Lonck 第 8 題通則）"),

    (854, 3008, 11850, "monthly",
     "臺灣省：第 1 款家庭生活補助每人每月 11,850 元；第 2 款每戶每月 6,825 元；"
     "第 2、3 款兒童生活補助每人每月 3,008 元；就學生活補助每人每月 6,825 元。"
     "福建省（金門、連江）另有一套：8,791／6,825／2,313／6,825。非連續區間。",
     "🔴 原值 2,308~8,079 是 109 年臺北市的**收入門檻**，不是補助金額"),

    # 🔴 750 填**年度上限**而不是每日上限（2026-09-30 dry-run 才發現的不一致）。
    #    ⚠️ 第一版填 `≤2,000 one_time`，但那個 2,000 是「**每日**最高」，
    #       而同批的 752 填的 300,000 是「**年度**最高」——
    #       兩筆都標 one_time，在同一個欄位裡卻是不同的時間尺度，
    #       🔴 排序或比較時 750 會看起來比 752「便宜 150 倍」，
    #       但實際上兩者的年度上限是 180,000 vs 300,000（差 1.7 倍）。
    #    ⇒ 同一個欄位只能放同一種尺度的數字。每日上限寫進 note。
    (750, None, 180000, "yearly",
     "🔴 核實補助，非固定發給：每人每日**最高**補助看護費 2,000 元"
     "（依實際看護收據核實，官方申請表上有全日／半日之分，實例單價 1,000 元）；"
     "同一年度最高補助上限 180,000 元。欄位填的是年度上限。",
     "核實補助 —— 只有上限（Lonck 第 9 題選 A）；填年度上限以與同類可比"),

    (752, None, 300000, "yearly",
     "🔴 核實＋比率補助，非定額：低收入戶之傷病患全額補助；中低收入戶"
     "近 3 個月自付醫療費累計 3 萬元以上者補助 80%；非屬前二款、患嚴重傷病"
     "且家庭總收入平均未達最低生活費 1.5 倍、近 3 個月自付累計 5 萬元以上者"
     "補助 70%。年度內每人最高 300,000 元為限"
     "（新竹市醫療補助審核作業規定第四點，原文查證）。",
     "核實＋比率 —— 比率裝不進金額欄位，但年度上限 30 萬可填 max"),
]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    conn = psycopg2.connect(dbname="welfare_check")
    cur = conn.cursor()
    ids = [p[0] for p in PLAN]

    bak = Path("/tmp/wc_backup")
    bak.mkdir(parents=True, exist_ok=True)
    cur.execute("SELECT row_to_json(b)::text FROM benefits b"
                " WHERE b.id = ANY(%s)", (ids,))
    rows = [r[0] for r in cur.fetchall()]
    if len(rows) != len(ids):
        print(f"🔴 備份 {len(rows)} 筆 ≠ 目標 {len(ids)} 筆，中止")
        return 1
    (bak / "amount_fix_before.jsonl").write_text(
        "\n".join(rows) + "\n", encoding="utf-8")
    print(f"✅ 已備份 {len(rows)} 筆整列"
          f" → /tmp/wc_backup/amount_fix_before.jsonl\n")

    cur.execute("SELECT id, name, amount_min, amount_max, amount_unit,"
                " amount_note FROM benefits WHERE id = ANY(%s) ORDER BY id",
                (ids,))
    cur_state = {r[0]: r for r in cur.fetchall()}

    for bid, amin, amax, unit, note, why in PLAN:
        _, name, o_min, o_max, o_unit, _o_note = cur_state[bid]
        def fmt(a, b, u):
            if a is None and b is None:
                return "null"
            if a is None:
                return f"≤ {b:,} {u}"
            if a == b:
                return f"{a:,} {u}"
            return f"{a:,}~{b:,} {u}"
        print(f"  [{bid}] {name}")
        print(f"        {fmt(o_min, o_max, o_unit or '')}"
              f"  →  {fmt(amin, amax, unit or '')}")
        print(f"        理由：{why}")
        print(f"        note：{note[:100]}…")

    if not args.apply:
        print("\n（dry-run，未寫入。確認後加 --apply）")
        return 0

    for bid, amin, amax, unit, note, _why in PLAN:
        cur.execute(
            "UPDATE benefits SET amount_min=%s, amount_max=%s,"
            " amount_unit=%s, amount_note=%s WHERE id=%s",
            (amin, amax, unit, note, bid))
    conn.commit()
    print(f"\n✅ 已寫入 {len(PLAN)} 筆")

    # 🔴 驗終點：讀回來比對，不信 UPDATE 的回報
    cur.execute("SELECT id, amount_min, amount_max, amount_unit, amount_note"
                " FROM benefits WHERE id = ANY(%s) ORDER BY id", (ids,))
    bad = []
    got = {r[0]: r for r in cur.fetchall()}
    for bid, amin, amax, unit, note, _ in PLAN:
        g = got.get(bid)
        if not g or (g[1], g[2], g[3], g[4]) != (amin, amax, unit, note):
            bad.append((bid, g))
    if bad:
        print(f"🔴 驗終點失敗：{bad}")
        return 1
    print("✅ 驗終點：4 筆全部讀回來與計畫一致")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
