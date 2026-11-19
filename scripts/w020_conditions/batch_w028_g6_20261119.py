"""W-028 第 6 組：新北市 22 筆中的 20 筆（576、591 FLAG 不在 X），依官方原文重編資格條件。
   2026-11-19 逐頁讀過 source_url 正文（curl＋瀏覽器 UA；583 原網址是 JS 轉址，讀的是轉址後的衛生局文章頁）。
   這批 20 筆的 `otherConditions` **全部是申請方式／地點／文件**（「郵寄或親送」「區公所申請」「隨到隨辦」…），
   不是資格 ⇒ 原值一律搬到 `_otherConditions_orig`（引擎不讀 `_` 開頭鍵、不再列進「還缺」），資格另依原文編。
   原則同 W-020 B：
   · 問卷問得到的 → 編成引擎條件；問不到的 → uncheckedConditions 原文照列（最高只能 possible）
   · 「符合其一」的 OR 條件 → 一律放 unchecked，不硬編成 AND
   · incomeThreshold 只在原文為「列冊低收／中低收」或「未達最低生活費 1.5 倍」時編
   · minResidencyMonths 只編申請人本人設籍滿 N（612「101/7/31 前設籍滿 1 年」是固定日期 ⇒ 不編）
   🔴 X 放的是**整份新的** eligibility_conditions（不是 add）；counties 保留原值並與 DB 比對。
   用法：python batch_w028_g6_20261119.py [--apply]（預設 dry-run，不寫 DB）"""
import json, os, sys
import psycopg2

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from eligibility_guard import assert_substantive  # noqa: E402

D = '2026-11-19'
NTPC = ['新北市']
SVC = '新北市政府申辦E服務「案件說明」頁'
WEL = '新北市政府「福利補助自己查」福利項目說明頁'
BACKUP = 'benefits_before_w028_g6_20261119'

# DB 現有 otherConditions 原值（全部是申請方式，不是資格）—— 寫入前逐字比對 DB
ORIG = {
 548: '符合資格民眾至本市29區衛生所辦理接種。',
 555: '郵寄、臨櫃及線上申辦至戶籍所在地之區公所辦理。',
 562: '懷孕4個月到生產前1個月，請備妥孕婦健康手冊、身分證明及相關福利核定文件，向「新北市弱勢家庭坐月子到宅服務平台」(社團法人台灣婦女展業協會)申請，服務專線：(02)8951-5868。',
 569: '民眾申請',
 583: '自行至本市合作醫療院所就診，由該機構向本府衛生局提出申請，由衛生局直接撥款予申請機構。',
 598: '一、每年申請日期由本府另公告之。\r\n二、申請人於備妥應備文件後得向戶籍所在地之區公所提出申請，各區公所受理申請案件後，應依本計畫就申請人資格及應備文件內容完成初審，如文件不齊全應通知限期補正，完成初審作業再轉送本府複審。\r\n三、本府受理申請案後應於三十日內完成核定，並以書面通知申請人。\r\n四、申請人對核定結果有異議時，得於收到核定通知書後檢附相關證明文件向戶籍所在地之區公所提出申覆。\r\n五、各區公所應於每年年底前通知申請人提具相關資料申請複查下年度資格，合於規定者得予繼續補貼。',
 605: '於取餐之超商(7-11、全家、萊爾富、OK)或八方雲集、梁社漢排骨、鬍鬚張魯肉飯、十八王公劉家肉粽及石門區集馨村便當求填寫個人基本資料',
 612: '臨櫃，郵寄',
 619: '符合補助條件之孕婦持身分證明文件至醫療院所，直接由醫療院所從自行負擔之費用中扣除補助費用，民眾無須額外進行補助費用申請。',
 626: '若學校有開班，可向就讀學校提出申請。',
 633: '書面。',
 640: '家長持相關證明文件向幼兒就讀之幼兒園提出申請。',
 647: '向戶籍所在地區公所社會課或社會人文課提出申請。',
 654: '隨到隨辦',
 661: '向各區公所社會課或社會人文課提出申請，經各區公所初審及本府社會局社工人員往訪評估後核定。',
 668: '向各區公所社會課或社會人文課提出申請。',
 675: '1.至本市境內各區公所提出申請，送府審核。\n2.經本府長期照顧管理中心各分站之評估人員作失能評估。',
 682: '匯款',
 689: '區公所申請。',
 1002: '郵寄或親送',
}


