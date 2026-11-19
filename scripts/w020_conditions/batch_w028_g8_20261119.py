"""W-028 第 g8 組：桃園市 693–718 共 26 筆中的 24 筆（709、712 列 FLAG，不在 X），依官方原文重編資格條件。
   2026-11-19 逐頁讀過正文：
   · 桃園 e-services（e-services.tycg.gov.tw item/detail）是 Angular SPA，curl 只拿到 1,593 字空殼 ⇒
     用 scripts/render_page.py 的 render()（headless Chrome --dump-dom）讀到 1,226～2,361 字全文，逐頁核對頁名與 id 相符
   · 701 新住民專區 QA/Detail/52：curl 與舊快取都是 ASP.NET 500 錯誤頁 ⇒ web_extract 讀到全文
   · 703 勞動局頁只有課程介紹 ⇒ 另讀附件「給民眾115年身心障礙者職業訓練一覽表」PDF（pypdf）的「報名資格」
   · 714 原民局頁 curl 讀到全文（3,658 字）
   原則（W-020 B／W-028 定案）：
   · 問卷問得到的 → 引擎條件；問不到的 → uncheckedConditions 原文照列（最高只能 possible）
   · 「符合其一」的 OR 條件 → 一律放 unchecked，不硬編成 AND
   · incomeThreshold 只在原文為「列冊低收／中低收」或「未達最低生活費 1.5 倍」且非 OR 時編
   · 既有的 otherConditions（引擎不檢查）→ 原值原封搬到 `_otherConditions_orig`（執行時從 DB 複製，逐字不改），刪掉 otherConditions
   · X 放的是**整份新的** eligibility_conditions（counties 保留原值，執行時 assert 與 DB 一致）
   用法：python batch_w028_g8_20261119.py [--apply]（預設 dry-run，不寫 DB）"""
import json, os, sys
import psycopg2

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from eligibility_guard import assert_substantive  # noqa: E402

D = 'W-028 2026-11-19'
TY = ['桃園市']
ES = '桃園網路e指通'  # e-services.tycg.gov.tw 單筆申辦頁

