"""2／10／20（新北、宜蘭、澎湖 低收／中低收認定）補 incomeEstimateSufficient —— 與另外 18 筆認定類一致（2026-10-29）。
   依據：Lonck 2026-10-20 定「推算只代表可以去申請列冊，最高 possible；認定類例外」（KNOWN-ISSUES W-020 第 1397 行附近）。
   g5 子代理刻意沒設（怕普通人回歸變紅）；認定類本來就該讓收入推算符合的人看到 confirmed，回歸白名單改由同一判準放行。
   用法：python mark_ies_2_10_20_20261029.py [--apply]"""
import json, sys, psycopg2
IDS = [2, 10, 20]
cur_conn = psycopg2.connect(dbname='welfare_check'); cur = cur_conn.cursor()
cur.execute('select id, name, eligibility_conditions from benefits where id = any(%s)', (IDS,))
for bid, name, ec in cur.fetchall():
    assert name == '低收入戶 / 中低收入戶認定', (bid, name)
    assert ec.get('incomeThreshold') == 'mid_low_income', (bid, ec)
    ec['incomeEstimateSufficient'] = True
    ec['_incomeEstimateNote'] = '認定類本身＝申請列冊，收入推算符合即可申請（Lonck 2026-10-20，比照 6／8）'
    print(bid, name)
    if '--apply' in sys.argv:
        cur.execute('update benefits set eligibility_conditions=%s, updated_at=now() where id=%s', (json.dumps(ec, ensure_ascii=False), bid))
if '--apply' in sys.argv:
    cur_conn.commit(); print('✅ 已寫入', len(IDS))
