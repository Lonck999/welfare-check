"""W-028 第 3 組：新北市 22 筆「只有引擎不檢查的鍵」的福利，依官方原文重編 eligibility_conditions。
   2026-11-19 逐頁讀過正文（curl 瀏覽器 UA；另用 web_extract／render_page.py 補讀）：
   · 559 source_url（原民局 information.php?p_id=171）正文只有一句「本府獎勵取得原住民族語言能力證明書」
     ⇒ 條件改讀新北市「福利補助自己查」同名頁 welfare.ntpc.gov.tw/viewService/show/268437186
   · 587 source_url 是三芝區公所「114年度」公告 ⇒ 另讀福利補助自己查 show/268435774（115年1月至12月實施）
   · 637 source_url 是稅捐處「低收入戶房屋稅免徵申報書」參考範例 PDF（pypdf）
   · 686 source_url 法規頁正文由 JS 載入，curl／render_page／web_extract 都只拿到法規名稱與修正日
     ⇒ 讀福利補助自己查 show/7009 ＋《新北市政府績優體育獎學金發給要點》第三點全文（學校轉載 PDF）
   · 955 另查 motor.ntpc.gov.tw：2026-11-19 各類仍有剩餘名額（雙汰舊剩 208）
   原則（Lonck 定案，同 W-020 B）：
   · 問卷問得到的 → 引擎條件；問不到的 → uncheckedConditions 原文照列（最高 possible）
   · 「符合其一」的 OR → 一律 unchecked，不硬編成 AND
   · incomeThreshold 只在原文為「列冊低收／中低收」時編（中低收入老人津貼資格不編）
   · otherConditions 本組全是申請方式／地點／文件，不是資格 ⇒ 原值搬到 _otherConditions_orig、刪 otherConditions
   · X 放「整份新的」eligibility_conditions（counties 保留原值）；FLAG（609）不在 X
   用法：set -a; . backend/.env; set +a; python batch_w028_g3_20261119.py [--apply]（預設 dry-run，不寫 DB）"""
import json, os, sys
import psycopg2

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from eligibility_guard import assert_substantive  # noqa: E402

D = '2026-11-19'
NTPC = ['新北市']
ABO = ['原住民']
WEL = '新北市「福利補助自己查」'
EGOV = '新北市「申辦e服務」案件說明頁'
BACKUP = 'benefits_before_w028_g3_20261119'

