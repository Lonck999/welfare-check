"""C-6b：414 高雄／417 嘉義市／421 彰化的「中低收入老人假牙補助（地方明細）」併了「一般長者」計畫 ⇒ 拆成獨立列。
   （413 臺南 description 只有中低收計畫，沒有併 ⇒ 不拆。）
   原列 → 只留中低收計畫（description／notes 的一般計畫段落移出；uncheckedConditions 的「符合其一 ②」移除，
          改成與 411/415/423 相同的單一計畫寫法）。
   新列 → 各依官方原文：
     高雄：衛生局「老人免費裝假牙」專區頁（一般老人段）
     嘉義市：社會處「115年度『一般身分別老人』補助裝置假牙計畫」公告＋計畫書 PDF
     彰化：社會處 6-1 頁＋「115年彰化縣補助65歲以上老人裝置全口假牙實施計畫」PDF＋「修正補助方式說明」PDF
   🔴 排除條件（彰化一般計畫「列冊低收／中低收…不適用」）引擎沒有欄位 ⇒ 放 uncheckedConditions。
   🔴 固定日期的設籍（高雄 99/11/26 前曾設籍；嘉義 110 年前入籍）不編 minResidencyMonths（eligibility.ts 規範）。
   備份：benefits_before_c6b_split_20261116
   用法：python split_denture_general_20261116.py [--apply]"""
import json, os, sys, psycopg2

KS_URL = 'https://health.kcg.gov.tw/Content_List.aspx?n=10DD8AF6AAB2F133'
CY_URL = 'https://social.chiayi.gov.tw/News_Content.aspx?n=1101&s=782706'
CH_URL = 'https://www.chcg.gov.tw/DTO/social/07other/other01_con.aspx?data_id=15816&topsn=711'
TAG = 'C-6b 2026-11-16 自原列拆出（一般長者計畫獨立成列）'

MIDLOW_ONE_OF = ('符合其一：列冊低收入戶／中低收入戶、領中低收入老人生活津貼、領身心障礙者生活補助費、'
                 '經政府全額補助收容安置、經政府補助身障日間照顧及住宿式照顧費用達 50% 以上')

