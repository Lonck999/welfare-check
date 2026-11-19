"""W-028 第 g10 批：新竹市／澎湖縣／臺中市／臺北市／臺南市 18 筆中的 17 筆（350 列 FLAG 不在 X），
   依官方原文替「只有引擎不檢查的鍵」的福利補條件。
   2026-11-19 逐頁讀過正文：
   · 臺南市社會局（sab.tainan.gov.tw）curl 拿到的 HTML 正文是 JS 載入 ⇒ 用 web_extract 讀到全文；
     532 讀 source_url 的 PDF《臺南市特殊境遇家庭扶助項目及內容》（pypdf，md5 與上一輪快取一致）
   · 519 source_url 是「114 年 0121 地震」扶助措施專頁 ⇒ 另搜「臺南市 115年度 天然災害補助」，
     找到社會局「天然災害救助」頁（115-02-11 修改）＋《臺南市災害救助辦法》（114-12-17 發布），依後者編
   · 臺中市社會局 732、738 web_extract 回 504 ⇒ 用上一輪 curl 快取（og:url 對得上 461550／461554）
   · 753 新竹市讀 source_url PDF《新竹市低收入戶學生助學金補助原則》（104.12.24 修正）
   原則（Lonck 已定案）：
   · 問卷問得到的 → 引擎條件；問不到的 → uncheckedConditions 原文照列（最高只能 possible）
   · 「符合其一」的 OR 條件 → 放 unchecked，不硬編成 AND
   · incomeThreshold 只在原文為「列冊低收／中低收」時編（特境「消費支出 1.5 倍」不編）
   · minResidencyMonths 只編申請人本人（959「本人(或配偶)」→ 拿掉，改放 unchecked）
   · 既有的不檢查鍵（otherConditions／incomeMonthlyMax／movableAssetsMax／realEstateMax／_note）
     搬到 `_<鍵>_orig` 保留原值（_note 直接刪，同 W-020 範本）
   用法：python batch_w028_g10_20261119.py [--apply]（預設 dry-run，不寫 DB）"""
import json, os, sys
import psycopg2

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from eligibility_guard import assert_substantive  # noqa: E402

D = '2026-11-19'
TN = ['臺南市']
TC = ['臺中市']
SCF = ['special_circumstance_family']
AH = ['acute_hardship']
TN_LOW_ORIG = {"_realEstateMax_orig": 3500000, "_incomeMonthlyMax_orig": 12389, "_movableAssetsMax_orig": 75000}
TN_SCF_ORIG = {"_realEstateMax_orig": 6500000, "_incomeMonthlyMax_orig": 30970, "_movableAssetsMax_orig": 371640}
TN_SCF_MONEY = ("家庭總收入按全家人口平均分配，每人每月未超過政府當年公布每月消費支出 1.5 倍（114 年度 38,589 元），"
                "且動產平均每人不超過 465,460 元、不動產全戶不超過 650 萬元")
TN_SCF_RES = "設籍臺南市，並實際居住國內超過 183 日（初次申請者不受居住期限限制）"
TN_JIJIU = '急難事由生活陷困者'
SAB = '臺南市社會局'
TCSOC = '臺中市社會局「老人福利」'

