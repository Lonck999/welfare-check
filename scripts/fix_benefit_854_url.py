#!/usr/bin/env python3
"""修 854：衛福部生活扶助網址在 DB 裡被截斷（W-007 ②）。

🔴 Lonck 2026-09-30 選 A：去來源站重新找。

原網址：`mohw.gov.tw/dl-65687-d81e7f69-d679-44c4-bfdb-e3105890b`
        —— 斷在 UUID 中間（少了最後 3 碼 `bd2`）。

⚠️ **補回 `bd2` 能打開，但不該用它**：
   那份是「**109 年度**低收入戶**類別條件**一覽表」——
   ① 109 年＝2020 年，過時六年
   ② 內容是**資格條件**（最低生活費門檻），不是這筆講的**扶助金額**

🔴 這是個容易上當的地方：網址修好了、頁面打得開、標題也有「低收入戶」，
   **每個表面訊號都說「修好了」**，但內容根本不是這筆補助在講的東西。
   ⇒ 判準不是「打不打得開」，是「**內容對不對得上這筆的 name**」。

✅ 改用「臺灣省及福建省低收入戶生活扶助金額表」
   `dl-86736-7e9a8f34-e240-45da-97fd-01d5856d7aaf.html`
   交叉驗證過是現行版本：它寫的 11,850／6,825／3,008
   與今天實抓的新竹市官網頁面（114/115 年）**完全一致**；
   舊版 `dl-58830` 是 11,040／6,358／2,802 ⇒ 已被取代。

⚠️ 115-03-12 行政院通過「六大社福津貼調增 23.5%」規劃，
   但**尚待預算完成法定程序**（預計 115 年 7 月起）⇒ 現行仍是 11,850。
   🔴 不可把「規劃中的金額」寫進資料庫 —— 那是還沒發生的事。
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import psycopg2

sys.path.insert(0, str(Path(__file__).parent))
from fetch_local_benefit import extract, strip_noise  # noqa: E402

BID = 854
NEW_URL = ("https://www.mohw.gov.tw/"
           "dl-86736-7e9a8f34-e240-45da-97fd-01d5856d7aaf.html")

# 🔴 這些數字必須在新來源裡出現，否則就是抓錯頁或對方改版了。
#    ⚠️ 不是「隨便挑幾個數字」—— 這四個是這筆補助的**全部給付項目**，
#    少任何一個都代表那頁不是完整的金額表。
MUST_HAVE = ("11,850", "6,825", "3,008", "8,791")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    conn = psycopg2.connect(dbname="welfare_check")
    cur = conn.cursor()

    bak = Path("/tmp/wc_backup")
    bak.mkdir(parents=True, exist_ok=True)
    cur.execute("SELECT row_to_json(b)::text FROM benefits b WHERE b.id = %s",
                (BID,))
    row = cur.fetchone()
    if not row:
        print(f"🔴 找不到 id={BID}")
        return 1
    (bak / f"benefit_{BID}_before.json").write_text(row[0], encoding="utf-8")
    print(f"✅ 已備份整列 → /tmp/wc_backup/benefit_{BID}_before.json\n")

    cur.execute("SELECT name, source_url, description FROM benefits"
                " WHERE id = %s", (BID,))
    r2 = cur.fetchone()
    if not r2:
        print(f"🔴 找不到 id={BID}")
        return 1
    name, old_url, old_desc = r2
    print(f"  [{BID}] {name}")
    print(f"    舊網址：{old_url}")
    print(f"    新網址：{NEW_URL}")

    txt = strip_noise(extract(NEW_URL) or "")
    print(f"    抓到 {len(txt)} 字")
    missing = [m for m in MUST_HAVE if m not in txt]
    if missing:
        print(f"    🔴 新來源缺少必要金額 {missing} ⇒ 整筆不動")
        return 1
    print(f"    ✅ 四個給付項目金額全部對上：{MUST_HAVE}")

    # 🔴 只取原文，不改寫。表格在抽取後會變成連續文字。
    body = re.sub(r"\s+", " ", txt).strip()
    # 砍掉「備註」之後的法條引用（對民眾沒有幫助，且會蓋掉金額）
    body = re.split(r"\s*備註：", body)[0].strip()

    new_desc = (
        f"{name}。"
        f"　{body}"
        f"　⚠️ 金額未填入欄位：依款別與身分別而異（第 1 款家庭生活補助"
        f"／第 2 款家庭生活補助／兒童生活補助／就學生活補助），非連續區間。"
        f"　🔴 行政院已通過「六大社福津貼調增 23.5%」規劃，"
        f"**尚待預算完成法定程序**，現行仍依上表金額。"
        f"　（來源：{NEW_URL}）"
    )[:1800]

    if len(new_desc) < len(old_desc or ""):
        print(f"    🔴 新描述 {len(new_desc)} < 舊的 {len(old_desc or '')}"
              f" ⇒ 整筆不動")
        return 1

    print(f"\n    描述 {len(old_desc or '')} → {len(new_desc)} 字")
    print(f"    ---- 新描述 ----\n    {new_desc[:700]}")

    if not args.apply:
        print("\n（dry-run，未寫入。確認後加 --apply）")
        return 0

    # 🔴 不動 amount_*：這筆的金額依款別而異，與 748 同理（Lonck 選 A）
    cur.execute(
        "UPDATE benefits SET source_url=%s, description=%s,"
        " last_verified_date=CURRENT_DATE WHERE id=%s",
        (NEW_URL, new_desc, BID))
    conn.commit()
    print("\n✅ 已寫入")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
