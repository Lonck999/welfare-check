"""C-6b：413 臺南「中低收入老人假牙補助（地方明細）」併了衛生局「長者免費裝置全口活動假牙計畫」（不限中低收）⇒ 拆成獨立列。
   🔴 這筆第一輪漏拆（split_denture_general_20261116.py 只拆 414/417/421）：我用 description LIKE '%一般%' 判斷，
      而臺南衛生局計畫的名稱是「65 歲以上老人暨 55 歲以上原住民免費裝置全口活動假牙計畫」，沒有「一般」兩字。
      KNOWN-ISSUES 2026-11-13 早就寫了 413 要拆 —— 讀 description 原文才發現。
   原文：臺南市政府衛生局「臺南市 115 年度長者免費裝置全口活動假牙計畫」PDF（114/10/20）＋衛生局公告頁
   備份：benefits_before_c6b_split_20261116（413 已追加）
   用法：python split_denture_general_tainan_20261116.py [--apply]"""
import json, os, sys, psycopg2

PAGE = 'https://health.tainan.gov.tw/page.asp?mainid=910A3D9A-893A-4F32-A1B1-720FDCFDAEF0&srcorcaid=53F30C1D-D30D-44C5-AF4E-A20F0065718D'
PDF = 'https://health.tainan.gov.tw/warehouse/53F30C1D-D30D-44C5-AF4E-A20F0065718D/F_1764574581923e.pdf'
TAG = 'C-6b 2026-11-16 自原列拆出（一般長者計畫獨立成列）'
CUT = '　臺南市：臺南市衛生局 65 歲以上老人暨 55 歲以上原住民免費裝置全口活動假牙計畫'
MIDLOW_ONE_OF = ('符合其一：列冊低收入戶／中低收入戶、領中低收入老人生活津貼、領身心障礙者生活補助費、'
                 '經政府全額補助收容安置、經政府補助身障日間照顧及住宿式照顧費用達 50% 以上')

X = dict(
  name='臺南市長者免費裝置全口活動假牙（65 歲以上、原住民 55 歲以上）',
  agency='臺南市政府衛生局',
  desc='臺南市 115 年度長者免費裝置全口活動假牙計畫（衛生局，不限中低收）：111 年 12 月 25 日以前設籍本市且持續在籍，'
       '民國 50 年 12 月 31 日以前出生（原住民 60 年 12 月 31 日以前出生，需檢附戶籍謄本），經合約牙醫院所評估需裝全口或單顎活動假牙'
       '（健康牙齒含智齒每顎 3 顆以內）。免費裝置，每顎上限 22,000 元、全口雙顎上限 44,000 元，由衛生局撥款至合約院所。'
       '每人每顎僅補助一次；113 年度綜合所得稅稅率 20% 以上者不受理。持健保卡、身分證向合約醫療院所申請，115/1/1–115/12/10 受理（經費用罄提前停止）。',
  cond={'ageMin': 65, 'ageMinByIdentity': {'原住民': 55}, 'uncheckedConditions': [
        '111 年 12 月 25 日以前設籍本市，且持續在籍',
        '民國 50 年 12 月 31 日以前出生；原住民為 60 年 12 月 31 日以前出生（需檢附戶籍謄本影本）',
        '經合約牙醫院所評估需裝全口活動假牙或單顎活動假牙（健康牙齒【含智齒】每顎 3 顆以內）',
        '每人每顎僅補助一次；已受「中低收入戶老人補助假牙」或「原住民族長者裝置假牙」補助者 5 年內不重複補助',
        '113 年度綜合所得稅稅率未滿 20%（綜合所得淨額未滿 1,330,001 元；被扶養者依扶養者申報稅率計算）',
        '115/1/1–115/12/10 向合約醫療院所申請，經費用罄提前停止收案']},
  amount_max=44000, amount_unit='one_time',
  amount_note='免費裝置（實物給付，衛生局撥款至合約院所）；每顎上限 22,000、全口雙顎上限 44,000；每人每顎一次',
  period='115/1/1–115/12/10 向合約醫療院所申請（12/11 以後併入 116 年審核），經費用罄提前停止',
  deadline_type='fixed', deadline_date='2026-12-10', quota=True,
  ex='四、實施對象 (一) 設籍於臺南市（111 年 12 月 25 日以前設籍於本市，且持續在籍者）且於 50 年 12 月 31 日以前出生，並經本市合約牙科醫療院所牙科醫師評估需裝假牙者。'
     '(二)…60 年 12 月 31 日以前出生之原住民（需檢附戶籍謄本影本）… (四) 補助者之限制：1.每人每顎僅補助一次。2.已申請「衛生福利部中低收入戶老人補助假牙實施計畫」或'
     '「臺南市政府 111-115 年度辦理原住民族長者裝置假牙實施計畫」並經補助者，5 年內不予重複補助。3.申請者綜合所得稅稅率未滿 20%者(以 113 年度為綜合所得淨額未滿新臺幣 1,330,001 元者)'
     '…五、(二) 裝置額度為每人每顎上限新臺幣 2 萬 2,000 元，全口雙顎上限為新臺幣 4 萬 4,000 元 六、實施期程：115 年 1 月 1 日起至 115 年 12 月 31 日。'
     '…2. 申請期程：(1) 自 115 年 1 月 1 日至 115 年 12 月 10 日接受民眾至合約醫療院所申請…但如因經費用罄則將提前停止收案。',
  evidence='2026-11-16 讀衛生局「臺南市 115 年度長者免費裝置全口活動假牙計畫」PDF（六、實施期程 115/1/1–115/12/31）')