X = {
 693: ({"counties": TY, "ageMin": 16, "ageMax": 65, "requiredFlags": ["disability_certificate"],
        "uncheckedConditions": [
          "領有身心障礙手冊（或證明），且身分證設籍桃園市",
          "取得勞動部核發之技術士證照（甲級 3 萬、乙級 1 萬、丙級／單一級 5 千），證照生效日起 12 個月內申請"]},
       f"{ES}「桃園市身心障礙者取得技術士證照獎勵」應備文件＋原 otherConditions（一、16 歲至 65 歲；三、領有身心障礙手冊或證明；六、取得勞動部技術士證照）"),
 694: ({"counties": TY, "ageMin": 18, "requiredFlags": ["disability_certificate"],
        "uncheckedConditions": [
          "設籍桃園市；非現任公職人員",
          "參加合法立案補習班之公務人員考試課程（含購買函授教材），上課或購買後 12 個月內申請第一階段；考試錄取取得及格證書後 12 個月內申請第二階段"]},
       f"{ES}「身心障礙者參加公務人員考試補習費用補助」申辦/補助資格說明、應備文件"),
 695: ({"counties": TY, "uncheckedConditions": [
          "符合其一：勞務提供地在桃園市，或爭議發生時已設籍桃園市滿 4 個月（工會幹部或個案勞工）",
          "勞資爭議事件經桃園市政府勞動局調解不成立，且非顯無勝訴之望；遭資方不當解僱或因職災未獲薪資而涉訟",
          "涉訟期間無資力、無收入，且未領勞保失業給付、傷病給付、生活補助、臨時工作津貼、訓練生活津貼等同性質補助",
          "應於提起每一審級訴訟之日起 6 個月內申請；同一事件已獲法院訴訟救助或他機關補助者不得重複；有工作能力無正當理由拒絕推介工作者不予補助"]},
       f"{ES}「訴訟期間生活補助金」服務簡介、申辦/補助資格說明、其他注意事項 1～5"),
 696: ({"counties": TY, "requiredFlags": ["special_circumstance_family"], "uncheckedConditions": [
          "全戶收入、動產、不動產符合特殊境遇家庭扶助標準",
          "符合其一：65 歲以下之配偶死亡或失蹤達 6 個月以上；因配偶惡意遺棄或受虐待經判決或協議離婚；家庭暴力受害者；未婚懷孕婦女（懷胎 3 個月以上至產後 2 個月內）；因喪偶、離婚或未婚生子獨自扶養 18 歲以下子女或祖父母扶養孫子女，且無工作能力或因重大傷病、照顧 6 歲以下幼兒無法工作；配偶服刑或受保安處分 1 年以上執行中；3 個月內遭逢重大變故致生活困難（非因個人責任、自願失業、債務）",
          "向戶籍所在地區公所社會課申請；重大變故須於變故發生 3 個月內申請"]},
       f"{ES}「桃園市特殊境遇家庭扶助」申辦/補助資格說明、其他注意事項"),
 697: ({"counties": TY, "ageMin": 20, "requiredIdentities": ["原住民"], "minResidencyMonths": 4,
        "uncheckedConditions": [
          "設籍桃園市並實際居住 4 個月以上；申請人係房屋所有權人或具原住民身分之配偶",
          "建購住宅未逾二年（以政府會計年度起始日往前推算），本人、配偶及共同生活之直系親屬均無其他自有住宅，且不曾接受政府其他住宅補助（不含內政部住宅貸款補貼）；另有房屋課稅現值依持分 10 萬元以下或原自用住宅遭災無法居住者，視為無其他自有住宅",
          "房屋登記原因為興建（第一次登記）或買賣（拍賣）取得，用途為住宅、農舍或含「住」字樣且確實自用居住",
          "經濟弱勢：原民會作業要點第五點（三）家庭總收入每人每月未超過最低生活費 2 倍，存款及不動產另有限額（e指通頁未列數字）"]},
       f"{ES}「經濟弱勢原住民建購住宅補助」服務簡介 1～3＋原 otherConditions（四）（五）（六）；所得門檻依原民會《補助經濟弱勢原住民建購及修繕住宅作業要點》第五點（114-03-06 修正）"),
 698: ({"counties": TY, "requiredIdentities": ["原住民"], "minResidencyMonths": 4, "requiresNoOwnedHome": True,
        "uncheckedConditions": [
          "申請人需滿 20 歲、具行為能力之原住民（單親獨立撫育未成年原住民子女者不在此限）；設籍桃園市 4 個月以上，戶籍應一併遷至租賃住宅所在地",
          "家庭成員無自用住宅，亦無借住公有住宅或宿舍；未接受政府安置於國宅、安置住所或平價住宅；合法租屋（以租約認定，本市國宅除外）",
          "家庭人口 3 人以上（單親家庭、低收入戶、身心障礙者、55 歲以上獨居老人不受人口數限制）",
          "符合其一：家庭符合政府公告每人每月最低生活費標準 1.5 倍者，或低收入戶、單親家庭、身心障礙者、55 歲以上獨居老人（每月補助 4,000 元）",
          "受理期限每年 3/1～4/30"]},
       f"{ES}「經濟弱勢原住民族家庭租屋補助計畫」服務簡介（受理期限、補助金額）＋其他注意事項「申請資格」1～5"),
 699: ({"counties": TY, "ageMin": 18, "ageMax": 65, "requiredFlags": ["disability_certificate"],
        "uncheckedConditions": [
          "設籍並實際居住桃園市；具創業意願及工作能力",
          "為所創事業登記或許可設立之負責人；公司、商業登記或執業許可證未逾 1 年（須於登記未逾 1 年內申請）；營業稅籍設於桃園市",
          "租金、設備補助每人終身各限一次；營業場所不得為本人、配偶或雙方直系血親所有；已領政府同性質創業補助者不得重複"]},
       f"{ES}「身心障礙者自力更生創業補助申請」申辦/補助資格說明、其他注意事項"),
 700: ({"counties": TY, "ageMin": 20, "requiredIdentities": ["原住民"], "minResidencyMonths": 4,
        "uncheckedConditions": [
          "設籍桃園市並實際居住 4 個月以上，且全家人口數達 2 人以上",
          "申請人係房屋所有權人或具原住民身分之配偶",
          "年度所得未超過政府公告每人每月最低生活費標準 2 倍（27,384 元）",
          "最近五年未曾獲政府其他修繕住宅補助"]},
       f"{ES}「經濟弱勢原住民修繕住宅補助」服務簡介「實施對象」1～4、應備文件（五年未獲補助切結書）"),
 701: ({"counties": TY, "requiredIdentities": ["新住民"], "requiresChildUnder": 7,
        "uncheckedConditions": [
          "持有居留證之外籍配偶，或依親居留期間持有居留證、長期居留或定居之陸港澳配偶",
          "參與桃園市政府就業職訓服務處辦理之（失業者）職業訓練期間，扶養 6 歲以下子女並就托於合法托育機構",
          "全日托每童每月最高 5,000 元、每年最高 1 萬 5,000 元；結訓後向訓練單位申請"]},
       "桃園市政府新住民專區 QA/Detail/52「新住民參加職業訓練是否有相關補助措施？」第 2 點【新住民參加職業訓練期間，子女托育補助】"),
 702: ({"counties": TY, "requiredFlags": ["has_disability_or_dementia_member"], "uncheckedConditions": [
          "經長期照顧管理中心評估，符合長期照顧需要等級（CMS）第 2 級（含）以上；未使用「住宿服務使用者補助方案」",
          "符合其一：65 歲以上長者、55 歲以上原住民、領有身心障礙證明（手冊）、失智症者、評估期間符合健保署急性後期整合照護計畫（PAC）收案對象",
          "撥打 1966、洽區公所／衛生所、醫院出院準備或智慧長照資訊系統線上申請，由照管專員到府評估後核定服務"]},
       f"{ES}「桃園市政府智慧長照資訊系統」服務簡介、申辦/補助資格說明、申辦流程"),
 703: ({"counties": TY, "uncheckedConditions": [
          "具生活自理能力並經評量為適訓者（具就業意願）",
          "符合其一：依身心障礙者權益保障法領有身心障礙證明者；或經精神科專科醫師診斷為精神疾病、病情穩定，且未取得身心障礙證明者",
          "依各班別報名截止日逕洽承訓單位報名；領有身心障礙證明者訓練期間得申請職訓生活津貼"]},
       "桃園市政府勞動局「115年身心障礙者職業訓練一覽表」頁附件《給民眾115年身心障礙者職業訓練一覽表》PDF「報名資格」"),
 704: ({"counties": TY, "requiredFlags": ["disability_certificate"], "uncheckedConditions": [
          "個人申請：設籍桃園市之聽（語）障者，或合併聽（語）障之多重障礙者（需附身心障礙證明）",
          "用於面試、職涯諮詢、職場溝通、教育訓練、會議、勞資爭議或司法事務等就業相關活動，服務地點以桃園市為主；申請事由未涉及私人商業利益",
          "服務日期 3 天前提出申請"]},
       f"{ES}「身心障礙者就業相關手語翻譯服務」申辦/補助資格說明（個人申請者）、應備文件、處理天數；單位申請者（機關、事業單位）不在本網站範圍"),
 705: ({"counties": TY, "uncheckedConditions": [
          "符合其一：勞務提供地在桃園市，或勞資爭議發生時已設籍桃園市達 4 個月以上（工會幹部或個案勞工）",
          "勞資爭議經桃園市政府勞動局調解不成立，且非顯無勝訴之望（裁決律師費：依勞資爭議處理法提起裁決事件；非訟律師費：雇主依勞動事件法第 49 條第 4 項命返還工資）",
          "申請人最近一年綜合所得在 96 萬元以上得不予補助；訴訟利益與補助不成比例得不予補助",
          "每一審級訴訟之日起 6 個月內申請；同一事件已獲法院訴訟救助或他機關補助者不得重複"]},
       f"{ES}「訴訟裁判費、律師費及裁決律師費」服務簡介、申辦/補助資格說明、其他注意事項 1～5"),
 706: ({"counties": TY, "requiredIdentities": ["農民", "漁民"], "uncheckedConditions": [
          "設籍桃園市且實際從事農業生產之農民或漁民，具農（漁）會會員資格",
          "已申辦並核准政策性農業專案貸款（農機、農糧業經營、漁業經營、畜禽產業、農民經營改善、產銷班、小大農、節能減碳、青年從農創業、農業天然災害低利貸款等），處於自行繳息期間",
          "未領其他政府機關（不含中央農業部）同性質利息貼補；補助最長 1 年、年利率最高 1.5%，每季檢據申請核撥"]},
       f"{ES}「政策性農業專案貸款利息補助」申辦/補助資格說明、其他注意事項 1～3"),
 707: ({"counties": TY, "requiredFlags": ["disability_certificate"], "uncheckedConditions": [
          "居住桃園市（含外縣市戶籍）且領有身心障礙證明，經身心障礙者需求評估中心評估有臨時及短期照顧需求",
          "同一時段未接受喘息服務、日間／住宿式照顧、居家服務、自立生活支持、家庭托顧、未聘僱外籍看護、未領政府特別照顧津貼（外籍看護無法照顧 30 日以上、請假，或重度以上身障與老邁／身障親屬同住等情形可放寬）"]},
       f"{ES}「桃園市身心障礙者臨時及短期照顧服務」申辦/補助資格說明（一般對象、排除條件、特別放寬條件）"),
 708: ({"counties": TY, "uncheckedConditions": [
          "設籍、居住或工作地點在桃園市，具工作意願及能力",
          "符合其一：15 歲以上領有身心障礙證明者；視覺功能漸失者；經精神科專科醫師診斷為精神疾病且病情穩定者；高級中等以上學校畢業前一年內經校轉介之身心障礙者；經地方政府職災勞工專業服務人員轉介之職業災害勞工；由教育、社政或醫療機構轉介之就業轉銜個案"]},
       f"{ES}「身心障礙者就業及職業重建服務」申辦/補助資格說明"),
 710: ({"counties": TY, "requiredIdentities": ["漁民"], "requiredFlags": ["recent_natural_disaster_damage"],
        "uncheckedConditions": [
          "受災地點經農業部公告為辦理漁業天然災害救助及低利貸款之地區，於公告翌日起 10 個工作日內向受災地區公所申請",
          "漁業損失程度達 20% 以上；陸上養殖需養殖漁業登記證、水權證明且已完成當季放養量申報；海上養殖需區劃／專用漁業權證明並已申報放養量；漁船（筏）因災毀損",
          "未辦理登記、不符土地使用法規或未如期辦理放養申報者不予救助；低利貸款須於受災證明書核發翌日起 15 日內向漁會信用部申貸"]},
       f"{ES}「申請漁業天然災害救助及低利貸款」服務簡介、申辦/補助資格說明、處理天數、其他注意事項"),
 711: ({"counties": TY, "ageMin": 18, "requiredFlags": ["disability_certificate"], "uncheckedConditions": [
          "實際居住桃園市（以本市市民為優先）",
          "夜間未安置於社會福利機構或精神醫療復健機構",
          "經需求評估中心及受補助單位專業團隊評估適合於社區居住與生活"]},
       f"{ES}「身心障礙者社區居住補助」申辦/補助資格說明"),
 713: ({"counties": TY, "requiredIdentities": ["農民", "漁民"], "requiredFlags": ["recent_natural_disaster_damage"],
        "uncheckedConditions": [
          "受災地點及項目經農業部公告辦理現金救助及低利貸款，於公告翌日起 10 日內向受災土地所在地區公所申請",
          "救助項目損害程度達 20% 以上；農業經營符合土地、水源及設施法令規定；畜牧業及漁業需符合公告飼養規模或具放養申報等證明",
          "長期作同曆年、短期作同產季救助以 1 次為限；同一災害符合其他救助規定僅得擇一領取"]},
       f"{ES}「申請農業天然災害救助及低利貸款」服務簡介、申辦/補助資格說明、處理天數"),
 714: ({"counties": TY, "requiredIdentities": ["原住民"], "minResidencyMonths": 4,
        "uncheckedConditions": [
          "個人：設籍並實際居住桃園市 4 個月以上之原住民族人（團體：已立案且設址本市之原住民機構、法人或團體，不在本網站範圍）",
          "補助法律諮詢、文件撰擬、調解／和解／仲裁代理、訴訟訴願代理或辯護、民事保全督促強制執行等；自案件發生之日起 6 個月內申請",
          "不予補助：無救濟途徑、已受同性質補助、刑事告訴告發或自訴之代理、偵查／訴訟中被列為被告（無罪或不起訴確定者除外）、相對人為本府或所屬機關、1 年內已獲補助 3 次等"]},
       "桃園市政府原住民族行政局「原住民族法律及諮詢服務」一、補助對象（一）個人；四、申請方式（一）；五、不予補助情形"),
 715: ({"counties": TY, "requiredIdentities": ["原住民"], "uncheckedConditions": [
          "申請公益彩券（立即型）經銷商用之工作能力證明，向原住民族行政局原民福利科臨櫃申請；不得以同一人名義重複申請"]},
       f"{ES}「原住民公益彩券工作能力證明」服務簡介、申辦/補助資格說明「具有原住民身分」、其他注意事項"),
 716: ({"counties": TY, "requiresChildUnder": 7, "uncheckedConditions": [
          "家中幼兒當學年度申請入桃園市公立或非營利幼兒園",
          "幼兒符合其一：身心障礙；低收入戶子女；中低收入戶子女；原住民；特殊境遇家庭子女；中度以上身心障礙者子女（身障幼兒應向本市特殊教育學生鑑定及就學輔導會申請鑑定安置）",
          "依各學年度招生公告期程於招生網或各園登記報名"]},
       f"{ES}「公立幼兒園及非營利幼兒園需要協助幼兒優先入園」申辦資格（一～六，符合之一）、申辦地點"),
 717: ({"counties": TY, "requiresChildUnder": 6, "uncheckedConditions": [
          "幼兒設籍桃園市且就讀本市公立或非營利幼兒園，學齡 2 至 5 歲",
          "幼兒符合其一：低收入戶、中低收入戶，或經核定為經濟情況特殊之幼兒",
          "由幼兒園於公告期間統一申請（平日留園全額補助；寒暑假每人每月最高 3,500 元）"]},
       f"{ES}「公立幼兒園及非營利幼兒園課後留園弱勢(幼兒)補助」申辦/補助資格說明、其他注意事項"),
 718: ({"counties": TY, "requiredIdentities": ["農民"], "requiredFlags": ["recent_natural_disaster_damage"],
        "uncheckedConditions": [
          "農田因天然災害流失或埋沒，每戶受災面積達 0.05 公頃以上；由該農田獨立且實際從事耕作之農戶具領",
          "農田限：非都市土地農牧用地、都市土地保護區或農業區、國家公園土地，且現供農作使用",
          "於中央公告救助地區翌日起 10 個工作日內向受災地區公所申請；同一期間同一救助種類已領其他災害救助金者不得重複"]},
       f"{ES}「農田受災救助」申辦/補助資格說明、處理天數、其他注意事項 1～3"),
}
# SKIP（不在 X，FLAG）：709 消費者便民服務（消費爭議申訴＝一般公共服務，非福利）、
#   712 社區(疑似)精神病患通報轉介（source 為通報轉介單 PDF，是衛生局派案通報機制，非申請人可申請之福利）
#   —— 見 ~/.hermes/cache/welfare_w028_20261119/g8_report.md

