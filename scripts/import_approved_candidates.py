#!/usr/bin/env python3
"""匯入「已核准的新福利候選」（C-6 來源 B）—— benefit_change_log.new_candidate → benefits。

🔴 2026-10-19 建。為什麼要有這支：
   `welfare_change_review.py apply` 核准後印的是
   「跑 import_county_opendata.py --county <來源> --apply」——
   但那支**只匯開放資料**。來源 B（搜尋）判出來的新福利**不在任何開放資料裡**
   ⇒ 核准了也永遠進不了 benefits，而且沒有任何訊號。
   10-19 實查：267–275 九筆 approved_at 有值、benefit_id 全 NULL、benefits 零筆對應。

做法：每筆的欄位**逐筆寫死**（同 import_gap_items.py 的理由：長尾項目人工查證比猜測式抽取可靠）。
   · 金額只填頁面原文讀到的；「最高」⇒ min=NULL（CLAUDE.md 金額三種性質）
   · 讀不到的一律 None
   · 寫入後回填 change_log.benefit_id，讓「核准了但沒進庫」查得出來

用法：
  import_approved_candidates.py            # dry-run
  import_approved_candidates.py --apply
"""
from __future__ import annotations

import argparse
import json
import sys

import psycopg2

# change_log id → (agency, search_group, amin, amax, unit, amount_note, deadline_type, deadline_date)
ITEMS = {
    267: ("桃園市政府婦幼發展局", "醫療與健康類", None, 6000, "monthly",
          "最高補助：6 歲以下每月 4,000、7～未滿 18 歲每月 3,000；低收入戶 6 歲以下每月 6,000（115/1/1 起施行）",
          "always", None),
    268: ("苗栗縣政府", "就業與勞工權益類", None, None, None,
          "取得甲級或乙級技術士證照者，全額補助報名費（各職類級別依技能檢定中心一覽表）",
          "fixed", "2026-11-30"),
    269: ("苗栗縣政府勞工及青年發展處", "就業與勞工權益類", None, None, None,
          "技術士證照津貼／就業培力津貼／穩定就業獎勵三項，金額見官方頁",
          "unknown", None),
    270: ("臺中市政府社會局", "醫療與健康類", None, 10000, "one_time",
          "每次懷孕 40 趟、單趟上限 250 點（上限 10,000 為 40×250 推算，頁面未直接寫總額）；115/10/1 起",
          "always", None),
    271: ("臺中市政府衛生局", "醫療與健康類", None, 44000, "one_time",
          "補助假牙裝置實體、非金錢給付；上下顎全口無牙活動式假牙最高 44,000；終身 1 次；限所得未達申報標準或稅率 5% 以下",
          "unknown", None),
    272: ("基隆市政府", "醫療與健康類", None, 20000, "one_time",
          "產檢車資、營養品、治裝費，每次孕期最高 20,000",
          "unknown", None),
    273: ("新竹縣政府社會處", "就業與勞工權益類", None, 6000, "yearly",
          "全國技術士證照津貼每次最高 3,000、每人每年限 2 次（年度上限 6,000 為 3,000×2 推算）；另有就業培力津貼",
          "unknown", None),
    274: ("金門縣政府", "現金與生活補助類", 30000, 30000, "one_time",
          "每名新生兒一次性發放加碼補助 30,000（115/8/21 修正）",
          "unknown", None),
    275: ("金門縣政府", "現金與生活補助類", None, None, None,
          "未滿 3 歲、送托本縣公共化或準公共托育者；金額見官方頁（115/5/1 起施行）",
          "unknown", None),
    # ── C-6 來源 C（目錄頁）2026-10-19 Lonck 核准 38 筆 ──
    321: ('屏東縣政府社會處', '現金與生活補助類', 2000, 2000, 'monthly', '每月2,000、連續12個月，最高24,000；115年(含)後出生須在未滿1歲前申請，逾期不受理', 'event', None),
    322: ('屏東縣政府社會處', '就業與勞工權益類', None, None, None, '依屏東客運票價按實際上班日補助往返交通費，每月上限22天；須經縣府轉介就業且同一僱主滿3個月', 'always', None),
    323: ('屏東縣政府社會處', '現金與生活補助類', None, None, None, '子女課後輔導及安親班車資補助（頁面未列金額上限）；受理115/1/1–12/31，當年度申請於12/5前', 'fixed', '2026-12-05'),
    324: ('屏東縣政府社會處', '醫療與健康類', None, 20000, 'one_time', '精神科住院自付餘額實支實付，每次療程最高2萬；由醫院於療程結束後3個月內申請', 'always', None),
    325: ('高雄市政府社會局', '醫療與健康類', None, 6000, 'monthly', '6～未滿18歲自費療育訓練，每月最高4,000；低收入戶每月最高6,000', 'always', None),
    326: ('高雄市政府社會局', '現金與生活補助類', 2313, 2661, 'monthly', '弱勢單親：子女未滿15歲每人每月2,661；15～未滿18歲且就學每人每月2,313（監護2名以上一律2,313）', 'always', None),
    327: ('高雄市政府社會局', '教育類', None, 14000, 'yearly', '已領單親子女生活補助者，18～未滿25歲就讀大專日間部，每學年最高14,000；每年3月底前申請', 'annual', None),
    328: ('高雄市政府社會局', '住宅類', None, 100000, 'one_time', '65歲以上低收／中低收／領中低老人津貼或身障生活補助者，每戶最高10萬（114/7/1起）；核准前勿先修繕', 'always', None),
    329: ('高雄市政府社會局', '現金與生活補助類', 24000, 24000, 'monthly', '中低收入、中重度失能長者入住評鑑合格機構，每人每月24,000；不得與其他津貼重複', 'always', None),
    330: ('高雄市政府社會局', '現金與生活補助類', 24000, 24000, 'monthly', '低收入戶中重度失能長者入住機構每月24,000；第1類重度另補耗材每月1,000、氧氣機每月最高3,000', 'always', None),
    331: ('高雄市政府社會局', '醫療與健康類', None, 150000, 'yearly', '低收入戶醫療費全額補助、中低收入戶超過3萬部分補80%，每人每年最高15萬；出院後3個月內申請', 'always', None),
    332: ('高雄市政府衛生局', '身心障礙福利', None, None, None, '補助拍痰器、抽痰機、氧氣製造機、呼吸器、壓力衣等13項醫療輔具與人工電子耳等醫療費用（金額見官方頁）', 'always', None),
    333: ('高雄市政府社會局', '身心障礙福利', None, 826, 'monthly', '法定補助之外，輕中度身障且稅率5%以下者另補健保自付額，每月最高826；免申請，由社會局主動報送', 'always', None),
    334: ('高雄市政府社會局', '身心障礙福利', None, None, None, '按月每坪補貼200元、以租金總額50%為上限（單身最高7坪、二口12坪、三口以上17坪）；每年12月受理', 'annual', None),
    335: ('高雄市政府社會局', '身心障礙福利', None, None, None, '貸款額度最高220萬，補貼與國民住宅基金利率間之利息差額；名額依年度公告；每年12月受理', 'annual', None),
    336: ('高雄市政府社會局', '身心障礙福利', None, 1000, 'monthly', '每月最高1,000；低收補月租50%、中低收40%、領身障生活補助25%；每年12月受理', 'annual', None),
    337: ('高雄市政府社會局', '身心障礙福利', None, None, None, '補利息差額：低收100%、中低收80%、領身障生活補助50%；每年12月受理', 'annual', None),
    338: ('高雄市政府交通局', '身心障礙福利', None, None, None, '身障停車：機車格免費、計時格每日前4小時免費、其餘多為半價（依識別證核發地與格位類型）', 'always', None),
    339: ('高雄市政府社會局', '身心障礙福利', None, None, None, '低收入戶全額補助、中低收入戶75%或85%；其餘依年齡與家庭經濟補25%～85%', 'always', None),
    340: ('高雄市政府教育局', '教育類', None, 6000, 'monthly', '國中小身障學生在家教育每月3,500；安置於社福機構依家長負擔額補助，每月最高6,000；每學期開學後14日內申請', 'annual', None),
    341: ('高雄市政府勞工局', '身心障礙福利', None, 7000, 'one_time', '駕訓班學費補1/2、最高7,000；考取另發獎勵金3,000；另補報名費450、領照費200；經費用罄即停（取得駕照1年內申請）', 'event', None),
    342: ('高雄市政府消防局', '一般性優惠與便民服務', None, None, None, '低收入戶、獨居長者或身障者居住5層樓以下住宅，補助住宅用火災警報器1顆（實物）', 'always', None),
    343: ('高雄市政府社會局', '醫療與健康類', 5000, 5000, 'one_time', '低收入戶高風險孕產婦及嬰幼兒，經醫師診斷需營養補充，每人每次5,000，每6個月得申請一次', 'always', None),
    344: ('高雄市政府社會局', '一般性優惠與便民服務', None, None, None, '低收入戶25歲以下高中職以上在學學生，每月60段次內免費搭乘市營公共車船，捷運以學生票計', 'always', None),
    345: ('高雄市政府社會局', '現金與生活補助類', None, 200000, 'one_time', '依高雄市災害救助金核發辦法：死亡失蹤20萬、重傷10萬、淹水50公分每戶1.5萬、毀損不堪居住每人2萬（每戶最高10萬）；災後30日內向區公所申請', 'event', None),
    346: ('高雄市政府社會局', '教育類', None, None, None, '低收入戶子女國三／高三／五專五年級升學補習費補助（金額見公告）；名額有限、額滿截止，須參與脫貧自立計畫', 'announced', None),
    347: ('高雄市政府社會局', '教育類', None, None, None, '低收入戶高中職以上在學子女購買電腦、翻譯機等學習設備補助（金額見公告）；名額有限、額滿截止', 'announced', None),
    348: ('高雄市政府社會局', '現金與生活補助類', 1500, 3000, 'monthly', '弱勢單親家庭子女就讀本市公私立幼兒園，每人每月1,500～3,000', 'always', None),
    349: ('高雄市政府社會局', '教育類', None, None, None, '單親家長就讀高中職或大專修習學位之學費及臨時托育費補助（金額見官方頁）；須經社工轉介', 'always', None),
    350: ('高雄市政府社會局', '現金與生活補助類', None, 50000, 'one_time', '經家防中心確定之家暴被害人，補助撰狀費及律師費最高5萬', 'always', None),
    351: ('澎湖縣政府教育處', '教育類', None, None, None, '就讀澎湖縣高中職學生，每人每學期5,000（現金或交通圖書券）；申請日期依縣府公告', 'announced', None),
    352: ('澎湖縣政府教育處', '教育類', None, 2000, 'one_time', '國小一年級新生制服及運動服每人2,000；國小學童文具每學年200；每年7/1～9/30由學校申請', 'annual', None),
    353: ('澎湖縣政府社會處', '現金與生活補助類', 3000, 3000, 'monthly', '未滿2歲嬰幼兒每月3,000、每季撥付，最多72,000或滿2歲止；出生60日內申請可追溯', 'always', None),
    354: ('澎湖縣政府衛生局', '醫療與健康類', None, 50000, 'one_time', '65歲以上、澎湖籍滿3年，活動假牙全口5萬、半口2.5萬、全口部分4萬、半口部分2萬；由合約牙醫診所申請', 'always', None),
    355: ('澎湖縣政府社會處', '醫療與健康類', None, None, None, '6歲以下幼童健保費自負額補助（父母一方設籍滿1年）；遷出即停', 'always', None),
    356: ('金門縣政府社會處', '現金與生活補助類', None, 30000, 'one_time', '設籍前新住民：醫療補助每次最高3萬（低收全額、中低收80%）；另有急難救助、產婦及嬰兒營養補助', 'always', None),
    357: ('金門縣政府社會處', '現金與生活補助類', None, None, None, '設籍前新住民遭逢特殊境遇：緊急生活扶助每次最高本縣最低生活費3個月；另有法律訴訟補助', 'event', None),
    358: ('金門縣政府社會處', '現金與生活補助類', 20000, None, 'one_time', '單胞胎2萬、雙胞胎6萬、三胞胎以上每胞胎4萬乘胎數；生產後8個月內向鄉鎮公所申請（與生育贈禮、支持生育加碼為不同方案）', 'event', None),
}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    conn = psycopg2.connect(dbname="welfare_check")
    cur = conn.cursor()
    cur.execute("""SELECT id, new_value, source_url, source_excerpt, benefit_id
                     FROM benefit_change_log
                    WHERE change_type='new_candidate' AND approved_at IS NOT NULL
                      AND rejected_at IS NULL ORDER BY id""")
    rows = cur.fetchall()
    missing = [r[0] for r in rows if r[4] is None and r[0] not in ITEMS]
    if missing:
        print(f"🔴 核准了但這支沒有欄位定義：{missing} —— 先補 ITEMS，整批不寫")
        return 1
    cur.execute("SELECT count(*) FROM benefits")
    before = cur.fetchone()[0]
    todo = []
    for cid, nv, url, excerpt, bid in rows:
        if bid is not None:
            continue
        county, name = nv.split("｜", 1)
        cur.execute("SELECT id FROM benefits WHERE county=%s AND replace(name,' ','')=replace(%s,' ','')",
                    (county, name))
        hit = cur.fetchone()
        if hit:
            print(f"  ⏭ 已在庫（id {hit[0]}），只回填 benefit_id：{county}｜{name}")
            todo.append((cid, None, county, name, url, excerpt, hit[0]))
            continue
        todo.append((cid, ITEMS[cid], county, name, url, excerpt, None))
        ag, grp, amin, amax, unit, note, dt, dd = ITEMS[cid]
        print(f"  + [{cid}] {county}｜{name}｜{ag}｜{grp}｜{amin}~{amax} {unit}")
    if not a.apply:
        print(f"\n（dry-run）會新增 {sum(1 for t in todo if t[1])} 筆、回填 {len(todo)} 筆 benefit_id")
        return 0
    new_ids = []
    for cid, item, county, name, url, excerpt, bid in todo:
        if item:
            ag, grp, amin, amax, unit, note, dt, dd = item
            ex = excerpt.split("　【判讀】")[0]
            desc = f"{name}。{note}。詳見官方頁面。"
            cur.execute("""
                INSERT INTO benefits
                  (name, agency, county, description, search_group, eligibility_conditions,
                   source_url, source_excerpt, last_verified_date, is_active,
                   amount_min, amount_max, amount_unit, amount_note,
                   deadline_type, deadline_date, source_tier,
                   validity_status, validity_checked_at, validity_evidence)
                VALUES (%s,%s,%s,%s,%s,%s::jsonb,%s,%s,CURRENT_DATE,true,
                        %s,%s,%s,%s,%s,%s,'official','valid_current',now(),%s)
                RETURNING id""",
                (name, ag, county, desc, grp,
                 json.dumps({"counties": [county], "_note": "資格條件見官方頁（C-6 來源 B 新增）"},
                            ensure_ascii=False),
                 url, ex[:900], amin, amax, unit, note, dt, dd,
                 f"C-6 來源 B 人工判讀＋2026-10-19 Lonck 核准；頁面原文：{ex[:300]}"))
            bid = cur.fetchone()[0]
            new_ids.append(bid)
        cur.execute("UPDATE benefit_change_log SET benefit_id=%s WHERE id=%s", (bid, cid))
    conn.commit()
    cur.execute("SELECT count(*) FROM benefits")
    after = cur.fetchone()[0]
    cur.execute("""SELECT count(*) FROM benefit_change_log
                    WHERE change_type='new_candidate' AND approved_at IS NOT NULL
                      AND rejected_at IS NULL AND benefit_id IS NULL""")
    left = cur.fetchone()[0]
    print(f"\n✅ benefits {before} → {after}（新增 {len(new_ids)}：{new_ids}）；核准但未入庫剩 {left}")
    if after - before != len(new_ids) or left:
        print("🔴 筆數不符或仍有核准未入庫")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
