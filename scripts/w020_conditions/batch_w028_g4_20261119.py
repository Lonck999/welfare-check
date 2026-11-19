"""W-028 第 4 組：新北市 22 筆（546…687、1000）中的 21 筆（588 FLAG 不在 X），依官方原文重編資格條件。
   2026-11-19 逐頁讀過正文：
   · service.ntpc.gov.tw「線上申辦-案件說明」頁、welfare.ntpc.gov.tw「福利補助自己查」頁：curl（瀏覽器 UA）讀得到全文
   · 553 衛生局 node=8765：curl 只拿到 57 字的 JS 轉址（location.href="/"），改用 web_extract 讀到全文
   · 560 原民局新聞頁 ＋ 附件《新北市政府補助原住民返鄉參加歲時祭儀交通費實施要點》.pdf（pypdf，820 字）
   原則（Lonck 已定案，同 W-020 B）：
   · 問卷問得到的 → 編成引擎條件；問不到的 → uncheckedConditions 原文照列（最高只能 possible）
   · 「符合其一」的 OR 條件 → 一律放 unchecked，不硬編成 AND
   · incomeThreshold 只在原文為「列冊低收／中低收」或「未達最低生活費 1.5 倍」時編
     （「領有／符合中低收入老人生活津貼資格」原文沒寫 1.5 倍 ⇒ 不編，放 unchecked）
   · requiredIdentities 只比對「本人」的問卷身分 ⇒ 受益人可能不是填問卷的人（學生、配偶、同戶家人）時，身分放 unchecked
   · 既有 otherConditions 一律搬到 `_otherConditions_orig`（原值保留）、刪掉 otherConditions；
     本組 21 筆的 otherConditions 全是「申請方式／地點／期限」，不是資格
   🔴 X 放的是**整份新的** eligibility_conditions（不是 add）；counties 保留原值並與 DB 比對
   用法：python batch_w028_g4_20261119.py [--apply]（預設 dry-run，不寫 DB）"""
import json, os, sys
from pathlib import Path
import psycopg2

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))   # scripts/
from eligibility_guard import assert_substantive

D = '2026-11-19'
NTPC = ['新北市']
SVC = '新北市政府線上申辦「案件說明」頁'
WEL = '新北市政府福利補助自己查「福利項目說明」頁'
IDS = [546, 553, 560, 567, 574, 581, 588, 596, 603, 610, 617, 624, 631, 638, 645, 652, 659, 666, 673, 680, 687, 1000]
FLAGGED = {588}   # 見 ~/.hermes/cache/welfare_w028_20261119/g4_report.md


def C(**kw):
    """整份新條件：counties 固定新北市，其餘照傳入"""
    return {"counties": NTPC, **kw}


