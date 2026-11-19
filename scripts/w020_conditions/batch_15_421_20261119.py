"""C-6b（2026-11-19）：15 雲林認定補條件＋換來源；421 彰化拆出第三個計畫（身障者假牙）。

15 雲林「低收入戶 / 中低收入戶認定」
  - 原 source_url law.yunlin FL047147 是「雲林縣低收入戶調查及生活扶助作業要點」，**民國 100/06/16 已廢止**（標題「廢/停」）
  - 改讀雲林社會處「115年度雲林縣低收入戶暨中低收入戶申請資格與方式介紹」（發布 115-01-01）
  - 條件比照其他 19 筆認定類（彰化 13／嘉義縣 16／南投 14）：incomeThreshold mid_low_income＋incomeEstimateSufficient
  - ⚠️ 雲林頁中低收動產寫「14萬4,400元」，衛福部 115 年標準臺灣省列為「14萬4,000元」—— 照錄兩者，不自己挑

421 彰化「中低收入老人假牙補助（地方明細）」
  - description 還併了「3-6 身心障礙者(中)低收入戶裝置假牙費用補助」（未滿 65 歲身障者）⇒ 拆成新列
  - 🔴 讀 421 自己的 source_url（計畫 PDF did=15818）後更正 11-16 的兩個判斷：
      ① 44,000 不只是身障計畫的數字 —— 老人計畫 PDF 五、「5年內最高補助金額不得逾新臺幣4萬4,000元」⇒ amount_max 留 44,000，
         但 amount_unit yearly → one_time（5 年內累計，不是每年），amount_note 改成 PDF 原文
      ② 「每年3月1日起至9月30日受理」**屬於老人計畫本身**（PDF 十、＋社會處 4-7 頁標題）—— 11-16 誤當成一般計畫的字刪掉了
         ⇒ application_period／deadline_type 補回，notes 補回
  - 新列條件：counties 彰化＋ageMax 64（未滿 65）＋requiredFlags disability_certificate（比照 445/861）＋incomeThreshold mid_low_income
用法：python batch_15_421_20261119.py [--apply]
"""
import json, os, sys, psycopg2

TAG = 'C-6b 2026-11-19'
YL_URL = 'https://social.yunlin.gov.tw/News_Content.aspx?n=737&s=350268'
CH_DIS_URL = 'https://www.chcg.gov.tw/DTO/social/06service/service01_con.aspx?data_id=25546&topsn=2434'
CH_ELD_PDF = 'https://social.chcg.gov.tw/getFile.aspx?did=15818&file=2&file_id=451336&type=2'
DIS_CUT = '　彰化縣：彰化縣(中)低收入身心障礙者裝置假牙補助'

YL_EX = ('115年度雲林縣低收入戶暨中低收入戶申請資格與方式介紹（發布 115-01-01）：(一)低收入戶資格 …每人每月在最低生活費以下（新臺幣1萬5,515元）。'
         '2.家庭動產：每人每年平均未達當年度公告動產限額（115年度為新臺幣9萬6,000元）。3.家庭不動產：…（115年度為新臺幣385萬元）。'
         '(二)中低收入戶資格 1.家庭總收入：…每人每月未達當年度公告最低生活費之1.5倍（115年度為新臺幣2萬3,273元）。'
         '2.家庭動產：…（115年度為新臺幣14萬4,400元）。3.家庭不動產：…（115年度為新臺幣578萬元）。'
         '二、申請方式：…洽戶籍所在地公所或戶籍所在地村（里）辦公處申辦。三、申請流程（完成審查約需1-2個月）')

