"""W-028 第 9 組：南投縣／嘉義市／基隆市／宜蘭縣／新竹市 18 筆中的 15 筆（754、757、777 不在 X），
   依官方原文替「只有引擎不檢查的鍵」的福利補條件。
   2026-11-19 逐頁讀過 source_url 正文（curl＋瀏覽器 UA；上一輪抓的 g9_pages/ 已逐頁核對 dataserno／s=／FL 編號對應正確的 id）：
   · 755、758 source_url 是南投縣開放資料 CSV（20250523115545.csv），重抓與快取逐位元組相同
   · 756 南投縣法規系統《南投縣中低收入老人生活津貼審核作業辦法》（112-02-03 修正）
   · 748～751 新竹市社會處「低收入戶及中低收入戶資格」各單頁；752 新竹市法規系統《新竹市醫療補助審核作業規定》
   · 760、775、779 嘉義市社會處單頁（上版 2026-01-01）；773 嘉義市《辦理急難救助實施要點》；774 嘉義市《災害救助金核發規定》
   · 961 基隆市社會處「老人參加全民健康保險保險費自付額補助」；963 宜蘭縣社會處「假牙補助：身心障礙者（55–64 歲）」
   原則同 W-020 B：
   · 問卷問得到的 → 編成引擎條件；問不到的 → uncheckedConditions 原文照列（最高只能 possible）
   · 「符合其一」的 OR 條件 → 一律放 unchecked，不硬編成 AND
   · incomeThreshold 只在原文為「列冊低收／中低收」或「未達最低生活費 1.5 倍」時編（2.5 倍不編）
   · 既有 otherConditions／incomeMonthlyMax／movableAssetsMax／realEstateMax 搬到 `_..._orig` 保留原值、刪掉原鍵
   🔴 X 裡放的是**整份新的** eligibility_conditions（不是 add）；counties 保留原值並 assert 與 DB 一致；
      每筆過 eligibility_guard.assert_substantive()
   SKIP（不在 X）：754 FLAG、777 FLAG、757 UNREADABLE —— 見 ~/.hermes/cache/welfare_w028_20261119/g9_report.md
   用法：先 `set -a; . backend/.env; set +a`，再 python batch_w028_g9_20261119.py [--apply]（預設 dry-run，不寫 DB）"""
import json, os, sys
from pathlib import Path
import psycopg2

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from eligibility_guard import assert_substantive  # noqa: E402

D = '2026-11-19'
BACKUP = 'benefits_before_w028_g9_20261119'
NT = ['南投縣']
CY = ['嘉義市']
KL = ['基隆市']
IL = ['宜蘭縣']
HC = ['新竹市']
DIS = ['disability_certificate']
HCSOC = '新竹市社會處「業務資訊＞社會救助＞低收入戶及中低收入戶資格」'
CYSOC = '嘉義市社會處「為民服務」'
NTCSV = '南投縣開放資料 CSV（20250523115545.csv）'

