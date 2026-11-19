"""W-028 FLAG 中「有前例可循」的 6 筆（2026-11-19，Lonck「照建議做／被打斷的繼續做」）。
  停用（比照前例）：
    678 新北失業勞工子女生活扶助：新北法規網 msgid=7471「115年9月14日…廢止…並自115年10月1日生效」（比照 842／747 條例落日／要點廢止）
    599 新北國中八年級子宮頸癌疫苗：與 1003 同一計畫，599 是舊版（只寫女生），1003 是 115/7/1 放寬後現行版（比照 296↔675 重複停用）
  改寫（比照 10-30 fix_ebike_flags：名稱是占位、原文是電動機車、DB 無同計畫啟用列 ⇒ 改寫）：
    350 臺北：原名「電動自行車購車補助（地方加碼）」→ 臺北市 113–115 年電動機車補助（環保局補助專區頁＋計畫 115/6/1 修正公告 PDF）
       臺北另一筆 325 已停用 ⇒ 不重複
  換來源＋編條件（原 source_url 指到別的東西，原文是對的那頁）：
    754 南投急難救助：原網址是原民處「原住民族急難救助申請表」；DB 內容其實來自南投開放資料 CSV（與 755／758 同一檔，11-19 重抓 7,134 bytes 與快取相同）
    757 南投中低收傷病醫療補助：原網址正文由 AJAX 載入、504 讀不到；同一份 CSV 有完整列 ⇒ 換來源
       ⚠️ 不編 catastrophic_illness：原文是「嚴重傷、病」不是「重大傷病卡」，編了會把列冊低收的一般傷病患者刷掉
    777 嘉義市急難紓困：原網址是《嘉義市辦理急難救助實施要點》（＝773 的來源）；換成嘉義市政府「強化社會安全網－急難紓困實施方案」頁
       🔴 舊 amount_note「新臺幣六千元…」是 773 那份要點的數字 ⇒ 清空，官方頁未列金額
用法：python fix_w028_flags_precedent_20261119.py [--apply]
"""
import json, os, sys, psycopg2
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from eligibility_guard import assert_substantive

T = '2026-11-19 W-028 FLAG'
NT_CSV = 'https://data.nantou.gov.tw/dataset/ad7db6e6-5483-4fd9-80d6-4db1d21ba696/resource/6a8a9e0a-4942-4fa6-a87a-f0c1945a05d0/download/20250523115545.csv'
TP_URL = 'https://www.dep.gov.taipei/News_Content.aspx?n=CE8746C01243996C&s=9B373391D9A680F0&sms=18E59B21BD8494A1'
CY_URL = 'https://www.chiayi.gov.tw/News_Content.aspx?n=455&s=828064'

DEACT = {
 678: f'{T} 再讀原文：已廢止 —— 新北法規網 msgid=7471「115年9月14日新北府勞組字第1151736255號令：廢止「新北市政府失業勞工子女生活扶助補助要點」，並自115年10月1日生效」（勞動部「失業勞工在學子女生活扶助金」是另一項）',
 599: f'{T} 再讀原文：與 1003 重複 —— 同一個新北國中八年級 HPV 疫苗計畫；599 來源為舊版（只寫女生），衛生局現行頁「自115年7月1日起，放寬資格為具我國國中學籍之八年級生」已由 1003 收錄',
}

