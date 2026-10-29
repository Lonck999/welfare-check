"""B 批 3（金門／連江）判讀順帶的 2 筆占位列，依官方原文改寫（2026-10-29）。
   345 金門電動機車地方加碼：10-13 C-6 判「5 個候選頁都不是」而停用 —— 環保局 115 年度要點就在（判讀 00），重新啟用並改寫。
   196 連江身障補助（地方加碼）：描述是「本次搜尋未查得」占位 —— 其 source_url（GL000413）就是身障生活津貼要點，113/1/4 修訂版（判讀 09）。
   兩筆都是「改寫既有列」不是新增 ⇒ 不走 change_log 核准；新增的 11 傳統建築另待 Lonck 判。
   用法：python fix_345_196_20261029.py [--apply]"""
import json, sys, psycopg2
KM = 'https://kepb.kinmen.gov.tw/cp.aspx?n=D39D1B9DF3A45294'
MT = 'https://www.matsu.gov.tw/chhtml/adddownloadcount/371040200A/93462?mcfilename=Mcfile&type=D'
X = {
 345: dict(active_before=False,
   name='金門縣 115 年度機車汰舊換新與新購電動二輪車補助',
   description='金門縣環保局 115 年度：淘汰老舊機車 1,000 元；淘汰老舊機車換購電動機車（重型／輕型）20,000 元；新購電動機車 重型 10,000 元／輕型 10,000 元；新購微型電動二輪車或電動輔助自行車 2,000 元。115/1/1–11/30 完成報廢或購車，115/12/15 前向環保局申請，經費用罄即停止。',
   validity='valid_current',  # 原文標「115年度」⇒ 判準 A
   excerpt='金門縣115年度機車汰舊換新與新購電動二輪車補助要點 附表一：淘汰老舊機車 1,000 元；淘汰老舊機車換購電動機車 重型／輕型 20,000 元；新購電動機車 10,000 元；微型電動二輪車、電動輔助自行車 2,000 元。年滿 18 歲設籍本縣之縣民或持有居留證並設籍於本縣達 1 年以上之外籍人士。申請補助者應於115年12月15日前向本縣環保局提出申請。',
   source_url=KM, amount_min=1000, amount_max=20000, amount_unit='one_time',
   cond={'counties': ['金門縣'], 'ageMin': 18,
         'uncheckedConditions': ['年滿 18 歲設籍金門縣之縣民，或持居留證並設籍金門縣達 1 年以上之外籍人士；每人以 1 輛為限',
                                 '歷年未受環境部與金門縣環保局電動二輪車補助',
                                 '淘汰類：老舊機車須於 113/12/31 前車籍已設於金門縣',
                                 '115/1/1–11/30 完成報廢／購車，115/12/15 前申請；經費用罄即停止']},
   src=f'金門縣環保局「金門縣115年度機車汰舊換新與新購電動二輪車補助要點」附表一：年滿 18 歲設籍本縣之縣民…；淘汰老舊機車 1,000 元、換購電動機車 20,000 元、新購電動機車 10,000 元、微型電動二輪車／電動輔助自行車 2,000 元；115年12月15日前申請（{KM}）'),
 196: dict(active_before=True,
   name='連江縣身心障礙者生活津貼',
   description='連江縣設籍滿一年、每年實際居住 183 日以上且領有身心障礙證明（手冊）者：輕／中／重度每月 3,500 元，極重度每月 4,000 元；向戶籍地鄉公所申請，審核合格當月起發給。現職軍公教、已領中低收身障生活補助／老農津貼／國保身障基本保證年金等其他生活津貼者、領月退者不得重複請領。',
   validity='valid_unconfirmed',  # 現行版 113/1/4 修訂，原文無 115 年度字樣 ⇒ 判準 B
   excerpt='連江縣政府發放身心障礙者生活津貼實施要點（113年1月4日修訂）一、補助對象：凡設籍本縣滿一年，且每年實際居住合計一百八十三日（含）以上，並依法領有身心障礙證明(或手冊)者為限。核定：每月發給身心障礙者生活津貼 3,500 元／4,000 元。',
   source_url=MT, amount_min=3500, amount_max=4000, amount_unit='monthly',
   cond={'counties': ['連江縣'], 'requiredFlags': ['disability_certificate'], 'minResidencyMonths': 12,
         'uncheckedConditions': ['每年實際居住連江縣合計 183 日（含）以上（村幹事查訪、村長開立證明）',
                                 '未具現職軍公教身分，未領取中低收入身障生活補助、老農津貼、國保身障基本保證年金等其他生活津貼，未領月退休金（一次退休金另有累計扣抵規定）']},
   src=f'連江縣政府發放身心障礙者生活津貼實施要點（113/1/4 修訂）一：凡設籍本縣滿一年，且每年實際居住合計一百八十三日（含）以上，並依法領有身心障礙證明(或手冊)者；核定欄：每月發給 3,500 元／4,000 元（{MT}）'),
}
conn = psycopg2.connect(dbname='welfare_check'); cur = conn.cursor()
cur.execute('select id, is_active, name from benefits where id = any(%s)', (list(X),))
rows = {r[0]: r[1:] for r in cur.fetchall()}; assert set(rows) == set(X)
for bid, x in sorted(X.items()):
    act, name = rows[bid]; assert act == x['active_before'], (bid, '狀態已變，停下來看', act)
    ec = dict(x['cond']); ec['_source'] = 'B批3 2026-10-29 依原文改寫占位列：' + x['src']
    print(bid, act, name, '→', x['name'], {k: v for k, v in ec.items() if not k.startswith('_') and k != 'uncheckedConditions'})
    if '--apply' in sys.argv:
        cur.execute('''update benefits set name=%s, description=%s, source_url=%s, amount_min=%s, amount_max=%s, amount_unit=%s,
                       eligibility_conditions=%s, source_tier='official', is_active=true, deactivated_at=null, deactivated_reason=null,
                       validity_status=%s, validity_checked_at=now(), source_excerpt=%s,
                       notes=null,  -- 舊 notes 是「本次搜尋未查得…」占位，原文已找到
                       last_verified_date=current_date, updated_at=now() where id=%s''',
                    (x['name'], x['description'], x['source_url'], x['amount_min'], x['amount_max'], x['amount_unit'],
                     json.dumps(ec, ensure_ascii=False), x['validity'], x['excerpt'], bid))
if '--apply' in sys.argv:
    conn.commit(); print('✅ 已寫入', len(X))
else:
    print('(dry-run)', len(X))
