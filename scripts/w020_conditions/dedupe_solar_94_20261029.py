"""經濟部「家戶屋頂設置太陽光電加速計畫」只留全國一筆 94（2026-10-29 Lonck 選 A）。
   957 桃園、972 新竹縣：原文「依據：經濟部補助直轄市及縣(市)政府辦理家戶屋頂設置太陽光電加速計畫審查作業要點」，
     金額 3,000／瓩、上限 30 萬；ATS 2 萬／瓩、上限 200 萬 —— 與 94 完全相同 ⇒ 縣市只是受理窗口 ⇒ 停用。
   保留：585 新北（標題「加速計畫**暨新北加碼補助**」，有地方自己的加碼）、989 臺東（縣府自辦每峰瓩 7,000，不同計畫）。
   94 描述補一句「向居住縣市政府申請」—— 停掉縣市那幾筆後，使用者要從 94 知道窗口在哪。
   用法：python dedupe_solar_94_20261029.py [--apply]"""
import sys, psycopg2
REASON = '2026-10-29 Lonck 選 A：與全國 94 同一個經濟部加速計畫（縣市只是受理窗口），只留全國一筆'
ADD = '申請窗口是居住地的直轄市、縣（市）政府（例：桃園市經濟發展局、新竹縣政府產業發展處），受理期限依各縣市公告；新北市、臺東縣另有地方自己的加碼或獎勵，見各自項目。'
conn = psycopg2.connect(dbname='welfare_check'); cur = conn.cursor()
cur.execute('select id, is_active, name, description from benefits where id in (94,957,972,585,989) order by id')
rows = {r[0]: r[1:] for r in cur.fetchall()}
for i in (94, 957, 972, 585, 989):
    assert rows[i][0] is True, (i, '已不是啟用中，停下來看')
d94 = rows[94][2]
assert ADD not in d94
print('停用 957', rows[957][1]); print('停用 972', rows[972][1]); print('保留 585', rows[585][1]); print('保留 989', rows[989][1])
print('94 描述補：', ADD)
if '--apply' in sys.argv:
    cur.execute("""update benefits set is_active=false, validity_status='deactivated', deactivated_at=now(),
                   deactivated_reason=%s, updated_at=now() where id in (957,972)""", (REASON,))
    assert cur.rowcount == 2
    cur.execute('update benefits set description=%s, updated_at=now() where id=94', (d94 + ADD,))
    conn.commit(); print('✅ 已寫入')
else:
    print('(dry-run)')
