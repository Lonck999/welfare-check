"""481 臺中「縣市政府急難慰問金（地方明細）」停用：source_url 與 719 臺中「市急難救助」是同一頁（社會局 post 135886，前者是選單路徑版），
description 是中央三層制度介紹 ⇒ 重複（比照 486／492／478、491）。用法：python ...py [--apply]"""
import os, sys, psycopg2
c = psycopg2.connect(os.environ['DATABASE_URL']); cur = c.cursor()
cur.execute("select a.name, a.is_active, b.is_active, a.source_url like '%%/135886', b.source_url like '%%/135886/post', position('三層制度' in a.description)>0 from benefits a, benefits b where a.id=481 and b.id=719")
n, aa, ba, u1, u2, ph = cur.fetchone(); assert n == '縣市政府急難慰問金（地方明細）' and aa and ba and u1 and u2 and ph
if '--apply' not in sys.argv: print('(dry-run) 481 → 保留 719'); sys.exit()
cur.execute('create table benefits_before_emerg_481_20261120 as select * from benefits where id=481')
cur.execute("update benefits set is_active=false, deactivated_at=now(), validity_status='deactivated', updated_at=now(), deactivated_reason=%s where id=481",
            ('2026-11-20 讀原文：與 719 重複 —— 481 是「縣市政府急難慰問金（地方明細）」占位列，description 是中央三層制度介紹，source_url 與 719 臺中市急難救助同一頁（post 135886）',))
c.commit(); print('✅ 停用 481')