EDIT = {
 350: dict(
   name='臺北市電動機車補助（113–115 年，新購／汰購）', agency='臺北市政府環境保護局', url=TP_URL,
   desc=('臺北市政府 113 年至 115 年電動機車補助計畫（115/6/1 修正公告）：年滿 18 歲、設籍臺北市滿 1 年（外籍人士居留或登記地址滿 1 年；'
         '新住民居留臺北滿 1 年且配偶設籍滿 1 年），新購或淘汰老舊機車並換購電動機車可申請；中低／低收入戶另有加碼，'
         '115 年另有電池資費加碼、育有設籍臺北 12 歲以下幼童的「袋鼠方案」加碼。每人限補助 1 輛。'
         '補助期間 113/1/1–115/12/31，至環保局線上申辦系統申請。金額見計畫附件二。'),
   cond={'counties': ['臺北市'], 'ageMin': 18, 'minResidencyMonths': 12,
         'uncheckedConditions': ['新購或汰購電動機車（汰購：淘汰之老舊機車車籍登記於臺北市）；每人限補助 1 輛，每輛新、舊車限申請 1 次',
                                 '外籍人士：持居留證且居留或登記地址於臺北市滿 1 年；新住民：居留臺北滿 1 年且配偶設籍滿 1 年',
                                 '已依「110 至 112 年電動機車補助計畫」獲新購或汰購補助者不予補助',
                                 '袋鼠方案加碼：115 年購車且育有設籍臺北市 12 歲以下（103/1/1 後出生）幼童',
                                 '補助期間 113/1/1–115/12/31；本局得視預算停止辦理']},
   period='113/1/1–115/12/31，至環保局線上申辦系統申請；得視預算停止', dl='fixed', ddate='2026-12-31',
   amount_note='金額見計畫附件二（官方頁「補助項目及金額：如附件」）',
   ex=('臺北市政府113年至115年電動機車補助計畫（115年6月1日府環空字第1153068659號修正公告）三、本計畫補助對象如下：'
       '(一)年滿18歲以上之中華民國國民，設籍於本市滿1年，或持有中華民國居留證之外籍人士居留或登記地址於本市滿1年。…'
       '(四)領有本市區公所核發中低或低收入戶證明文件之中低及低收入戶…(七)袋鼠方案加碼補助…同時育有設籍於本市之12歲以下…幼童者。'
       '｜補助專區頁：4.補助期間：113年1月1日起至115年12月31日止。5.每人限補助1輛'),
 ),
 754: dict(
   url=NT_CSV,
   desc=('南投縣急難救助：設籍南投縣，遭逢急難致生活困難，家庭總收入未超過當年度最低生活費 2.0 倍、家戶動產平均未超過 2.5 倍者，'
         '於急難事由發生兩個月內向戶籍地鄉（鎮、市）公所社會課或民政課申請。應備：申請書、診斷證明或醫療收據或死亡證明等、'
         '全戶戶籍謄本及財產所得資料。洽詢：社會及勞動局社會救助科 (049)2244155。（來源：南投縣開放資料）'),
   cond={'counties': ['南投縣'], 'requiredFlags': ['acute_hardship'],
         'uncheckedConditions': ['設籍南投縣，遭逢急難致生活困難',
                                 '家庭總收入未超過當年度最低生活費 2.0 倍；家戶動產平均分配全家人口未超過 2.5 倍',
                                 '急難事由發生兩個月內提出申請']},
   ex=('南投縣開放資料「社會救助各項補助」CSV：急難救助｜設籍條件：設籍於南投縣｜收入條件每人每月上限：家庭總收入未超過當年度社會救助調查辦法最低生活費之2.0倍｜'
       '動產條件每人上限：依當年度社會救助調查辦法家戶內動產分配全家人口未超過2.5倍｜其他條件：急難救助之申請應於急難事由發生兩個月內提出申請。'),
 ),
 757: dict(
   url=NT_CSV,
   desc=('南投縣低收入戶及中低收入戶傷病醫療補助：設籍南投縣，(1) 列冊低收入戶有自付醫療費；(2) 列冊中低收入戶患嚴重傷病、近三個月醫療費累計達 3 萬元以上；'
         '(3) 一般戶家庭總收入人均未達最低生活費 1.5 倍、近三個月醫療費累計達 5 萬元以上。限健保部分負擔或健保未給付之醫療費用'
         '（不含義肢、義齒、配鏡、看護費、指定病房費等）。出院或就醫後三個月內向戶籍地公所社會課或民政課申請。'
         '洽詢：社會及勞動局社會救助科 (049)2244155。（來源：南投縣開放資料）'),
   cond={'counties': ['南投縣'],
         'uncheckedConditions': ['符合其一：列冊低收入戶之傷、病患者（有自付醫療費）；列冊中低收入戶患嚴重傷病、最近三個月醫療費累計達 3 萬元以上；'
                                 '一般戶家庭總收入人均未達最低生活費 1.5 倍、最近三個月醫療費累計達 5 萬元以上',
                                 '動產、不動產未超過當年度標準 1.5 倍',
                                 '限健保部分負擔或健保未給付之醫療費用（不含義肢、義眼、義齒、配鏡、看護費、指定病房費等）',
                                 '自出院或就醫後三個月內檢齊資料申請']},
   ex=('南投縣開放資料 CSV：中低收入戶傷病醫療補助｜身分：1.本縣列冊低收入戶之傷、病患者。2.列冊中低收入戶患嚴重傷、病…3.一般戶患嚴重傷、病…｜'
       '收入條件：家庭總收入未超過當年度社會救助調查辦法最低生活費之1.5倍｜其他條件：…最近三個月內所生之醫療費用需累計達新台幣3萬元以上者。'
       '3.一般戶…最近三個月所生之醫療費用需累計達新台幣5萬元以上者。4.自出院或就醫後三個月內檢齊資料申請。'),
 ),
 777: dict(
   url=CY_URL,
   desc=('嘉義市「強化社會安全網－急難紓困實施方案」：針對因一時急難事故致經濟陷困之個人及家庭，依急難事由及陷困情形提供一次性或分月分次發放關懷救助金，'
         '並轉介其他福利服務。受理窗口：里辦公處、區公所、市政府。'),
   cond={'counties': ['嘉義市'], 'requiredFlags': ['acute_hardship'],
         'uncheckedConditions': ['符合其一：家庭成員死亡、失蹤或罹患重傷病、失業或其他原因無法工作致家庭生活陷於困境；因經濟性因素致自殺通報；'
                                 '因經濟性因素經通報為脆弱家庭成員；遭家暴、性侵害經通報或庇護安置、緊急生活扶助金尚未核發期間生活陷困；'
                                 '被通報家暴、核發保護令或結束監護處分後因經濟因素暫無居所；申請福利項目尚未核准期間生活陷困；其他變故致家庭生活陷於困境',
                                 '向里辦公處、區公所或市政府申請']},
   amount_note_clear=True,
   ex=('嘉義市政府「強化社會安全網－急難紓困實施方案」（2024-07-06 西區公所）一、實施內容：針對因一時急難事故致經濟陷困之個人及家庭，'
       '依急難事由及陷困情形提供一次性關懷救助金、或分月分次發放關懷救助金…二、救助對象：1.因家庭成員死亡、失蹤或罹患重傷病…7.其他因遭逢變故…三、受理窗口：里辦公處、公所、直轄市、縣（市）政府'),
 ),
}

