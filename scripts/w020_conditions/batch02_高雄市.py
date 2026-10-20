"""W-020 B 第二批：高雄市 29 筆，依官方原文（社會局／衛生局／勞工局／環保局／市府新聞）編資格條件。
   2026-10-20 逐頁讀過正文（curl + 瀏覽器 UA；885、895 原網址是 JS 轉址，讀的是轉址後的頁）。
   原則同第一批：
   · 問卷問得到的 → 編成引擎條件（ageMin／incomeThreshold／requiredFlags／requiresChildUnder…）
   · 問卷問不到的 → uncheckedConditions 原文照列（最高只能 possible）
   · 「符合其一」的 OR 條件、引擎表達不了的 → 一律放 unchecked，不硬編成 AND（會把該看到的人刷掉）
   · incomeThreshold：引擎用「人均月收入 ≤ 最低生活費（×1.5）」推算，與原文「列冊低收／中低收」「未達最低生活費 1.5 倍」同一把尺
   用法：python batch02_高雄市.py [--apply]"""
import json, sys, psycopg2
D = '2026-10-20'
DIS = ["disability_certificate"]
SCF = ["special_circumstance_family"]
X = {
 6:   ({"incomeThreshold": "mid_low_income"},
       "大寮區公所申請流程表：設籍並實際居住本市、人均月收入未超過最低生活費 1.5 倍（低收／中低收認定本身）"),
 354: ({"uncheckedConditions": [
          "設籍高雄市；淘汰出廠滿 10 年燃油機車並新購電動機車，或純新購（月租費補助）",
          "🔴 官方頁註明：2026/8/11 補助金額已用罄"]},
       "環保局最新消息（2026-08-11 更新）：115 年汰舊換新購電動機車補助"),
 879: ({"requiresChildUnder": 18, "uncheckedConditions": [
          "兒少 6 歲以上未滿 18 歲，經醫師診斷有持續療育需求",
          "符合其一：列冊低收／中低收（或符合弱勢兒少、弱勢單親扶助資格）；或具重大傷病／罕見疾病證明"]},
       "社會局頁「補助對象」：設籍並實際居住本市 6～未滿 18 歲、經醫師診斷有持續療育需求且符合其一"),
 880: ({"requiresChildUnder": 18, "incomeThreshold": "mid_low_income", "requiredFlags": SCF, "uncheckedConditions": [
          "設籍並實際居住本市滿半年以上，父或母獨自扶養未滿 18 歲未婚子女（配偶死亡／離婚單獨監護／非婚生等 8 種情形之一）",
          "全家動產 1 戶 4 口內未超過 120 萬（第 5 口起每口加 18 萬）；土地房屋總值未超過 650 萬"]},
       "社會局頁「服務對象」：人均月收入未達最低生活費 1.5 倍"),
 881: ({"requiredFlags": SCF + ["is_student"], "uncheckedConditions": [
          "已領有弱勢單親家庭子女生活補助",
          "子女 18 歲以上未滿 25 歲，就讀國內大學／專科日間部學士或副學士"]},
       "社會局頁「服務對象」"),
 882: ({"ageMin": 65, "uncheckedConditions": [
          "符合其一：列冊低收／中低收入戶、領中低收入老人生活津貼、領身心障礙者生活補助",
          "非居住於公有宿舍或安置於老人福利機構／護理之家",
          "核准前勿先修繕"]},
       "社會局頁「申請資格與內容」：實際居住本市之 65 歲以上老人"),
 883: ({"ageMin": 65, "ageMinByIdentity": {"原住民": 55}, "incomeThreshold": "mid_low_income", "uncheckedConditions": [
          "列冊中低收入戶，或領取未達最低生活費 1.5 倍之中低收入老人生活津貼（低收入戶請見「低收入戶失能老人養護服務補助」）",
          "經衛生局長照中心評估為中度或重度失能（長照需要等級 4–8 級），有進住機構需求",
          "進住本市評鑑合格之老人福利機構／護理之家／住宿長照機構"]},
       "社會局頁「補助對象及資格」：設籍本市 65 歲以上、原住民 55 歲以上"),
 884: ({"ageMin": 65, "ageMinByIdentity": {"原住民": 55}, "incomeThreshold": "low_income", "uncheckedConditions": [
          "經衛生局長照中心評估為中度或重度失能（長照需要等級 4–8 級），有進住機構需求",
          "進住本市評鑑合格之老人福利機構／護理之家／住宿長照機構"]},
       "社會局頁「補助對象及資格」：設籍本市 65 歲以上（原住民 55）、列冊低收入戶"),
 885: ({"uncheckedConditions": [
          "醫療費：本市列冊低收或中低收入戶",
          "看護費：列冊低收／中低收，或領中低收入老人生活津貼、身心障礙者生活補助",
          "出院或醫療／看護行為發生後 3 個月內申請"]},
       "社會局頁（轉址後 s_id=706）「申請資格」：設籍本市並符合其一"),
 886: ({"requiredFlags": DIS, "uncheckedConditions": [
          "經 3 個月內專科醫師診斷／輔具評估確有需要（電動拍痰器、抽痰機、氧氣製造機、呼吸器、壓力衣等 13 項）"]},
       "社會局頁「應備表件」：身心障礙證明、戶籍、診斷證明"),
 887: ({"requiredFlags": DIS, "uncheckedConditions": [
          "輕度或中度身心障礙",
          "設籍本市滿 1 年且最近一年國內居住超過 183 天",
          "64 歲以下：綜合所得稅率 5% 以下或未達申報標準；65 歲以上：稅率 12% 以下",
          "免申請（社會局篩選後直接報送健保署）"]},
       "社會局頁「服務內容」二"),
 888: ({"requiredFlags": DIS, "requiresNoOwnedHome": True, "uncheckedConditions": [
          "設籍與租賃房屋皆在本市；租賃房屋非直系親屬所有",
          "家庭總收入人均未達最低生活費 2.5 倍",
          "現未接受政府租金或貸款利息補貼、住宿式照顧費用補助，未使用公有房舍或平價住宅",
          "每年 12 月受理"]},
       "社會局頁「對象資格」（須符合所有條件）"),
 889: ({"requiredFlags": DIS, "requiresOwnedHome": True, "uncheckedConditions": [
          "身心障礙者本人；設籍與購買房屋皆在本市且未滿 5 年",
          "家庭總收入人均未達最低生活費 4 倍",
          "除本次購屋外，本人、配偶及戶內直系親屬均無其他自有住宅；已辦妥住宅貸款且未清償",
          "名額依年度公告，每年 12 月受理"]},
       "社會局頁「對象資格」（須符合所有條件）"),
 890: ({"requiredFlags": DIS, "uncheckedConditions": [
          "身心障礙者本人為車輛所有人，並領有同種車類有效駕照",
          "列冊低收／中低收入戶，或領有身心障礙者生活補助",
          "已承租停車位且租期逾 3 個月；未接受政府同性質補助",
          "每年 12 月受理"]},
       "社會局頁「對象資格」（須符合所有條件）"),
 891: ({"requiredFlags": DIS, "uncheckedConditions": [
          "身心障礙者本人為車輛所有人，並領有同種車類有效駕照",
          "列冊低收／中低收入戶，或領有身心障礙者生活補助",
          "購買之停車位在本市且已有貸款；未接受政府同性質補助",
          "每年 12 月受理"]},
       "社會局頁「對象資格」（須符合所有條件）"),
 892: ({"requiredFlags": DIS, "uncheckedConditions": [
          "已申領加註車號之身心障礙者專用停車位識別證，或懸掛專用車牌／經檢驗合格之特製機車"]},
       "社會局頁「服務對象」（交通局承辦）"),
 893: ({"requiredFlags": DIS, "uncheckedConditions": [
          "設籍本市；未領身心障礙者生活補助（日間照顧可同時申領）及其他政府生活補助",
          "家庭總收入人均：30 歲以下 ≤ 最低生活費 4 倍；30 歲以上（或父母一方滿 65、家中 2 位以上身障者）≤ 6 倍",
          "安置於評鑑合格之身障福利機構／老人福利機構／護理之家"]},
       "社會局頁「服務對象」"),
 894: ({"requiredFlags": DIS, "uncheckedConditions": [
          "學籍設於本市國中、小之身心障礙學生",
          "經本市特教學生鑑定及就學輔導會鑑定，須在家教育或安置於社福機構",
          "每學期開學後 14 日內向學校申請"]},
       "社會局頁「申請資格」（教育局承辦）"),
 895: ({"requiredFlags": DIS, "uncheckedConditions": [
          "設籍高雄市；取得汽車駕照之日起 1 年內申請",
          "未曾獲政府或團體相關汽車駕駛考照訓練補助",
          "經費執行完畢即停止受理"]},
       "勞工局頁（轉址後）「申請資格」"),
 896: ({"uncheckedConditions": [
          "居住 5 層樓以下透天厝／公寓／平房（非應設火警自動警報設備場所）",
          "符合其一：低收入戶、獨居長者、領有身心障礙證明",
          "每戶限 1 顆"]},
       "社會局頁「服務對象」（消防局承辦）"),
 897: ({"incomeThreshold": "low_income", "uncheckedConditions": [
          "孕產婦（未滿 19 歲或 35 歲以上／兩年內曾早產、流產或難產／貧血 HB ≤ 11）或嬰幼兒（出生體重 < 2,500 公克／5 歲內身高體重低於生長曲線 25 百分位）",
          "經醫師診斷需要營養補充"]},
       "社會局頁「申請資格」：本市列冊低收入戶孕產婦及嬰幼兒"),
 898: ({"incomeThreshold": "low_income", "requiredFlags": ["is_student"], "uncheckedConditions": [
          "戶內 25 歲以下、就讀高中（職）以上之在學學生（空大、進修補校、在職班、學分班、遠距教學不補助）"]},
       "社會局頁「補助條件」：本市列冊低收入戶"),
 899: ({"requiredFlags": ["recent_natural_disaster_damage"], "uncheckedConditions": [
          "因災致死亡失蹤重傷、住屋淹水超過 50 公分、毀損不堪居住、土石流入等（毀損未達不堪居住者限低收／中低收）",
          "災後向區公所申請（區公所於災後 20 日內會同勘查）"]},
       "社會局頁：高雄市災害救助金核發辦法"),
 900: ({"incomeThreshold": "low_income", "requiredFlags": ["is_student"], "uncheckedConditions": [
          "子女就讀國三、高三或五專五年級，因升學參與補習",
          "參與社會局脫貧自立計畫且經社工評估有需求；三年內未受相同補助",
          "名額視年度經費，額滿截止"]},
       "社會局頁「申請資格」：本市列冊低收入戶子女"),
 901: ({"incomeThreshold": "low_income", "requiredFlags": ["is_student"], "uncheckedConditions": [
          "戶內高中職以上在學學生，因就學需要購買學習設備（電腦、翻譯機等）",
          "五年內未受相同補助；名額視年度經費，額滿截止"]},
       "社會局頁「申請資格」：本市列冊低收入戶"),
 902: ({"requiresChildUnder": 7, "incomeThreshold": "mid_low_income", "requiredFlags": SCF, "uncheckedConditions": [
          "設籍並實際居住本市滿半年，父或母獨力扶養就讀本市公私立幼兒園之子女（配偶死亡／離婚單獨監護等 7 種情形之一）",
          "須先核定弱勢單親家庭子女生活補助，至區公所開立弱勢單親家庭證明書",
          "全家動產 1 戶 4 口內未超過 120 萬；土地房屋總值未超過 650 萬"]},
       "社會局頁「補助對象」：人均月收入未達最低生活費 1.5 倍"),
 903: ({"requiresChildUnder": 18, "requiredFlags": SCF + ["returning_to_education"], "uncheckedConditions": [
          "單親家長獨自扶養 18 歲以下子女（離婚／喪偶／未婚生子／配偶服刑／受暴分居等）；受暴單親須經社工轉介",
          "家長本人就讀高中職或大專並修習學位（不含學分班、碩博士班）",
          "家庭總收入人均未超過最低生活費 2.5 倍，且未超過臺灣地區平均消費支出 1.5 倍；存款本金限額",
          "未領取政府學費／學雜費補助或減免"]},
       "社會局頁「補助對象」"),
 904: ({"uncheckedConditions": [
          "設籍本市，經社會局家庭暴力及性侵害防治中心確定為家庭暴力被害人",
          "家庭總收入人均未超過最低生活費 2.5 倍及平均消費支出 1.5 倍；動產 1 口內 120 萬（每增 1 口加 18 萬）；不動產 650 萬"]},
       "社會局頁「服務對象」"),
 967: ({"requiresChildUnder": 13, "uncheckedConditions": [
          "300 億擴大租金補貼或高市增額租金補貼核定戶，或入住市府興建／國住都於高雄興辦之社會住宅",
          "育有 12 歲以下子女且為兩胎以上（兩胎、三胎以上級距不同）",
          "社宅住戶申請至 115/12/31 下午 5 時止；租補核定戶由都發局主動寄確認函"]},
       "市府新聞（育兒租金補貼 3.0）"),
}
conn = psycopg2.connect(dbname='welfare_check'); cur = conn.cursor()
cur.execute('select id, eligibility_conditions from benefits where id = any(%s)', (list(X),))
old = dict(cur.fetchall())
assert set(old) == set(X), set(X) - set(old)
for bid, (add, src) in X.items():
    ec = dict(old[bid] or {})
    assert ec.get('counties') == ['高雄市'], (bid, ec.get('counties'))
    ec.pop('_note', None)
    ec.update(add)
    ec['_source'] = f'W-020 {D} 依官方原文補條件：{src}'
    print(bid, json.dumps({k: v for k, v in ec.items() if k not in ('_source', 'referenceData')}, ensure_ascii=False)[:150])
    if '--apply' in sys.argv:
        cur.execute('update benefits set eligibility_conditions = %s, updated_at = now() where id = %s',
                    (json.dumps(ec, ensure_ascii=False), bid))
if '--apply' in sys.argv:
    conn.commit(); print('✅ 已寫入', len(X))
else:
    print('(dry-run)', len(X))