X = {
 # ─────────────── 新竹市 ───────────────
 753: ({"counties": ["新竹市"], "incomeThreshold": "low_income", "ageMax": 25, "requiredFlags": ["is_student"],
        "uncheckedConditions": [
          "列冊低收入戶，持有新竹市區公所核發之低收入戶證明書",
          "25 歲（含）以下，持續於國內公私立大專院校、高中職校或新竹市公立國民中小學在學；重讀、延修或新轉系降讀者不補助",
          "申請期限：第一學期 10/1～10/25、第二學期 3/10～3/31（逾期不受理），送交各里里幹事"],
        "_otherConditions_orig": "1.列冊低收入戶持有本市區公所所核發之低收入戶證明書者。2.年滿25歲(含)以下並持續於國內公私立大專院校、高中職校及本市公立國民中小學在學之低收入戶學生;重讀、延修或新轉系降讀之學生，不予補助。"},
       "新竹市《低收入戶學生助學金補助原則》（104.12.24 修正）二、補助對象（一）（二）；四、申請期限"),
 # ─────────────── 澎湖縣 ───────────────
 942: ({"counties": ["澎湖縣"], "minResidencyMonths": 36, "requiredFlags": ["disability_certificate"],
        "uncheckedConditions": [
          "以發放節日當日之前 90 日為基準，領有澎湖縣核（換、補）發之身心障礙證明",
          "申請人或代理人至縣府提出申請（身障證明影本、金融機構帳戶封面影本、領據）"]},
       "澎湖縣社會處「身心障礙者三節慰問金發放作業要點」（112-03-16 府社福字第1121202945號）發放對象：設籍滿三年之本縣縣民、且以發放節日當日之前九十日為基準，領有本縣核（換、補）發身心障礙證明者"),
 # ─────────────── 臺中市 ───────────────
 732: ({"counties": TC, "requiredFlags": ["severe_disability_or_dementia"],
        "uncheckedConditions": [
          "受照顧者：領有中低收入老人生活津貼；未接受機構收容安置、居家服務、未僱看護（傭）、未領政府日間照顧或其他照顧服務補助；日常生活活動功能量表評估重度以上且實際由家人照顧；實際居住於戶籍所在地",
          "照顧者：年滿 16 歲未滿 65 歲，無社會救助法第 5 條之 3 第 1～3、6、7 款情事；屬同為中低收入老人生活津貼應計算人口、出嫁女兒／入贅子及其配偶、或受照顧者二親等內直系血親卑親屬之一",
          "照顧者未從事全時工作且實際負責照顧，與受照顧者設籍及實際居住於同一直轄市、縣（市）",
          "向受照顧者戶籍地區公所申請"],
        "_otherConditions_orig": "◎受照顧者應符合下列規定：1.領有中低收入老人生活津貼。2.未接受機構收容安置、居家服務、未僱用看護（傭）、未領有政府提供之日間照顧服務補助或其他照顧服務補助。3.失能程度經日常生活活動功能量表評估為重度以上，且實際由家人照顧。4.實際居住於戶籍所在地。◎照顧者應符合下列規定：1.年滿十六歲，未滿六十五歲，且無社會救助法第五條之三第一款至第三款、第六款及第七款規定之情事。2.屬下列情形之一者：　a.同為領取中低收入老人生活津貼應計算家庭總收入全家人口之成員。　b.出嫁之女兒或子為他人贅夫者及其配偶。　c.受照顧者二親等以內之直系血親卑親屬。3.未從事全時工作，且實際負責照顧受照顧者。"},
       f"{TCSOC}「中低收入老人特別照顧津貼」頁「對象、標準」◎受照顧者 1～4、◎照顧者 1～4"),
 734: ({"counties": TC,
        "uncheckedConditions": [
          "符合其一：實際居住臺中市之獨居老人；或未獲市府各單位同性質住屋修繕補助之臺中市弱勢民眾",
          "不符「臺中市中低收入老人修繕住屋補助辦法」及「老人及身心障礙者居家無障礙環境改善」補助規定者",
          "修繕住屋須在臺中市且申請人實際居住；須經本計畫協助修繕之民間團體評估及社會局核定後才修繕；同案 3 年內不得重複申請",
          "建築物非申請人所有者，須附所有權人修繕同意書；向各區公所申請"],
        "_otherConditions_orig": "不符「臺中市中低收入老人修繕住屋補助辦法」及「老人及身心障礙者居家無障礙環境改善」補助相關規定且實際居住本市之獨居老人暨未獲本府各單位同性質住屋修繕補助之本市弱勢民眾。"},
       f"{TCSOC}「空間行善者-獨居銀髮族暨弱勢民眾住屋愛心修繕補助」頁「對象、標準」「原則、金額」3.不予補助情形"),
 738: ({"counties": TC, "ageMin": 65, "incomeThreshold": "mid_low_income",
        "uncheckedConditions": [
          "設籍並實際居住臺中市之 65 歲以上老人，具低收入戶或中低收入戶資格",
          "因精神障礙或其他心智缺陷，有辦理監護或輔助宣告之需",
          "補助對象於法院指定醫院鑑定後 6 個月內，由聲請監護宣告之人或民間團體向社會局長青福利科申請"],
        "_otherConditions_orig": "1.設籍並實際居住臺中市之65歲以上老人2.具低收入戶或中低收入戶資格3.因精神障礙或其他心智缺陷，有辦理監護或輔助宣告之需。"},
       f"{TCSOC}「老人聲請監護輔助宣告費用補助」頁「對象、標準」：設籍並實際居住臺中市之65歲以上老人、具低收入戶或中低收入戶資格"),
 745: ({"counties": TC, "ageMin": 65, "ageMinByIdentity": {"原住民": 55},
        "uncheckedConditions": [
          "115 年：於 50/12/31 前（原住民 60/12/31 前）出生，且於 115/8/27 前設籍臺中市",
          "115/8/27 前亡故或失蹤仍未除籍者、因出境未能於發放期間完成領取者不發放",
          "115 年辦理期間 9/30～10/19；期限內未領取並經區公所通知者得延長至 115/11/30，逾期不得領取"],
        "_otherConditions_orig": "一、凡於48年12月31日前(原住民58年12月31日前)出生，且於113年8月20日前設籍本市，65歲以上之長者及55歲以上原住民皆可致贈重陽節敬老禮金，但有下列情形之一者，不予發放:(一)113年8月20日前亡故或失蹤仍未除籍者。(二)因出境未能於發放期間完成領取手續者。二、辦理時間：自113年9月19日起至113年10月11日止。期限內未領取並經各區公所通知者，得延長期限至113年11月30日，逾期不得領取。"},
       f"{TCSOC}「臺中市重陽節敬老禮金」頁 一、發放對象：設籍本市之 65 歲以上長者（原住民 55 歲以上）＋115 年發放對象、辦理期間"),
 959: ({"counties": TC, "ageMax": 45,
        "uncheckedConditions": [
          "申請人本人（或配偶）設籍臺中市 6 個月（含）以上",
          "經專科醫師認定罹癌，預計經化學、放射或賀爾蒙藥物等治療而可能影響生育功能（須診斷證明），且凍卵／凍精療程於癌症治療前",
          "當年度取卵、凍卵及凍精療程未申請衛福部試管嬰兒補助、醫療性生育保存補助或其他縣市公費補助；曾受本補助者不再補助（終身 1 次）",
          "療程結束後 6 個月內向衛生局申請；115 年最遲 115/11/30 前送達（12/1 後以 116 年度經費支應）"],
        "_minResidencyMonths_orig": 6},
       "臺中市衛生局「115年時來孕轉-幸福臺中凍卵凍精補助計畫」一、補助對象資格（均需符合）（一）～（五）、五、申請文件（三）；（一）原文為「本人(或配偶)設籍」⇒ 不編 minResidencyMonths"),
 # ─────────────── 臺南市 ───────────────
 501: ({"counties": TN, "incomeThreshold": "low_income",
        "uncheckedConditions": [
          "臺南市列冊之低收入戶（第一款每人每月 11,918 元、第二款每戶每月 6,825 元）",
          "由社會局逕撥入低收入戶指定之郵政（農會）帳戶；洽戶籍所在地區公所社會（政）課"],
        "_otherConditions_orig": "經濟狀況不佳致生活陷於困境者", **TN_LOW_ORIG},
       f"{SAB}「低收入戶家庭生活補助」頁 六、服務內容；七、服務對象：本市列冊之低收入戶"),
 509: ({"counties": TN, "requiredFlags": AH,
        "uncheckedConditions": [
          "臺南市市民戶內人口遭受意外傷害或罹患重病致生活陷於困境",
          "出院或就醫後 3 個月內向戶籍所在地區公所申請；同一事由 3 個月內不得重複申請"],
        "_otherConditions_orig": TN_JIJIU},
       f"{SAB}「臺南市急難救助－傷病救助」頁 六、服務內容；七、服務對象；八、應備文件"),
 510: ({"counties": TN, "requiredFlags": AH,
        "uncheckedConditions": [
          "符合其一：戶內人口遭受意外傷害或罹患重病致生活陷於困境；戶內人口死亡無力殮葬；負家庭主要生計責任者失業、失蹤、服役、服刑、羈押、拘禁等無法工作致生活陷困；財產或存款帳戶遭強制執行、凍結致生活陷困；已申請福利或保險給付尚未核准期間生活陷困；其他重大變故經區公所訪視評估確有救助需要",
          "向戶籍所在地區公所社會（政）課申請"],
        "_otherConditions_orig": TN_JIJIU},
       f"{SAB}常見問答「如何申請急難救助?甚麼情形可以申請急難救助?」（二）急難救助協助對象 1～6"),
 511: ({"counties": TN,
        "uncheckedConditions": [
          "符合其一：臺南市市民在他縣（市）獲得職業，缺乏車費無法前往報到；或行旅臺南市之他縣（市）民缺乏車資無法返鄉",
          "檢具身分證明或就職通知單至社會局或指定派出所辦理乘車換票證；3 個月內不得重複申請"],
        "_otherConditions_orig": TN_JIJIU},
       f"{SAB}「臺南市急難救助－行旅川資救助」頁 七、服務對象；八、申請程序"),
 512: ({"counties": TN,
        "uncheckedConditions": [
          "臺南市市民戶內人口死亡無力殮葬",
          "戶內人口死亡後 3 個月內向戶籍所在地區公所申請；同一事由 3 個月內不得重複申請"],
        "_otherConditions_orig": TN_JIJIU},
       f"{SAB}「臺南市急難救助－喪葬救助」頁 六、服務內容；七、服務對象；八、應備文件"),
 513: ({"counties": TN, "requiredFlags": AH,
        "uncheckedConditions": [
          "符合其一：家庭成員死亡、失蹤或罹患重傷病、失業或其他原因無法工作致家庭生活陷困；因經濟性因素致自殺通報個案；因經濟性因素經通報為脆弱家庭成員；遭家暴／性侵害經通報或庇護安置、緊急生活扶助金尚未核發期間生活陷困；經通報家暴、核發保護令或結束監護處分因經濟因素暫無居所；申請福利尚未核准期間生活陷困；其他遭逢變故致家庭生活陷困",
          "急難事由以最近 3 個月內發生者，同一事由以申請一次為限；向現居地區公所社會（政）課申請"],
        "_otherConditions_orig": TN_JIJIU, "_realEstateMax_orig": 5250000},
       f"{SAB}「強化社會安全網-急難紓困實施方案」頁 六、救助對象（一）～（七）；七、申請期限"),
 519: ({"counties": TN, "requiredFlags": ["recent_natural_disaster_damage"],
        "uncheckedConditions": [
          "本國國民於臺南市轄區內遭受水、火、雹、風、旱、地震或其他災害，致損害重大影響生活",
          "符合其一：因災害死亡或失蹤（死亡／失蹤救助）；因災重傷或住院 15 日內自負醫療費達 10 萬元（重傷救助）；住屋毀損達不堪居住程度（安遷救助，災害發生時須已在現址設籍並實際居住）；住屋淹水達 50 公分以上（淹水救助）；住屋土石流入侵達 30 公分以上或面積達 1/2（土石流救助）",
          "災害發生後 30 日內向災害發生地區公所申請（災情嚴重時得公告延長）"],
        "_otherConditions_orig": TN_JIJIU},
       "source_url 為臺南市政府「114 年 0121 地震 扶（協）助措施」專頁（多項已過受理期）⇒ 依現行 "
       f"{SAB}「天然災害救助」頁（115-02-11 修改）＋《臺南市災害救助辦法》（114-12-17 發布）第三、四、五、八條"),
 529: ({"counties": TN, "requiredFlags": SCF,
        "uncheckedConditions": [
          TN_SCF_RES, TN_SCF_MONEY,
          "符合特殊境遇家庭扶助條例第 4 條第 1 項第 3 款（家庭暴力受害者），無力負擔訴訟費用",
          "訴訟事實發生 3 個月內向戶籍所在地區公所申請；補助最高 5 萬元"],
        **TN_SCF_ORIG},
       f"{SAB}「特殊境遇家庭法律訴訟補助」頁 六、服務內容說明；七、服務對象"),
 530: ({"counties": TN,
        "uncheckedConditions": [
          TN_SCF_RES, TN_SCF_MONEY,
          "符合其一：65 歲以下配偶死亡或失蹤協尋未獲達 6 個月；因配偶惡意遺棄或不堪同居之虐待經判決離婚或協議離婚；家庭暴力受害者；未婚懷孕婦女懷胎 3 個月以上至分娩 2 個月內；因離婚、喪偶、未婚生子獨自扶養 18 歲以下子女或孫子女且無工作能力或因重大傷病／照顧 6 歲以下子女致不能工作；配偶處 1 年以上徒刑或保安處分執行中；經市府評估 3 個月內生活發生重大變故（非因個人責任、債務、自願性失業）",
          "應於各款情形發生後 6 個月內向戶籍所在地區公所申請；每人同一事由以補助一次為限"],
        **TN_SCF_ORIG},
       f"{SAB}「特殊境遇家庭緊急生活扶助」頁 六、服務內容說明；七、申請期限；八、服務對象（一）～（七）"),
 532: ({"counties": TN,
        "uncheckedConditions": [
          "申請人及其子女須設籍並實際居住臺南市（與本市市民結婚之新住民未取得國籍前不受設籍限制）",
          "符合特殊境遇家庭第 1～7 款之一（配偶死亡失蹤／惡意遺棄或受虐離婚／家暴受害／未婚懷孕／獨自扶養子女無法工作／配偶服刑／經評估重大變故）",
          "家庭收入及財產須符合特殊境遇家庭標準（社會局特境頁：人均每月未超過消費支出 1.5 倍、動產每人 465,460 元、不動產 650 萬元）",
          "須參加全民健保：未滿 6 歲子女或孫子女補助自付醫療費；申請人及 6～未滿 18 歲子女或孫子女自付醫療費超過 3 萬元部分最高補助 70%，每人每年最高 12 萬元",
          "傷病發生後 3 個月內向戶籍所在地區公所申請"],
        **TN_SCF_ORIG},
       "臺南市社會局 PDF《臺南市特殊境遇家庭扶助項目及內容》一、補助對象（一）（二）；二、補助項目「特殊境遇家庭傷病醫療補助」列（財產標準引自同局「特殊境遇家庭緊急生活扶助」頁八、服務對象）"),
}
# SKIP（不在 X）：350 FLAG —— 見 ~/.hermes/cache/welfare_w028_20261119/g10_report.md
ALL_IDS = [753, 942, 732, 734, 738, 745, 959, 350, 501, 509, 510, 511, 512, 513, 519, 529, 530, 532]
FLAGGED = {350}
assert set(X) | FLAGGED == set(ALL_IDS) and not (set(X) & FLAGGED)