NEW = [
 dict(county='高雄市', agency='高雄市政府衛生局', url=KS_URL,
  name='高雄市一般老人免費裝假牙（65 歲以上，名額有限額滿為止）',
  desc='高雄市老人免費裝假牙計畫「一般老人」類（不限中低收）：民國 50 年 12 月 31 日（含）前出生之 65 歲以上長輩，'
       '民國 99 年 11 月 26 日（含）前曾設籍原高雄（縣）市且計畫開辦期間仍在籍；113 年度個人綜合所得稅率達 20%（含）以上者排富不予補助；'
       '同一顎每人終身補助一次。持健保卡、身分證正本及印章至篩檢單位篩檢，審查合格取得「裝假牙證明書」後至特約牙醫院所裝假牙，提供 1 年免費保固。'
       '115 年度自 3 月 1 日起受理，已於 3 月 7 日額滿截止。',
  cond={'ageMin': 65, 'uncheckedConditions': [
        '民國 99 年 11 月 26 日（含）前曾設籍原高雄（縣）市，且計畫開辦期間仍在籍本市',
        '113 年度個人綜合所得稅率達 20%（含）以上者排富不予補助',
        '同一顎每人終身補助一次',
        '經篩檢審查合格取得「裝假牙證明書」',
        '每年 3 月 1 日起受理、名額有限額滿為止（115 年度已於 3 月 7 日額滿截止）']},
  amount=dict(amount_max=None, amount_unit=None, amount_note='實物給付（免費裝假牙）；官方頁未載金額上限'),
  period='每年 3 月 1 日起篩檢，名額有限額滿為止（115 年度已於 115/3/7 額滿截止）',
  dl=dict(deadline_type='announced', deadline_date=None), quota=True,
  ex='本年度補助計畫申請於115年3月7日額滿截止。…1. 一般老人 (一)篩檢條件：年齡：民國50年12月31日(含)前出生之65歲以上長輩。'
     '戶籍：民國99年11月26日(含)前曾設籍原高雄(縣)市，且計畫開辦期間仍在籍本市者。排富條件：「113年度個人綜合所得稅率」達20%以上(含)進行排富不予補助。'
     '同一顎每人終身補助一次(需排富)。(二)篩檢期間：115年3月1日起額滿為止(名額有限，額滿即停止篩檢)。(三)篩檢攜帶文件：健保卡、身分證正本及印章。',
  evidence='2026-11-16 讀衛生局專區頁：「本年度補助計畫申請於115年3月7日額滿截止」＋一般老人篩檢條件'),
 dict(county='嘉義市', agency='嘉義市政府社會處', url=CY_URL,
  name='嘉義市一般身分別老人補助裝置假牙（75 歲以上，終身一次）',
  desc='嘉義市 115 年度「一般身分別老人」補助裝置假牙計畫（不限福利身分）：年滿 75 歲（民國 40 年 12 月 31 日（含）前出生）且於民國 110 年前入籍、'
       '設籍本市滿 5 年者，終身可申請一次。實物給付，由合約診所向市府請款：上下顎全口活動假牙最高 44,000 元、單顎全口 22,000 元、'
       '部分活動假牙 17,000～39,000 元。市府於過年後寄發通知單，持通知單、身分證、健保卡至合約牙醫院所篩檢，經牙醫師公會審查通過才可製作。',
  cond={'ageMin': 75, 'minResidencyMonths': 60, 'uncheckedConditions': [
        '民國 40 年 12 月 31 日（含）前出生，且於民國 110 年前入籍本市（東西區互遷視為戶籍異動，需自行舉證已住滿 5 年）',
        '未曾接受過本計畫補助（終身一次）',
        '持社會處通知單至合約牙醫院所篩檢，經牙醫師公會審查通過後才可製作（未收到通知單請洽 05-2254321#153／#120）',
        '診治計畫書須於 115 年 12 月 18 日前送達市府']},
  amount=dict(amount_max=44000, amount_unit='one_time',
              amount_note='實物給付，診所向市府請款；上下顎全口 44,000／單顎全口 22,000／全口併部分 39,000／上下顎部分 33,000／單顎部分 17,000；終身一次'),
  period='115/1/1–115/12/31；診治計畫書最後收件 115/12/18（由診所送件）',
  dl=dict(deadline_type='fixed', deadline_date='2026-12-18'), quota=False,
  ex='凡年滿75歲且設籍嘉義市滿5年以上者，終身可申請一般身分別老人假牙補助一次 本計畫認定之補助對象為民國40年12月31日(含)前出生者，且於民國110年前入籍本市之長者'
     '…計畫書：參、辦理期程 受理診治計畫書最後收件日：115 年 12 月 18 日(五)前送達本府。肆、補助對象 三、未曾接受過本計畫補助者。'
     '捌、補助基準 上下顎全口活動假牙 4 萬 4,000 元…上顎部分活動假牙 1 萬 7,000 元',
  evidence='2026-11-16 讀社會處公告（上版 2026-01-01、下版 2026-12-31）＋115 年度計畫書 PDF'),
 dict(county='彰化縣', agency='彰化縣政府社會處', url=CH_URL,
  name='彰化縣補助65歲以上老人裝置全口活動假牙（一般戶，終身一次）',
  desc='彰化縣補助 65 歲以上老人裝置全口活動假牙（一般戶，非低收／中低收）：年滿 65 歲、設籍本縣滿 3 年且實施期間仍設籍，'
       '經牙醫師評估需裝置全口活動假牙（上、下顎健康牙齒各存 3 顆以內）。上下顎全口補助 4 萬元（民眾自付 4,000 元）、'
       '單上顎或單下顎全口補助 2 萬元（自付 2,000 元），補助款由縣府直撥診所。同一部位終身一次。'
       '每年 3 月 1 日至 9 月 30 日受理（經費用罄提前停止），持身分證及私章向戶籍地公所申請。',
  cond={'ageMin': 65, 'minResidencyMonths': 36, 'uncheckedConditions': [
        '經牙醫師評估需裝置全口活動假牙（上、下顎健康牙齒各存 3 顆（含）以內，或單顎全口）',
        '同一部位每人終身補助一次',
        '不適用本計畫者：列冊低收入戶／中低收入戶、領中低收入老人生活津貼、領身心障礙者生活補助費、經縣府全額補助收容安置、'
        '經縣府補助身障日間照顧及住宿式照顧費用達 50% 以上（這些身分改申請中低收入老人假牙補助）',
        '每年 3 月 1 日至 9 月 30 日受理，經費用罄提前停止收案']},
  amount=dict(amount_max=40000, amount_unit='one_time',
              amount_note='上下顎全口 40,000（民眾自付 4,000）／單上顎或單下顎全口 20,000（自付 2,000）；縣府直撥診所；同一部位終身一次'),
  period='每年 3 月 1 日至 9 月 30 日受理，經費用罄提前停止；持身分證及私章向戶籍地公所申請',
  dl=dict(deadline_type='annual', deadline_date=None), quota=True,
  ex='三、補助對象及資格限制：(一)申請資格：1、年齡：年滿65歲以上老人。2、戶籍：設籍本縣滿三年以上，且實施期間仍設籍本縣者。'
     '(二)同一部位補助，每人終身以一次為限 (三)以下資格者，不適用本計畫：1、列冊低收入戶、中低收入戶。2、領有中低收入老人生活津貼…'
     '五、上、下顎全口活動假牙 4 萬元 民眾自付 4,000 元；單上顎全口活動假牙 2 萬元 2,000 元 十一、申請期程於每年3月1日起至9月30日止…該年度經費用罄則提前停止收案。'
     '十二、本計畫辦理期間，自中華民國115年1月1日起至115年12月31日。',
  evidence='2026-11-16 讀 115 年實施計畫 PDF（十二、辦理期間 115/1/1–115/12/31）＋修正補助方式說明 PDF'),
]

