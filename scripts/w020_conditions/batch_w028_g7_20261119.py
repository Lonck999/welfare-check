"""W-028 第 7 組：新北市 22 筆中的 19 筆（549、577、599 FLAG 不在 X），依官方原文重編資格條件。
   2026-11-19 逐頁讀過 source_url 正文（curl＋瀏覽器 UA，存於 ~/.hermes/cache/welfare_w028_20261119/g7_pages/，
   每頁標題已核對與 DB 名稱一致）。
   · 這 19 筆原本只有 counties＋otherConditions（引擎不檢查的鍵 ⇒ 對任何人 possible）；
     19 筆的 otherConditions 讀原文後**全部是申請方式／地點**（臨櫃、郵寄、向區公所／學校／幼兒園申請），不是資格
     ⇒ 原值逐字搬到 `_otherConditions_orig`（見 ORIG，執行時會比對 DB 一字不差），刪掉 otherConditions，資格另依原文編。
   · X 放的是**整份新的** eligibility_conditions（不是 add）；counties 保留原值並 assert 與 DB 一致。
   原則同 W-020 B：
   · 問卷問得到的 → 引擎條件；問不到的 → uncheckedConditions 原文照列（最高只能 possible）
   · 「符合其一」的 OR 條件 → 一律放 unchecked，不硬編成 AND
   · incomeThreshold 只在原文為「列冊低收／中低收」或「未達最低生活費 1.5 倍」時編
   · 受益人是子女（原住民幼童／學生）時，不把原住民編成 requiredIdentities（問卷身分是填表人本人的，
     非原住民的父或母填表會被刷掉）；子女設籍滿 N 個月也不編 minResidencyMonths（那是學生本人不是申請人）
   用法：set -a; . backend/.env; set +a; python batch_w028_g7_20261119.py [--apply]（預設 dry-run，不寫 DB）"""
import json, os, sys
import psycopg2
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from eligibility_guard import assert_substantive

D = '2026-11-19'
NTPC = ['新北市']
ESVC = '新北市政府申辦e服務「案件說明」頁'
WELF = '新北市政府福利補助自己查「福利項目說明」頁'

