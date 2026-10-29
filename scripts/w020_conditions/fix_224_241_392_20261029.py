"""B 批 2 判讀順帶查到的 3 筆既有資料錯誤（2026-10-29），依原文更正。
   224 臺東健保代繳：原文「年滿 70 歲且設籍臺東滿一年」—— DB 寫 65 歲（錯）
   241 花蓮健保補助：原文 115/6/1 起「凡設籍花蓮縣滿 1 年且年滿 65 歲以上長者」—— DB 描述仍是舊的「65–未滿 70 歲中低收」
   392 臺東重陽禮金：原文 115 年起 500 → 2,000 元 —— DB 描述只寫敬老卡
   用法：python fix_224_241_392_20261029.py [--apply]"""
import json, sys, psycopg2
TT = 'https://ttdp.taitung.gov.tw/News_Content.aspx?n=13561&s=143664'
HL = 'https://www.hl.gov.tw/News_Content.aspx?n=32725&s=210063'
X = {
 224: dict(name='臺東縣 70 歲以上長者健保費代繳',
           description='臺東縣政府自 115 年起，為年滿 70 歲且設籍臺東滿一年之長者代繳全民健保自付保險費（每月最高約 826 元），免申請。',
           cond={'ageMin': 70, 'minResidencyMonths': 12},
           src=f'臺東縣社會處新聞 114-12-09「敬老再升級．幸福加碼在臺東」：年滿 70 歲且設籍臺東滿一年之長者代繳健保費自付額（{TT}）',
           anchor_old=('ageMin', 65)),
 241: dict(name='花蓮縣 65 歲以上長者健保費補助',
           description='花蓮縣自 115 年 6 月 1 日起，設籍花蓮縣滿 1 年且年滿 65 歲以上之長者，補助全民健保自付保險費，每人每月最高 826 元（健保第六類地區人口自付額）；由縣府彙整送健保署，民眾無須申請、切勿自行退保。',
           cond={'ageMin': 65, 'minResidencyMonths': 12},
           src=f'花蓮縣政府新聞稿「擴大補助 65 歲以上健保費…自 6 月 1 日起實施」：凡設籍花蓮縣滿 1 年且年滿 65 歲以上長者均可享有健保費補助（{HL}）',
           anchor_old=('ageMin', 65)),
 392: dict(name=None,
           description='臺東縣敬老福利：敬老卡點數每月 1,500 點（1 點 1 元）；重陽節敬老禮金自 115 年起由 500 元提高為 2,000 元。',
           cond=None,
           src=f'臺東縣社會處新聞 114-12-09：重陽節敬老禮金由 500 元提高至 2,000 元（{TT}）',
           anchor_old=('ageMin', 65)),
}
conn = psycopg2.connect(dbname='welfare_check'); cur = conn.cursor()
cur.execute('select id, name, description, eligibility_conditions, source_url from benefits where id = any(%s) and is_active', (list(X),))
rows = {r[0]: r[1:] for r in cur.fetchall()}; assert set(rows) == set(X), set(X) - set(rows)
for bid, x in sorted(X.items()):
    name, desc, ec, url = rows[bid]; ec = dict(ec or {})
    k, v = x['anchor_old']; assert ec.get(k) == v, (bid, '舊值已變，停下來看', ec)
    new_ec = dict(ec)
    if x['cond']:
        new_ec.update(x['cond'])
    new_ec['_source'] = 'W-020/B批2 2026-10-29 依原文更正：' + x['src']
    new_name = x['name'] or name
    print(bid, name, '→', new_name, '|', {kk: new_ec[kk] for kk in new_ec if not kk.startswith('_')})
    if '--apply' in sys.argv:
        cur.execute('update benefits set name=%s, description=%s, eligibility_conditions=%s, updated_at=now() where id=%s',
                    (new_name, x['description'], json.dumps(new_ec, ensure_ascii=False), bid))
if '--apply' in sys.argv:
    conn.commit(); print('✅ 已寫入', len(X))
else:
    print('(dry-run)', len(X))
