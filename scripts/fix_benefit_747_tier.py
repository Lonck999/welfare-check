#!/usr/bin/env python3
"""修 747 臺中市原住民幼兒托教補助 —— W-009 剩下的最後一筆。

🔴 原本登記的問題是「source_url 是機關首頁卻標 official」。
   查下去發現**三件事全是錯的**，而且每一件都是我自己踩過的雷：

① 🔴 **opendata 原始來源本來就有逐筆網址，是匯入丟掉的**（＝§5.7，昨天剛寫）
   `data.gov.tw/dataset/138589` 的 CSV 欄位叫「**網址**」（三個字），
   值是 `https://www.ipd.taichung.gov.tw/1741901/post`。
   而 `ALIAS["link"]` 昨天修過（補了桃園的 `sourceUrl`）**卻沒有「網址」**
   ⇒ fallback 到 `competentAuthorityUrl`（局處首頁）⇒ 看起來正常。
   ⚠️ 昨天我自己在 §5.7 寫下「**補齊清單只撐到下次新增**」—— 一天後驗證。

② 🔴 **那個逐筆網址已經死了**（渲染 0 字、無標題）
   ⚠️ 但 §5.8 說「`web_extract` 抓不到不代表網址死」⇒ 用 render_page.py 渲染，
   仍是 0 字；**negative control**：同站 `/12613/12703/12710` 渲染得到 2,788 字
   ⇒ 工具正常，是這個頁真的沒了。
   **沒有 negative control 就分不出「頁面死了」與「我的工具壞了」。**

③ 🔴 **中央法源早就廢止了**（＝§5.9，昨天剛寫）
   `law.cip.gov.tw/LawContent.aspx?id=GL000141`
   法規名稱：**廢**原住民族委員會辦理原住民幼兒就讀幼兒園補助作業要點
   廢止日期：民國 113 年 08 月 21 日（原民教字第11300411641號令）
   ⚠️ 本文八點完整寫著「公立 8,500／私立 10,000」，從頭到尾沒提自己被廢止
   ⇒ **只讀本文會抓出一組看起來很權威的現行金額**（這是 48 小時內第二次）。

🔴 所以「金額待查證」這個描述是對的，但理由寫錯了 ——
   不是「只找到 2015 年新聞稿所以不確定」，
   而是**那組金額的法源已經廢止，去查新聞稿永遠查不到答案**。

⚠️ 為什麼不換成「現行公告頁」：原民會官網「各項福利措施」**只有 7 篇公告**
   （已逐一渲染確認標題：國家考試／語言認證／技術士證照／長者假牙／
   勞動合作社／法律服務／機構證明書）—— **沒有托教補助**。
   ⇒ 這個補助在臺中市原民會的現行公告裡**不存在**。

🔴 處理方式（與 id 865 急難救助同一個判準，使用者 2026-10-08 選的 A）：
   `official` → `unknown`、金額維持 NULL、**描述寫明三個互相衝突的事實**，
   並給**實際可走的路**（教育局托育一條龍是現行的，法源在 law.taichung）。
   **不隱藏**（家長真的在找這個補助），**但不給一組可能已不存在的數字**。

執行：
    python scripts/fix_benefit_747_tier.py            # dry-run
    python scripts/fix_benefit_747_tier.py --apply
"""
from __future__ import annotations

import os
import sys

import psycopg2

BID = 747

NEW_TIER = "unknown"

NEW_DESC = (
    "臺中市原住民幼兒托教補助（又稱原住民幼兒學前教育補助）。"
    "補助對象需具原住民身分、年滿 3 足歲至 4 足歲（即中小班），"
    "就讀本市立案公私立幼兒園；原民會版本無設籍限制"
    "（就讀準公共化、非營利幼兒園及中低收入戶除外）。"
    "年齡以幼兒入園當學年度 9 月 1 日滿該歲數認定。"
    "\n\n"
    "🔴 金額無法確認，而且不是「還沒查到」—— 是三個來源互相衝突：\n"
    "（1）中央法源「原住民族委員會辦理原住民幼兒就讀幼兒園補助作業要點」"
    "（公立每學期最高 8,500 元、私立 10,000 元）"
    "已於民國 113 年 8 月 21 日廢止"
    "（原民教字第11300411641號令，law.cip.gov.tw/LawContent.aspx?id=GL000141）。\n"
    "（2）臺中市 opendata（data.gov.tw/dataset/138589）仍登載這個補助項目，"
    "但它提供的逐筆網址（www.ipd.taichung.gov.tw/1741901/post）已經失效。\n"
    "（3）臺中市原民會官網「各項福利措施」現行公告共 7 篇"
    "（國家考試、語言認證、技術士證照、長者假牙、勞動合作社、法律服務、"
    "機構證明書），其中沒有托教補助。\n"
    "\n"
    "✅ 現行確定還在辦的是教育局「托育一條龍／臺中市幼兒學前教育補助方案」"
    "（2～未滿 5 歲，就讀私立幼兒園每學期最高 15,000 元、公立免學費，"
    "另有經濟弱勢加額補助；申請期間上學期 9/1-10/15、下學期 3/1-4/15，"
    "由幼兒園造冊向教育局請款）。"
    "原民會版本過去與托育一條龍是整合性辦理（非擇一或雙向請領）："
    "需先依身分別向原民會申請，符合托育一條龍者如有差額由教育局另行撥付。"
    "🔴 年滿 2 足歲未滿 3 歲（幼幼班）及 5 足歲未滿 6 歲（大班）"
    "一律改申請教育局托育一條龍及教育部免學費補助。\n"
    "\n"
    "⚠️ 要申請請直接電洽臺中市政府原住民族事務委員會文教福利組 "
    "04-22289111 轉 50106 確認「這個學年度還辦不辦、金額多少」，"
    "不要照本頁或舊新聞稿的數字準備預算。"
)

