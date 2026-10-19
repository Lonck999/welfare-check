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