X = {
 546: (C(uncheckedConditions=[
          "符合其一：遭受職場性騷擾之被害人（運用心理諮商）；或自然人雇主、登記設立之公私立機構／事業單位依性別平等工作法第 13 條第 2 項為被害人提供或轉介心理諮商",
          "115 年度受理時間 115/1/1～115/12/31"]),
       f"{SVC}（itemId=112074）「申請說明」「申請對象」「備註」"),
 553: (C(requiredFlags=["infertility_treatment_needed"], uncheckedConditions=[
          "至少一方具中華民國國籍之不孕夫妻，且妻年齡 44 歲（含）以下（以申請日之月份計算）",
          "經人工生殖機構施術醫師診斷為不孕夫妻，須接受體外受精（試管嬰兒）人工生殖技術，於國民健康署特約人工生殖機構施術",
          "補助次數：受術妻 39 歲以下每胎次最多 6 次；40～44 歲最多 3 次",
          "國民健康署已公告修正「不孕症試管嬰兒補助3.0方案」，115/9/1 起實施，以最新方案為準"]),
       "新北市衛生局「體外受精(俗稱試管嬰兒)人工生殖技術補助方案民眾申辦作業說明」頁「補助對象」「補助次數」；衛生局「人工生殖補助」頁（3.0 方案 115/9/1 起實施公告）"),
 560: (C(uncheckedConditions=[
          "符合其一：設籍新北市且具原住民族身分；或其同戶籍內共同生活之直系血親及配偶（同戶籍申請人不得超過 3 人）",
          "返鄉參加歲時祭儀，自祭儀日起 3 個月內向區公所申請（十二月份之祭儀須於次年 1/5 前），須附祭儀照片及邀請函／票根等證明",
          "每人每年限申請一次；已獲其他相同性質補助者不予補助"]),
       "原民局新聞「新北市政府辦理原住民返鄉參加歲時祭儀交通費補助簡化說明」壹、申請受理期間；附件《新北市政府補助原住民返鄉參加歲時祭儀交通費實施要點》第三、五、七、八點"),
 567: (C(uncheckedConditions=[
          "居住新北市之新住民（國人之配偶）本人，結婚後首次入境 6 個月內尚未加入全民健保前",
          "因突發意外或罹病，無使用健保、須自行負擔醫療費用",
          "自醫療補助原因發生後或醫療費用單據開立後 6 個月內，向本市任一戶政事務所申請；同一補助對象最高補助 5 萬元",
          "實施期間 109/1/1～119/12/31"]),
       "民政局「愛心大平台新住民關懷計畫」頁 一、實施時間；二、補助對象；三、補助標準 5；四、申請手續"),
 574: (C(requiredFlags=["has_disability_or_dementia_member"], uncheckedConditions=[
          "失能者經長期照顧管理中心評估，符合長期照顧服務請領資格（核定長照需要等級及給付額度）",
          "交通接送服務須失能評估等級 2 級以上；喘息服務須有照顧者事實；居家服務類於個案名下聘有外籍看護時不可使用"]),
       f"{WEL}（長期照顧服務3.0）「補助內容」「福利說明」2～4；同全國版 96 號用 has_disability_or_dementia_member"),
 581: (C(ageMax=29, uncheckedConditions=[
          "年滿 18 歲至 29 歲（畢業於高級中等學校者不受年滿 18 歲之限制）、未在學、有就業意願之本國籍青年",
          "初次跨域尋職：開立介紹卡推介就業前未曾參加勞工保險；親自向公立就業服務機構求職登記並經推介就業",
          "推介或就業地點與日常居住處所距離 30 公里以上；受僱於同一雇主連續就業滿 30 日",
          "搬遷／租屋／交通補助金須於事由發生日起 90 日內向就業當地公立就業服務機構申請"]),
       f"{WEL}（青年跨域就業促進補助）「福利說明」服務對象 1～5、「補助內容」"),
 596: (C(minResidencyMonths=4, uncheckedConditions=[
          "符合其一：年滿 20 歲具行為能力之原住民，或未滿 20 歲已結婚具行為能力之原住民；申請人係房屋所有權人或申請人之配偶具原住民身分",
          "建購住宅於取得建物次年度起算 3 年內，且不曾接受本府其他住宅補助（輔助購屋貸款不在此限）",
          "本人、配偶及共同生活之直系親屬均無其他自有住宅（房屋課稅現值依持分 10 萬元以下或原住宅遭災無法居住者視為無）；未接受安遷計畫或購買國宅／青年住宅",
          "房屋以興建或買賣（拍賣）取得，不得向直系親屬、配偶、兄弟姊妹購買；用途須為住宅／農舍或含「住」字樣並自用居住",
          "受理期間每年 3/1～4/30（115 年已截止，次年度再申請），評點選擇補助"]),
       f"{SVC}（itemId=117007）「申請說明」一～四、「申請對象」(一)～(三)、「備註」受理期間；設籍本市並實際居住 4 個月以上＝申請人本人"),
 603: (C(incomeThreshold="low_income", requiredFlags=["is_student"], uncheckedConditions=[
          "新北市列冊第二、三款低收入戶之未滿 25 歲學生",
          "高中（職）以上在學學生（不含空中大學、在職班、學分班、僅假日上課、遠距教學、安置身心障礙機構及在學公費生）",
          "每學期結束前檢具已註冊完成之學生證明文件向戶籍地區公所申請"]),
       f"{SVC}（itemId=110070）「申請說明」一：本府列冊二、三款未滿25歲低收入戶資格之高中（職）以上在學學生"),
 610: (C(requiredFlags=["occupational_injury"], uncheckedConditions=[
          "勞工因執行職務（或通勤災害）死亡（由家屬申請）、致失能第 1～15 等級，或因執行職務傷病住院連續 7 天以上",
          "設籍新北市勞工與非設籍本市勞工金額不同；非設籍本市勞工因通勤災害死亡者不發放",
          "須檢附勞工職災保險給付核定通知函影本等職業災害證明"]),
       f"{SVC}（itemId=112004）「申請說明」「申請對象」（設籍本市勞工／非設籍本市勞工）、「應備證件」三"),
 617: (C(ageMin=40, ageMax=74, uncheckedConditions=[
          "設籍新北市，符合其一：中低收入戶、低收入戶（含中低收入老人）、原住民或身心障礙者",
          "自 114/10/1 起經預防保健糞便潛血檢查為有效陽性個案，並以無痛大腸鏡檢查完成確診（每案上限 5,000 元）"]),
       "新北市衛生局「提供中低、低收入戶、原住民或身心障礙者無痛大腸鏡費用服務」頁 二、服務對象：設籍本市40歲至未滿75歲"),
 624: (C(requiresChildUnder=5, uncheckedConditions=[
          "幼兒設籍新北市，學齡於當年度 9/1 為 2 歲以上未滿 5 歲",
          "符合其一：低收入戶、中低收入戶、弱勢兒少、特殊境遇家庭或寄養家庭之身分",
          "就讀本市立案私立幼兒園（不含準公共及非營利幼兒園），依當學期開辦公文時程向幼兒園申請"]),
       f"{SVC}（itemId=105040）「申請說明」"),
 631: (C(uncheckedConditions=[
          "設籍新北市，符合其一：12 歲以下身心障礙或發展遲緩兒童（身障手冊或一年內早期療育評估報告書）；12 至未滿 65 歲中低收入戶身心障礙者；12 至未滿 60 歲低收入戶身心障礙者",
          "至衛生局特約機構就診，由特約機構向衛生局申請治療補助費用"]),
       f"{SVC}（itemId=124054）「應備證件」補助對象(一)(二)、「申請方式」"),
 638: (C(requiredFlags=["is_student"], uncheckedConditions=[
          "學生具原住民身分，並設籍新北市滿 6 個月以上之高級中等以上學校在學學生",
          "未領有其他政府機關及公營事業單位之獎助學金；當學期（前一學期）無記過以上處分",
          "學業優秀獎學金：公私立高中職／大專成績總平均 75 分以上（低收入戶 60 分以上）、研究所 80 分以上，一年級新生不得申請；升學獎學金：升入高中職／五專或考取大專（附設進修學校學生不得申請）"]),
       f"{SVC}（itemId=105001）「申請說明」一、申請資格 1～3；二、申請標準"),
 645: (C(requiredFlags=["disability_certificate"], ageMin=18, uncheckedConditions=[
          "設籍新北市且年滿 18 歲以上之身心障礙者（不足名額依比例開放外縣市身障者）",
          "親自向各分校承辦單位報名，春季班 2～3 月、秋季班 8～9 月，額滿為止；中低收入戶／領身障生活補助者報名費折半、低收入戶免費"]),
       "新北市社會局「身心障礙者福利」新北市身心障礙者樂活大學頁「申請對象、報名方式與期間」"),
 652: (C(requiredFlags=["pregnant_or_recent_birth"], uncheckedConditions=[
          "懷孕中之孕婦（須附孕婦健康手冊含預產日期頁或 1 個月內診斷證明），產後不適用",
          "符合其一：孕婦本人設籍新北市；或與設籍本市市民辦理結婚登記之非本國籍孕婦"]),
       f"{SVC}（itemId=110071）「申請說明」「應備證件」(一)"),
 659: (C(ageMin=65, uncheckedConditions=[
          "設籍並實際居住新北市，經審查符合本府中低收入老人生活津貼領取資格",
          "最近 3 個月內罹患嚴重傷病住院治療；無家屬可提供照顧或家屬無力照顧，經醫師證明須僱請專人看護且有照顧事實（不含加護病房、長期慢性病療養及呼吸治療中心）",
          "未僱請外籍看護工；未領有中低收入老人特別照顧津貼",
          "醫療看護行為結束日起 3 個月內向戶籍地區公所申請"]),
       f"{SVC}（itemId=110051）「申請說明」二、申請對象（一）～（三）、「申請方式」；年齡依中低收入老人生活津貼資格（年滿 65 歲，見 666 同站頁）"),
 666: (C(ageMin=65, incomeThreshold="mid_low_income", uncheckedConditions=[
          "設籍並實際居住於新北市，且最近一年居住國內超過 183 日",
          "家庭總收入人均每月未超過最低生活費 1.5 倍（115 年 26,625 元），且未超過臺灣地區平均每人每月消費支出 1.5 倍（39,960 元）",
          "全家人口存款本金、投資及有價證券合計：僅申請人 1 人時未超過 250 萬元，每增加 1 人增加 25 萬元",
          "全家人口所有之土地或房屋未超過合理價值（115 年度 708 萬元）",
          "未接受政府公費收容安置；未入獄服刑、因案羈押或依法拘禁"]),
       f"{SVC}（itemId=110027）「申請說明」申請對象一～四：家庭總收入每人每月未超過最低生活費標準之1.5倍"),
 673: (C(ageMin=65, uncheckedConditions=[
          "領有新北市中低收入老人生活津貼",
          "實際居住修繕房屋滿 6 個月（居住公有宿舍、出租國宅、社福／護理機構、榮民之家或違章建築者不予補助）；非自有房屋須所有權人修繕及 3 年以上使用同意書或經公證 3 年以上租約",
          "申請人或修繕房屋 3 年內未接受本補助或低收入戶住宅興修建補助",
          "核定函送達後始可施工，最高補助 5 萬元"]),
       f"{SVC}（itemId=110006）「申請說明」二、補助對象 1～3、「應備證件」五"),
 680: (C(requiredFlags=["disability_certificate"], ageMin=16, ageMax=65, minResidencyMonths=6, uncheckedConditions=[
          "自行報名參加職業訓練課程之身心障礙者（職訓機構／汽車駕駛人訓練機構／立案補習班）",
          "須先經本府各職業重建服務中心評估後始得報名繳費，並於課程開訓後 2 星期內申請（課程短於 2 星期者應於結訓前）"]),
       f"{SVC}（itemId=112019）「申請對象」：設籍本市6個月以上，年滿16至65歲，自行報名參加職業訓練課程之身心障礙者；「申請期限」"),
 687: (C(uncheckedConditions=[
          "軍公教人員因作戰、因公、因病或意外死亡，其婚生子女、養子女（或無子女者之同胞弟妹）",
          "就讀新北市所屬公私立高中職及國民中小學；由學校初審後提出申請，每學年辦理二次",
          "同時符合其他政府教育補助優待者僅能擇一；公營事業機關人員遺族不適用"]),
       f"{SVC}（itemId=105021）「申請說明」（一）（二）、「備註」（二）（八）"),
 1000: (C(requiresChildUnder=16, uncheckedConditions=[
          "家中有就讀新北市公私立國民中小學之學生（學生無須另外申請，由學校於上課日提供免費午餐）"]),
       f"{WEL}（免費營養午餐）「福利說明」：就讀本市公私立國民中小學學生；「申請方式」學生無須另外辦理申請作業"),
}
# SKIP（不在 X）：588 FLAG（社區大學＝一般民眾終身學習課程，不是福利）

