#!/usr/bin/env python3
"""858 換成苗栗縣真正有的補助（W-007 ②，Lonck 第 7 題選 B）。

🔴 **這不是「修網址」，是「這筆資料本身是錯的」。**

原始狀態：
  name       低收入戶住宅修繕補助
  county     苗栗縣
  source_url webws.miaoli.gov.tw/Download.ashx?...&n=MjAxNz  ← 斷在參數中間
  amount     6,115~11,448（🔴 那是**低收入戶資格門檻**，不是補助金額）

查證過程（2026-09-30）：
  ① 把截斷的網址補全後**打得開**（1,327 字）
     —— 但內容是「低收入戶/中低收入戶**申請須知**」，不是住宅修繕補助
  ② gov.tw 官方跨縣市對照表：苗栗縣在「(中)低收入戶修繕住宅補助」欄，
     **只有「65 歲以上老人」打勾，「未限定年齡」是空的**
  ③ 內政部國土署全國性調查表：苗栗縣該項標示「**未辦理**」

🔴 結論：**苗栗縣沒有「低收入戶住宅修繕補助」（不限年齡的那種）。**
   這筆的來源是「衛福部跨縣市對照表」，但那張表列的是**全國性法規項目**
   （《低收入戶及中低收入戶住宅補貼辦法》最高 6 萬），
   **縣市可以選擇不辦理** —— 苗栗就是沒辦。

⚠️ 這跟 Lonck 2026-09-28 點破的是同一個形狀：
   「這筆根本該不該存在」，而不是「怎麼把值修對」。
   ⇒ 我原本提的三個選項全在修網址／修金額，等於默認這筆可以留著。

✅ Lonck 選 B：換成苗栗縣**真的有**的項目。

新內容（`law.miaoli.gov.tw` FL049905 原文逐條查證）：
  名稱   苗栗縣中低收入老人住宅設施修繕設備補助
  對象   設籍本縣並實際居住於申請修繕房屋滿 6 個月以上，
         且具中低收入資格**年滿 65 歲**之老人（第 3 條）
  金額   以戶為單位，3 年內按改善內容**核實補助**，最高 50,000 元（第 5 條）
  期間   每年 1 月 1 日至 11 月 30 日（第 10 條）
  受理   戶籍所在地公所（第 6 條）

🔴 金額填法沿用第 9 題 A：核實補助 ⇒ `min = NULL, max = 50000`
   （「最高新臺幣五萬元整」＝上限，實際按改善內容核實）。
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import psycopg2

sys.path.insert(0, str(Path(__file__).parent))
from fetch_local_benefit import extract, strip_noise  # noqa: E402

BID = 858
NEW_URL = "https://law.miaoli.gov.tw/glrsnewsout/LawContent.aspx?id=FL049905"
NEW_NAME = "苗栗縣中低收入老人住宅設施修繕設備補助"

# 🔴 這些片語必須在新來源裡出現，否則就是抓錯頁或對方改版。
#    ⚠️ 不是隨便挑的 —— 涵蓋「對象／金額／期間」三個決定性事實，
#    少任何一個都代表那頁不足以支撐這筆資料。
MUST_HAVE = (
    "年滿六十五歲",          # 對象（第 3 條）
    "最高新臺幣五萬元整",    # 金額（第 5 條）
    "一月一日起至十一月三十日止",  # 期間（第 10 條）
)

NEW_DESC = (
    "苗栗縣中低收入老人住宅設施修繕設備補助。"
    "　補助對象：設籍本縣並實際居住於申請修繕房屋滿六個月以上，"
    "且具中低收入資格年滿六十五歲之老人；修繕房屋限座落於本縣轄內。"
    "　補助項目：一、屋頂防水及室內給水、排水設施、設備（含璧癌處理）。"
    "二、衛浴設施、設備。三、改善入口玄關、走道、樓梯動線等。"
    "四、其他住宅安全輔助器具、設施及設備。"
    "　補助標準：以戶為單位，三年內按改善內容核實補助，最高新臺幣五萬元整；"
    "七十歲以上獨居或失能者優先補助；領有身心障礙手冊者應優先申請"
    "身心障礙者生活輔具器具費用補助。"
    "　申請期間：每年一月一日起至十一月三十日止。"
    "　受理單位：戶籍所在地鄉（鎮、市）公所。"
    "　🔴 本筆原為「低收入戶住宅修繕補助」，但查證後苗栗縣**未辦理**"
    "不限年齡的低收入戶修繕補助（gov.tw 跨縣市對照表僅「65 歲以上老人」"
    "欄打勾；內政部國土署調查表標示「未辦理」），"
    "已於 2026-09-30 更正為本縣實際辦理之項目。"
    f"　（來源：{NEW_URL}）"
)

NEW_NOTE = (
    "🔴 核實補助，非固定發給：以戶為單位，三年內按改善內容核實補助，"
    "最高新臺幣五萬元整（苗栗縣中低收入老人住宅設施修繕設備補助辦法第 5 條）。"
    "欄位填的是上限。"
)


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

    cur.execute("SELECT name, county, source_url, description, amount_min,"
                " amount_max FROM benefits WHERE id = %s", (BID,))
    r2 = cur.fetchone()
    if not r2:
        return 1
    o_name, county, o_url, o_desc, o_min, o_max = r2

    print(f"  [{BID}] {county}")
    print(f"    名稱：{o_name}")
    print(f"      → {NEW_NAME}")
    print(f"    網址：{o_url}")
    print(f"      → {NEW_URL}")
    print(f"    金額：{o_min:,}~{o_max:,}（🔴 那是資格門檻）")
    print(f"      → ≤ 50,000 one_time（核實補助上限）")

    txt = strip_noise(extract(NEW_URL) or "")
    print(f"\n    新來源抓到 {len(txt)} 字")
    missing = [m for m in MUST_HAVE if m not in txt]
    if missing:
        print(f"    🔴 新來源缺少必要事實 {missing} ⇒ 整筆不動")
        return 1
    print(f"    ✅ 對象／金額／期間三個決定性事實全部在原文裡")

    print(f"\n    描述 {len(o_desc or '')} → {len(NEW_DESC)} 字")
    if len(NEW_DESC) < len(o_desc or ""):
        print("    🔴 新描述比舊的短 ⇒ 整筆不動")
        return 1

    if not args.apply:
        print(f"\n    ---- 新描述 ----\n    {NEW_DESC[:600]}")
        print("\n（dry-run，未寫入。確認後加 --apply）")
        return 0

    cur.execute(
        "UPDATE benefits SET name=%s, source_url=%s, description=%s,"
        " amount_min=NULL, amount_max=50000, amount_unit='one_time',"
        " amount_note=%s, last_verified_date=CURRENT_DATE WHERE id=%s",
        (NEW_NAME, NEW_URL, NEW_DESC, NEW_NOTE, BID))
    conn.commit()

    # 🔴 驗終點
    cur.execute("SELECT name, source_url, amount_min, amount_max,"
                " amount_unit FROM benefits WHERE id = %s", (BID,))
    g = cur.fetchone()
    if g != (NEW_NAME, NEW_URL, None, 50000, "one_time"):
        print(f"🔴 驗終點失敗：{g}")
        return 1
    print("\n✅ 已寫入，驗終點通過")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
