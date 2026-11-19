"""W-028 第 1 組：新北市 23 筆「只有 otherConditions（引擎不檢查的鍵）」的福利，依官方原文重編資格條件。
   2026-11-19 逐頁讀過 source_url 正文：
   · 多數頁 curl（瀏覽器 UA）即可讀到；快取在 ~/.hermes/cache/welfare_w028_20261119/pages/txt_<id>.txt
   · 543 source_url（衛生局 node=14223）curl 只回 JS 轉址 ⇒ web_extract 讀到全文，但那是 114 年擴大補助新聞稿；
     再搜「新北市 115年 帶狀疱疹疫苗 補助」⇒ 依 115/9/1 起的新版對象編（板橋區衛生所等公告）
   · 557 貢寮區衛生所頁只寫「自費接種」，另讀新北「福利補助自己查」MMR0 頁（268437197）：設籍新北者免費 1 劑
   · 600 法規頁 FLAWDAT01 只顯示標題 ⇒ 用瀏覽器點「所有條文」讀到第一～六點全文
   · 593（部落大學）是課程招生入口、不是福利 ⇒ FLAG，不在 X
   原則（W-028，Lonck 已定案）：
   · 問卷問得到的 → 編成引擎條件；問不到的 → uncheckedConditions 原文照列（最高只能 possible）
   · 「符合其一」的 OR 條件 → 一律放 unchecked，不硬編成 AND
   · otherConditions 這 22 筆全部是「申請方式／文件／地點」不是資格 ⇒ 搬到 _otherConditions_orig、刪掉 otherConditions
   · X 放的是「整份新的」eligibility_conditions（counties 保留原值，執行時另 assert 與 DB 一致）
   · 每筆都過 eligibility_guard.assert_substantive()
   用法：python batch_w028_g1_20261119.py [--apply]（預設 dry-run，不寫 DB）"""
import json, os, sys
from pathlib import Path
import psycopg2

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))   # scripts/
from eligibility_guard import assert_substantive

D = '2026-11-19'
NTPC = ['新北市']
EADM = '新北市政府申辦E服務「案件說明」頁'
WELF = '新北市政府「福利補助自己查」福利項目說明頁'
DIS = ['disability_certificate']