X = {
 # ─────────────── 南投縣 ───────────────
 755: ({"counties": NT, "requiredFlags": DIS, "uncheckedConditions": [
          "設籍並實際居住南投縣，最近一年居住國內超過 183 日",
          "家庭總收入平均分配全家人口之金額，未達當年度每人每月最低生活費 2.5 倍，且未超過臺灣地區平均每人每月消費支出 1.5 倍",
          "動產：一人時新臺幣 200 萬元，每增加一人增加 25 萬元；不動產每戶 650 萬元",
          "同時符合本補助費及政府其他生活補助或生活津貼要件者，僅能擇一領取"],
        "_otherConditions_orig": "同時符合申請本生活補助費及政府所提供其他生活補助或生活津貼要件者，僅能擇一領取。"},
       f"{NTCSV}「身心障礙者生活補助費(非低收入戶及中低收入者)」列：設籍條件、居住日數、身分（領有身心障礙證明）、收入／動產／不動產條件、其他條件"),
 756: ({"counties": NT, "ageMin": 65, "uncheckedConditions": [
          "設籍並實際居住南投縣，最近一年居住國內超過 183 日（中低收入老人生活津貼發給辦法第二條）",
          "家庭總收入人均每月未超過最低生活費 2.5 倍；存款本金、投資及有價證券一人 250 萬元、每增加一人加 25 萬元",
          "全家人口所有之不動產價值合計未超過新臺幣 650 萬元",
          "未接受政府公費收容安置；未入獄服刑、因案羈押或依法拘禁",
          "外住就養榮民領取就養給付者不得申領（符合本府列冊低收入戶第一款資格者補發差額）"],
        "_otherConditions_orig": "一、未接受政府公費收容安置。二、未入獄服刑、因案羈押或依法拘禁。"},
       "南投縣主管法規系統《南投縣中低收入老人生活津貼審核作業辦法》（112-02-03 修正）第三條、第四條（不動產 650 萬）、第八條（外住就養榮民）；"
       "年齡／2.5 倍／居住 183 日依同辦法所引《中低收入老人生活津貼發給辦法》第二條（另對照南投縣開放資料 CSV 同名列）"),
 758: ({"counties": NT, "incomeThreshold": "mid_low_income", "uncheckedConditions": [
          "設籍南投縣；符合其一：本縣列冊低收入戶，或家庭總收入平均分配未達當年度每人每月最低生活費 1.5 倍者",
          "動產、不動產未超過社會救助調查辦法所定標準之 1.5 倍",
          "低收入戶：須有住院及雇請專業看護之事實",
          "中低收入（1.5 倍以下）：最近三個月罹患嚴重傷病住院治療，經證明需雇請專人看護，每月自行負擔看護費超過 3 萬元或最近三個月累計超過 5 萬元，非本人或扶養義務人所能負擔",
          "看護行為發生三個月內檢齊資料向戶籍地鄉（鎮、市）公所申請"],
        "_otherConditions_orig": "1.低收入戶需有住院及雇請專業看護之事實者。2.中低收入戶最近三個月罹患嚴重傷病住院治療，經證明需雇請專人看護，每月自行負擔看護費用超過新台幣3萬元或最近三個月累計超過5萬元以上，非其本人或扶養義務人所能負擔者。3.看護行為發生三個月內檢齊資料申請。"},
       f"{NTCSV}「中低收入戶傷病住院看護費用補助」列：身分（列冊低收入戶／家庭總收入平均未達最低生活費 1.5 倍者）、收入條件、其他條件"),
 # ─────────────── 嘉義市 ───────────────
 760: ({"counties": CY, "incomeThreshold": "low_income", "incomeEstimateSufficient": True,
        "_incomeEstimateNote": f"{D} 低收入戶認定本身（申請列冊），同 6、8、748 的做法",
        "uncheckedConditions": [
          "設籍並實際居住嘉義市，最近一年居住國內超過 183 日",
          "全家人口之動產（含存款、股票及投資）平均每人不超過新臺幣 9 萬 6,000 元",
          "全家人口之不動產（含土地及房屋）價值不超過新臺幣 385 萬元"],
        "_incomeMonthlyMax_orig": 12388, "_movableAssetsMax_orig": 75000, "_realEstateMax_orig": 3500000},
       f"{CYSOC}「低收入戶」頁（上版 2026-01-01）申請資格：家庭總收入平均每人每月 15,515 元以下（＝115 年最低生活費）；舊值 12,388／7.5 萬／350 萬已過時"),
 773: ({"counties": CY, "requiredFlags": ["acute_hardship"], "uncheckedConditions": [
          "設籍嘉義市；符合其一：戶內人口死亡無力殮葬；戶內人口遭受意外傷害或罹患重病；負家庭主要生計責任者失業、失蹤、服役、服刑、羈押、拘禁或其他原因無法工作；財產或存款帳戶遭強制執行、凍結未能及時運用；已申請福利或保險給付尚未核准；其他重大變故經訪視評估確有救助需要——且致生活陷於困境",
          "事實發生後三個月內向戶籍地聯合里辦公處／區公所申請；同一事故之救助一年以一次為限",
          "已依其他社會救助／福利獲補助、取得社會保險給付或損害賠償者不得申請（取得後生活仍陷困境經查明屬實者除外）"],
        "_otherConditions_orig": "1.戶內人口死亡無力殮葬致生活陷困。\n2.戶內人口遭受意外傷害或罹患重病，致生活陷於困境。\n3.負家庭主要生計責任者，失業、失蹤、應徵集召集入營服兵役或替代?現役、入獄服刑、因案羈押、依法拘禁或其他原因，無法工作致生活陷困者。\n4.財產或存款帳戶因遭強制執行、凍結或其他原因未能及時運用，致生活陷於困境。\n5.已申請福利項目或保險給付，尚未核准期間生活陷於困境。\n6.其他遭受重大變故，致生活陷於困境，經訪視評估，認定確有救助需要。\n7.流落本市之他縣(市)民眾短缺川資者，由本府開立單程返鄉乘車換票證供其順利返鄉。"},
       "嘉義市主管法規系統《嘉義市辦理急難救助實施要點》（100-08-02 修正）三、急難救助標準（一）～（六）及末段三個月／一年一次；五、申請程序（設籍嘉義市市民）；六、不得申請之情形"),
 774: ({"counties": CY, "requiredFlags": ["recent_natural_disaster_damage"], "uncheckedConditions": [
          "嘉義市轄內遭受水、火、風、雹、旱、地震及其他不可抗力災害，致損害重大影響生活（含火災；問卷題目只問風災／震災／水災）",
          "符合其一：因災死亡（含重傷 30 日內死亡）；因災失蹤經警察機關登記協尋 30 日以上；因災重傷或住院 15 日內自付醫療費達重傷救助金額；住屋毀損達不堪居住程度（須災前已在現址設籍且災時居住）；住屋淹水達一樓室內樓地板起算 50 公分以上（須災時居住於現址）",
          "災害發生後三個月內向災害發生地區公所申請；已領政府其他相同性質災害救助金者不得重複具領"],
        "_otherConditions_orig": "1.死亡救助：因災致死或因災致重傷，於災害發生後三十日內死亡者。\n 2.失蹤救助：因災致行蹤不明並於警察機關登記協尋三十日以上未著者。\n3.重傷救助：因災致重傷或未達重傷程度，必須緊急救護住院治療，自住院之日起十五日內（住院期間）所發生自付醫療費用總額達重傷救助金金額者。\n 4.安遷救助：住屋因災毀損，達不堪居住程度者。申請人需於災害發生前已在現址辦妥戶籍登記，且災害發生時居住於現址者為限。                                5.住屋淹水救助：住屋因災致淹水，淹水高度自一樓室內樓地板起算達五十公分以上者。申請人需於災害發生時居住於現址者為限。"},
       "嘉義市主管法規系統《嘉義市災害救助金核發規定》（104-12-07 修正）二、三（三個月內申請）、四（救助金種類）、八（不得重複具領）；flag 比照 103、899 天然災害救助"),
 775: ({"counties": CY, "uncheckedConditions": [
          "一般民眾旅遊外地，一時川資短缺致無法返回原籍者（由市府填發返回原籍地之火車普通車／國光客運換票證）",
          "持身分證、印章向鐵路警察局嘉義分駐所、嘉義市各轄區派出所或市府社會處申請"],
        "_otherConditions_orig": "一般民眾旅遊外地，一時川資短缺致無法返回原籍者。"},
       f"{CYSOC}「短缺川資補助」頁（上版 2026-01-01）一、申請資格；二、補助標準；四、受理單位"),
 779: ({"counties": CY, "requiredFlags": DIS, "uncheckedConditions": [
          "設籍且實際居住嘉義市",
          "家庭總收入平均未達當年度每人每月最低生活費 2.5 倍（38,787 元），且未超過臺灣地區平均每人每月消費支出 1.5 倍（39,960 元）",
          "動產未超過 200 萬元，每增加一人增加 25 萬元；全戶不動產未超過臺灣省不動產限額 2 倍（770 萬元）",
          "未領有政府提供之其他生活補助或津貼，且未經公費收容安置（低收入戶生活扶助及榮民就養金不在此限）"],
        "_otherConditions_orig": "1.未接受政府補助收容安置                 2.領有身心障礙證明",
        "_incomeMonthlyMax_orig": 30970, "_movableAssetsMax_orig": 2000000, "_realEstateMax_orig": 6500000},
       f"{CYSOC}「身心障礙者生活補助」頁（上版 2026-01-01）二、申請資格；舊值 30,970／650 萬已過時"),
 # ─────────────── 基隆市 ───────────────
 961: ({"counties": KL, "ageMin": 65, "ageMinByIdentity": {"原住民": 55}, "minResidencyMonths": 36, "uncheckedConditions": [
          "設籍基隆市滿三年且實際繼續設籍居住",
          "保費已由各級政府全額補助者不再補助；未達補助額度者補差額（每人每月最高 826 元）"]},
       "基隆市社會處「老人福利＞健康維護＞老人參加全民健康保險保險費自付額補助」一、申請對象：設籍本市滿三年且實際繼續設籍居住之年滿65歲（原住民55歲）以上老人；二、補助標準"),
 # ─────────────── 宜蘭縣 ───────────────
 963: ({"counties": IL, "ageMin": 55, "ageMax": 64, "requiredFlags": DIS, "minResidencyMonths": 12, "uncheckedConditions": [
          "經醫師評估缺牙需裝置活動假牙",
          "符合其一：低收入戶、中低收入戶、領有身心障礙者生活補助費",
          "申請至當年度經費用罄為止；5 年內同一顎或同一牙位已受縣府社會處假牙補助者不得再申請"]},
       "宜蘭縣社會處「服務項目＞身心障礙者服務＞假牙補助：身心障礙者（年滿55歲至64歲）假牙裝置補助實施計畫」（上版 114-12-05，附 115 年度特約院所名單）一、申請資格；二、申請日期；四"),
 # ─────────────── 新竹市 ───────────────
 748: ({"counties": HC, "incomeThreshold": "low_income", "incomeEstimateSufficient": True,
        "_incomeEstimateNote": f"{D} 低收入戶認定本身（申請列冊），同 6、8 號的做法",
        "uncheckedConditions": [
          "設籍並實際居住新竹市",
          "全家人口存款本金及投資之平均每人每年未超過 96,000 元",
          "全家人口所有之土地及房屋價值未逾 385 萬元"],
        "_otherConditions_orig": "1.設籍並實際居住本市之市民。2.家庭總收入按全家人口平均分配，每人每月未超過當年公布最低生活費（112年標準為14，230元）。3.全家人口存款本金及投資之平均每人每年未超過80，000元。4.全家人口所有之土地及房屋價值未逾358萬元者。"},
       f"{HCSOC}「低收入戶資格及生活補助」（114-10-16 更新）申請資格 1～4：每人每月未超過最低生活費（114 及 115 年皆 15,515 元）；舊值 112 年 14,230／8 萬／358 萬已過時"),
 749: ({"counties": HC, "incomeThreshold": "low_income", "requiredGender": "female", "uncheckedConditions": [
          "符合其一：生育，或妊娠滿二十週以上之死產或自然流產（申請人為產婦本人）"],
        "_otherConditions_orig": "新竹市列冊之低收入戶婦女，其生育或妊娠滿二十週以上之死產或自然流產者。"},
       f"{HCSOC}「低收入戶產婦及嬰兒營養費補助」申請資格：新竹市列冊之低收入戶婦女，其生育或妊娠滿二十週以上之死產或自然流產者（原文明寫婦女本人生育／流產 ⇒ requiredGender）"),
 750: ({"counties": HC, "incomeThreshold": "low_income", "uncheckedConditions": [
          "因重病住院，經醫師診斷證明住院期間須 24 小時專人照顧（診斷書須註明住、出院日期）",
          "看護須具合格證明，看護收據須由醫師、護理人員、社工員或合法看護協會／中心蓋章證明",
          "每人每日最高補助 2,000 元，同一年度最高 18 萬元；向戶籍所在地區公所社政課申請"],
        "_otherConditions_orig": "本市列冊低收入戶者，每人每日最高補助看護費新台幣2，000元整，同一年度最高補助新台幣180，000元整。"},
       f"{HCSOC}「低收入戶重病住院看護費補助」補助標準：本市列冊低收入戶者；應備文件 2、3、6"),
 751: ({"counties": HC, "incomeThreshold": "low_income", "uncheckedConditions": [
          "本市列冊低收入戶成員死亡，由家屬或親屬申請（無家屬由里長代辦；委託機構安置者由機構代為申請）",
          "死亡三個月內檢具證明文件向死亡者戶籍所在地區公所申請；不得重複申領其他喪葬費用補助"],
        "_otherConditions_orig": "1.本市列冊低收入戶。2.低收入戶成員死亡，應由家屬或親屬提出申請；無家屬或親屬者，由里長代辦；本府委託之福利機構收容安置之低收入戶院民由受委託福利機構代為申請。3.前項申請應於死亡三個月內，檢具證明文件向死亡者戶籍所在地區公所申請。"},
       f"{HCSOC}「低收入戶喪葬費補助」補助對象：本市列冊低收入戶；申請方式；補助金額 2（不得重覆申領）"),
 752: ({"counties": HC, "incomeThreshold": "mid_low_income", "uncheckedConditions": [
          "設籍並實際居住新竹市，於健保特約醫療院所就醫且未獲其他單位醫療補助",
          "符合其一：低收入戶之傷、病患（全額補助）；中低收入戶傷病患，醫療費非本人或扶養義務人所能負擔且最近三個月醫療費累計達 3 萬元以上（補助 80%）；非屬前二款，患嚴重傷病、家庭總收入平均未達最低生活費 1.5 倍、醫療費非本人或扶養義務人所能負擔且最近三個月累計達 5 萬元以上（補助 70%）",
          "補助項目限健保部分負擔或健保未給付之醫療費用（不含掛號、看護、指定病房、義齒、配鏡等）；年度內每人最高 30 萬元",
          "出院或就醫後三個月內向戶籍所在地區公所申請"],
        "_otherConditions_orig": "1.本市列冊低收入戶，於出院或就醫日內３個月內提出。2.補助項目為因疾病、傷害事故就醫所生全民健康保險之部分負擔醫療費用或健康保險給付未涵蓋之醫療費用。"},
       "新竹市主管法規系統《新竹市醫療補助審核作業規定》（110-01-26 發布）第二點（一）～（三）、第三點、第四點、第五點；三款皆在最低生活費 1.5 倍以內 ⇒ mid_low_income（比照 932）"),
}
# SKIP（不在 X）：754 FLAG（source_url 是原住民族急難救助要點，非一般急難救助）、
#                777 FLAG（source_url 是急難救助實施要點，急難紓困條件不在該頁）、
#                757 UNREADABLE（welfare.nantou.gov.tw 504＋正文 AJAX 載入）—— 見 g9_report.md

