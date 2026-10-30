"""FLAG 10 筆「電動自行車購車補助（地方加碼）」依原文處理（2026-10-30，Lonck 選 A：有 115 年現行方案就改名編條件，舊年度／停辦就停用）。
   名稱與來源全部不符 —— 10 筆來源都是電動「機車」補助，沒有一筆是電動自行車。
   改寫（3）：該縣市 115 年度現行方案讀得到，且 DB 沒有其他啟用中的同計畫列
     359 新竹縣：「115年度新竹縣機車汰舊及低污染車輛補助辦法」（環保局機車資訊網）
     361 彰化縣：「115 年度彰化縣淘汰高車齡機車及新(換)購電動機車補助計畫」（環保局補助相關條文）
     362 南投縣：「115 年度南投縣淘汰老舊機車或換購、新購電動機車補助計畫」（環保局 PDF）
   停用－同計畫已有啟用中的列（4）：351→958 桃園／352→328 臺中／355→331 基隆／369→345 金門
   停用－停辦或查無 115 年現行方案（3）：
     360 苗栗：原文「在 109 年起即停止補助」（電動二輪車部分）；苗栗 115 年老舊機車淘汰另有 336
     367 花蓮：來源「112年度…名額已額滿」；經濟部電動機車產業網「中央及各縣市補助資訊」花蓮只列 114.01.01–114.12.31
     368 澎湖：來源是 109 年版辦法「補助期間至一百十年十二月三十一日止」；產業網 115 年各縣市清單無澎湖
   用法：python fix_ebike_flags_20261030.py [--apply]"""
