"""B 重跑批 1 匯入的 10 筆（benefits 977–986）依官方原文編資格條件（2026-10-20）。

   匯入程式只寫 counties ⇒ 條件未整理 ⇒ 最高 possible（W-020 安全預設）。
   這支依 p66/NN.txt 正文把條件編進去，並把 3 筆衛福部全國方案改成「全國」（Lonck 10-20 選 A）。
   🔴「符合其一」一律放 uncheckedConditions（引擎只做 AND）。
   用法：python batch_import452.py [--apply]
"""
import json, sys, psycopg2
D = '2026-10-20'
DIS = ["disability_certificate"]
NATIONAL = {981, 984, 985}
X = {
 977: ({"counties": ["雲林縣"], "minResidencyMonths": 6, "uncheckedConditions": [
          "補助項目各有對象（擇一符合）：人工生殖（試管嬰兒）、母血唐氏症／NIPT、羊膜穿刺、婚後孕前健康檢查、凍卵；各項資格見附件計畫"]},
       '雲林縣衛生局 115 年好孕上場：本計畫補助設籍六個月以上的縣民'),
 978: ({"counties": ["雲林縣"], "uncheckedConditions": [
          "接受政府公費乳房、子宮頸、大腸、胃、口腔或肺部癌症篩檢，結果為「疑似異常」",
          "大腸鏡限 114/10/1 後糞便潛血陽性、114/12/16 後完成大腸鏡者；交通補助依戶籍地至醫院來回距離 10 公里以上"]},
       '雲林縣衛生局 115 年六項癌篩疑似異常補助：補助對象'),
 979: ({"counties": ["雲林縣"], "uncheckedConditions": [
          "設籍雲林縣，且為以下其一：低收入戶、中低收入戶、各級政府補助之經濟弱勢者或經政府認定經濟困難並開立證明者、街友安置輔導對象"]},
       '斗六市衛生所 115 年公益彩券回饋金弱勢族群醫療補助：申請資格'),
 980: ({"counties": ["嘉義市"], "ageMin": 18, "ageMax": 29, "requiredFlags": ["is_employed"], "uncheckedConditions": [
          "任職事業單位位於嘉義市，且於同一單位連續就業滿 3 個月（須有勞保投保證明）"]},
       '嘉義市勞青處 115 年青年求職加薪：計畫對象'),
 981: ({"counties": ["全國"], "uncheckedConditions": [
          "具以下資格之一（免申請、由政府主動匯款）：低收入戶、中低收入戶、領有身心障礙者生活補助、領有中低收入老人生活津貼、領有弱勢兒少生活扶助或緊急生活扶助、特殊境遇家庭子女生活津貼或子女教育補助"]},
       '嘉義市西區公所轉知衛福部 115 年弱勢加發生活補助：七大類'),
 982: ({"counties": ["嘉義市"], "uncheckedConditions": [
          "各項擇一符合：①孕婦產檢：孕婦或配偶設籍滿 6 個月、30 歲以上、孕期 20 週內 ②新生兒篩檢：115 年起出生、父或母設籍滿 6 個月 ③育齡癌友凍卵／凍精：設籍滿 6 個月、女 18–45／男 18–49 歲癌症病人 ④115 年出生設籍嘉義市嬰幼兒輪狀病毒疫苗"]},
       '嘉義市衛生局 115 年在嘉好好孕幼健康：一～四'),
 983: ({"counties": ["嘉義市"], "requiredFlags": ["pregnant_or_recent_birth"], "uncheckedConditions": [
          "孕婦設籍並實際居住於嘉義市；或設籍前新住民孕婦，其配偶設籍嘉義市並實際居住"]},
       '嘉義市社會處嘉有好孕乘車補助：一、補助對象'),
 984: ({"counties": ["全國"], "requiredFlags": DIS, "uncheckedConditions": [
          "已核定領取身心障礙者住宿式照顧費用補助（入住機構）",
          "身心障礙證明為中度以上"]},
       '嘉義市政府轉知衛福部 115–117 年身障住宿費用加碼：補助資格'),
 985: ({"counties": ["全國"], "uncheckedConditions": [
          "入住依法設立之住宿式服務機構（一般／精神護理之家、老人福利機構（安養床除外）、身障福利機構等）",
          "長照需要等級第 4 級以上，或持中度以上身心障礙證明（擇一）"]},
       '屏東縣長照處轉知衛福部 115 年住宿式服務機構使用者補助方案'),
 986: ({"counties": ["嘉義縣"], "ageMax": 45, "requiresNoOwnedHome": True, "uncheckedConditions": [
          "申請日前一年度為中央「三百億元擴大租金補貼」核定戶：45 歲以下一、二級，或未滿 40 歲三級",
          "申請及補貼期間設籍並租屋於嘉義縣",
          "🔴 實施計畫寫「114 年全年」、受理期間 114/4/1–6/30；115 年是否續辦未確認，請洽嘉義縣政府經濟發展處"]},
       '嘉義縣青年租屋加碼補貼實施計畫（114/1/8 修正）陸、柒、玖'),
}
conn = psycopg2.connect(dbname='welfare_check'); cur = conn.cursor()
cur.execute('select id, county, eligibility_conditions from benefits where id = any(%s) and is_active', (list(X),))
old = {r[0]: r[1:] for r in cur.fetchall()}; assert set(old) == set(X), set(X) - set(old)
for bid, (ec, src) in sorted(X.items()):
    county, prev = old[bid]
    assert set(prev) <= {'counties', '_note'}, (bid, '已有條件，不覆寫', prev)
    if bid not in NATIONAL:
        assert prev['counties'] == ec['counties'], (bid, prev['counties'], ec['counties'])
    ec = dict(ec); ec['_import452'] = f'{D} 依官方頁正文編入：{src}'
    new_county = '全國' if bid in NATIONAL else county
    print(bid, county, '→', new_county, json.dumps({k: v for k, v in ec.items() if k not in ('uncheckedConditions', '_import452')}, ensure_ascii=False))
    if '--apply' in sys.argv:
        cur.execute('update benefits set eligibility_conditions=%s, county=%s, updated_at=now() where id=%s',
                    (json.dumps(ec, ensure_ascii=False), new_county, bid))
if '--apply' in sys.argv:
    cur.execute("update benefits set validity_status='valid_unconfirmed' where id=986")
    conn.commit(); print('✅ 已寫入', len(X))
else:
    print('(dry-run)', len(X))