IDS = sorted(X)
APPLY = '--apply' in sys.argv
ORIG_KEYS = ('otherConditions', 'incomeMonthlyMax', 'movableAssetsMax', 'realEstateMax')

conn = psycopg2.connect(os.environ['DATABASE_URL']); cur = conn.cursor()
cur.execute('select id, name, eligibility_conditions from benefits where id = any(%s)', (IDS,))
rows = {r[0]: (r[1], r[2]) for r in cur.fetchall()}
assert set(rows) == set(X), set(X) - set(rows)

# 先全部驗過，任何一筆不合格就整批不動
new_rows = {}
for bid, (new, src) in X.items():
    name, old = rows[bid]
    old = old or {}
    assert old.get('counties') == new.get('counties'), (bid, old.get('counties'), new.get('counties'))
    for k in ORIG_KEYS:  # 既有不檢查鍵：原鍵必須刪掉、原值逐字搬到 _..._orig
        assert k not in new, (bid, k)
        if k in old:
            assert new.get(f'_{k}_orig') == old[k], (bid, k, '原值沒有逐字保留')
    ec = dict(new)
    ec['_source'] = f'W-028 {D} 依官方原文補條件：{src}'
    assert_substantive(ec, label=f'{bid}｜{name}')
    new_rows[bid] = ec
    print(bid, name, json.dumps({k: v for k, v in ec.items() if not k.startswith('_')}, ensure_ascii=False)[:160])

if APPLY:
    cur.execute(f'create table {BACKUP} as select * from benefits where id = any(%s)', (IDS,))
    for bid, ec in new_rows.items():
        cur.execute('update benefits set eligibility_conditions = %s, updated_at = now() where id = %s',
                    (json.dumps(ec, ensure_ascii=False), bid))
    conn.commit(); print(f'✅ 已寫入 {len(new_rows)}（備份表 {BACKUP}）')
else:
    conn.rollback(); print('(dry-run)', len(new_rows), '筆全部通過 counties／原值保留／assert_substantive 檢查，未寫入 DB')
