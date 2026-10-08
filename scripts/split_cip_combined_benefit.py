#!/usr/bin/env python3
"""把 id 34「原住民族委員會補助（創業貸款/獎助學金/急難救助）」拆成三筆。

🔴 為什麼要拆（W-009 剩下的 2 筆之一）：
   這一筆名稱裡就寫著三個補助，而它們的**法源、金額、申請窗口、現行狀態
   全都不同** —— 壓成一筆的話使用者無法知道自己該申請哪個、去哪裡辦。
   ⚠️ 它原本的問題被登記成「source_url 指向首頁」，
   但那只是症狀：**一筆混三個補助，本來就不可能有單一來源網址。**

   子表的證據自己就把它們分開了：
     benefit_documents：「在學證明/成績單（獎助學金）」「創業輔導課程證明（創業貸款）」
     benefit_locations：cip.gov.tw（主管機關）與 cipgrant.fju.edu.tw（獎助學金系統）

═══ 🔴 三筆的金額全部留 NULL，這是刻意的 ═══

| 項目 | 官方數字 | 為什麼不填 |
|---|---|---|
| 獎助學金 | 32,000／20,000／30,000／20,000 | **四種擇一**（要點第四點「以一項為限」），不是區間。填 20,000~32,000 會讓人以為能領到中間值，**而中間值一個都不存在**（同 W-007 id 748 的錯） |
| 事業貸款 | 開辦費 200 萬／週轉金 500 萬／資本支出 5,000 萬 | 🔴 **那是「可以借多少」不是「可以領多少」**。放進一個叫「福利查詢」的 amount 欄位會被讀成可領金額 |
| 急難救助 | 死亡 2 萬／醫療 2 萬／生活 1 萬／災害 5 萬 | 🔴 **法源已於 2026-05-08 廢止**，那組數字沒有現行依據（見下） |

金額級距一律寫進 `amount_note` 與 `description`，讓人看得到但不會被當成單一數字。

═══ 🔴 急難救助：法源已廢止，但 E 政府還在公告（Lonck 選 A）═══

三個互相衝突的事實，全部都要寫進資料：
  · `law.cip.gov.tw/LawContent.aspx?id=GL000032` 標題是「**廢**…實施要點」，
    廢止日期 **民國 115-05-08（＝2026-05-08）**
    ⚠️ **那一列在表格裡長得跟「修正日期」一模一樣**，而本文十點
    從頭到尾沒提自己被廢止 ⇒ 只讀本文會抓出一組看起來很權威的金額
  · 財劃法修法後中央專款被刪，責任轉地方自籌；
    台東縣成功鎮公所**已公告暫停受理**（往年約 40 餘萬元額度）
  · E 政府「急難紓困方案」頁（更新 2026-08-27，**比廢止晚三個半月**）
    仍列著原住民急難救助與同一組金額，窗口寫「戶籍地公所」

🔴 ⇒ `source_tier='unknown'`、金額 NULL、描述明寫「依戶籍地公所為準」。
   **不隱藏這筆**（多數鄉鎮仍在辦，而急難時這是救命錢），
   但也不給一個可能已經不存在的數字讓人去據此做決定。

═══ 寫入規則（沿用 split_label_benefits.py 的模式）═══
· 三筆新增，各帶自己的子表（applicants / documents / locations）
· 🔴 原本那筆標 `is_active=false` 並在描述註明「已拆分為 3 筆」，
  **保留不刪** —— 刪掉的話月更比對會把它當成新缺口再抓一次
· 🔴 可重複執行：同名已存在就跳過
"""
from __future__ import annotations

import argparse
import json
import sys

import psycopg2

SRC_ID = 34
AGENCY = "原住民族委員會"
GROUP = "特殊身分族群類"
CAT = 41