X = {
 556: ({"counties": NTPC, "requiresChildUnder": 1, "uncheckedConditions": [
          "設籍新北市之嬰幼兒，出生滿 6 週起接種第 1 劑、間隔 4 週接第 2 劑；年齡大於 24 週則無法接種",
          "嬰幼兒須具備以下接種身分其一：原住民、低收或中低收入戶、罕見疾病、重大傷病、早產兒（懷孕週數小於 37 週或出生體重小於 2,500 公克）、戒斷症候嬰兒、設籍新北寄養家庭、20 歲以下小爸媽之子女、身心障礙者之子女、新北特殊境遇家庭、新北市 13 偏遠地區（瑞芳、深坑、石碇、坪林、三芝、石門、八里、平溪、雙溪、貢寮、金山、萬里、烏來）",
          "自 115 年 7 月 1 日起實施；至本市各區衛生所預約接種，攜兒童手冊、健保卡及身分證明"]},
       "新莊區衛生所最新消息「口服輪狀病毒疫苗二劑型-新北市公費(自115年7月1日起實施)」一、接種資格及檢附資料；二、疫苗接種"),
 563: ({"counties": NTPC, "uncheckedConditions": [
          "飼主為設籍新北市市民，或家犬貓為新北市公立動物之家認養之動物",
          "家犬貓已完成絕育手術且已辦寵物登記；術後 14 日內（含例假日）以郵寄、委託送件或臨櫃申請",
          "依「先申請者先審核」原則，辦理至本年度預算用罄為止（用罄時於動保處網站公告不再受理）"]},
       f"{ESVC}「家犬貓絕育補助」申請說明、應備證件、申請方式、備註"),
 570: ({"counties": NTPC, "uncheckedConditions": [
          "已與新北市政府所屬機關訂定市有基（房）地租約之承租人，承租市有基地並設籍於該地上房屋作自用住宅使用",
          "符合其一：承租人或其配偶符合身心障礙資格（租金 6 折）；或承租人為低收入戶、或領有中低收入老人生活津貼（租金 4 折）"]},
       f"{WELF}「低收入戶、身心障礙或中低收入老人承租市有基地租金優惠」福利說明一、二；補助內容"),
 584: ({"counties": NTPC, "uncheckedConditions": [
          "實際居住偏遠與原住民族地區（依《偏遠與原住民族及離島地區石油設施及運輸費用補助辦法》所定地區；問卷只問到縣市）使用家用桶裝瓦斯之用戶",
          "每年 5 月 1 日至 6 月 30 日檢具身分證至區公所或里辦公處申請並填具申請補助領據；同一戶內成員不得重複申請"]},
       "經濟部能源署便民服務「偏遠與原住民族及離島地區石油設施及運輸費用補助作業」補助對象（二）家用桶裝瓦斯差價補助；申請程序（八）"),
 592: ({"counties": NTPC, "uncheckedConditions": [
          "具勞工身分（非具勞工身分不適用優待辦法），報名新北市勞工大學課程",
          "符合其一：同時修習勞動教育課程（其他課程學分費半價，一門勞動教育課程限優惠一門職能課程）；或夫妻同時報名、新住民、原住民、身心障礙（持手冊）、低收入戶（學分費 8 折，雙重以上身分擇一）",
          "第二項優待須於招生簡章所示申請日期前親送或傳真證明文件並電話通知校本部／分校"]},
       f"{WELF}「勞工大學學分費優待」福利說明 1、2；申請方式"),
 606: ({"counties": NTPC, "requiresChildUnder": 7, "uncheckedConditions": [
          "設籍新北市、屬第 3 胎（含）以上之 0-6 歲幼兒",
          "至張貼「新北市嘉惠生育第3胎，0-6歲掛號費減免」標誌之合作醫療院所就醫，持健保卡、第 3 胎以上兒童證明卡或戶口名簿"]},
       f"{WELF}「第3胎(含)以上之幼兒掛號費減免之優惠措施」福利說明"),
 613: ({"counties": NTPC, "uncheckedConditions": [
          "勞務提供地在新北市轄內之勞工（或會址設於本市之工會）",
          "符合其一：就權利事項勞資爭議申請調解不成立（或成立但雇主未履行）後起訴；向法院起訴經調解不成立續行訴訟；申請交付仲裁；申請裁決；雇主經裁決構成不當勞動行為後以勞工為被告起訴；依勞動事件法第 40 條提起不作為訴訟；爭議行為遭雇主提起民刑事訴訟；其他經審議小組認定之重大勞資爭議",
          "同一事件該審期間曾領政府或受託民間團體同性質補助或法律扶助者不予補助；須經資力審查",
          "應於各程序終結前（調解成立、和解、撤回、判決等）提出，逾期不受理"]},
       f"{ESVC}「勞資爭議事件及涉訟權益補助金(免召開審查會)」申請對象（一）～（八）、申請時限"),
 620: ({"counties": NTPC, "uncheckedConditions": [
          "設籍新北市且符合其一：0-6 歲經社會局核定之低收入戶兒童；0-6 歲中低收入戶或符合中低收入弱勢兒少生活扶助資格；0-12 歲兒童符合罕見疾病或健保重大傷病範圍；65 歲以上經核定之低收入戶老人；55-65 歲經核定之低收入戶原住民",
          "須先申請醫療補助證，至合約醫療院所就醫（補助掛號費、健保部分負擔、住院自付額每日 1,000 元／全年 15,000 元為上限）"]},
       "新北市衛生局醫事管理「新北市醫療補助」※補助對象 第一類～第五類、※補助內容"),
 627: ({"counties": NTPC, "requiresChildUnder": 13, "uncheckedConditions": [
          "子女就讀新北市國民小學且學校有開辦課後照顧服務班",
          "符合其一（優先並免費）：低收入戶、身心障礙、原住民學生；其他經學校評估需扶助之情況特殊學生得減免收費（名額依教育局年度經費核定）"]},
       "新北市法規查詢系統《新北市國民小學辦理課後照顧服務班補充規定》（115-06-22 修正）第十三點"),
 634: ({"counties": NTPC, "ageMin": 50, "ageMinByIdentity": {"原住民": 40}, "requiredIdentities": ["農民", "漁民"],
        "uncheckedConditions": [
          "設籍新北市，本人為本市各農漁會正會員或實際從事農業之農保被保險人",
          "2 年 1 次、依排定時程受檢；接獲農（漁）會通知後向戶籍所在地農漁會報名"]},
       f"{ESVC}「農漁民長者健康檢查」申請說明：設籍本市年滿50歲（原住民為40歲），且為本市各農漁會正會員或實際從事農業之農保被保險人"),
 641: ({"counties": NTPC, "requiresChildUnder": 7, "uncheckedConditions": [
          "幼兒就讀新北市公立幼兒園、非營利幼兒園或職場互助教保中心，學齡滿 2 足歲至入國民小學（含緩讀生）",
          "符合其一：低收入戶；中低收入戶；家戶年所得 30 萬元以下之 5 足歲幼兒（不含擁有第 3 筆以上不動產且公告現值合計超過 650 萬、或年利息所得 10 萬以上者）；經濟情況特殊幼兒（身障含發展遲緩、原住民族、特殊境遇家庭子女等，經專案核備）",
          "依各園開辦延長照顧期程向就讀幼兒園申請"]},
       f"{WELF}「學期期間新北市公立幼兒園…課後延長照顧服務；寒暑假…加托服務」福利說明、應備證件一～四"),
 648: ({"counties": NTPC, "requiresChildUnder": 2, "uncheckedConditions": [
          "兒童設籍新北市且未滿 2 足歲",
          "兒童未經政府公費安置，且未接受公共化或準公共化托育服務"]},
       f"{ESVC}「育有未滿二歲兒童育兒津貼」一、補助對象 1～3"),
 655: ({"counties": NTPC, "incomeThreshold": "mid_low_income", "incomeEstimateSufficient": True,
        "_incomeEstimateNote": f"{D} 中低收入戶認定本身（申請列冊），同 6、8、11、18 號的做法",
        "uncheckedConditions": [
          "設籍並實際居住新北市，且最近一年居住國內超過 183 日",
          "全家人口現金（含存款本金、利息）、有價證券、汽車及投資合計每人每年未超過 15 萬元",
          "全家人口土地公告現值及房屋評定標準價格合計未超過 708 萬元"]},
       f"{ESVC}「申請中低收入戶資格-含改列、增列、減列及申復」一、（二）審查標準 1～3：家庭總收入平均每人每月低於最低生活費1.5倍(115年即2萬6,625元)"),
 662: ({"counties": NTPC, "requiredFlags": ["disability_certificate"], "uncheckedConditions": [
          "設籍新北市之身心障礙者，因需仰賴他人扶助、訓練或完全無法自理生活，且有入住與本市簽約之機構（身障機構、老人機構、護理之家等）或日間照顧之需求",
          "最近一年居住國內超過 183 日",
          "符合補助標準（依障別程度、家庭總收入人均達最低生活費之倍數、特殊條件核算）且未接受政府其他相同性質之服務或補助；每年年底須重新申請次年度複查"]},
       f"{ESVC}「身心障礙者日間照顧及住宿式照顧費用補助」申請說明 1～3、補助基準"),
 669: ({"counties": NTPC, "requiredFlags": ["recent_natural_disaster_damage"], "uncheckedConditions": [
          "因天然災害致死亡、失蹤、重傷、住屋毀損達不堪居住（須災前居住於該屋）、住屋淹水達 50 公分以上或土石流入侵（符合其一）",
          "災害發生後 3 個月內，檢附相關文件向災害發生地區公所申請"]},
       f"{ESVC}「申請天然災害災害救助」一、申請時限；二、補助內容（一）～（六）"),
 676: ({"counties": NTPC, "uncheckedConditions": [
          "家庭所得及財產在內政部國土管理署所定一定標準以下",
          "符合其一：無自有住宅之家庭（先申請、核定後 2 年內購屋貸款），或申請人 2 年內購置住宅並已辦理貸款",
          "受理期間由內政部國土管理署每年訂定（約每年 7 月中旬公告），非受理期間不受理"]},
       f"{ESVC}「自購住宅貸款利息補貼」申請說明（受理期間、適用對象）"),
 683: ({"counties": NTPC, "requiresChildUnder": 13, "uncheckedConditions": [
          "學生為原住民，設籍新北市連續 6 個月以上，且就讀本市公私立國民小學",
          "向就讀學校提出申請（清寒獎學金／優秀獎學金各 3,000 元）"]},
       f"{ESVC}「國小原住民學生獎學金申請撥付」申請說明、補助內容"),
 690: ({"counties": NTPC, "requiresChildUnder": 3, "uncheckedConditions": [
          "幼童為原住民，滿 2 歲未滿 3 歲，就讀新北市公私立幼兒園",
          "由家長向就讀幼兒園申請，幼兒園於每年 3/1～4/20、9/1～10/20 函送原民局複審"]},
       f"{ESVC}「原住民子女學前教育補助」申請對象、補助金額、備註（受理期間）"),
 1003: ({"counties": NTPC, "requiresChildUnder": 16, "uncheckedConditions": [
          "具我國國中學籍之八年級生（自 115 年 7 月 1 日起放寬，不限性別），以校園接種為主",
          "補接種：未於校園接種或尚未完成接種、具我國國中學籍之八年級及九年級生（113 年以前入學者需具本國籍）",
          "特殊公費對象：未具本國籍且不具我國國中學籍者，家長任一方須具本國籍"]},
        "新北市衛生局「人類乳突病毒疫苗補接種」一、公費接種對象（一）常規（二）補接種；三、特殊公費對象"),
}