# 原列：只留中低收計畫
OLD = {
 414: dict(
  desc='高雄市：高雄市115年老人免費裝假牙計畫「中低收老人」類　對象：(一)篩檢條件：1.年齡：民國50年12月31日(含)前出生之65歲以上長輩或'
       '民國60年12月31日(含)前出生之55歲以上原住民。2.戶籍：計畫開辦期間仍設籍本市者。3.社福資格：(1)列冊低收入戶、中低收入戶。'
       '(2)領有中低收入老人生活津貼。(3)領有身心障礙者生活補助費。(4)經各級政府全額補助收容安置。(5)經各級政府補助身心障礙者日間照顧及住宿式照顧費用達百分之五十以上。'
       '4.「同一顎已補助者，須滿5年以上」，經牙醫師評估有重新裝置必要，始得重新提出申請。(二)篩檢期間：115年3月1日起額滿為止(名額有限，額滿即停止篩檢)。'
       '（一般老人類已拆為獨立一筆）'),
 417: dict(cut_from='嘉義市：嘉義市「中低收入老人」補助裝置假牙計畫',
  notes_old='申請方式：*如有民眾已滿足上述條件卻仍未收到通知單者',
  notes_new='申請方式：備齊區公所開立之低收／中低收／中低收老人生活津貼／身障生活補助證明書正本（或市府補助收容安置、身障照顧費用達 50% 以上公函影本，或社會處通知單）'
            '及身分證正反面影本，至本市合約牙醫院（診所）篩檢。洽詢：嘉義市政府社會處 05-2254321。（一般身分別老人計畫已拆為獨立一筆）'),
 421: dict(cut_from='彰化縣：彰化縣政府辦理低收入戶及中低收入老人裝置假牙補助',
  notes_old='申請方式：每年自3月1日起至9月30日受理，請持身份證及印章至戶籍所在地公所辦理',
  notes_new='申請方式：請持身分證及私章逕向戶籍所在地公所辦理。（一般戶 65 歲以上全口活動假牙計畫已拆為獨立一筆）'),
}