conn = psycopg2.connect(os.environ['DATABASE_URL']); cur = conn.cursor()
cur.execute('select id, name, eligibility_conditions from benefits where id = any(%s)', (list(X),))
rows = {r[0]: (r[1], r[2]) for r in cur.fetchall()}
assert set(rows) == set(X), set(X) - set(rows)
out = {}
for bid, (new, src) in X.items():
    name, old = rows[bid]
    old = dict(old or {})
    ec = json.loads(json.dumps(new, ensure_ascii=False))
    assert ec.get('counties') == old.get('counties'), (bid, ec.get('counties'), old.get('counties'))
    # 舊鍵一個都不能默默消失：保留原名、或搬到 _<鍵>_orig 且值相同（_note 依範本可刪）
    for k, v in old.items():
        if k in ec or k == '_note':
            continue
        assert ec.get(f'_{k}_orig') == v, (bid, k, v, ec.get(f'_{k}_orig'))
    for dead in ('otherConditions', 'incomeMonthlyMax', 'movableAssetsMax', 'realEstateMax', '_note'):
        assert dead not in ec, (bid, dead)
    ec['_source'] = f'W-028 {D} 依官方原文補條件：{src}'
    assert_substantive(ec, label=f'{bid}｜{name}')
    out[bid] = ec
    print(bid, name, json.dumps({k: v for k, v in ec.items() if not k.startswith('_')}, ensure_ascii=False)[:160])

if '--apply' in sys.argv:
    cur.execute('create table benefits_before_w028_g10_20261119 as select * from benefits where id = any(%s)', (list(X),))
    for bid, ec in out.items():
        cur.execute('update benefits set eligibility_conditions = %s, updated_at = now() where id = %s',
                    (json.dumps(ec, ensure_ascii=False), bid))
    conn.commit(); print('✅ 已寫入', len(out))
else:
    conn.rollback(); print('(dry-run) 全部通過 assert_substantive／counties／舊鍵保留檢查：', len(out), '筆；FLAG 不寫：', sorted(FLAGGED))
