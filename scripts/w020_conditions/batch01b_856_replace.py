"""W-020 856 處理（Lonck 2026-10-20 選 A）：停用 856（來源法規 102-12-04 已廢止），新增現行社會處頁面那筆。
   用法：python _tmp-w020_856.py [--apply]"""
import json, sys, psycopg2
URL = ('https://society.hccg.gov.tw/ch/home.jsp?id=127&parentpath=0,3,26&mcustomize=onemessages_view.jsp'
       '&toolsflag=Y&dataserno=201603290062&t=SocietyOnes&mserno=201603090030')
EXCERPT = ('設籍並實際居住新竹市、領有本市核（換）發或註記之身心障礙證明，且符合下列規定者：'
           '(一)家庭總收入平均未達當年度每人每月最低生活費標準2.5倍或未超過臺灣地區平均每人每月消費支出1.5倍者。…'
           '(六)身心障礙者、配偶及其戶籍內之直系親屬，於各縣市均無自有住宅。'
           '申請租賃房屋租金補助標準：…三口以上家庭每平方公尺100元，最高補助44平方公尺，並以租金總額50%為上限。'
           '（頁面更新日期：114-05-16）')
html = open('/Users/lonck/.hermes/cache/welfare_w020/hc_rent.html', encoding='utf-8', errors='ignore').read()
for frag in ['家庭總收入平均未達當年度每人每月最低生活費標準2.5倍', '最高補助44平方公尺', '於各縣市均無自有住宅', '更新日期：114-05-16']:
    assert frag in html.replace('\xa0', ' ').replace(' ', '').replace('：', '：') or frag.replace(' ', '') in html.replace(' ', ''), f'原文找不到：{frag}'
EC = {
    "counties": ["新竹市"],
    "requiredFlags": ["disability_certificate"],
    "uncheckedConditions": [
        "家庭總收入平均未達最低生活費 2.5 倍，或未超過臺灣地區平均每人每月消費支出 1.5 倍",
        "租金補貼：本人、配偶及戶籍內直系親屬於各縣市均無自有住宅，且租屋在本市",
        "購屋貸款利息補貼：家庭總收入平均未達最低生活費 4 倍；無自有住宅或僅一戶 5 年內購買且貸款未清償；每年 5/1–5/30 受理",
        "未接受政府其他租金／貸款利息補貼、未獲住宿式照顧補助、未使用公有房舍或平價住宅",
    ],
    "_source": "W-020 2026-10-20 依新竹市社會處現行頁面（更新 114-05-16）；取代 856（依據的作業要點 102-12-04 已廢止）",
}
cx = psycopg2.connect(dbname='welfare_check'); cur = cx.cursor()
cur.execute('select is_active, name from benefits where id = 856'); print('856 現況', cur.fetchone())
cur.execute("select id from benefits where source_url = %s", (URL,)); print('同網址既有', cur.fetchall())
if '--apply' not in sys.argv:
    print('(dry-run)'); sys.exit()
cur.execute("""update benefits set is_active = false, deactivated_at = now(), updated_at = now(), validity_status = 'deactivated',
     deactivated_reason = 'W-020：來源「新竹市政府身心障礙者租賃房屋租金及購屋貸款利息補助作業要點」102-12-04 已廢止；現行版本另立新筆'
   where id = 856 and is_active""")
assert cur.rowcount == 1
cur.execute("""insert into benefits (name, agency, county, description, search_group, is_time_sensitive, application_period,
     eligibility_conditions, source_url, source_excerpt, last_verified_date, is_active, amount_max, amount_unit, amount_note,
     deadline_type, source_tier, validity_status, validity_checked_at, validity_evidence)
   values (%s,%s,%s,%s,%s,false,%s,%s,%s,%s,current_date,true,%s,%s,%s,'always','official','valid_current',now(),%s) returning id""",
  ('新竹市身心障礙者房屋租金及購屋貸款利息補貼', '新竹市政府社會處', '新竹市',
   '領有身障證明、設籍並實際居住新竹市者，租屋可申請租金補貼（每平方公尺 100 元，依家庭人口最高 20／32／44 平方公尺，不超過租金 50%）；'
   '購屋可申請貸款利息補貼（每年 5 月受理）。詳見官方頁面。',
   '現金與生活補助類', '租金補貼隨時申請；購屋貸款利息補貼每年 5/1–5/30',
   json.dumps(EC, ensure_ascii=False), URL, EXCERPT,
   4400, 'monthly', '推算：每平方公尺 100 元 × 最高 44 平方公尺（三口以上家庭）＝每月最高 4,400，且不超過租金總額 50%',
   '頁面更新日期 114-05-16，現行受理中'))
new_id = cur.fetchone()[0]
cur.execute("""insert into benefit_change_log (benefit_id, change_type, field_name, old_value, new_value, source_url, source_excerpt,
     detected_at, reviewed_by, approved_at) values (%s,'new_candidate','name',null,%s,%s,%s,now(),'Lonck',now())""",
  (new_id, '新竹市｜新竹市身心障礙者房屋租金及購屋貸款利息補貼（取代 856）', URL, EXCERPT))
cx.commit()
print('✅ 856 停用；新增', new_id)