# 🔴 每一筆的 source_url 都是**逐筆的權威頁**，不是機關首頁
#    （那正是 W-009 要修掉的那種錯）。全部已用 web_extract 實抓過正文。
ITEMS: list[dict] = [
    {
        "name": "原住民族委員會大專校院原住民學生獎助學金",
        "url": "https://law.cip.gov.tw/LawContent.aspx?id=FL029068",
        "tier": "official",
        "deadline_type": "annual",
        "effort": 2,
        "desc": (
            "就讀教育部核准立案之國內公私立大專校院、具原住民身分的在學學生"
            "（🔴 不含延長修業年限、五專前三年、研究所、在職專班、推廣教育、"
            "附設進修學校、空中大學）。"
            "📋 四種擇一，**領取以一項為限**（要點第四點）："
            "① 前一學期學業成績達 70 分以上 → 獎學金每學期 32,000 元；"
            "② 成績達 60 分以上，或設籍臺東縣蘭嶼鄉具雅美族身分 → "
            "一般助學金每學期 20,000 元；"
            "③ 低收入戶學生且成績達 60 分以上 → 每學期 30,000 元；"
            "④ 中低收入戶學生且成績達 60 分以上 → 每學期 20,000 元。"
            "⚠️ 享有政府公費待遇、或學雜費與食宿費由就讀學校全額負擔者不得申請。"
            "🔴 每學期須完成校務服務或部落服務合計 24 小時才能支領助學金，"
            "但通過中高級以上族語認證、成績達班級前 30%、考取相關證照等情形可減免。"
            "申請：先至原民會大專校院獎助學金申請系統線上填寫並列印申請表，"
            "連同前一學期成績單正本繳交至就讀學校學生事務處或原住民族學生資源中心"
            "（大一新生用高三上下學期成績單）。"
            "🔴 本筆自「原住民族委員會補助（創業貸款/獎助學金/急難救助）」拆出 —— "
            "原資料把三個法源、金額、窗口都不同的補助併成一筆。"
        ),
        "excerpt": (
            "三、本要點獎助學金申請基準與獎助金額如下：（一）學生前一學期學業成績達"
            "七十分以上者，得申請獎學金期新臺幣三萬二千元。（二）學生前一學期學業成績"
            "達六十分以上或設籍臺東縣蘭嶼鄉具雅美族身分者，得申請一般助學金，每學期"
            "新臺幣二萬元。（三）低收入戶或中低收入戶學生前一學期學業成績達六十分以上"
            "者，得申請低收入戶助金每學期新臺幣三萬元或中低收入戶助學金每學期新臺幣"
            "二萬元。四、學生領取前點獎助學金以一項為限。"
            "（原住民族委員會獎助大專校院原住民學生實施要點，修正日期：民國 114-06-20）"
        ),
        # 🔴 不填 amount_min/max：四種擇一不是區間
        "amount_note": (
            "🔴 四種擇一、領取以一項為限，**不是區間**：獎學金 32,000／"
            "一般助學金 20,000／低收入戶 30,000／中低收入戶 20,000（每學期）。"
            "⚠️ 刻意不填 amount_min/max —— 填成 20,000~32,000 會讓人以為"
            "能領到中間值，而中間值一個都不存在。"
        ),
        "eligibility": {
            "requiredIdentities": ["原住民"],
            "otherConditions": (
                "就讀國內公私立大專校院在學學生；不含延長修業年限、五專前三年、"
                "研究所、在職專班、推廣教育、附設進修學校、空中大學；"
                "前一學期學業成績達 60 分以上（獎學金需 70 分以上）；"
                "每學期須完成服務學習 24 小時（有減免條件）"
            ),
        },
        "applicants": [("self", None)],
        "documents": [
            ("原住民身分證明", None),
            ("前一學期成績單正本（大一新生為高三上下學期成績單）", "就讀學校"),
            ("線上申請系統列印之申請表", "原民會大專校院獎助學金申請系統"),
        ],
        "locations": [
            ("就讀學校學生事務處或原住民族學生資源中心", None, None, None),
            ("原住民族委員會大專校院獎助學金申請系統", None, None,
             "https://cipgrant.fju.edu.tw/"),
        ],
    },
    {
        "name": "原住民族事業貸款（原住民族綜合發展基金）",
        "url": ("https://www.cip.gov.tw/zh-tw/news/data-list/"
                "23DD6FC526F7465A/0C3331F0EBD318C2D25E81EB3374F16A-info.html"),
        "tier": "official",
        "deadline_type": "always",
        "effort": 3,
        "desc": (
            "🔴 **這是貸款不是補助 —— 借到的錢要還。**"
            "對象：年滿 18 歲至 65 歲、具行為能力的原住民，且無信用不良紀錄；"
            "並須於申請前三年內參加本貸款要點列舉單位辦理的創業輔導課程或"
            "創業相關活動至少 20 小時或 2 學分以上。"
            "📋 額度（**可借上限，不是可領金額**）：開辦費／準備金最高 200 萬元；"
            "農林漁牧業週轉金最高 500 萬元或資本支出最高 5,000 萬元。"
            "利率：按郵政儲金二年期定期儲金機動利率加碼 0.125% 浮動計息。"
            "申請方式：填具貸款計畫申請書並檢附應備文件後，逕向原民會派駐各縣（市）"
            "的金融輔導員提出申請，初審符合規定者轉送承辦金融機構辦理徵信、審核及貸放。"
            "免付費原住民金融服務專線 0800-508-188（全臺原住民族金融輔導員服務）。"
            "🔴 本筆自「原住民族委員會補助（創業貸款/獎助學金/急難救助）」拆出。"
        ),
        "excerpt": (
            "一、貸款對象:(一)年滿 18歲至 65歲具有行為能力之原住民，並無信用不良"
            "紀錄者。(二) 於申請本貸款前三年內曾參加本貸款要點列舉單位所舉辦之"
            "創業輔導課程或創業相關活動至少二十小時或二學分以上者。"
            "二、貸款利率:按「郵政儲金二年期定期儲金機動利率」加碼 0.125%浮動計息。"
            "三、申請方式:借款人填具貸款計畫申請書並檢附應備文件後，逕向本會派駐"
            "各縣（市）之金融輔導員提出申請。（原住民族事業貸款公告頁）"
        ),
        "amount_note": (
            "🔴 **這是借款額度不是補助金額**，所以刻意不填 amount_min/max —— "
            "200 萬／500 萬／5,000 萬放在「可領金額」欄位會被嚴重誤讀。"
            "額度依用途不同：開辦費或準備金最高 200 萬；農林漁牧業週轉金最高 500 萬、"
            "資本支出最高 5,000 萬。利率為郵政儲金二年期機動利率加 0.125%。"
        ),
        "eligibility": {
            "requiredIdentities": ["原住民"],
            "ageMin": 18,
            "ageMax": 65,
            "otherConditions": (
                "具行為能力、無信用不良紀錄；申請前三年內參加創業輔導課程或"
                "創業相關活動至少 20 小時或 2 學分以上"
            ),
        },
        "applicants": [("self", None)],
        "documents": [
            ("貸款計畫申請書（要點附件 1）", None),
            ("創業輔導課程或創業相關活動證明（20 小時或 2 學分以上）", None),
            ("原住民族事業貸款申辦應備文件（要點附件 2）所列各項", None),
        ],
        "locations": [
            ("原住民族委員會派駐各縣（市）金融輔導員", None,
             "0800-508-188", "https://ipl.cip.gov.tw/"),
            ("原住民族委員會", "242030 新北市新莊區中平路439號北棟14F-16F",
             "02-89953456", "https://www.cip.gov.tw/"),
        ],
    },
    {
        "name": "原住民急難救助（中央法源已廢止，改依地方規定）",
        "url": "https://law.cip.gov.tw/LawContent.aspx?id=GL000032",
        # 🔴 A 案：法源已廢止 ⇒ 不可標 official（那會終止查證）
        "tier": "unknown",
        "deadline_type": "event",
        "effort": 2,
        "desc": (
            "🔴 **中央法源已於 2026-05-08（民國 115-05-08）廢止** —— "
            "「原住民族委員會輔助原住民急難救助實施要點」已廢止"
            "（原民社字第 11500179233 號令），"
            "且財政收支劃分法修法後中央原民會不再補助縣市辦理此項救助，"
            "經費改由地方政府自行籌措。"
            "⚠️ **是否仍受理、金額多少，一律依戶籍地公所為準** —— "
            "台東縣成功鎮公所已公告「暫停受理」（往年約可申請 40 餘萬元額度），"
            "鄰近鄉鎮多以預編預算或墊付款方式持續辦理。"
            "📋 舊制救助項目與上限（**已失去法源依據，僅供理解制度，不可當現行標準**）："
            "死亡救助最高 1 萬或 2 萬／醫療補助最高 1 萬或 2 萬／生活扶助最高 1 萬／"
            "重大災害救助最高 1 萬至 5 萬。"
            "⚠️ E 政府「急難紓困方案」頁（更新 2026-08-27，比廢止日晚三個半月）"
            "仍列著原住民急難救助與同一組金額，窗口寫「戶籍地公所、"
            "原住民事務委員會」—— 🔴 **中央法源、E 政府公告、地方實際受理狀況"
            "三者目前不一致，打電話問戶籍地公所是唯一可靠的確認方式。**"
            "✅ 替代路徑：一般民眾適用的「急難紓困」（關懷救助金 1 萬~3 萬，"
            "急迫個案訪視時先發 5,000 元）與社會救助法第 21 條的急難救助仍有效，"
            "可撥 1957 福利諮詢專線（每日 08:00-22:00）詢問。"
            "🔴 本筆自「原住民族委員會補助（創業貸款/獎助學金/急難救助）」拆出。"
        ),
        "excerpt": (
            "法規名稱：**廢**原住民族委員會輔助原住民急難救助實施要點／"
            "廢止日期：民國 115 年 05 月 08 日／發文字號：原民社字第11500179233號 令。"
            "（廢止前條文）五、認定及核發基準如下：（一）死亡救助：…負擔家庭生計者"
            "死亡，最高補助二萬元；其非負擔家庭生計者死亡，最高補助一萬元。"
            "（二）醫療補助：…最高補助二萬元／一萬元。（三）生活扶助：…最高補助一萬元。"
            "（四）重大災害救助：…死亡或失蹤者最高補助五萬元；重傷者最高補助三萬元；"
            "無人傷亡，每戶最高補助一萬元。"
            "🔴 本段為**已廢止**法規之條文，不得作為現行金額依據。"
        ),
        "amount_note": (
            "🔴 刻意不填 amount_min/max —— **法源已廢止，舊制金額沒有現行依據**，"
            "且實際是否發放、發多少已改由各地方政府決定。"
            "填上舊制數字會讓人據此做決定（例如先墊錢辦喪事），"
            "而那筆錢在他的鄉鎮可能已經停發。"
        ),
        "eligibility": {
            "requiredIdentities": ["原住民"],
            "otherConditions": (
                "舊制：遭遇緊急危難或災害致生活陷於困境之原住民；"
                "救助項目為死亡救助、醫療補助、生活扶助、重大災害救助；"
                "應於急難事由發生日起三個月內提出申請；"
                "同一事由每年度最多兩次。"
                "🔴 中央法源已廢止，現行條件依戶籍地公所規定"
            ),
        },
        "applicants": [("self", None), ("family", "parent"),
                       ("family", "child"), ("family", "sibling")],
        "documents": [
            ("🔴 先電話確認戶籍地公所是否仍受理本項救助", None),
            ("戶口名簿影本（共同生活）", "戶政事務所"),
            ("死亡證明書／診斷證明書／醫療費用收據（依申請項目）", "醫院或戶政"),
            ("村里長證明或低收入戶、中低收入戶證明", "村里辦公處或公所"),
        ],
        "locations": [
            ("戶籍所在地鄉（鎮、市、區）公所", None, None, None),
            ("直轄市、縣（市）政府原住民族行政單位", None, None, None),
            ("1957 福利諮詢專線（每日 08:00-22:00）", None, "1957", None),
        ],
    },
]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    conn = psycopg2.connect(dbname="welfare_check")
    cur = conn.cursor()

    cur.execute("SELECT name, is_active FROM benefits WHERE id=%s", (SRC_ID,))
    row = cur.fetchone()
    if not row:
        sys.exit(f"🔴 找不到 id={SRC_ID}")
    src_name, src_active = row
    print(f"來源：[{SRC_ID}] {src_name}（is_active={src_active}）\n")

    made = 0
    for it in ITEMS:
        cur.execute("SELECT id FROM benefits WHERE name=%s", (it["name"],))
        hit = cur.fetchone()
        if hit:
            print(f"⏭ 已存在，跳過：[{hit[0]}] {it['name']}")
            continue
        print(f"+ {it['name']}")
        print(f"    tier={it['tier']}　deadline={it['deadline_type']}"
              f"　amount=NULL（理由見 amount_note）")
        print(f"    來源 {it['url']}")
        print(f"    子表：applicants {len(it['applicants'])}／"
              f"documents {len(it['documents'])}／"
              f"locations {len(it['locations'])}")
        made += 1
        if not args.apply:
            continue

        cur.execute("""
            INSERT INTO benefits
              (name, agency, county, description, search_group,
               category_number, application_period, eligibility_conditions,
               source_url, source_excerpt, last_verified_date, is_active,
               amount_note, deadline_type, effort_level, source_tier)
            VALUES (%s,%s,NULL,%s,%s,%s,%s,%s::jsonb,%s,%s,
                    CURRENT_DATE,true,%s,%s,%s,%s)
            RETURNING id""",
            (it["name"], AGENCY, it["desc"], GROUP, CAT, "",
             json.dumps(it["eligibility"], ensure_ascii=False),
             it["url"], it["excerpt"], it["amount_note"],
             it["deadline_type"], it["effort"], it["tier"]))
        got = cur.fetchone()
        if got is None:          # 🔴 RETURNING 沒回東西 ⇒ 不可繼續寫子表
            sys.exit("🔴 INSERT 沒有回傳 id，整批中止（子表會掛到錯的 benefit）")
        new_id = got[0]

        for role, rel in it["applicants"]:
            cur.execute("""INSERT INTO benefit_applicants
                             (benefit_id, role, relation) VALUES (%s,%s,%s)
                           ON CONFLICT DO NOTHING""", (new_id, role, rel))
        for doc, loc in it["documents"]:
            cur.execute("""INSERT INTO benefit_documents
                             (benefit_id, document_name, obtain_location)
                           VALUES (%s,%s,%s)""", (new_id, doc, loc))
        for nm, addr, ph, web in it["locations"]:
            cur.execute("""INSERT INTO benefit_locations
                             (benefit_id, name, address, phone, website)
                           VALUES (%s,%s,%s,%s,%s)""",
                        (new_id, nm, addr, ph, web))
        print(f"    → 寫入 id={new_id}")

    if args.apply and made:
        # 🔴 原筆停用但**保留** —— 刪掉的話月更比對會把它當成新缺口再抓一次
        cur.execute("""UPDATE benefits
                          SET is_active=false,
                              description=%s,
                              last_verified_date=CURRENT_DATE
                        WHERE id=%s""",
                    (f"（已於 2026-10-08 拆分為 {made} 筆獨立補助，本筆不再顯示）"
                     f"原名：{src_name}。"
                     f"🔴 拆分原因：這一筆把**三個法源、金額、申請窗口、"
                     f"現行狀態全都不同**的補助併成一筆 —— "
                     f"① 大專校院獎助學金（現行有效，law.cip.gov.tw FL029068，"
                     f"修正 114-06-20）"
                     f"② 原住民族事業貸款（現行有效，🔴 是借款不是補助）"
                     f"③ 急難救助（🔴 中央法源已於 2026-05-08 廢止，"
                     f"經費改由地方自籌，是否受理依戶籍地公所為準）。"
                     f"⚠️ 原本的 source_url 指向 cipgrant.fju.edu.tw"
                     f"（輔大代辦的獎助學金系統首頁）—— 那只是症狀，"
                     f"**一筆混三個補助本來就不可能有單一來源網址**。",
                     SRC_ID))
        conn.commit()
        print(f"\n✅ 新增 {made} 筆；id={SRC_ID} 已標 is_active=false（保留不刪）")
    elif not args.apply:
        print(f"\n（dry-run，未寫入。會新增 {made} 筆並停用 id={SRC_ID}）")
    else:
        print("\n（沒有新增任何筆，原筆不動）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
