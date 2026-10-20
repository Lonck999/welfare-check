"""問卷第 3 題性別（2026-10-20 Lonck 定 A）：原文明寫限女性的 2 筆設 requiredGender。
   🔴 名稱有「婦女」不等於限女性：221 特殊境遇婦女／家庭扶助（家庭也可）、599 子宮頸疫苗（國中八年級生不分性別）、
      912／925 婦女生產補助（已用懷孕旗標）—— 都不設。
   293 順修：原條件 requiredFlags ['spouse_no_income']（配偶無收入）在勞動部原文找不到，是錯編 ⇒ 改成原文條件。
   用法：python batch_gender.py [--apply]"""
import json, sys, psycopg2
D = '2026-10-20'
X = {
    293: ({"requiredGender": "female", "uncheckedConditions": [
              "離開職場 180 日以上（115 年修正：不限家庭因素）",
              "向公立就業服務機構辦理求職登記並報名本計畫；再就業獎勵須受僱滿 30 日"]},
          ['requiredFlags'],
          '勞動部新聞稿（更新 2026-04-07）：凡離開職場180日以上之婦女皆可適用'),
    589: ({"requiredGender": "female", "ageMin": 18, "ageMax": 70, "uncheckedConditions": [
              "設籍本市之婦女，或與本市市民結婚之新住民婦女",
              "以無工作或無就學之一般家庭主婦為主"]},
          [],
          '新北市原文：年滿18歲至70歲以下設籍本市之婦女或與本市市民結婚之新住民婦女'),
}
conn = psycopg2.connect(dbname='welfare_check'); cur = conn.cursor()
cur.execute('select id, eligibility_conditions from benefits where id = any(%s) and is_active', (list(X),))
old = dict(cur.fetchall()); assert set(old) == set(X)
for bid, (add, drop, src) in X.items():
    ec = dict(old[bid] or {})
    for k in drop:
        print(bid, '移除', k, ec.pop(k, None))
    ec.update(add); ec['_source'] = f'{D} 依原文：{src}'
    print(bid, json.dumps({k: v for k, v in ec.items() if k != '_source'}, ensure_ascii=False)[:200])
    if '--apply' in sys.argv:
        cur.execute('update benefits set eligibility_conditions=%s, updated_at=now() where id=%s', (json.dumps(ec, ensure_ascii=False), bid))
if '--apply' in sys.argv:
    conn.commit(); print('✅ 已寫入', len(X))