X = {
 545: ({"counties": NTPC, "ageMin": 15, "requiredIdentities": ABO, "requiredFlags": ["has_labor_insurance"],
        "uncheckedConditions": [
          "由依法為勞工保險或就業保險之投保單位加保之受僱勞工（排除職業工會及職業訓練單位加保）；工作地在新北市",
          "115/1/1 起始受僱、一般職場僱傭關係，申請時在職且於同一投保單位 3 個月以上（原由營造業僱用之原住民失業勞工為 1 個月；114/10/10 起受僱者亦適用，自 115 年 1 月起計）",
          "不予發給：薪資由政府預算編列；同一時期已領政府其他就業促進補助；受僱者為雇主／負責人之配偶、直系血親或三親等內旁系血親；由不同投保單位再受僱且離職未逾 90 日、或同一投保單位再受僱且離職未逾 1 年"]},
       f"{WEL}「115年度促進原住民族就業獎勵計畫」補助內容一、申請資格（一）～（三）、二、不予發給情形（一）～（五）"),
 552: ({"counties": NTPC, "ageMin": 30, "requiredFlags": ["has_labor_insurance"],
        "uncheckedConditions": [
          "設籍或居留（新住民）新北市達 1 年以上（以收件日為準）",
          "參加新北市勞工局自辦或委辦職前訓練之失業或待業勞工",
          "結訓後 90 日內加入勞保或就保（不含訓字號、裁減續保、職災續保、職業工會、農會及漁會）且投保薪資第 4 級以上，受同一投保單位連續僱用從事與參訓職類相關之工作滿 3 個月，申請時仍在職",
          "符合中央青年就業獎勵、鼓勵失業勞工受僱照顧服務業／特定行業／營造業等就業獎勵者排除",
          "取得資格後 3 個月內申請，逾期不受理"]},
       f"{EGOV}「職前訓練穩定就業獎勵金申請」申請對象、備註一、二"),
 559: ({"counties": NTPC, "minResidencyMonths": 4, "requiredIdentities": ABO,
        "uncheckedConditions": [
          "依原住民族語言能力認證辦法取得族語能力證明書（中高級／高級／優級）；相同語言別及等級以申請一次為限",
          "原民會寄發當年度族語能力證明書之日起 2 個月內申請"]},
       f"{WEL}「原住民族語言能力獎勵」（show/268437186）福利說明、申請方式；source_url 原民局頁正文僅「本府獎勵取得原住民族語言能力證明書」"),
 566: ({"counties": NTPC, "requiresChildUnder": 7,
        "uncheckedConditions": [
          "我國籍幼兒：育兒津貼為生理年齡滿 2 歲至當學年度 9/1 前學齡未滿 5 歲；就學補助為學齡滿 5 歲至入國民小學前",
          "排除：滿 2 歲當月已領衛福部 0～2 歲育兒津貼或托育公共／準公共補助（改依衛福部資訊直接審定）；2～5 歲經政府公費安置；就讀公立／非營利／準公共幼兒園、互助教保服務中心等（含寒暑假）",
          "由幼兒父母雙方或監護人申請，向幼兒現戶籍所在地區公所或教育部指定網站申請"]},
       f"{EGOV}「2歲以上未滿5歲幼兒育兒津貼及5歲至入國民小學前幼兒就學補助」申請說明一、二、三；requiresChildUnder 7 涵蓋入國小前（可能已滿 6 歲）"),
 573: ({"counties": NTPC, "minResidencyMonths": 6, "requiredIdentities": ABO,
        "uncheckedConditions": [
          "年滿 15 歲以上或國民中學畢業（符合其一）",
          "報名政府核准立案補習班之就業考試補習課程，或公立職訓機關、許可設立之職訓機構、大專院校／高中職（不含學分班）、立案人才培訓人民團體、短期補習班、人才培訓公司法人舉辦之職業訓練（養成／轉業訓練）",
          "課程結束日起 2 個月內申請（課程短於 2 週者 2 週內）；每人每 2 年一次、最多 2 次，相同性質課程不得重複"]},
       "新北市原民局「本府補助原住民職業訓練及就業考試補習課程費用」二、適用對象（設籍本市繼續六個月以上）、三、補助範圍、四、補助標準、六、申請方式"),
 580: ({"counties": NTPC, "requiredFlags": ["unemployed"],
        "uncheckedConditions": [
          "符合其一：失業高齡者；或失業之中高齡者／就業保險被保險人，且失業期間連續達 3 個月以上或為非自願離職",
          "就業地點與原日常居住處所距離 30 公里以上（跨域就業）",
          "向公立就業服務機構辦理求職登記、經就業諮詢推介跨域就業，連續受僱同一雇主 30 日後向就業當地就業服務機構申請（異地交通／租屋補助於受僱滿 30 日起 90 日內、搬遷補助於搬遷日起 90 日內）"]},
       "勞動部勞動力發展署「勞工補助／跨域津貼」頁「跨域就業津貼」段：適用對象、辦理方式及申請程序、申領期限"),
 587: ({"counties": NTPC,
        "uncheckedConditions": [
          "亡者設籍新北市且具原住民身分（依原住民身分法認定），由支出喪葬費之家屬請領（無家屬者以有名無主屍辦理，不得請領）",
          "115 年 1 月至 12 月實施，每年度預計 140 名；1 位亡者以 1 人請領為限",
          "完辦殯殮事宜後 3 個月內申請"]},
       f"{WEL}「新北市原住民喪葬補助」（show/268435774）補助內容一、補助對象、二、實施日期（115年1月至12月）；source_url 為三芝區公所 114 年度公告"),
 595: ({"counties": NTPC, "ageMin": 65, "ageMinByIdentity": {"原住民": 55},
        "uncheckedConditions": [
          "符合其一：列冊低收入戶；或列冊中低收入戶／具領中低收入老人生活津貼 1.5 倍資格，且經本市長照管理中心評估為中度或重度失能（CMS 4 級以上）",
          "入住與本府簽有收容安置契約、最近一次評鑑乙等以上或合格之住宿式機構、護理之家、康復之家、呼吸照顧病房或衛福部所屬公立老人長照／住宿式機構",
          "無法定傳染病（須體檢表）"]},
       f"{EGOV}「低收入戶、中低收入失能老人接受長期照顧機構安置補助計畫」一、補助對象、二、補助資格、申請對象"),
 602: ({"counties": NTPC,
        "uncheckedConditions": [
          "役男須為應徵（召）集在營（勤）服義務役；扶助對象為現役役男家屬、傷殘役男家屬及死亡役男遺族",
          "家庭總收入平均分配家屬人數，每人每月未達役男家屬戶籍所在地當年最低生活費，且家庭財產未逾一定金額",
          "經公所調查家況、市府核定列級生活扶助戶後發給；生育／喪葬／急難／醫療／健保費補助另向區公所申請（健保費限甲級扶助戶）"]},
       f"{EGOV}「服兵役役男貧困家屬生活扶助」申請條件 1、2 與補助內容"),
 616: ({"counties": NTPC,
        "uncheckedConditions": [
          "符合其一：當年度 5/31 前經社會局核可之低收入戶、中低收入戶、中低收入老人、弱勢兒童及少年，或符合身心障礙者生活補助者",
          "免申請，環保局於每年 8 月主動匯款；焚化廠所在地里民（新店德安里、八里下罟里、林口太平里、樹林樂山里）已另領者不重複發放"]},
       f"{WEL}「新北市政府補助垃圾清除處理費」福利說明、申請方式、備註欄"),
 623: ({"counties": NTPC, "requiredFlags": ["disability_certificate"],
        "uncheckedConditions": [
          "身心障礙者本人搭乘；依障礙類別／ICD 註記／等級分級：第一、二級須設籍本市（或領本市榮譽市民證、或領居留證並領本市核發身障證明之外籍人士）且符合第7類【05】、第2類【01】重度以上、第1類【09】，或需乘坐輪椅等條件之一；第三級為其他身障者或非設籍本市之重度以上特定類別",
          "服務範圍新北、臺北、基隆、桃園；設籍本市者起訖須有一端在本市，非設籍者起點須在本市；費率為計程車費率 1/3（設籍本市低收入戶每月 8 趟免費）"]},
       f"{WEL}「新北市身心障礙者小型復康巴士服務」福利說明（一）～（三）、補助內容"),
 630: ({"counties": NTPC, "ageMin": 30,
        "uncheckedConditions": [
          "檢查頻率：30～39 歲每 5 年 1 次；40～64 歲每 3 年 1 次；65 歲以上每年 1 次；35 歲以上小兒麻痺患者每年 1 次（須證明）；55 歲以上原住民每年 1 次",
          "B、C 型肝炎篩檢：40～79 歲民眾及原住民終身 1 次",
          "檢查當日攜帶健保卡，至成人預防保健服務特約醫事機構／衛生所"]},
       "新北市衛生局「《公費》成人健康檢查(30歲以上皆可做)」一、服務對象、二、四(4)"),
 637: ({"counties": NTPC, "incomeThreshold": "low_income", "requiresOwnedHome": True,
        "uncheckedConditions": [
          "房屋供自住使用，無出租、營業情形",
          "於社會局低收入戶申請書勾選稅捐減免，或自行持低收入戶證明向稅捐處申報；每期開徵 40 日（3/22）前申報，逾期自次期適用；證明書效期屆滿未再申報自次期恢復課徵"]},
       "新北市稅捐處「低收入戶房屋稅免徵申報書」參考範例 PDF 本文（已取具低收入戶證明文件且房屋係供自住使用，無出租、營業情形）及注意事項 1、2"),
 644: ({"counties": NTPC, "requiresChildUnder": 12,
        "uncheckedConditions": [
          "我國籍兒童，已完成出生登記或戶籍登記（原文未寫年齡上限；收托單位為托嬰中心、社區公共托育家園、居家托育人員）",
          "送托與政府簽約之公設民營托嬰中心、社區公共托育家園、私立托嬰中心或居家托育人員，每週送托 30 小時以上",
          "申報期間未經政府公費安置、未領取因照顧該名幼兒之育兒津貼；不得指定一對一收托（發展遲緩、身障、罕病或特殊狀況兒童除外）",
          "托育事實發生 15 日內申請"]},
       f"{EGOV}「托育公共及準公共化暨合作聯盟服務費用補助」一、福利說明（一）～（五）；requiresChildUnder 12 依原文「兒童」（兒少權法：未滿 12 歲）"),
 651: ({"counties": NTPC, "requiredFlags": ["disability_certificate"],
        "uncheckedConditions": [
          "符合其一：低收入戶、中低收入戶、或領有身心障礙者生活補助",
          "身心障礙者本人為車輛所有人且持同種車類有效駕照；購買停車位有貸款（利息補貼）或承租停車位且租期至少 3 個月（租金補助，每月最高 1,000 元）"]},
       f"{EGOV}「身心障礙者購買停車位貸款利息補貼或承租停車位補助」申請對象 1、2 與應備證件 2、4、5"),
 658: ({"counties": NTPC, "ageMin": 65, "ageMax": 69,
        "uncheckedConditions": [
          "設籍並實際居住本市、參加全民健保之中低收入老人（中低收入老人生活津貼資格）",
          "排除：依健保法無須自付保費、保費已由退輔會支付、或已符合其他由政府編列預算支付之健保費補助",
          "免申請（社會局主動傳送健保署減免）；未減免者向戶籍地區公所申請核退"]},
       f"{EGOV}「65歲以上未滿70歲中低收入老人全民健康保險自付保險費補助」申請對象一、補助對象"),
 665: ({"counties": NTPC, "ageMin": 65, "ageMinByIdentity": {"原住民": 55},
        "uncheckedConditions": [
          "實際居住本市且非居住於機構，經評估需關懷",
          "符合其一：獨自居住且無直系血親卑親屬居住新北市；同住家屬缺乏生活自理或照顧能力；其他有特殊需求者"]},
       f"{EGOV}「獨居老人關懷服務」申請說明（服務對象）"),
 672: ({"counties": NTPC, "requiresChildUnder": 8,
        "uncheckedConditions": [
          "兒童設籍本市且符合其一：未達學齡之身心障礙、疑似發展遲緩或發展遲緩兒童；或已達學齡、經特教鑑輔會同意暫緩入學之發展遲緩或身障兒童",
          "持疑似發展遲緩診斷證明書者須設籍於本市療育資源不足地區（三芝、石碇、平溪、烏來、雙溪、石門、貢寮、坪林、萬里、八里、金山、瑞芳、深坑、鶯歌）",
          "須檢附身障證明、綜合評估報告書或診斷證明書，及療育單據"]},
       f"{EGOV}「發展遲緩兒童療育補助」申請說明（服務對象一、二）；requiresChildUnder 8 涵蓋未達學齡＋暫緩入學一年"),
 679: ({"counties": NTPC, "requiredFlags": ["unemployed"],
        "uncheckedConditions": [
          "設籍本市失業中、有工作意願及工作能力",
          "屬特定對象之一：獨力負擔家計者、身心障礙者、原住民、低收或中低收入戶中有工作能力者、更生受保護人、中高齡者及高齡者、家庭暴力被害人、新住民（居留證地址視為設籍地）等",
          "須親至新北市就業服務處所屬站臺辦理求職登記並臨櫃申請"]},
       f"{EGOV}「求職交通補助金」申請說明、應備證件一（一）～（九）"),
 686: ({"counties": NTPC,
        "uncheckedConditions": [
          "申請日前繼續設籍本市 1 年以上之在學學生（國小至大專，含國外正式學籍），不含有正職工作者；以申請前一年 5/31 前設籍本市為準",
          "最近一年內（前一年 6/1～當年 5/31）參加運動競賽符合要點第三點各款之一（國家代表隊參加奧運／亞運等國際賽名次、代表本市參加全運會前三名、全民運前二名、全中運／指定盃賽／市中小運最優級名次等）",
          "不受理個人申請：每年 6/1 前送就讀學校或本市體育總會各單項委員會彙整，6/15 前送體育局"]},
       f"{WEL}「體育獎學金申請撥付」（show/7009）福利說明、申請方式＋《新北市政府績優體育獎學金發給要點》（115-02-05 修正）第三點；source_url 法規頁正文 JS 載入讀不到，只見法規名稱與修正日"),
 955: ({"counties": NTPC, "minResidencyMonths": 12,
        "uncheckedConditions": [
          "車主須為新北市民，且購買電動機車時已設籍本市滿一年",
          "向新北市經銷商新購電動機車，發票日期 115/1/1（含）以後；換購者汰舊之燃油機車車籍須為新北市",
          "名額有限，依申請順序至預算用罄為止（新購 7,000 名、換購 8,000 名、早鳥 4,500 名、雙汰舊 1,000 名；中低收入戶加碼 1 萬元不限額）；退件或逾期視同放棄"]},
       "新北市政府市政新聞 2025-12-31「新北115年電動機車補助方案出爐」第三～五段；2026-11-19 motor.ntpc.gov.tw 顯示各類仍有剩餘名額"),
}
# FLAG（不在 X）：609 動力漁船補助保險費 —— 補助對象是 100 噸以下動力漁船（船主／漁業經營者，持漁業執照經漁會送件），
#   屬業者營運保費補助、非個人福利。詳見 ~/.hermes/cache/welfare_w028_20261119/g3_report.md
EXPECTED = {545, 552, 559, 566, 573, 580, 587, 595, 602, 609, 616, 623, 630, 637, 644, 651, 658, 665, 672, 679, 686, 955}
FLAGGED = {609}
assert set(X) | FLAGGED == EXPECTED and not (set(X) & FLAGGED), '範圍不符'