conn = psycopg2.connect(os.environ['DATABASE_URL']); cur = conn.cursor()
cur.execute('select count(*) from benefits_before_c6b_split_20261116'); assert cur.fetchone()[0] == 3

plans = {}
for bid, o in OLD.items():
    cur.execute('select name, description, notes, eligibility_conditions from benefits where id=%s', (bid,))
    name, desc, notes, ec = cur.fetchone()
    assert name == '中低收入老人假牙補助（地方明細）', (bid, name)
    u = ec['uncheckedConditions']
    assert u[0].startswith('符合其一：①（中低收計畫）') and '②' in u[0], (bid, u[0][:40])
    new_desc = o['desc'] if 'desc' in o else desc[desc.index(o['cut_from']):] + '（一般長者計畫已拆為獨立一筆）'
    if o.get('notes_old'):
        assert o['notes_old'] in notes, bid
        new_notes = notes[:notes.index(o['notes_old'])] + o['notes_new']
    else:
        new_notes = notes
    new_ec = {**ec, 'uncheckedConditions': [MIDLOW_ONE_OF] + u[1:],
              '_source': ec['_source'] + f'｜{TAG}：移除「符合其一 ②（一般長者計畫）」，該計畫改為獨立一筆'}
    plans[bid] = (new_desc, new_notes, new_ec)
    print(f'── 改寫 {bid}：desc {len(desc)}→{len(new_desc)}字；unchecked[0] → {MIDLOW_ONE_OF[:20]}…')
    print('   desc 開頭：', new_desc[:60])
    if new_notes != notes: print('   notes 尾：', new_notes[-70:])

for x in NEW:
    cur.execute("select id from benefits where replace(name,' ','')=replace(%s,' ','')", (x['name'],))
    assert cur.fetchone() is None, x['name']
    print(f'＋ 新增 {x["county"]}｜{x["name"]}｜ageMin {x["cond"]["ageMin"]}｜設籍月 {x["cond"].get("minResidencyMonths")}｜max {x["amount"]["amount_max"]}')

if '--apply' not in sys.argv:
    print('(dry-run)'); sys.exit()

for bid, (d, n, ec) in plans.items():
    cur.execute('''update benefits set description=%s, notes=%s, eligibility_conditions=%s::jsonb, updated_at=now() where id=%s''',
                (d, n, json.dumps(ec, ensure_ascii=False), bid))
new_ids = []
for x in NEW:
    ec = {'counties': [x['county']], **x['cond'], '_source': f'{TAG}：{x["ex"]}（{x["url"]}）'}
    cur.execute("""INSERT INTO benefits (name, agency, county, description, search_group, is_time_sensitive, application_period,
                     eligibility_conditions, source_url, source_excerpt, last_verified_date, is_active, created_at, updated_at,
                     amount_max, amount_unit, amount_note, deadline_type, deadline_date, quota_limited,
                     source_tier, validity_status, validity_checked_at, validity_evidence)
                   VALUES (%s,%s,%s,%s,'現金與生活補助類',false,%s,%s::jsonb,%s,%s,CURRENT_DATE,true,now(),now(),
                           %s,%s,%s,%s,%s,%s,'official','valid_current',now(),%s) RETURNING id""",
                (x['name'], x['agency'], x['county'], x['desc'], x['period'], json.dumps(ec, ensure_ascii=False), x['url'], x['ex'],
                 x['amount']['amount_max'], x['amount']['amount_unit'], x['amount']['amount_note'],
                 x['dl']['deadline_type'], x['dl']['deadline_date'], x['quota'], x['evidence']))
    new_ids.append(cur.fetchone()[0])
conn.commit(); print('✅ 改寫', list(plans), '；新增', new_ids)