import json, sys, psycopg2
HC = 'https://hcepb-rmei.easylife.net.tw/01_news_page.asp?news=20250307154018962'
CH = 'https://moto.chepb.gov.tw/mode02.aspx?boss=20231228161732271'
NT = 'https://www.ntepb.gov.tw/df_ufiles/sub2/1.南投縣115年度淘汰老舊機車或換購、新購電動機車補助計畫.pdf'
MEID = 'https://meid.nat.gov.tw/lev/subsidy/city'
REWRITE = {
 359: dict(county='新竹縣', name='新竹縣 115 年度機車汰舊及新購電動機車補助', agency='新竹縣政府環境保護局', url=HC,
   amin=1000, amax=8000,
   desc='新竹縣環保局 115 年度：淘汰老舊機車 1,000–1,500 元；新購重型電動機車 5,500 元、輕型及小型輕型 2,500 元；同一車主汰舊換購再加碼 2,500 元。115/1/1–12/31 報廢或購車，116/1/5 前申請；各項名額用罄即停止。',
   cond={'ageMin': 18, 'uncheckedConditions': ['新購電動機車車主須於 114/12/31 前設籍新竹縣（每人限 1 輛），新車車籍登記新竹縣、1 年內不得轉讓',
                                               '淘汰之老舊機車為 104/12/31 前出廠之燃油機車、車籍在新竹縣，115/1/1 後完成報廢及回收',
                                               '115/1/1–12/31 期間辦理，116/1/5 前申請；名額用罄即停止']},
   ex='115年度新竹縣機車汰舊及低污染車輛補助辦法 二、本辦法補助對象如下：(一)年滿 18 歲以上之中華民國國民。(年齡以購車發票日期進行認定)…新購電動機車車主戶籍須登記於新竹縣，且須於中華民國 114 年 12 月 31 日(含)以前設籍於本縣。(每人限補助一輛)…四、本辦法補助期間自中華民國 115 年 1 月 1 日起至中華民國 115 年 12 月 31 日止。'),
 361: dict(county='彰化縣', name='彰化縣 115 年度淘汰高車齡機車及新（換）購電動機車補助', agency='彰化縣環境保護局', url=CH,
   amin=1500, amax=12000,
   desc='彰化縣環保局 115 年度：淘汰高車齡機車 1,500 元、淘汰二行程機車 3,000 元、新購電動機車 5,000 元、淘汰高車齡機車並換購電動機車 12,000 元（每輛限申請一項）。115/1/1–12/31 報廢或購車，收件至 116/1/10。',
   cond={'ageMin': 18, 'minResidencyMonths': 12,
         'uncheckedConditions': ['新購電動機車：115 年內購置可掛牌電動機車，新車車籍設彰化縣，車主設籍彰化縣連續 1 年以上；每人限 1 輛',
                                 '淘汰類：高車齡機車（105/12/31 前出廠）車籍與車主設籍彰化縣連續 1 年以上；二行程機車須連續 5 年以上',
                                 '收件至 116/1/10，依申請先後、預算用罄為止']},
   ex='115 年度彰化縣淘汰高車齡機車及新(換)購電動機車補助計畫 附表一：淘汰高車齡機車 1,500；淘汰二行程機車 3,000；新購電動機車 5,000；淘汰高車齡機車並換購電動機車 1 萬 2,000。附表二 新購電動機車：車輛所有人須為年滿 18 歲之自然人…且設籍應設於彰化縣連續 1 年以上。十二、本計畫申請補助收件期間自公告日起至民國116年1月10日止。'),
 362: dict(county='南投縣', name='南投縣 115 年度淘汰老舊機車或換購、新購電動機車補助', agency='南投縣政府環境保護局', url=NT,
   amin=2500, amax=16000,
   desc='南投縣環保局 115 年度（擇一）：淘汰老舊機車並新購電動機車 16,000 元、新購電動機車 5,000 元、純淘汰老舊機車 2,500 元。115/1/1–12/31，依申請順序至預算用罄為止。',
   cond={'ageMin': 18, 'uncheckedConditions': ['新購電動機車車主須於 114/12/31 前設籍南投縣（以購車發票日期認定年滿 18 歲）',
                                               '淘汰之老舊機車為 96/6/30 前出廠之燃油機車、114/12/31 前車籍在南投縣，115 年內報廢並回收',
                                               '依申請順序，預算用罄即停止受理']},
   ex='115 年度南投縣淘汰老舊機車或換購、新購電動機車補助計畫 三、補助項目及金額(擇一申請) 115 年 1 月 1 日至 115 年 12 月 31 日(或預算用罄為止)：(1)淘汰老舊機車並新購電動機車 16,000 元 (2)新購電動機車 5,000 元 (3)純淘汰老舊機車 2,500 元。五、(二)1. 新購電動機車車主：年滿十八歲以上之中華民國國民(以購車發票日期為準)，且於114年12月31日(含)前設籍本縣之縣民。'),
}
DEACT = {
 351: '名稱「電動自行車」與來源不符：來源是「115年度桃園市電動機車補助」，與啟用中的 958 同一方案',
 352: '名稱「電動自行車」與來源不符：來源是臺中市環保局「補助新購電動機車（中低收入戶）切結書」，同計畫由啟用中的 328 涵蓋',
 355: '名稱「電動自行車」與來源不符：來源是 114 年「公益青年電動機車」新聞；基隆 115 年度電動機車補助計畫由啟用中的 331 涵蓋',
 369: '名稱「電動自行車」與來源不符：來源是 108 年申請表；金門 115 年度機車汰舊換新與新購電動二輪車補助由啟用中的 345 涵蓋',
 360: '已停辦：來源（107 年新聞）原文「在 109 年起即停止補助」；苗栗 115 年老舊機車淘汰補助另見 336',
 367: f'查無 115 年現行方案：來源原文「112年度電動機車花東基金補助名額已額滿」；經濟部電動機車產業網中央及各縣市補助資訊花蓮只列 114.01.01–114.12.31（{MEID}）',
 368: f'查無 115 年現行方案：來源是 109 年版辦法「補助期間至中華民國一百十年十二月三十一日止」；經濟部電動機車產業網 115 年各縣市清單無澎湖（{MEID}）',
}
conn = psycopg2.connect(dbname='welfare_check'); cur = conn.cursor()
ids = list(REWRITE) + list(DEACT)
cur.execute('select id, county, is_active, name from benefits where id = any(%s)', (ids,))
rows = {r[0]: r[1:] for r in cur.fetchall()}; assert set(rows) == set(ids)
for i in ids:
    assert rows[i][1] is True and '電動自行車' in rows[i][2], (i, '狀態／名稱已變，停下來看', rows[i])
for i, x in REWRITE.items():
    assert rows[i][0] == x['county']; print('改寫', i, rows[i][2], '→', x['name'])
for i, r in DEACT.items():
    print('停用', i, rows[i][0], '｜', r[:50])
if '--apply' in sys.argv:
    for i, x in REWRITE.items():
        ec = {'counties': [x['county']], **x['cond'], '_source': '2026-10-30 FLAG 依原文改寫（Lonck 選 A）：' + x['ex'] + f'（{x["url"]}）'}
        cur.execute('''update benefits set name=%s, agency=%s, description=%s, source_url=%s, source_excerpt=%s,
                       amount_min=%s, amount_max=%s, amount_unit='one_time', eligibility_conditions=%s,
                       source_tier='official', validity_status='valid_current', validity_checked_at=now(), notes=null,
                       last_verified_date=current_date, updated_at=now() where id=%s''',
                    (x['name'], x['agency'], x['desc'], x['url'], x['ex'], x['amin'], x['amax'],
                     json.dumps(ec, ensure_ascii=False), i))
        assert cur.rowcount == 1
    for i, r in DEACT.items():
        cur.execute("""update benefits set is_active=false, validity_status='deactivated', deactivated_at=now(),
                       deactivated_reason=%s, updated_at=now() where id=%s""", ('2026-10-30 FLAG 讀原文（Lonck 選 A）：' + r, i))
        assert cur.rowcount == 1
    conn.commit(); print('✅ 改寫', len(REWRITE), '停用', len(DEACT))
else:
    print('(dry-run)')
