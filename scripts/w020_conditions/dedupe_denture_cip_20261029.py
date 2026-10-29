"""原住民族長者裝置假牙：只留全國一筆（2026-10-29 Lonck 選 A，同屋頂太陽光電判準）。
   原文：原民會「115年度原住民族長者裝置假牙實施計畫」（114/11/24 原民社字第1140052353號函核定，掃描 PDF 第 1–2 頁逐字讀）
     貳、補助機關：原住民族委員會；辦理機關：直轄市及縣（市）政府　參、實施地區：全國
     肆、實施期程：114/11/1 起至 115/10/31 止
     伍、一（一）服務對象為年滿 55 歲以上原住民，資格限制：1 經醫師評估缺牙需裝置假牙，且非衛福部「中低收入老人補助裝置假牙實施計畫」服務對象
       2 未申請其他政府機關所辦假牙計畫補助者　3 5 年內（含本年度）最高不得逾 4 萬元（維修不在此限）　4 同顎同牙位滿 5 年以上始得重新申請
     （二）申請：攜健保卡逕向健保特約牙科提出；由戶籍地直轄市及縣（市）政府審查（10 個工作天內）
   ⇒ 新增全國一筆；停用 988 宜蘭、990 臺東（都是原民會這個計畫、上限同為 4 萬）；
     保留 604 新北（原文分「申請原民會補助」與「申請本局補助」兩條，低收／中低收最高 4 萬 4,000 ＝ 新北自己的加碼）。
   用法：python dedupe_denture_cip_20261029.py [--apply]"""
import json, sys, psycopg2
PDF = 'https://www.hchfe.gov.tw/admin/upload/twgov_file_202605221624491850.pdf'
CIP = 'https://cipdenture.cip.gov.tw/'
REASON = '2026-10-29 Lonck 選 A：與全國「原民會原住民族長者裝置假牙」同一計畫（縣市只是審查窗口），只留全國一筆'
NAME = '原住民族長者裝置假牙補助（原民會）'
DESC = ('原住民族委員會全國計畫：年滿 55 歲以上原住民，經牙醫師評估缺牙需裝置假牙，攜健保卡至全臺健保特約牙科診所申請，'
        '由戶籍地直轄市、縣（市）政府審查；5 年內（含本年度）最高補助 4 萬元（假牙維修不在此限）。'
        '年度計畫：115 年度受理 114/11/1 至 115/10/31，116 年度自 115/11/1 起。'
        '已是衛福部「中低收入老人補助裝置假牙」服務對象者不適用本計畫（改申請該計畫）；新北市另有加碼，見新北項目。')
EXCERPT = ('原住民族委員會115年度原住民族長者裝置假牙實施計畫（114年11月24日原民社字第1140052353號函核定）'
           '貳、辦理機關：一、補助機關：原住民族委員會。二、辦理機關：直轄市及縣（市）政府。參、實施地區：全國 '
           '肆、實施期程：自114年11月1日起至115年10月31日止。伍、一、（一）服務對象為年滿55歲以上原住民，資格限制如下：'
           '1、經醫師評估缺牙需裝置假牙，且非衛生福利部「中低收入老人補助裝置假牙實施計畫」服務對象資格者。'
           '2、未申請其他政府機關所辦假牙計畫補助者。3、服務對象獲本計畫補助，5年內(含本年度)最高補助金額不得逾新臺幣4萬元整(假牙維修不在此限)。')
COND = {'counties': ['全國'], 'ageMin': 55, 'requiredIdentities': ['原住民'],
        'uncheckedConditions': ['經牙醫師評估缺牙需裝置假牙',
                                '非衛福部「中低收入老人補助裝置假牙實施計畫」服務對象（是的話改申請該計畫）',
                                '未申請其他政府機關所辦假牙計畫補助',
                                '5 年內（含本年度）本計畫補助合計不得逾 4 萬元；同顎同牙位滿 5 年且經評估有必要才可重新申請'],
        '_source': f'原民會 115 年度原住民族長者裝置假牙實施計畫（掃描 PDF 第 2 頁「伍、一（一）」逐字讀）（{PDF}）'}
conn = psycopg2.connect(dbname='welfare_check'); cur = conn.cursor()
cur.execute('select id, is_active, name from benefits where id in (988,990,604) order by id')
rows = {r[0]: r[1:] for r in cur.fetchall()}
for i in (988, 990, 604):
    assert rows[i][0] is True, (i, '已不是啟用中，停下來看')
cur.execute("select id from benefits where county='全國' and name=%s", (NAME,))
assert cur.fetchone() is None, '全國那筆已存在'
print('新增 全國｜', NAME); print('停用 988', rows[988][1]); print('停用 990', rows[990][1]); print('保留 604', rows[604][1])
if '--apply' in sys.argv:
    cur.execute("""INSERT INTO benefits (name, agency, county, description, search_group, eligibility_conditions,
                     source_url, source_excerpt, last_verified_date, is_active, amount_min, amount_max, amount_unit, amount_note,
                     deadline_type, application_period, source_tier, validity_status, validity_checked_at, validity_evidence)
                   VALUES (%s,'原住民族委員會（由直轄市、縣市政府受理審查）','全國',%s,'原住民族福利',%s::jsonb,%s,%s,CURRENT_DATE,true,
                     NULL,40000,'one_time','5 年內最高 4 萬元（維修不在此限）','announced','每年 11/1 起至隔年 10/31（年度計畫）',
                     'official','valid_current',now(),%s) RETURNING id""",
                (NAME, DESC, json.dumps(COND, ensure_ascii=False), PDF, EXCERPT,
                 '2026-10-29 讀原民會 115 年度實施計畫掃描 PDF（標題含 115 年度，判準 A）；審核系統 ' + CIP))
    nid = cur.fetchone()[0]
    cur.execute("""update benefits set is_active=false, validity_status='deactivated', deactivated_at=now(),
                   deactivated_reason=%s, updated_at=now() where id in (988,990)""", (REASON + f'（全國 id {nid}）',))
    assert cur.rowcount == 2
    conn.commit(); print('✅ 新增 id', nid, '；停用 988、990')
else:
    print('(dry-run)')