DIS = dict(
    name='彰化縣身心障礙者(中)低收入戶裝置假牙費用補助（未滿 65 歲）',
    agency='彰化縣政府社會處', county='彰化縣', url=CH_DIS_URL,
    desc=('彰化縣身心障礙者(中)低收入戶裝置假牙費用補助：設籍本縣、列冊低收入戶或中低收入戶、未滿 65 歲且領有身心障礙證明，'
          '經醫師評估缺牙需裝置假牙者。健保給付項目不補助；自費部分依口腔診治補助價目標準表實報實銷，'
          '低收入戶每年最高 44,000 元、中低收入戶每年最高 22,000 元。同一顎已取得相同補助者，固定假牙 5 年內、活動假牙 3 年內不得再申請。'
          '流程：持身障證明影本至公所辦低收／中低收證明並填申請書 → 至口腔篩檢服務單位擬診治計畫書 → 審核通過、縣府發核定函後才可製作。'
          '洽詢：社會處身心障礙福利科 04-7532399。'),
    cond={'counties': ['彰化縣'], 'ageMax': 64, 'requiredFlags': ['disability_certificate'],
          'incomeThreshold': 'mid_low_income',
          'uncheckedConditions': ['經醫師評估缺牙需裝置假牙',
                                  '同一顎已取得相同補助者：固定假牙 5 年內、活動假牙 3 年內不得再次申請',
                                  '須先經審核篩檢單位審核、縣府發核定函後才可製作假牙']},
    amount_max=44000, amount_unit='yearly',
    amount_note='健保給付項目不補助；自費依口腔診治補助價目標準表實報實銷：低收入戶每年最高 44,000／中低收入戶每年最高 22,000',
    period='常態受理（處理期限一個月）；須先申請核准後才能製作假牙',
    ex=('二、補助對象及資格限制： (一) 設籍本縣列冊低收入戶、中低收入戶之未滿六十五歲領有身心障礙證明者，經醫師評估缺牙需裝置假牙者。'
        ' (二)服務對象同一顎已取得相同補助項目者，固定假牙5年內不得再次申請，活動假牙3年內不得再次申請。'
        '四、補助費用標準：(一)健保給付項目不列入補助項目 (二)…1.低收入戶…每年實報實銷申請總金額不得超過新臺幣44,000元 '
        '2.中低收入戶…每年實報實銷申請總金額不得超過新臺幣22,000元'),
    evidence='2026-11-19 讀社會處申辦服務頁「3-6身心障礙者(中)低收入戶裝置假牙費用補助」（承辦：身心障礙福利科）',
)

ELD_PERIOD = '每年 3 月 1 日至 9 月 30 日受理，經費用罄提前停止收案；須先申請核准後才能製作假牙'
ELD_AMOUNT_NOTE = ('計畫 PDF 五：5 年內最高補助金額不得逾 44,000 元（假牙維修不在此限）；上下顎全口 44,000／單顎全口 22,000／'
                   '單顎全口併另一顎部分 39,000／上下顎部分 34,000／單顎部分 17,000；維修每年最高 6,600；固定式每顆 4,400、當年度至多 10 顆')
ELD_NOTES_TAIL = '申請方式：請持身分證及私章逕向戶籍所在地公所辦理。（一般戶 65 歲以上全口活動假牙計畫已拆為獨立一筆）'
ELD_NOTES_NEW = ('申請方式：每年 3 月 1 日至 9 月 30 日受理（經費用罄提前停止），請持身分證及私章逕向戶籍所在地公所辦理。'
                 '（一般戶 65 歲以上全口活動假牙計畫、未滿 65 歲身障者假牙計畫已各拆為獨立一筆）')

conn = psycopg2.connect(os.environ['DATABASE_URL']); cur = conn.cursor()

# ── 15 ──
cur.execute('select name, source_url, eligibility_conditions from benefits where id=15')
n15, u15, ec15 = cur.fetchone()
assert n15 == '低收入戶 / 中低收入戶認定' and 'FL047147' in u15, (n15, u15)
assert set(ec15) == {'counties', 'referenceData'}, ec15
new15 = {**ec15, 'incomeThreshold': 'mid_low_income', 'incomeEstimateSufficient': True,
         '_incomeEstimateNote': f'{TAG} 低收／中低收認定本身（申請列冊），原文：每人每月未達最低生活費之 1.5 倍（115 年度 23,273 元）',
         'uncheckedConditions': ['家庭動產：低收每人每年未達 9 萬 6,000 元／中低收未達 14 萬 4,400 元（雲林頁原文；衛福部 115 年標準臺灣省列為 14 萬 4,000 元）；'
                                 '不動產：低收全家未達 385 萬元／中低收未達 578 萬元'],
         '_source': f'{TAG} 原 source_url（law.yunlin FL047147）為已於民國 100/06/16 廢止之作業要點 ⇒ 改讀雲林社會處 115 年度申請資格頁：{YL_EX}（{YL_URL}）'}
desc15 = ('雲林縣低收入戶／中低收入戶認定（申請列冊）。115 年度：低收入戶每人每月在最低生活費 15,515 元以下、'
          '中低收入戶未達 1.5 倍（23,273 元），並符合動產、不動產限額。備身分證、印章、全戶金融帳戶存簿封面與內頁影本、'
          '授權公所調查同意書等，洽戶籍所在地公所或村（里）辦公處申辦，審查約 1–2 個月。（來源：雲林縣政府社會處）')