conn = psycopg2.connect(os.environ['DATABASE_URL']); cur = conn.cursor()
cur.execute('select count(*) from benefits_before_c6b_split_20261116 where id=413'); assert cur.fetchone()[0] == 1
cur.execute('select name, description, eligibility_conditions from benefits where id=413'); name, desc, ec = cur.fetchone()
assert name == '中低收入老人假牙補助（地方明細）'
assert desc.count(CUT) == 1, '找不到臺南衛生局段落'
u = ec['uncheckedConditions']; assert u[0].startswith('符合其一：①（中低收計畫）') and '②' in u[0]
new_desc = desc[:desc.index(CUT)] + '（衛生局長者免費裝置全口活動假牙計畫已拆為獨立一筆）'
new_ec = {**ec, 'uncheckedConditions': [MIDLOW_ONE_OF] + u[1:],
          '_source': ec['_source'] + f'｜{TAG}：移除「符合其一 ②（衛生局一般長者計畫）」，該計畫改為獨立一筆'}
cur.execute("select id from benefits where replace(name,' ','')=replace(%s,' ','')", (X['name'],)); assert cur.fetchone() is None
print(f'── 改寫 413：desc {len(desc)}→{len(new_desc)}字；尾：{new_desc[-60:]}')
print(f'＋ 新增 臺南市｜{X["name"]}｜ageMin 65（原住民 55）｜max 44000｜截止 2026-12-10')
if '--apply' not in sys.argv:
    print('(dry-run)'); sys.exit()
cur.execute('update benefits set description=%s, eligibility_conditions=%s::jsonb, updated_at=now() where id=413',
            (new_desc, json.dumps(new_ec, ensure_ascii=False)))
ec_new = {'counties': ['臺南市'], **X['cond'], '_source': f'{TAG}：{X["ex"]}（{PDF}）'}
cur.execute("""INSERT INTO benefits (name, agency, county, description, search_group, is_time_sensitive, application_period,
                 eligibility_conditions, source_url, source_excerpt, last_verified_date, is_active, created_at, updated_at,
                 amount_max, amount_unit, amount_note, deadline_type, deadline_date, quota_limited,
                 source_tier, validity_status, validity_checked_at, validity_evidence)
               VALUES (%s,%s,'臺南市',%s,'現金與生活補助類',false,%s,%s::jsonb,%s,%s,CURRENT_DATE,true,now(),now(),
                       %s,%s,%s,%s,%s,%s,'official','valid_current',now(),%s) RETURNING id""",
            (X['name'], X['agency'], X['desc'], X['period'], json.dumps(ec_new, ensure_ascii=False), PAGE, X['ex'],
             X['amount_max'], X['amount_unit'], X['amount_note'], X['deadline_type'], X['deadline_date'], X['quota'], X['evidence']))
nid = cur.fetchone()[0]; conn.commit(); print('✅ 改寫 413；新增', nid)