X = {
 543: ({"counties": NTPC, "ageMin": 65, "ageMinByIdentity": {"原住民": 55}, "incomeThreshold": "mid_low_income",
        "uncheckedConditions": [
          "設籍新北市",
          "須持當年度新北市低收或中低收入戶證明（持「新北市中低收入老人生活津貼證明書」不符合）；原住民 55 歲以上另攜戶口名簿或戶籍謄本",
          "至新北市 29 區衛生所預約接種（完整 2 劑）；疫苗缺貨時暫停施打"]},
       "source_url 為 114 年新聞稿「新北市自9月24日起擴大全額補助帶狀疱疹疫苗對象」（舊版：需罹患高風險慢性疾病／重大傷病）；"
       "依 115 年新版：板橋區衛生所「115年度新北市接種帶狀皰疹疫苗擴大接種對象」（二）實施對象：設籍新北市且滿65歲(原住民55歲)以上之低收或中低收入戶者；"
       "衛生局新聞「六都最優！新北市9月1日起擴大全額補助帶狀疱疹疫苗條件」"),
 550: ({"counties": NTPC, "ageMin": 18, "ageMax": 29, "uncheckedConditions": [
          "設籍或實際居住新北市之本國籍青年，未在學且具就業意願及有意參加職業訓練",
          "符合其一：尋職青年（失業期間連續達 180 日以上，以未參加勞保／就保之日起算）；"
          "或非典型勞動青年（目前僅從事非典型工作或待業中，且近 2 年內從事定期契約／部分工時／派遣／政府短期就業等非典型工作合計 90 日以上，"
          "或近 1 年內運用網路平台／APP 接案 3 次以上，或經就業服務處認定）"]},
       "新北勞動雲「新北市青年全方位就業計畫(尋職青年/非典型勞動青年)」服務對象"),
 557: ({"counties": NTPC, "requiresChildUnder": 1, "uncheckedConditions": [
          "設籍新北市、6 個月以上未滿 1 歲之嬰幼兒，欲前往麻疹流行地區（須出示出國相關證明文件）",
          "攜兒童健康手冊、健保 IC 卡至新北市 29 區衛生所接種（採預約制）；非設籍新北市者須自費"]},
       "貢寮區衛生所「麻疹、德國麻疹及腮腺炎混合疫苗(MMR疫苗)公告」1～4 點；"
       "新北市福利補助自己查「MMR0疫苗」（268437197）：設籍新北市欲前往麻疹流行地區之6個月以上未滿1歲嬰幼兒，免費接種1劑"),
 564: ({"counties": NTPC, "requiresChildUnder": 7, "uncheckedConditions": [
          "幼兒具本國籍且就學當學年度 9 月 1 日前滿 2 歲至入國小前，並實際就讀新北市公立幼兒園",
          "非本國籍幼兒持新式居留證者比照第 1 胎收費（具身心障礙身分者免繳費用）",
          "入學即免繳／減繳，家長免申請；不得與其他相同性質補助重複請領"]},
       f"{WELF}「公立幼兒園就學補助」補助內容：補助對象一～三"),
 571: ({"counties": NTPC, "requiredFlags": DIS, "uncheckedConditions": [
          "車輛符合其一：身心障礙者本人所有且供本人使用；或供身障者使用、為其配偶或同一戶籍二親等以內親屬所有，且車籍地或住居所地址與身障者戶籍地相同",
          "每一身心障礙者以 1 輛免稅為限；免稅額以 2400cc（電動車 262HP）之稅額為限，超過部分不予免徵"]},
       f"{EADM}「使用牌照稅身心障礙者免稅申請案件」申請說明一～四、備註 5"),
 578: ({"counties": NTPC, "requiredFlags": ["unemployed"], "uncheckedConditions": [
          "失業勞工符合其一：失業期間連續達 30 日以上、非自願離職、或經公立就業服務機構評估",
          "符合其一：領有照顧服務員訓練結業證明書、照顧服務員技術士證、高中職以上護理／照顧相關科系畢業、或完成衛福部公告之照服員修業課程",
          "先向公立就業服務機構求職登記取得推介卡；受僱於長照單位連續達 30 日以上、月薪不低於基本工資，於受僱每滿 30 日之次日起 90 日內申請"]},
       "勞動部勞動力發展署「缺工獎勵」頁「照顧服務就業獎勵」適用對象（勞工資格）、辦理方式及申請程序"),
 585: ({"counties": NTPC, "uncheckedConditions": [
          "於新北市轄內私有建築物屋頂設置太陽光電發電設備，並於 114/1/1 起依再生能源發電設備設置管理辦法取得設備登記文件（或全數更換並取得備查文件）",
          "依法令負有設置太陽光電義務者不符；同一設備登記已獲本局或其他太陽光電獎勵者不予獎勵",
          "設備須為新品（中央獎勵另需符合台灣高效能太陽光電模組技術規範）",
          "申請期限：公告日起至 115/11/30 前（郵戳為憑），逾期不予受理"]},
       "新北市經濟發展局「115年家戶屋頂設置太陽光電加速計畫暨新北加碼補助」計畫簡介表：一、獎勵對象；二、獎勵標準；四、申請期間"),
 600: ({"counties": NTPC, "requiresChildUnder": 16, "uncheckedConditions": [
          "具學籍且在法定修業年限內，就讀新北市公私立國民中學或國民小學之學生",
          "符合其一：持有效低收入戶證明；本人戶籍註記為原住民；領有有效身心障礙手冊；父、母或法定監護人領有有效身心障礙手冊",
          "每學期註冊時檢具證明文件向就讀學校申請；具多種身分者擇一申請，不得重複請領相同性質補助"]},
       "新北市法規查詢《新北市政府辦理原住民及低收入戶與身心障礙學生及身心障礙者子女就讀國民中小學教科書費補助要點》(103-07-08 修正) 第二點、第四點、第五點"),
 607: ({"counties": NTPC, "requiredFlags": DIS, "uncheckedConditions": [
          "設籍新北市且具身心障礙證明（手冊）",
          "檢附 3 個月內診斷證明；呼吸器、氧氣製造機、壓力衣、咳痰機等另需 3 個月內醫療輔具評估報告"]},
       f"{EADM}「身心障礙者醫療輔具補助費用申請（含人工電子耳手術費用）(申請及核定階段)」申請對象、應備證件"),
 614: ({"counties": NTPC, "incomeThreshold": "low_income", "requiresChildUnder": 13, "uncheckedConditions": [
          "持政府發給「低收入戶」證明之新北市公立國小學生（持中低收入戶證明者不符）",
          "每學年辦理二次，由學校於教育局函知申請日起 15 日內提出申請，逾期不受理"]},
       f"{WELF}「新北市國小低收入戶學童就學補助」福利說明、應備證件、備註欄"),
 621: ({"counties": NTPC, "requiredFlags": ["pregnant_or_recent_birth"], "uncheckedConditions": [
          "新生兒之母或父於出生日符合其一，且申請時母或父仍設籍新北市：母或父一方設籍新北滿 10 個月以上（可併計基北北桃）；"
          "或設籍未滿 10 個月但出生後繼續設籍累計滿 10 個月（115/1/1 起出生適用，不併計）；或設籍滿 10 個月之未婚婦女；"
          "或生父認領且生父符合設籍規定；或釋字 748 施行法第二條關係之收養",
          "向戶政事務所臨櫃或線上申辦"]},
       f"{EADM}「生育獎勵金」★申請條件（一）～（五）、★申領資格"),
 628: ({"counties": NTPC, "requiresChildUnder": 7, "uncheckedConditions": [
          "幼兒就讀新北市公立幼兒園並參加延長照顧服務（18 時至 19 時）",
          "113 學年度起入學者每小時 35 元、經濟需要協助幼兒免收費；112 學年度（含）前入學者除點心費外免收費",
          "家長免申請，由教育局依幼兒園開辦情況核撥"]},
       f"{WELF}「新北市公立幼兒園辦理延長照顧服務(18時至19時)」福利說明、補助內容"),
 635: ({"counties": NTPC, "requiredIdentities": ["農民"], "uncheckedConditions": [
          "具農民健康保險被保險人資格（補助被保險人自付之 30% 保費）",
          "免申請：由新北市各基層農會將具農保資格之農友資料送市府辦理"]},
       f"{WELF}「農民補助-健康保險自付額」福利說明、補助內容、申請方式"),
 642: ({"counties": NTPC, "ageMin": 60, "ageMinByIdentity": {"原住民": 55}, "uncheckedConditions": [
          "設籍新北市；60–64 歲（非原住民）須為列冊新北市低收入戶",
          "65 歲以上（原住民 55）須為列冊低收入戶，或符合其一：中低收入戶、領中低收入老人生活津貼、經市府全額補助收容安置、領身心障礙者生活補助費、市府補助身障日照及住宿式照顧費用達 50% 以上",
          "經醫師評估缺牙需裝置假牙；事前申請制（申請前已完成假牙製作者不予補助），向戶籍地區公所申請",
          "同一顎／同一齒 5 年內不重複補助；5 年內已取得原民局老人假牙補助相同項目者不得申請"]},
       f"{EADM}「中、低收入老人補助裝置假牙」申請說明：補助資格 1、2，補助限制一～六（編法同 410 號）"),
 649: ({"counties": NTPC, "requiredFlags": DIS, "uncheckedConditions": [
          "持有新北市身心障礙證明，且符合《新北市政府身心障礙者輔具費用補助基準表》所定各項目補助對象",
          "須經核定後始得購置（未經核定不予補助），核定後 6 個月內請款；每人每二年以補助四項輔具為原則"]},
       f"{EADM}「身心障礙者輔具費用補助」申請說明、申請對象、備註 1～3"),
 656: ({"counties": NTPC, "requiresChildUnder": 18, "uncheckedConditions": [
          "符合其一：低收入戶及中低收入戶；符合弱勢兒童及少年生活扶助；符合弱勢家庭兒少緊急生活扶助資格；符合特殊境遇家庭兒少緊急生活扶助；早產兒；罕見疾病或領有健保重大傷病證明",
          "補助項目：健保未涵蓋之發展遲緩療育訓練費（6 歲入國小後至未滿 18 歲，治療次日起 3 個月內申請）、住院看護費／膳食費／自付住院費、未滿 18 歲未婚懷孕生產流產費、親子血緣鑑定費（醫療結束日起 6 個月內申請）",
          "同一事件已依法取得政府相關扶助者不予補助"]},
       f"{EADM}「弱勢兒童及少年醫療補助」申請說明：壹、補助對象一～六；貳、補助項目及額度一～五"),
 663: ({"counties": NTPC, "requiredFlags": DIS, "requiresNoOwnedHome": True, "uncheckedConditions": [
          "設籍並實際居住新北市，租賃房屋座落新北市、具合法房屋證明、非社會住宅，且實際居住於租賃處所",
          "家庭總收入平均未達當年度每人每月最低生活費 2.5 倍，或未超過臺灣地區平均每人每月消費支出 1.5 倍",
          "現未接受政府相關租金或貸款利息補貼；未獲政府補貼住宿式照顧費用、未使用公有房舍或平價住宅",
          "身心障礙者、配偶及其戶籍內或同住之直系親屬均無自有住宅"]},
       f"{EADM}「身心障礙者房屋租金補貼」申請對象 1～8"),
 670: ({"counties": NTPC, "uncheckedConditions": [
          "設籍新北市並符合其一：（一）列冊低收入戶之傷病患者；（二）患嚴重傷病，經社會局社會救助機構免費收容或委託收容者；"
          "（三）患嚴重傷病、最近三個月內自行負擔醫療費超過 2 萬元，非本人或扶養義務人所能負擔，且符合其一：列冊中低收入戶、領弱勢兒少生活扶助、具特殊境遇家庭扶助身分、"
          "領身心障礙者生活補助費、領中低收入老人生活津貼、或家庭人均每月不超過最低生活費 2.5 倍且家庭動產不超過低收入戶標準 2.5 倍",
          "應於就醫、出院或死亡後三個月內向戶籍所在地區公所申請"]},
       f"{EADM}「市民醫療補助」申請對象一、（一）～（三）；申請方式（二）"),
 677: ({"counties": NTPC, "uncheckedConditions": [
          "實際居住新北市，患有智障、自閉症、失智症等心智障礙者，或有走失之虞者（免費申請特殊編號手鍊）"]},
       f"{EADM}「預防走失手鍊」申請說明、申請對象"),
 684: ({"counties": NTPC, "requiresChildUnder": 16, "uncheckedConditions": [
          "原住民學生，設籍新北市連續 6 個月以上，且就讀新北市公私立國中",
          "經就讀學校初審核章後彙整申請（清寒獎學金、優秀獎學金各 5,000 元；各獎項之細部資格頁面未載明）"]},
       f"{EADM}「國中原住民學生獎學金申請撥付」申請說明、備註"),
 691: ({"counties": NTPC, "ageMin": 18, "ageMax": 39, "uncheckedConditions": [
          "單身、新婚，或育（孕）有未成年子女（胎兒）者",
          "現於新北市設籍或就學或就業",
          "家庭成員於新北市、臺北市、桃園市及基隆市均無自有住宅（其他縣市有房不在此限，故未編 requiresNoOwnedHome）",
          "家庭年收入及每人每月平均收入低於當年度公告標準",
          "受理期間約為每年 9 月公告，申請方式依當年度公告為準"]},
       f"{EADM}「青年租屋補貼」申請說明、申請對象（一）～（四）"),
 1004: ({"counties": NTPC, "requiresChildUnder": 7, "uncheckedConditions": [
          "就讀新北市公立幼兒園且學齡滿 2 足歲至入國民小學前（含緩讀生）",
          "符合其一：領弱勢兒少生活扶助、特殊境遇家庭、身心障礙或發展遲緩（須確診）、寄養家庭、原住民幼生（3～5 歲）、家庭突發因素致無力支付餐點費用（導師及園方認定）",
          "已依「公立幼兒園就學補助」免繳費用者（含餐點費）非本案對象",
          "申請時間：每年 3/1～3/31 及 9/1～9/30，向就讀幼兒園申請"]},
        f"{WELF}「公立幼兒園弱勢家庭幼生學雜費補助」福利說明、補助內容、應備證件、備註欄"),
}
# SKIP（不在 X）：593 FLAG（新北市原住民族部落大學＝課程招生入口，不是福利）—— 見 ~/.hermes/cache/welfare_w028_20261119/g1_report.md
IDS = [543, 550, 557, 564, 571, 578, 585, 593, 600, 607, 614, 621, 628, 635, 642, 649, 656, 663, 670, 677, 684, 691, 1004]
FLAGGED = {593}
assert set(X) | FLAGGED == set(IDS) and not (set(X) & FLAGGED)

