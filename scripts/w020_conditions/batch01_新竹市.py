"""W-020 B 第一批：新竹市 11 筆，依官方原文（附件 PDF/ODT/新聞稿）編資格條件。
   每筆的條件都標出處；問卷問不到的寫進 uncheckedConditions（原文照抄要點）。
   856 法規已廢止（102-12-04）→ 不編、不停用，另列給 Lonck。
   用法：python _tmp-w020_hc.py [--apply]"""
import json, sys, psycopg2
D = '2026-10-20'
X = {
 8:   ({"incomeThreshold": "mid_low_income"}, "law.hccg FL084049（低收／中低收認定本身）"),
 819: ({"ageMin": 65}, "113-03-15 核定、114-04-15 修正 §五：設籍本市並年滿 65 歲"),
 820: ({"ageMin": 65, "ageMinByIdentity": {"原住民": 55}, "incomeThreshold": "low_income",
        "uncheckedConditions": ["聽力損失 45–110 分貝（6 個月內醫院診斷＋聽力圖），或領有聽覺機能障礙身障證明"]},
       "115-02-25 核定 §四：本市列冊低收入戶之 65 歲以上老人（原住民 55）"),
 821: ({"ageMin": 65, "uncheckedConditions": [
          "截至申請日連續設籍並實際居住本市滿 10 年",
          "最近一年個人綜合所得總額未達 50 萬元",
          "個人土地房屋價值合計未達 500 萬元（自住唯一房屋可扣 400 萬）",
          "非現職軍公教、未領月退休金、未領老農津貼／榮民就養／安老津貼等（見計畫伍之一）"]},
       "115-01-09 核定 §伍：年滿 65 歲、連續設籍滿 10 年，無排除情形"),
 822: ({"ageMin": 65, "ageMinByIdentity": {"原住民": 55}, "uncheckedConditions": [
          "符合其一：列冊低收／中低收入戶、領中低收入老人生活津貼、領身障生活補助、經市府全額補助收容安置、身障日照住宿補助達 50% 以上",
          "經醫師評估缺牙需裝置活動假牙"]},
       "114-12-19 核定 §二：設籍本市 65 歲以上（原住民 55），且符合下列之一"),
 823: ({"requiresElderOver": 65, "requiredFlags": ["severe_disability_or_dementia"], "uncheckedConditions": [
          "受照顧者已領有中低收入老人生活津貼"]},
       "審核辦法 §3：照顧者申請；受照顧者已領生活津貼、失能程度重度以上"),
 824: ({"ageMin": 65, "uncheckedConditions": [
          "符合中低收入老人生活津貼發給辦法第二條要件（家庭收入、存款）",
          "全家人口土地及房屋價值合計未超過 750 萬元"]},
       "審核作業規則 §2、§4"),
 825: ({"ageMin": 65, "uncheckedConditions": [
          "符合本市中低收入老人生活津貼請領資格（低收入戶老人不適用本計畫）",
          "最近三個月內自付醫療費用累計達 2 萬元以上，且未獲其他補助或保險給付"]},
       "實施計畫 §3 補助對象"),
 960: ({"ageMin": 65, "ageMinByIdentity": {"原住民": 55}, "uncheckedConditions": [
          "未獲政府機關健保費自付額全額補助（免申請，市府直接撥給健保署）"]},
       "市府新聞稿：設籍竹市 65 歲以上、原住民 55 歲以上，且未獲全額補助"),
 970: ({"requiresChildUnder": 6, "uncheckedConditions": ["須正在領取育兒津貼（加碼免申請、直接入帳）"]},
       "市府新聞稿：領取育兒津貼家長，每月再加 1,000"),
 971: ({"uncheckedConditions": [
          "本市青年（年齡範圍新聞稿未寫，見官方頁）",
          "訂閱使用 AI 工具的費用（弱勢青年最高 6,000）"]},
       "市府新聞稿：本市青年訂閱 AI 工具費用每人每年最高 3,000"),
}
cur_conn = psycopg2.connect(dbname='welfare_check'); cur = cur_conn.cursor()
cur.execute('select id, eligibility_conditions from benefits where id = any(%s)', (list(X),))
old = dict(cur.fetchall())
assert set(old) == set(X), set(X) - set(old)
for bid, (add, src) in X.items():
    ec = dict(old[bid] or {})
    ec.pop('_note', None)
    ec.update(add)
    ec['_source'] = f'W-020 {D} 依官方原文補條件：{src}'
    print(bid, json.dumps({k: v for k, v in ec.items() if k != '_source'}, ensure_ascii=False)[:160])
    if '--apply' in sys.argv:
        cur.execute('update benefits set eligibility_conditions = %s, updated_at = now() where id = %s', (json.dumps(ec, ensure_ascii=False), bid))
if '--apply' in sys.argv:
    cur_conn.commit(); print('✅ 已寫入', len(X))
else:
    print('(dry-run)')
