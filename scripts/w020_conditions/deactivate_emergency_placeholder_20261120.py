"""「縣市政府急難慰問金（地方明細）」占位列 3 筆停用（2026-11-20，比照 11-19 491↔754）。
三筆的 description 都是同一段「急難救助是三層制度…」中央制度介紹（不是該縣市原文），條件只有 acute_hardship＋縣市；
source_url 與該縣市已收錄、條件依原文編過的「急難救助」列一字不差 ⇒ 同一項福利重複出現。
  486 嘉義市 → 773（嘉義市辦理急難救助實施要點）
  492 雲林縣 → 830（雲林智慧福利資訊網「急難救助」）
  478 臺北市 → 794（臺北市急難救助）
用法：python deactivate_emergency_placeholder_20261120.py [--apply]"""
import os, sys, psycopg2
PAIR = {486: 773, 492: 830, 478: 794}
c = psycopg2.connect(os.environ['DATABASE_URL']); cur = c.cursor()
for p, k in PAIR.items():
    cur.execute('select a.name, a.is_active, a.source_url = b.source_url, b.is_active, b.name, position(%s in a.description) > 0 '
                'from benefits a, benefits b where a.id=%s and b.id=%s', ('三層制度', p, k))
    n, aact, same, bact, bn, ph = cur.fetchone()
    assert n == '縣市政府急難慰問金（地方明細）' and aact and same and bact and ph, (p, k, n, aact, same, bact, ph)
    print(f'{p} → 保留 {k}（{bn}）')
if '--apply' not in sys.argv: print('(dry-run)'); sys.exit()
cur.execute('create table benefits_before_emerg_placeholder_20261120 as select * from benefits where id = any(%s)', (list(PAIR),))
for p, k in PAIR.items():
    r = (f'2026-11-20 讀原文：與 {k} 重複 —— {p} 是「縣市政府急難慰問金（地方明細）」占位列，description 是中央三層制度介紹、'
         f'source_url 與 {k}（已依該縣市原文編條件）相同（比照 11-19 491↔754）')
    cur.execute("update benefits set is_active=false, deactivated_at=now(), deactivated_reason=%s, validity_status='deactivated', updated_at=now() where id=%s", (r, p))
c.commit(); print('✅ 停用', sorted(PAIR))