print('── 15：source →', YL_URL); print('   新鍵：', sorted(set(new15) - set(ec15)))

# ── 421 ──
cur.execute('select name, description, notes, eligibility_conditions, amount_max, amount_unit, deadline_type from benefits where id=421')
n421, d421, no421, ec421, am, au, dt = cur.fetchone()
assert n421 == '中低收入老人假牙補助（地方明細）'
assert DIS_CUT in d421 and d421.count(DIS_CUT) == 1
assert no421.endswith(ELD_NOTES_TAIL), no421[-80:]
assert (am, au) == (44000, 'yearly'), (am, au)
new_d421 = d421[:d421.index(DIS_CUT)] + '（一般長者計畫、未滿 65 歲身障者計畫已各拆為獨立一筆）'
assert '身心障礙證明者' not in new_d421 and '六十五歲以上' in new_d421
new_no421 = no421[:-len(ELD_NOTES_TAIL)] + ELD_NOTES_NEW
new_ec421 = {**ec421, '_source': ec421['_source'] + f'｜{TAG}：拆出「3-6 身心障礙者(中)低收入戶裝置假牙」為獨立一筆；'
             f'讀本筆計畫 PDF（{CH_ELD_PDF}）更正金額單位為 5 年內累計、補回 3/1–9/30 受理期'}
print('── 421：desc', len(d421), '→', len(new_d421), '字；結尾：', new_d421[-40:])
print('   amount_unit yearly → one_time；deadline_type', dt, '→ annual；period →', ELD_PERIOD)

cur.execute("select id from benefits where replace(name,' ','')=replace(%s,' ','')", (DIS['name'],))
assert cur.fetchone() is None
print('＋ 新增', DIS['name'], '｜', {k: v for k, v in DIS['cond'].items() if k != 'uncheckedConditions'})

if '--apply' not in sys.argv:
    print('(dry-run)'); sys.exit()

cur.execute('create table benefits_before_c6b_15_421_20261119 as select * from benefits where id in (15,421)')
cur.execute('select count(*) from benefits_before_c6b_15_421_20261119'); assert cur.fetchone()[0] == 2
cur.execute('''update benefits set source_url=%s, description=%s, eligibility_conditions=%s::jsonb, source_excerpt=%s,
               last_verified_date=CURRENT_DATE, validity_status='valid_current', validity_checked_at=now(),
               validity_evidence=%s, updated_at=now() where id=15''',
            (YL_URL, desc15, json.dumps(new15, ensure_ascii=False), YL_EX,
             f'{TAG} 讀雲林社會處 115 年度申請資格頁（發布 115-01-01）；原來源要點已於 100/06/16 廢止'))
cur.execute('''update benefits set description=%s, notes=%s, eligibility_conditions=%s::jsonb, amount_unit='one_time',
               amount_note=%s, application_period=%s, deadline_type='annual', updated_at=now() where id=421''',
            (new_d421, new_no421, json.dumps(new_ec421, ensure_ascii=False), ELD_AMOUNT_NOTE, ELD_PERIOD))
ec = {**DIS['cond'], '_source': f'{TAG} 自 421 拆出：{DIS["ex"]}（{DIS["url"]}）'}
cur.execute("""INSERT INTO benefits (name, agency, county, description, search_group, is_time_sensitive, application_period,
                 eligibility_conditions, source_url, source_excerpt, last_verified_date, is_active, created_at, updated_at,
                 amount_max, amount_unit, amount_note, deadline_type, deadline_date, quota_limited,
                 source_tier, validity_status, validity_checked_at, validity_evidence)
               VALUES (%s,%s,%s,%s,'現金與生活補助類',false,%s,%s::jsonb,%s,%s,CURRENT_DATE,true,now(),now(),
                       %s,%s,%s,'always',null,false,'official','valid_unconfirmed',now(),%s) RETURNING id""",
            (DIS['name'], DIS['agency'], DIS['county'], DIS['desc'], DIS['period'], json.dumps(ec, ensure_ascii=False),
             DIS['url'], DIS['ex'], DIS['amount_max'], DIS['amount_unit'], DIS['amount_note'], DIS['evidence']))
nid = cur.fetchone()[0]
conn.commit(); print('✅ 改寫 15／421；新增', nid)