def _dsn():
    if 'DATABASE_URL' not in os.environ:
        env = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'backend', '.env')
        for line in open(env, encoding='utf-8'):
            line = line.strip()
            if line.startswith('DATABASE_URL='):
                os.environ['DATABASE_URL'] = line.split('=', 1)[1].strip().strip('"\'')
    return os.environ['DATABASE_URL']


conn = psycopg2.connect(_dsn()); cur = conn.cursor()
cur.execute('select id, eligibility_conditions from benefits where id = any(%s)', (list(X),))
old = dict(cur.fetchall())
assert set(old) == set(X), set(X) - set(old)
new_all = {}
for bid, (cond, src) in X.items():
    ec_old = dict(old[bid] or {})
    assert ec_old.get('counties') == cond.get('counties'), (bid, ec_old.get('counties'), cond.get('counties'))
    ec = dict(cond)
    for k in ('otherConditions', 'incomeMonthlyMax', 'movableAssetsMax', 'realEstateMax'):
        if k in ec_old:                       # 引擎不檢查的鍵：原值搬到 _ 開頭鍵保留
            ec[f'_{k}_orig'] = ec_old[k]
    if '_note' in ec_old:
        ec['_note_orig'] = ec_old['_note']
    assert 'otherConditions' not in ec, bid
    ec['_source'] = f'W-028 {D} 依官方原文重編條件：{src}'
    assert_substantive(ec, label=f'新北市｜{bid}')
    new_all[bid] = ec
    print(bid, json.dumps({k: v for k, v in ec.items() if not k.startswith('_')}, ensure_ascii=False)[:160])

if '--apply' in sys.argv:
    cur.execute(f'create table {BACKUP} as select * from benefits where id = any(%s)', (list(X),))
    for bid, ec in new_all.items():
        cur.execute('update benefits set eligibility_conditions = %s, updated_at = now() where id = %s',
                    (json.dumps(ec, ensure_ascii=False), bid))
    conn.commit(); print('✅ 已寫入', len(new_all), '｜備份表', BACKUP)
else:
    conn.rollback(); print('(dry-run) 通過 assert_substantive', len(new_all), '筆；FLAG', sorted(FLAGGED))