NEW_NOTES = (
    "🔴 查證：中央法源已於民國 113-08-21 廢止，"
    "opendata 提供的逐筆網址已失效，原民會現行公告 7 篇中無此項 "
    "⇒ source_tier 由 official 降為 unknown、金額維持 NULL。"
    "⚠️ 不可因為「opendata 還登著」就回復 official —— "
    "opendata 的詮釋資料更新日晚於法規廢止日，"
    "那代表資料集沒跟上，不代表補助還在。"
)

# 🔴 來源維持原民會首頁（不改成已失效的逐筆頁）：
#    降成 unknown 之後，首頁當來源不再是「沒來源卻掛官方認證」的問題，
#    而且它仍是使用者查這件事唯一還活著的官方入口。


def main() -> int:
    apply = "--apply" in sys.argv
    dsn = os.environ.get("DATABASE_URL")
    conn = psycopg2.connect(dsn) if dsn else psycopg2.connect(dbname="welfare_check")
    cur = conn.cursor()

    cur.execute(
        "SELECT name, source_tier, amount_min, amount_max, source_url, "
        "LENGTH(description), last_verified_date FROM benefits WHERE id=%s",
        (BID,),
    )
    row = cur.fetchone()
    if row is None:
        sys.exit(f"🔴 找不到 id={BID}，整批中止")
    name, tier, amin, amax, url, dlen, lvd = row

    print(f"[{BID}] {name}")
    print(f"  現況　tier={tier}　amount={amin}~{amax}　desc={dlen} 字　"
          f"last_verified={lvd}")
    print(f"  source_url={url}")
    print(f"  改成　tier={NEW_TIER}　amount 維持 NULL　desc={len(NEW_DESC)} 字")

    # 🔴 前置驗證：金額本來就該是 NULL。若不是，代表有人補過值 ——
    #    那要先搞清楚他憑什麼補，不可被這支腳本默默蓋掉。
    if amin is not None or amax is not None:
        sys.exit(
            f"🔴 id={BID} 的金額不是 NULL（{amin}~{amax}）—— "
            "有人補過值，先查清來源再決定，本腳本中止"
        )

    if not apply:
        print("\n(dry-run，加 --apply 才寫入)")
        return 0

    cur.execute(
        "UPDATE benefits SET source_tier=%s, description=%s, notes=%s, "
        "last_verified_date=CURRENT_DATE WHERE id=%s",
        (NEW_TIER, NEW_DESC, NEW_NOTES, BID),
    )
    if cur.rowcount != 1:
        conn.rollback()
        sys.exit(f"🔴 UPDATE 影響 {cur.rowcount} 列（預期 1），已 rollback")
    conn.commit()

    # 🔴 驗終點：從 DB 讀回來，不信 rowcount
    cur.execute(
        "SELECT source_tier, amount_min, amount_max, LENGTH(description) "
        "FROM benefits WHERE id=%s",
        (BID,),
    )
    got = cur.fetchone()
    if got is None:          # 🔴 寫完卻讀不回來 ⇒ 不可印「已驗證」
        sys.exit(f"🔴 寫入後讀不回 id={BID}，無法驗證")
    assert got[0] == NEW_TIER, got
    assert got[1] is None and got[2] is None, got
    print(f"\n✅ 已寫入並讀回驗證：tier={got[0]}　amount={got[1]}~{got[2]}　"
          f"desc={got[3]} 字")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