assert set(X) | FLAGGED == set(IDS) and not (set(X) & FLAGGED), '範圍不符'


def db_url():
    if os.environ.get('DATABASE_URL'):
        return os.environ['DATABASE_URL']
    env = Path(__file__).resolve().parents[2] / 'backend' / '.env'
    for line in env.read_text().splitlines():
        if line.startswith('DATABASE_URL='):
            return line.split('=', 1)[1].strip().strip('"\'')
    raise SystemExit('找不到 DATABASE_URL')


conn = psycopg2.connect(db_url()); cur = conn.cursor()
cur.execute('select id, name, eligibility_conditions from benefits where id = any(%s)', (list(X),))
rows = {r[0]: (r[1], r[2]) for r in cur.fetchall()}
assert set(rows) == set(X), set(X) - set(rows)

new = {}
for bid, (cond, src) in X.items():
    name, old = rows[bid]
    old = old or {}
    assert old.get('counties') == cond['counties'], (bid, old.get('counties'))
    ec = dict(cond)
    # 既有的不檢查鍵：原值搬到 _ 開頭鍵保留（本組只有 otherConditions）
    for k in ('otherConditions', 'incomeMonthlyMax', 'movableAssetsMax', 'realEstateMax'):
        if k in old:
            ec[f'_{k}_orig'] = old[k]
    assert 'otherConditions' not in ec
    # 舊條件裡其他鍵（若有）一律要被 X 明確處理，不可默默丟掉
    leftover = set(old) - {'counties', 'otherConditions', 'incomeMonthlyMax', 'movableAssetsMax', 'realEstateMax'}
    assert not leftover, (bid, leftover)
    ec['_source'] = f'W-028 {D} 依官方原文重編條件（otherConditions 為申請方式，已搬到 _otherConditions_orig）：{src}'
    assert_substantive(ec, label=f'新北市｜{bid} {name}')
    new[bid] = ec
    print(bid, name, json.dumps({k: v for k, v in ec.items() if not k.startswith('_')}, ensure_ascii=False)[:160])

if '--apply' in sys.argv:
    cur.execute('create table benefits_before_w028_g4_20261119 as select * from benefits where id = any(%s)', (list(X),))
    for bid, ec in new.items():
        cur.execute('update benefits set eligibility_conditions = %s, updated_at = now() where id = %s',
                    (json.dumps(ec, ensure_ascii=False), bid))
    conn.commit(); print('✅ 已寫入', len(new), '（備份表 benefits_before_w028_g4_20261119）')
else:
    conn.rollback(); print('(dry-run) 全部通過 assert_substantive，未寫入：', len(new), '筆；FLAG 不在 X：', sorted(FLAGGED))