def C(bid, **cond):
    """整份新的條件：counties 原值＋原文條件＋otherConditions 原值搬到 _otherConditions_orig"""
    return {'counties': NTPC, **cond, '_otherConditions_orig': ORIG[bid]}


X = {
 548: (C(548, incomeThreshold='mid_low_income', requiresChildUnder=7, uncheckedConditions=[
          '設籍新北市之低收或中低收入戶嬰幼兒（須持有效期內低收／中低收入戶證明）',
          '年齡滿 2 個月至 6 歲（接種年－出生年≦6 歲）；第 1～3 劑接種時年齡均須符合，超過年齡無法補接種']),
       '新莊區衛生所「高端腸病毒A71型疫苗-新北市公費(自114年5月14日起實施)」一、接種資格：需同時具備設籍新北市、低收或中低收入戶、年齡滿 2 個月至 6 歲三項'),
 555: (C(555, requiredIdentities=['原住民'], minResidencyMonths=4, uncheckedConditions=[
          '年滿 20 歲具行為能力之原住民，或未滿 20 歲已結婚而具行為能力之原住民',
          '設籍新北市並實際居住 4 個月以上',
          '申請人係房屋所有權人或申請人之配偶具原住民身分',
          '自用住宅屋齡超過 7 年且因老舊或設備損壞（遭受火災或天然災害者不在此限）',
          '全家人口均無其他自有住宅，且近 5 年內不曾接受本要點補助',
          '受理期間每年 3/1～4/30，5/31 前通知評選結果']),
       f'{SVC}「原住民修繕住宅補助(申請階段)」申請說明一、二＋申請對象＋備註受理期間'),
 562: (C(562, requiredFlags=['pregnant_or_recent_birth'], uncheckedConditions=[
          '申請者為新生兒之母或父，設籍並實際居住新北市（含原住民）',
          '符合其一：列冊低收入戶、列冊中低收入戶、孕婦或其配偶領有本市身心障礙證明、符合特殊境遇家庭扶助、領有弱勢兒少生活扶助（孕婦為監護人）、符合設籍前新住民社會救助；或其他經社工訪視評估有實際需求者',
          '懷孕 4 個月到生產前 1 個月向「新北市弱勢家庭坐月子到宅服務平台」申請']),
       f'{WEL}「新北市弱勢家庭坐月子到宅服務」福利說明「服務對象」(1)(2)＋申請方式'),
 569: (C(569, uncheckedConditions=[
          '符合其一：使用人符合身心障礙資格、為低收入戶、或領有中低收入老人生活津貼',
          '使用市有基（房）地並設籍於該地上房屋作自用住宅使用',
          '使用人已繳清 5 年使用補償金']),
       f'{WEL}「低收入戶、中低收入老人或身心障礙使用市有基地使用補償金減免」福利說明一、二'),
 583: (C(583, uncheckedConditions=[
          '具健保身分，且非執行法律規定之酒癮治療（如緩刑附帶條件、禁戒處分、緩起訴附命戒癮治療、酒駕吊銷駕照重新考照要求之酒癮治療）',
          '經醫師評估有戒酒需求；至新北市 12 家酒癮治療指定機構就診（補助直接撥付機構，每人每年最多 4 萬元）']),
       '新北市衛生局「新北市酒癮治療服務暨指定機構清冊（酒癮治療費用補助方案）」Q&A「戒酒治療有補助嗎？」（原 node=678 網址 JS 轉址至此頁）'),
 598: (C(598, ageMin=18, requiredFlags=['disability_certificate'], uncheckedConditions=[
          '設籍並實際居住新北市，本人領有身心障礙手冊或證明',
          '購買或承租坐落於新北市之公有市場商店攤販，且購買或承租未滿 2 年',
          '原文寫「年滿二十歲」（頁面更新 2025-04-17；民法成年已改 18 歲，市府頁另寫「應為成年人」，故引擎只編 18）',
          '未曾接受政府同性質貸款利息補貼或租金補貼',
          '家庭總收入平均分配全家人口，每人每月未達當年度最低生活費 2.5 倍']),
       '永和區公所「身心障礙者購買或承租商店攤販低利貸款或租金補貼」申請資格'),
 605: (C(605, requiresChildUnder=19, uncheckedConditions=[  # 原文「18歲以下」含 18 歲；引擎是嚴格小於
          '就讀、設籍於新北市或在新北市發生急難事由之 18 歲以下高中職、國中小學生及兒童',
          '家遇急難、有飢餓求助需求：至北臺 8 縣市四大超商或新北市合作餐飲店填寫基本資料取餐（100 元內、店內食用）']),
       '新北市政府市政新聞（2023-12-29）「北臺8縣市推動「幸福保衛站」 共同守護180萬學童」；另搜「新北市 幸福保衛站 115年」：自由時報 2026-08-20 報導教育局表示原有服務持續辦理'),
 612: (C(612, ageMin=65, ageMinByIdentity={'原住民': 55}, uncheckedConditions=[
          '101 年 7 月 31 日前設籍新北市滿 1 年以上，且申請時設籍新北市',
          '曾從事煤礦工作且有投保紀錄']),
       f'{SVC}「辦理退休煤礦工慰問金發放」申請說明（新北市辦理退休煤礦工慰問金實施要點）'),
 619: (C(619, requiredFlags=['pregnant_or_recent_birth'], uncheckedConditions=[
          '孕婦符合其一：34 歲以上；或經診斷／證明本人或配偶罹患遺傳性疾病、曾生育過異常兒、家族有遺傳性疾病、血清篩檢染色體異常危險機率大於 1/270、超音波篩檢胎兒有異常可能',
          '持身分證明文件至醫療院所直接扣除，無須另外申請']),
       f'{WEL}「產前遺傳診斷」福利說明 1、2'),
 626: (C(626, requiresChildUnder=13, uncheckedConditions=[
          '國小弱勢家庭學童（由學校認定低收入、單親、失親、隔代教養等經濟弱勢、下課後無人照顧）',
          '須就讀學校有申請辦理夜光天使點燈專案（115 學年度第 1 學期 15 所學校）']),
       '新北市政府施政成果網「夜光天使點亮孩子心燈」正文（提供國小弱勢家庭學童課後照顧及夜間照護；115 學年度第 1 學期 15 校）'),
 633: (C(633, incomeThreshold='low_income', minResidencyMonths=6, uncheckedConditions=[
          '新北市列冊有案之低收入戶；設籍且實際居住新北市滿 6 個月',
          '非居住於公有宿舍、出租國宅、社會住宅及社會福利機構',
          '5 年內未曾接受本補助或政府其他修繕住宅費用之補貼',
          '修繕住宅應為建築完成 10 年以上，且為自有或二等親以內親屬持有之住宅',
          '115 年度受理至 115/12/31 或經費用罄為止']),
       f'{SVC}「低收入戶修繕住宅補助(資格申請)」申請說明二、申請對象；三、修繕住宅規定；備註受理期間'),
 640: (C(640, requiresChildUnder=8, uncheckedConditions=[  # 入國小前含緩讀生（可能滿 7 歲）；引擎是嚴格小於
          '就讀新北市公立幼兒園，學齡滿 2 足歲至入國民小學前（含緩讀生）',
          '符合其一：弱勢兒少、特殊境遇家庭、身心障礙或發展遲緩（須確診）、寄養家庭、原住民幼生（3～5 歲）、家庭突發因素致無力支付餐點費用（導師及園方審核認定）',
          '已依教育部公立幼兒園就學補助／少子女化對策計畫免繳費用者非申請對象',
          '申請時間每年 3/1～3/31 及 9/1～9/30']),
       f'{WEL}（itemId 1008052，頁面標題為「公立幼兒園弱勢家庭幼生學雜費補助」，內容為餐點費用補助）福利說明＋補助內容二＋備註欄'),
 647: (C(647, uncheckedConditions=[
          '新北市市民因意外事故死亡（以亡者戶籍所在地區公所受理）',
          '死亡發生日（相驗屍體證明書所載日期或法院宣告死亡日）起 6 個月內申請',
          '具領人順序：配偶、子女、父母、兄弟姊妹、祖父母；低收 50 萬、中低收 30 萬、一般市民 15 萬']),
       f'{SVC}「新北市市民意外事故致死救助」申請說明一～三'),
 654: (C(654, uncheckedConditions=[
          '非設籍新北市之民眾，在新北市需返回戶籍地（車票限莒光號以下車種或國光客運）',
          '每人一年限申請一次']),
       f'{SVC}「申請車資救助」申請說明一～四'),
 661: (C(661, requiresChildUnder=18, uncheckedConditions=[
          '未滿 18 歲之兒童及少年，設籍新北市（或實際居住超過 6 個月之無戶（國）籍兒少），且未接受公費收容安置',
          '家庭狀況符合其一：父母一方或監護人失業／入獄／重大傷病／精神疾病／藥酒癮戒治致生活困境；父母離婚或一方死亡失蹤他方無力維持；父母一方因家暴等出走；父母雙亡或遭遺棄由無經濟能力親屬撫養；未滿 18 歲未婚懷孕或有非婚生子女；其他經社工評估確有生活困難',
          '經濟狀況：家庭總收入人均未達最低生活費 1.5 倍（115 年 26,625 元）、動產人均低於 15 萬、不動產總值低於 708 萬；或不符前述但有事實足證最近 1 年生活陷困經訪視評估確有必要（符合其一）']),
       f'{SVC}「弱勢家庭兒童及少年緊急生活扶助」申請說明補助對象一、二＋申請對象'),
 668: (C(668, incomeThreshold='low_income', incomeEstimateSufficient=True,
         _incomeEstimateNote=f'{D} 低收入戶認定本身（申請列冊），同 W-020 B 6、8、18 號的做法',
         uncheckedConditions=[
          '設籍並實際居住新北市，且最近一年居住國內超過 183 日',
          '動產：全家人口現金（含存款本金、利息）、有價證券、汽車及投資合計每人每年未超過 10 萬元',
          '不動產：全家人口土地公告現值及房屋評定標準價格合計未超過 472 萬元']),
       f'{SVC}「申請低收入戶資格-含改列、增列、減列及申復」申請說明一、（二）審查標準：家庭總收入人均每月低於最低生活費（115 年 1 萬 7,750 元）'),
 675: (C(675, requiredFlags=['severe_disability_or_dementia'], uncheckedConditions=[
          '受照顧者：領有中低收入老人生活津貼；未接受機構收容安置、居家服務、未僱看護、未領日間照顧或其他照顧服務補助；日常生活活動功能量表評估重度以上且實際由家人照顧；實際居住於戶籍所在地',
          '照顧者：年滿 16 歲未滿 65 歲；為同一應計算家庭人口、出嫁之女兒／贅夫及其配偶、或 2 親等內直系血親卑親屬（符合其一）；未從事全時工作且實際負責照顧；與受照顧者設籍並實際居住新北市']),
       f'{SVC}「中低收入老人特別照顧津貼」申請說明一～四＋補助對象（照顧者資格）'),
 682: (C(682, ageMin=20, ageMax=65, minResidencyMonths=6,
         requiredFlags=['disability_certificate', 'has_startup_intent'], uncheckedConditions=[
          '設籍新北市 6 個月以上、本人領有身心障礙手冊或證明，具工作能力及創業意願',
          '向公、民營金融機構辦理之創業貸款已核准',
          '取得公司、商業登記或開（執）業許可登記未滿 1 年，且登記地址與實際營業地址相同']),
       f'{SVC}「身心障礙者創業貸款利息補貼」申請說明＋申請對象：設籍於新北市 6 個月以上之身心障礙者，年齡 20-65 歲'),
 689: (C(689, requiredIdentities=['原住民'], uncheckedConditions=[
          '新北市原住民',
          '符合其一：戶內人口死亡無力殮葬；戶內人口罹患嚴重傷病住院 3 天以上致家庭生活陷於困境；負擔家庭生計者失業／失蹤／服役／服刑／羈押等無法工作致生活陷困；其他重大變故經訪視評估確有救助需要；遭受風災水災火災震災等重大災害致損害重大']),
       f'{SVC}「原住民急難救助」申請說明一～四＋申請對象：本市原住民'),
 1002: (C(1002, requiredFlags=['legal_dispute_or_consultation_needed'], uncheckedConditions=[
          '在新北市提供勞務之受僱者或求職者',
          '符合其一：因雇主違反性別平等工作法規定向法院提起民事訴訟；或遭受工作場所性騷擾經事業單位或地方主管機關認定成立而向法院提起民事訴訟（申請者死亡得由承受訴訟者或繼承人申請）',
          '申請勞動調解及訴訟期間必要生活費用者另須：最近 1 年個人綜所稅平均每月收入未逾 6 萬 5 千元、個人名下資產未逾 300 萬元（不含自住不動產）',
          '115 年度申請期間 115/1/1～115/10/30（本年度已截止）；須於各審訴訟／強制執行程序終結前提出']),
       '新北勞動雲「補助性別平等工作法律扶助」（上版 2026-06-22）一、申請期間；二、補助對象（一）～（四）'),
}
# SKIP（不在 X）：576 FLAG（補助對象是社區／申請單位）、591 FLAG（單一課程報名頁、不是福利）
#   —— 見 ~/.hermes/cache/welfare_w028_20261119/g6_report.md