conn = psycopg2.connect(os.environ['DATABASE_URL']); cur = conn.cursor()
cur.execute('select id, name, eligibility_conditions from benefits where id = any(%s)', (list(X),))
rows = {r[0]: (r[1], r[2]) for r in cur.fetchall()}
assert set(rows) == set(X), set(X) - set(rows)

new_all = {}
for bid, (cond, src) in X.items():
    name, old = rows[bid]
    old = dict(old or {})
    assert old.get('counties') == cond['counties'], (bid, old.get('counties'))
    ec = json.loads(json.dumps(cond, ensure_ascii=False))       # 深拷貝
    # 既有的不檢查鍵：搬到 _ 開頭鍵保留原文（這 22 筆的 otherConditions 都是申請方式／文件／地點）
    for k in ('otherConditions', 'incomeMonthlyMax', 'movableAssetsMax', 'realEstateMax'):
        if k in old:
            ec[f'_{k}_orig'] = old[k]
    for k in ('minResidencyMonths', 'referenceData'):          # 若原本有就保留（本組皆無）
        if k in old and k not in ec:
            ec[k] = old[k]
    ec['_source'] = f'W-028 {D} 依官方原文重編條件：{src}'
    assert 'otherConditions' not in ec
    assert_substantive(ec, label=f'{bid}｜新北市｜{name}')
    new_all[bid] = ec
    print(bid, name[:18], json.dumps({k: v for k, v in ec.items()
                                     if not k.startswith('_') and k != 'uncheckedConditions'}, ensure_ascii=False),
          f"unchecked×{len(ec.get('uncheckedConditions', []))}")

if '--apply' in sys.argv:
    cur.execute('create table benefits_before_w028_g1_20261119 as select * from benefits where id = any(%s)', (list(X),))
    for bid, ec in new_all.items():
        cur.execute('update benefits set eligibility_conditions = %s, updated_at = now() where id = %s',
                    (json.dumps(ec, ensure_ascii=False), bid))
    conn.commit(); print('✅ 已寫入', len(new_all), '（備份表 benefits_before_w028_g1_20261119）')
else:
    conn.rollback(); print('(dry-run) 全部通過 assert_substantive／counties 檢查：', len(new_all), '筆；FLAG 不在 X：', sorted(FLAGGED))
