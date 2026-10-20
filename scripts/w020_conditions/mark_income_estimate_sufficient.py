"""W-020：標記「推算收入就夠、不需要已列冊」的項目（incomeEstimateSufficient）。
   2026-10-20 Lonck：「用推算的只能證明他今年的收入明年可以去申請」
   ⇒ 引擎預設：有 incomeThreshold 的項目，只靠推算最高 possible；
     只有下面這幾筆的原文本身就是「依收入審查」而非「須已列冊」，推算符合才可 confirmed。
   每筆附原文依據。用法：python mark_income_estimate_sufficient.py [--apply]"""
import json, sys, psycopg2
X = {
    6:   '低收／中低收認定本身（申請列冊），原文：人均月收入未超過最低生活費 1.5 倍',
    8:   '低收／中低收認定本身（申請列冊）',
    173: '中低收入老人生活津貼，原文：家庭人均月所得未達最低生活費 1.5 倍（含列冊低收／中低收）—— 依收入審查，不限已列冊',
    853: '國民年金「所得未達一定標準」是國保自己的認定，不是社會救助列冊',
}
conn = psycopg2.connect(dbname='welfare_check'); cur = conn.cursor()
cur.execute('select id, name, eligibility_conditions from benefits where id = any(%s)', (list(X),))
rows = cur.fetchall()
assert len(rows) == len(X), [r[0] for r in rows]
for bid, name, ec in rows:
    assert ec and ec.get('incomeThreshold'), (bid, '沒有 incomeThreshold，標了也沒作用')
    ec = dict(ec); ec['incomeEstimateSufficient'] = True
    ec['_incomeEstimateNote'] = '2026-10-20 ' + X[bid]
    print(bid, name, '→ incomeEstimateSufficient')
    if '--apply' in sys.argv:
        cur.execute('update benefits set eligibility_conditions=%s, updated_at=now() where id=%s', (json.dumps(ec, ensure_ascii=False), bid))
if '--apply' in sys.argv:
    conn.commit(); print('✅ 已寫入', len(X))
else:
    print('(dry-run)')