# 原 otherConditions（全部是申請方式，不是資格）——逐字搬到 _otherConditions_orig；執行時比對 DB 必須一字不差
ORIG = {
 556: "符合資格民眾至本市29區衛生所辦理接種。",
 563: "申請人於家犬貓術後 14 日內(含例假日)，以紙本郵寄、委託送件、臨櫃辦理或到絕育補助管理系統線上申請。",
 570: "民眾申請",
 584: "由申請人至鄉\r\n（鎮、市區）\r\n公所或村（里）辦公處提出申請，並填具申請補助領據",
 592: "第一項福利申請方式：達成指定選課條件，由系統判別並給予學分費優待。\r\n第二項福利申請方式：於招生簡章所示申請日期之前，親送或傳真相關證明文件，並以電話通知五股校本部或三重分校人員辦理，逾期不予受理。",
 606: "「新北市第3胎(含)以上兒童證明卡」的申請方式：\r\n1.符合資格之新生兒，由各區戶政事務所於民眾辦理新生兒出生登記時協助核發。\r\n2.其他符合優惠減免資格之市民，可直接至衛生局或郵寄(傳真)提出申請並檢附相關證明文件，再由衛生局核發(寄)證明卡。",
 613: "臨櫃，郵寄",
 620: "符合資格者需檢附相關證明文件，可郵寄或臨櫃辦理（衛生局地址：新北市板橋區英士路192之1號）。",
 627: "若學校有開班，可向就讀學校提出申請。",
 634: "符合資格者，向戶籍所在地農漁會報名參加。",
 641: "向幼兒就讀之幼兒園提出申請。",
 648: "逕向本市境內各區公所社會(人文)課臨櫃申請、線上申請或於衛生福利部社會及家庭署指定之網站(https://twbaby.sfaa.gov.tw)提出申請",
 655: "向各區公所社會課或社會人文課提出申請。",
 662: "檢附應備文件向本市各區公所社會課提出申請",
 669: "向事發地之區公所提出申請。",
 676: "一、臨櫃送件。\n二、郵寄。\n三、線上申請：內政部國土管理署住宅補貼線上申請作業網站(https://has.nlma.gov.tw/subsidyOnline/)。",
 683: "向就讀學校提出申請",
 690: "由原住民幼童家長向就讀之幼兒園提出申請，幼兒園辦理初審後送件本局申請。",
 1003: "可使用線上或至學校健康中心、衛生所臨櫃辦理申請",
}
# SKIP（FLAG，不在 X）：549（補助對象為公司／商業）、577（受理對象限機關學校社區公司，一般民眾不提供）、
#                     599（與 1003 同一計畫重複，source 為舊版只限女生）—— 見 ~/.hermes/cache/welfare_w028_20261119/g7_report.md
FLAGGED = [549, 577, 599]
assert set(X) == set(ORIG) and not set(X) & set(FLAGGED)

