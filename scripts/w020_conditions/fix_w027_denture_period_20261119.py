"""W-027（2026-11-19）：假牙補助 application_period 範本句＋「5 年內」金額單位。
2026-11-19 19:4x 逐筆 web_extract（🔴 單筆抓、以網址對應 —— 同批多網址回傳順序會跟輸入不同，第一次批次抓整份對錯）。

A. 原文寫得出受理期 → 照原文改（並設 deadline_type）
B. amount_note 原文是「5 年內最高…」→ amount_unit yearly → one_time
C. 原文沒寫受理期 → 範本「常態受理」是沒依據的主張 ⇒ 改成中性句，不自己編期間
D. 來源不對（舊年度／問卷／新聞／404）→ 期間也改中性句，換來源另排（KNOWN-ISSUES W-027）
用法：python fix_w027_denture_period_20261119.py [--apply]
"""
import os, sys, psycopg2

TEMPLATE = '常態受理，須先申請核准後才能至合約診所製作假牙'
NEUTRAL = '官方頁未載受理期間；須先申請核准後才能至合約診所製作假牙'
A = {  # id: (period, deadline_type, deadline_date, 原文片段)
 411: ('年度內經費用罄後不再受理申請；須先申請核准後才能至合約診所製作假牙', 'annual', None, '3、年度內經費用罄後不再受理申請。'),
 412: ('即日起至 115/10/31 止（郵戳為憑，經費用罄可能提前停止）；由特約診所送件', 'fixed', '2026-10-31',
       '受理期程 假牙補助申請期限：即日起至115年10月31日止，以郵戳為憑…逾期不受理（經費用罄即可能停止受理申請）'),
 417: ('115/1/1–115/12/31；社會處於農曆年後寄發通知單', 'fixed', '2026-12-31', '四、本項補助條件自115年1月1日起至115年12月31日止'),
 418: ('當年度至經費用罄為止；向戶籍地鄉（鎮、市）公所申請', 'annual', None, '二、申請日期：當年度至經費用罄為止。'),
 430: ('每年 1/1–9/30（4 月底前優先受理中低收入戶老人，5/1 起受理非中低收入戶老人）；經費用罄即停止', 'annual', None,
       '十一、…受理申請補助期限自每年一月一日起至九月三十日前截止'),
 604: ('每年 1/1–10/31，經費用罄提前停止收案', 'annual', None, '肆、受理申請期間 每年1月1日至10月31日。…該年度假牙補助經費用罄，則提前停止收案'),
}
B = [410, 412, 418, 604, 642]          # amount_note 原文「5 年內最高補助金額不得逾…」
C = [408, 409, 410, 415, 423, 428, 429]   # 642 的 period 是「20天」（處理期限），不是範本句，不動
D = [413, 414, 419, 420, 422, 425, 427]  # 來源要換

conn = psycopg2.connect(os.environ['DATABASE_URL']); cur = conn.cursor()
ids = sorted(set(A) | set(B) | set(C) | set(D))
cur.execute('select id, application_period, amount_unit, amount_note from benefits where id = any(%s)', (ids,))
cur_rows = {r[0]: r[1:] for r in cur.fetchall()}
assert set(cur_rows) == set(ids)
assert not (set(A) & set(C)) and not (set(A) & set(D)) and not (set(C) & set(D))
for i in (set(A) | set(C) | set(D)) - {604}:
    assert cur_rows[i][0] == TEMPLATE, (i, cur_rows[i][0])
for i in B:
    assert cur_rows[i][1] == 'yearly' and ('5年內' in cur_rows[i][2] or '五年內' in cur_rows[i][2]), (i, cur_rows[i][1:3])
for i in ids:
    tag = 'A' if i in A else 'C' if i in C else 'D' if i in D else ''
    print(i, tag, 'B' if i in B else '', '｜舊：', (cur_rows[i][0] or '')[:20], '→', (A[i][0] if i in A else NEUTRAL if tag else '(期間不動)')[:40])
if '--apply' not in sys.argv:
    print('(dry-run)'); sys.exit()
cur.execute('create table benefits_before_w027_20261119 as select * from benefits where id = any(%s)', (ids,))
for i, (p, dt, dd, ex) in A.items():
    cur.execute('update benefits set application_period=%s, deadline_type=%s, deadline_date=%s, updated_at=now() where id=%s', (p, dt, dd, i))
for i in C + D:
    cur.execute('update benefits set application_period=%s, updated_at=now() where id=%s', (NEUTRAL, i))
for i in B:
    cur.execute("update benefits set amount_unit='one_time', updated_at=now() where id=%s", (i,))
conn.commit(); print('✅ A', sorted(A), 'B', B, 'C', C, 'D', D)
