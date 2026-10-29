"""W-020 B 第 G2 批：雲林縣＋全國（counties 空）共 24 筆中可編的 16 筆，依官方原文編資格條件。
   2026-10-29 逐頁讀正文（curl + 瀏覽器 UA；被擋的再用 render_page.py headless 重試）。
   雲林智慧福利網 welfare.yunlin.gov.tw 可讀；law.yunlin／dsh.yunlin／social.yunlin 兩法皆 Cloudflare 403 → 列 UNREADABLE 不編。
   原則同 batch02：
   · 問卷問得到的 → 編成引擎條件；問不到的 → uncheckedConditions 原文照列（最高只能 possible）
   · 「符合其一」OR 條件 → 一律放 unchecked，不硬編成 AND
   · incomeThreshold 只在原文是「列冊低收／中低收」或「未達最低生活費 1.5 倍」才編
   SKIP（FLAG／UNREADABLE，不在 X 裡）：15、28、93、320、321、324、363、831 —— 見 ~/.hermes/cache/welfare_w020b_20261029/g2_report.md
   用法：python batch_g2_20261029.py [--apply]（預設 dry-run，不寫 DB）"""
import json, sys, psycopg2
D = '2026-10-29'
YL = ['雲林縣']
SCF = ["special_circumstance_family"]
P = 'welfare.yunlin.gov.tw 智慧福利資訊網 CaseInfo'
X = {
 826: ({"incomeThreshold": "mid_low_income", "uncheckedConditions": [
          "住院期間經醫師診斷證明確需聘僱專人看護（須附看護費收據、看護者身分證與看護訓練證書）",
          "住院或出院日起三個月內向戶籍所在地公所申請"]},
       f"{P}/202006018「低收入戶及中低收入戶住院看護費用補助申請表」申請說明（一）：應備當年度低收入戶證明或中低收入戶證明"),
 827: ({"incomeThreshold": "mid_low_income", "uncheckedConditions": [
          "設籍本縣之傷、病患者，符合其一：（一）低收入戶（二）中低收入戶（三）非列冊但患嚴重傷病、家庭總收入平均未達最低生活費 1.5 倍，且醫療費用非本人或扶養義務人所能負擔"]},
       f"{P}/202006019「雲林縣醫療費用補助申請表」補助對象（三款皆以最低生活費 1.5 倍以內為前提）"),
 828: ({"ageMax": 64, "incomeThreshold": "mid_low_income", "uncheckedConditions": [
          "設籍並實際居住本縣，且已列冊低收入戶或中低收入戶",
          "修繕限臥室／廚房／浴廁、供電照明給排水防水、牆壁天花板樓梯地板、無障礙及住宅安全必要設施",
          "房屋非申請人所有者，須附自申請年度起三年以上租（借）約及所有權人修繕同意書"]},
       f"{P}/202006020「未滿六十五歲低收入戶及中低收入戶住宅修繕補助」申請說明一：設籍並實際居住本縣，且未滿六十五歲已列冊之低收入戶及中低收入戶"),
 829: ({"requiredFlags": ["acute_hardship"], "uncheckedConditions": [
          "符合其一：家庭成員死亡／失蹤／重傷病／失業或因故無法工作致生活陷困；因經濟因素有自殺之虞之通報個案；經濟因素經通報為脆弱家庭；遭家暴／性侵經通報或庇護安置、緊急生活扶助金尚未核發；申請福利尚未核准期間生活陷困；其他變故致生活陷困",
          "向村里辦公處、鄉鎮市公所或縣府申請或通報"]},
       f"{P}/202006022「強化社會安全網-急難紓困實施方案」救助對象一～六"),
 830: ({"requiredFlags": ["acute_hardship"], "uncheckedConditions": [
          "設籍本縣、遭逢急難且家庭經濟能力無法負擔",
          "符合其一：戶內人口死亡無力殮葬；戶內人口罹患重病致生活陷困；主要生計者失蹤／入獄等致生活陷困；財產因故凍結無法及時運用；申請社會福利尚未核准；家庭重大變故經訪視評估需救助"]},
       f"{P}/202006023「急難救助」對象（一）～（六）"),
 832: ({"requiredFlags": ["enrolled_national_pension"], "uncheckedConditions": [
          "須為國民年金被保險人",
          "所得未達一定標準（雲林官方頁與附件申請表、流程圖均未列標準數字，依國民年金法由縣府審核全家人口所得財產）"]},
       f"{P}/202005008「國民年金被保險人所得未達一定標準保費減免」申請說明＋附件（作業流程圖、申請表）；頁面未載所得標準"),
 833: ({"requiresChildUnder": 18, "uncheckedConditions": [
          "須有《弱勢家庭兒童及少年緊急生活扶助》要點第二點第一項所列情事之一（官方頁未列明細，應備「足資證明」文件）",
          "審查全家人口最近一年所得及財產；兒少就學者附學生證"]},
       f"{P}/202006009「弱勢家庭兒童及少年緊急生活扶助」應備證件 3～7（兒童及少年＝未滿 18 歲）"),
 834: ({"requiresChildUnder": 18, "uncheckedConditions": [
          "須符合《兒童及少年生活扶助》要點第四點資格（官方頁未列明細；第四點第一項第一款者只需附中低收入戶證明）",
          "每年向兒少戶籍所在鄉鎮市公所申請；14～未滿 18 歲應附學生證"]},
       f"{P}/202006010「兒童及少年生活扶助」申請說明 1、應備證件 3、5"),
 835: ({"requiresChildUnder": 2, "uncheckedConditions": [
          "符合其一：委託人最近一年綜合所得總額未達申報標準或稅率未達 20%；或經認定為低收／中低收入戶或弱勢家庭（幼兒發展遲緩／身障、特殊境遇家庭等）",
          "幼兒送托準公共化合作對象，每週時數 30 小時以上（不得指定一對一收托，特殊幼兒除外）",
          "幼兒未經公費安置，委託人未領該幼兒之育嬰留職停薪津貼、育兒津貼或同性質津貼",
          "托育事實發生之日起 15 日內繳齊文件"]},
       f"{P}/202006011「0-2歲準公共化托育補助」申請說明（一）～（四）"),
 836: ({"requiredFlags": SCF, "uncheckedConditions": [
          "須符合特殊境遇家庭扶助條例所定特殊境遇情形及家庭收入、財產標準（官方頁只列申請方式與文件，未列標準）",
          "向戶籍所在地村里辦公處申請；子女教育補助附學生證、托育津貼附幼兒園收據、醫療補助附診斷書等"]},
       f"{P}/202006012「特殊境遇家庭扶助」申請方式（一）～（四）、應備證件"),
 837: ({"requiredIdentities": ["新住民"], "uncheckedConditions": [
          "須為本縣「設籍前」新住民（尚未取得我國戶籍）",
          "家庭總收入人均每月未超過最低生活費 2.5 倍及臺灣地區平均每人每月消費支出 1.5 倍，且家庭財產未超過中央公告金額",
          "符合其一：配偶死亡或失蹤 6 個月以上；因配偶惡意遺棄／虐待經判決或協議離婚；家暴／性侵／犯罪受害無力負擔醫療或訴訟費；單親無工作能力或因重大傷病／照顧 6 歲以下在臺婚生子女未能就業；配偶受 1 年以上徒刑或保安處分執行中；3 個月內生活重大變故（非個人責任、債務、自願失業）"]},
       f"{P}/202006013「設籍前新住民遭逢特殊境遇相關福利及扶助補助項目」（一）補助對象、（二）申辦原則 2"),
 838: ({"uncheckedConditions": [
          "申請人為受托幼兒之（曾）祖父母，且具保母資格（親屬保母）",
          "幼兒家長雙方在職（或有中重度身障、服義務役、在監服刑等證明），並確實在本縣托育",
          "每年度案件總清查須重新送件；弱勢家庭另附低收／中低收、發展遲緩、身障或特殊境遇證明"]},
       f"{P}/202006014「祖孫托育補助」申請說明、應備證件（一般家庭 a～j、弱勢家庭 b）"),
 839: ({"requiresChildUnder": 18, "uncheckedConditions": [
          "設籍本縣之弱勢兒少，符合其一：低收／中低收入戶兒少；領弱勢家庭兒少緊急生活扶助；受保護兒少；安置於機構或寄養家庭；特境家庭未滿 6 歲兒童；發展遲緩兒童；早產兒；因懷孕或生育遭遇困境之兒少及其子女；罕見疾病或重大傷病兒少；其他經社會處評估有必要者"]},
       f"{P}/202006015「弱勢兒童及少年醫療費用補助」醫療費用補助對象（一）～（十）"),
 840: ({"ageMin": 20, "ageMax": 65, "requiresChildUnder": 19, "requiresNoOwnedHome": True,
        "incomeThreshold": "mid_low_income", "requiredFlags": SCF, "uncheckedConditions": [
          "設籍且實際租賃房屋居住本縣，因喪偶、離婚、未婚生子、配偶判決確定服刑 1 年以上或失蹤半年以上，獨力扶養 18 歲以下在學未婚子女",
          "現未接受政府同性質補助；租賃合法建築物，所有權人非直系親屬；未住公有房舍",
          "租賃期間需達當年度 6 個月以上"]},
       f"{P}/202006016「弱勢兒少家庭租賃房屋租金補助」申請說明（一）～（六）：家庭總收入平均未達最低生活費 1.5 倍、因無自有住宅而租屋"),
 42:  ({"requiredFlags": ["legal_dispute_or_consultation_needed"], "uncheckedConditions": [
          "符合其一：符合法律扶助法相關規定之無資力；或因其他原因無法受到法律適當保護（訴訟扶助另經財力與案情審查）",
          "就近至法律扶助基金會各地分會申請"]},
       "司法院全球資訊網「法律扶助簡介」二、基金會服務項目：民眾只要符合法律扶助法相關規定之無資力，或因其他原因，無法受到法律適當保護，均可就近至基金會各地分會申請"),
 347: ({"uncheckedConditions": [
          "自然人，於補助購買期間（發票日期 112/01/01～115/12/31）購置一級能效冷氣機或電冰箱新品並汰換舊產品（附廢四機回收聯單）",
          "安裝於用電種類為「表燈非營業用」之住宅用戶；發票不得載買受人統編",
          "申請期間至 116/01/31，如經費用罄將提前結束；同一產品不得另獲其他政府機關補助"]},
       "能源署 save3000「住宅家電汰舊換新節能補助作業要點」第四點補助對象＋首頁【發票日期】【申請期間】"),
}
EXPECT_COUNTIES = {bid: (None if bid in (42, 347) else YL) for bid in X}
conn = psycopg2.connect(dbname='welfare_check'); cur = conn.cursor()
cur.execute('select id, eligibility_conditions from benefits where id = any(%s)', (list(X),))
old = dict(cur.fetchall())
assert set(old) == set(X), set(X) - set(old)
for bid, (add, src) in X.items():
    ec = dict(old[bid] or {})
    exp = EXPECT_COUNTIES[bid]
    if exp is None:
        assert not ec.get('counties'), (bid, ec.get('counties'))   # 全國項目：counties 為空／None
    else:
        assert ec.get('counties') == exp, (bid, ec.get('counties'))
    assert not (set(add) & {'openToAll'}), bid
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