conn = psycopg2.connect(os.environ['DATABASE_URL']); cur = conn.cursor()
cur.execute('select id, eligibility_conditions from benefits where id = any(%s)', (list(X),))
old = dict(cur.fetchall())
assert set(old) == set(X), set(X) - set(old)
new_all = {}
for bid, (cond, src) in X.items():
    ec_old = old[bid] or {}
    assert ec_old.get('counties') == cond['counties'], (bid, ec_old.get('counties'))
    # 舊值只有 counties＋otherConditions，整份換掉不會丟其他鍵
    assert set(ec_old) <= {'counties', 'otherConditions'}, (bid, sorted(ec_old))
    assert ec_old.get('otherConditions') == ORIG[bid], (bid, 'otherConditions 與 ORIG 不一致')
    assert 'otherConditions' not in cond
    ec = dict(cond)
    ec['_otherConditions_orig'] = ORIG[bid]
    ec['_source'] = f'W-028 {D} 依官方原文補條件：{src}'
    assert_substantive(ec, label=f'新北市｜{bid}')
    new_all[bid] = ec
    print(bid, json.dumps({k: v for k, v in ec.items() if not k.startswith('_')}, ensure_ascii=False)[:150])

if '--apply' in sys.argv:
    cur.execute('create table benefits_before_w028_g7_20261119 as select * from benefits where id = any(%s)', (list(X),))
    for bid, ec in new_all.items():
        cur.execute('update benefits set eligibility_conditions = %s, updated_at = now() where id = %s',
                    (json.dumps(ec, ensure_ascii=False), bid))
    conn.commit(); print('✅ 已寫入', len(new_all), '（備份表 benefits_before_w028_g7_20261119）')
else:
    conn.rollback(); print('(dry-run) 通過 assert_substantive', len(new_all), '筆；FLAG', FLAGGED)
