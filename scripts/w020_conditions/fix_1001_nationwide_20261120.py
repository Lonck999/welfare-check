"""1001 新北環保葬鼓勵措施改為全國都查得到（2026-11-20 Lonck 選：「原文不限市民，家人骨灰放在新北的人住哪都可能用得到」）。
原文申請條件（三）「申請人及亡者不限新北市民」⇒ 限的是骨灰（骸）存放地，不是申請人戶籍。
🔴 /api/check 是用 benefits.county 撈資料（check.ts:211：county IS NULL／'全國'／本縣市／工作縣市），
   只改 eligibility_conditions.counties 不夠 ⇒ county 也要改成「全國」（比照 993 原民會假牙：county 全國＋counties ['全國']）。
   名稱與機關仍寫新北，「新北骨灰」條件寫進 unchecked 第一條。
用法：python fix_1001_nationwide_20261120.py [--apply]"""
import json, os, sys, psycopg2
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from eligibility_guard import assert_substantive
c = psycopg2.connect(os.environ['DATABASE_URL']); cur = c.cursor()
cur.execute('select name, county, eligibility_conditions from benefits where id=1001')
n, co, ec = cur.fetchone()
assert n == '新北市環保葬鼓勵措施' and co == '新北市' and ec['counties'] == ['新北市'], (n, co, ec.get('counties'))
u = [x for x in ec['uncheckedConditions'] if x != '申請人及亡者不限新北市民（原文）']
assert len(u) == len(ec['uncheckedConditions']) - 1
new = {**ec, 'counties': ['全國'],
       'uncheckedConditions': ['骨灰（骸）原存放於新北市公立納骨塔、或埋葬（藏）於新北市公墓（申請人及亡者不限新北市民，住哪裡都可申請）'] + u,
       '_source': ec['_source'] + '｜2026-11-20 Lonck 選全國可見：原文（三）「申請人及亡者不限新北市民」，限的是骨灰存放地；county 改全國（check.ts 依 county 撈）'}
assert_substantive(new, label='1001')
print(json.dumps(new['uncheckedConditions'], ensure_ascii=False, indent=1))
if '--apply' not in sys.argv: print('(dry-run)'); sys.exit()
cur.execute('create table benefits_before_1001_20261120 as select * from benefits where id=1001')
cur.execute("update benefits set county='全國', eligibility_conditions=%s::jsonb, updated_at=now() where id=1001", (json.dumps(new, ensure_ascii=False),))
c.commit(); print('✅ 1001 → 全國')
