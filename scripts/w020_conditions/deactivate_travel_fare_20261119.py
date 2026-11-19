"""775 嘉義市短缺川資／511 臺南行旅川資停用（2026-11-19 Lonck 選停用）。
理由（Lonck 原話）：「網站是給填問卷的人查自己能領什麼，故鄉以外的過路客不會來查」。
對象是在當地身無分文的外地旅客，與「依填表人戶籍／居住地查自己能領什麼」的網站定位不合。
用法：python deactivate_travel_fare_20261119.py [--apply]"""
import os, sys, psycopg2
R = '2026-11-19 Lonck 選停用：對象是在當地缺旅費的外地旅客（給車資回戶籍地），網站是給填問卷的人查自己能領什麼，過路客不會來查'
IDS = {775: '短缺川資補助', 511: '行旅川資救助'}
c = psycopg2.connect(os.environ['DATABASE_URL']); cur = c.cursor()
cur.execute('select id, name, is_active from benefits where id = any(%s)', (list(IDS),))
rows = {i: (n, a) for i, n, a in cur.fetchall()}
assert all(rows[i] == (n, True) for i, n in IDS.items()), rows
print('將停用', sorted(IDS))
if '--apply' not in sys.argv: print('(dry-run)'); sys.exit()
cur.execute('create table benefits_before_travel_fare_20261119 as select * from benefits where id = any(%s)', (list(IDS),))
cur.execute("update benefits set is_active=false, deactivated_at=now(), deactivated_reason=%s, validity_status='deactivated', updated_at=now() where id = any(%s)", (R, list(IDS)))
c.commit(); print('✅ 停用', sorted(IDS))