conn = psycopg2.connect(os.environ['DATABASE_URL']); cur = conn.cursor()
ids = list(DEACT) + list(EDIT)
cur.execute('select id, is_active, eligibility_conditions from benefits where id = any(%s)', (ids,))
cur_rows = {i: (a, e) for i, a, e in cur.fetchall()}
assert set(cur_rows) == set(ids) and all(a for a, _ in cur_rows.values()), cur_rows.keys()
new_ec = {}
for i, x in EDIT.items():
    old = cur_rows[i][1]
    assert old.get('counties') == x['cond']['counties'], (i, old.get('counties'))
    ec = {**x['cond'], '_source': f'{T} 依官方原文重編條件：{x["ex"]}（{x["url"]}）'}
    if 'otherConditions' in old: ec['_otherConditions_orig'] = old['otherConditions']
    assert_substantive(ec, label=str(i)); new_ec[i] = ec
    print(f'改寫 {i}：鍵 {sorted(k for k in ec if not k.startswith("_"))}')
print('停用', sorted(DEACT))
if '--apply' not in sys.argv:
    print('(dry-run)'); sys.exit()

cur.execute('create table benefits_before_w028_flagsfix_20261119 as select * from benefits where id = any(%s)', (ids,))
for i, r in DEACT.items():
    cur.execute("update benefits set is_active=false, deactivated_at=now(), deactivated_reason=%s, validity_status='deactivated', updated_at=now() where id=%s", (r, i))
for i, x in EDIT.items():
    cur.execute('''update benefits set source_url=%s, description=%s, eligibility_conditions=%s::jsonb, source_excerpt=%s,
                   last_verified_date=CURRENT_DATE, validity_checked_at=now(), validity_evidence=%s, updated_at=now() where id=%s''',
                (x['url'], x['desc'], json.dumps(new_ec[i], ensure_ascii=False), x['ex'], f'{T} 讀原文換來源／重編條件', i))
    if 'name' in x:
        cur.execute('''update benefits set name=%s, agency=%s, application_period=%s, deadline_type=%s, deadline_date=%s,
                       amount_note=%s, validity_status='valid_current' where id=%s''',
                    (x['name'], x['agency'], x['period'], x['dl'], x['ddate'], x['amount_note'], i))
    if x.get('amount_note_clear'):
        cur.execute("update benefits set amount_max=null, amount_min=null, amount_unit=null, amount_note='官方頁未列金額（依急難事由及陷困情形核發關懷救助金）' where id=%s", (i,))
conn.commit(); print('✅ 停用', sorted(DEACT), '；改寫', sorted(EDIT))