assert set(ORIG) == set(X), set(ORIG) ^ set(X)
assert not {576, 591} & set(X)


def full(bid, new, src):
    ec = dict(new)
    ec['_source'] = f'W-028 {D} 依官方原文重編條件（otherConditions 原值為申請方式，搬至 _otherConditions_orig）：{src}'
    return ec


conn = psycopg2.connect(os.environ['DATABASE_URL']); cur = conn.cursor()
cur.execute('select id, eligibility_conditions from benefits where id = any(%s)', (list(X),))
old = dict(cur.fetchall())
assert set(old) == set(X), set(X) - set(old)
for bid, (new, src) in X.items():
    ec_old = old[bid] or {}
    assert ec_old.get('counties') == new['counties'], (bid, ec_old.get('counties'))
    assert ec_old.get('otherConditions') == ORIG[bid], (bid, '原 otherConditions 與 ORIG 不一致')
    assert 'otherConditions' not in new, bid
    # 原有鍵只能是 counties／otherConditions／minResidencyMonths（633 原就有 6，原文相符保留）
    assert set(ec_old) <= {'counties', 'otherConditions', 'minResidencyMonths'}, (bid, sorted(ec_old))
    if 'minResidencyMonths' in ec_old:
        assert new.get('minResidencyMonths') == ec_old['minResidencyMonths'], bid
    ec = full(bid, new, src)
    assert_substantive(ec, label=f'新北市｜#{bid}')
    print(bid, json.dumps({k: v for k, v in ec.items() if k not in ('_source', '_otherConditions_orig', '_incomeEstimateNote')}, ensure_ascii=False)[:150])
if '--apply' in sys.argv:
    cur.execute(f'create table {BACKUP} as select * from benefits where id = any(%s)', (list(X),))
    for bid, (new, src) in X.items():
        cur.execute('update benefits set eligibility_conditions = %s, updated_at = now() where id = %s',
                    (json.dumps(full(bid, new, src), ensure_ascii=False), bid))
    conn.commit(); print('✅ 已寫入', len(X), '；備份表', BACKUP)
else:
    conn.rollback(); print('(dry-run)', len(X))