conn = psycopg2.connect(os.environ['DATABASE_URL']); cur = conn.cursor()
cur.execute('select id, name, eligibility_conditions from benefits where id = any(%s)', (list(X),))
rows = {r[0]: (r[1], r[2] or {}) for r in cur.fetchall()}
assert set(rows) == set(X), set(X) ^ set(rows)
new_all = {}
for bid, (new, src) in X.items():
    name, old = rows[bid]
    assert new.get('counties') == old.get('counties'), (bid, new.get('counties'), old.get('counties'))
    assert 'otherConditions' not in new, bid
    ec = json.loads(json.dumps(new, ensure_ascii=False))
    # 原 otherConditions 逐字搬到 _otherConditions_orig（不論是資格或申請方式，都不再被引擎列成「還缺」）
    if 'otherConditions' in old:
        ec['_otherConditions_orig'] = old['otherConditions']
    ec['_source'] = f'{D} 依官方原文重編條件（W-028：原只有引擎不檢查的 otherConditions）：{src}'
    assert_substantive(ec, label=f'桃園市｜{bid} {name}')
    new_all[bid] = ec
    print(bid, name, json.dumps({k: v for k, v in ec.items() if not k.startswith('_')}, ensure_ascii=False)[:160])

if '--apply' in sys.argv:
    cur.execute('create table benefits_before_w028_g8_20261119 as select * from benefits where id = any(%s)', (list(X),))
    for bid, ec in new_all.items():
        cur.execute('update benefits set eligibility_conditions = %s, updated_at = now() where id = %s',
                    (json.dumps(ec, ensure_ascii=False), bid))
    conn.commit(); print('✅ 已寫入', len(new_all), '（備份表 benefits_before_w028_g8_20261119）')
else:
    conn.rollback(); print('(dry-run) 全部通過 counties 比對與 assert_substantive：', len(new_all), '筆；FLAG 不在 X：709、712')
