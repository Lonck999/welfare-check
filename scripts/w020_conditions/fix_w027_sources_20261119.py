"""W-027 D（2026-11-19）：中低收入老人假牙補助（地方明細）換成 115 年度／現行官方來源。

範圍 7 筆：413 臺南、414 高雄、419 新竹縣、420 苗栗、422 南投、425 屏東、427 花蓮。
來源逐筆單抓（web_extract 單網址／curl + pypdf），讀正文；原文存
~/.hermes/cache/welfare_w027_20261119/*.txt，報告 sources_report.md。

只改：source_url、source_excerpt、application_period、amount_max/unit/note（有原文依據才改）、
last_verified_date=CURRENT_DATE。eligibility_conditions / description 一律不動（不一致處列在報告）。
每筆先 assert 舊值與 DB 一致（source_url、application_period、amount_*、amount_note/source_excerpt 的 md5）。

用法：python fix_w027_sources_20261119.py [--apply]   （預設 dry-run）
"""
import os, sys, hashlib, psycopg2

NEUTRAL = '官方頁未載受理期間；須先申請核准後才能至合約診所製作假牙'
KEEP = object()  # 不改此欄

def md5(s):
    return hashlib.md5(s.encode()).hexdigest() if s else None

# 舊值：(source_url, application_period, amount_max, amount_unit, md5(amount_note), md5(source_excerpt))
OLD = {
 413: ('https://w3fs.tainan.gov.tw/Download.ashx?n=6Ie65Y2X5biC5pS%2F5bqcMTExIOW5tOW6puS4reS9juaUtuWFpeiAgeS6uuijnOWKqeijnee9ruWBh%2BeJmeWvpuaWveioiOeVqy5wZGY%3D&u=LzAwMS9VcGxvYWQvMTYzL3JlbGZpbGUvMTc3NDcvNzg3NDAyMi9hNTA0NjUyOS1mMmE1LTQ4OTMtYTllMi1lMGQyNjQ3ODUzZjMucGRm',
       NEUTRAL, 44000, 'one_time', 'd0c14238ed3cd4557df593c84be3af47', '33697f155af749876475874216c06122'),
 414: ('https://orgws.kcg.gov.tw/001/KcgOrgUploadFiles/463/RelFile/0/85588/f9ffecdb-3862-4173-be18-4b26aa270d6d.pdf',
       NEUTRAL, None, None, None, '33697f155af749876475874216c06122'),
 419: ('https://travel.hsinchu.gov.tw/News/Content/Go5lQr1XvQkY',
       NEUTRAL, 44000, 'yearly', '622e19eb96fe35a6ccc74c6db97415fb', '33697f155af749876475874216c06122'),
 420: ('https://webws.miaoli.gov.tw/Download.ashx?n=MjAxNjA3MDQwNTUyMTIxMTQzNTc1NDgwLnBkZg%3D%3D&u=LzAwMS9VcGxvYWQvMDAxL3VwbG9hZC80NTgvcmVsZmlsZS8xMDU3My8xMjg0MjYvMGM4NzcwYTQtMjA5Zi00ODI5LTkyODYtYTEwNTM4ODAxOWUwLnBkZg%3D%3D',
       NEUTRAL, None, None, None, '33697f155af749876475874216c06122'),
 422: ('https://www.nantou.gov.tw/big5/news_content.php?dptid=376480000&id=149267',
       NEUTRAL, None, None, None, '33697f155af749876475874216c06122'),
 425: ('https://www.pthg.gov.tw/News_Content.aspx?n=EC690F93E81FF22D&s=B69882359E3DA422',
       NEUTRAL, None, 'yearly', 'c504f2736af7c7a17840fad0245d7bd1', '0440c0d8f546ecc8c9d02c584bd59af6'),
 427: ('https://sa.hl.gov.tw/Upload/202609301352475228171.pdf',
       NEUTRAL, 44000, 'yearly', '1069b8839cc38820ac420fb630f09615', '33697f155af749876475874216c06122'),
}

# 新值：url, excerpt（只放講到本項的句子）, period, amount_max, amount_unit, amount_note
NEW = {
 413: dict(  # 臺南市政府社會局「中低收入老人補助裝置假牙實施計畫」頁附件：臺南市115年度實施計畫.pdf
  url='https://w3fs.tainan.gov.tw/Download.ashx?u=LzAwMi9GUzAxLzE3Ny9yZWxmaWxlLzE5NDk3LzQzNzgzMDAvNjRhN2U2NzAtOTRhNC00MWNkLTljMjMtZWFmYWRkOTkyMmUxLnBkZg%3d%3d&n=6Ie65Y2X5biCMTE15bm05bqm5Lit5L2O5pS25YWl6ICB5Lq66KOc5Yqp6KOd572u5YGH54mZ5a%2bm5pa96KiI55WrLnBkZg%3d%3d',
  excerpt='臺南市115年度中低收入老人補助裝置假牙實施計畫：四、計畫實施日及受理期限：(一)申請者：自即日起接受民眾申請至115年12月10日止（或額滿為止）；若申請人數眾多而經費不足支應時，依補助態樣之優先順序予以補助。(二)診所：115年12月15日前寄件至公會。…八、…1 上下顎全口活動假牙 上、下顎全口假牙 44,000元…9 活動假牙維修費…6,600元',
  period='即日起至 115/12/10 止（或額滿為止，經費不足依補助態樣優先順序）；合約診所 115/12/15 前寄件至牙醫師公會，郵戳為憑',
  amount_max=KEEP, amount_unit=KEEP,
  amount_note='上下顎全口活動假牙最高補助 44,000 元；同一顎已取得相同補助須滿 5 年始得重新申請；活動假牙維修費最高 6,600 元'),
 414: dict(  # 高雄市政府衛生局 老人免費裝假牙「專區介紹」（中低收老人段）；海報/QA PDF 為圖檔，未載裝置金額 → 金額不動
  url='https://health.kcg.gov.tw/Content_List.aspx?n=10DD8AF6AAB2F133',
  excerpt='本年度補助計畫申請於115年3月7日額滿截止。…2. 中低收老人 (一)篩檢條件：1.年齡：民國50年12月31日(含)前出生之65歲以上長輩或民國60年12月31日(含)前出生之55歲以上原住民。…(二)篩檢期間：115年3月1日起額滿為止(名額有限，額滿即停止篩檢)。',
  period='115/3/1 起篩檢至額滿為止（名額有限，額滿即停止篩檢）；衛生局專區公告「本年度補助計畫申請於115年3月7日額滿截止」',
  amount_max=KEEP, amount_unit=KEEP, amount_note=KEEP),
 419: dict(  # 新竹縣政府高齡長照處「中低收入老人假牙補助」頁附件：新竹縣115年度中低收入老人補助裝置假牙實施計畫.pdf
  url='https://ws.hsinchu.gov.tw/Download.ashx?u=LzAwMS9VcGxvYWQvMjkvcmVsZmlsZS8xMDI1Ni8zMTE3MDIvMTJmMDdiOTctYjhiYi00MTNjLWE5OGEtZjA4OTMxYjcwZmI4LnBkZg%3d%3d&n=5paw56u557ijMTE15bm05bqm5Lit5L2O5pS25YWl6ICB5Lq66KOc5Yqp6KOd572u5YGH54mZ5a%2bm5pa96KiI55WrLnBkZg%3d%3d',
  excerpt='新竹縣115年度中低收入老人補助裝置假牙實施計畫：（二）服務對象經核准獲本計畫補助者，自核准年度起5年內不得再次申請。每次補助最高金額不得逾新臺幣（下同）4萬4,000元，惟假牙維修不在此限。…十二、本計畫實施期間，自中華民國115年1月1日至115年12月31日止。',
  period='115/1/1–115/12/31（計畫實施期間）；治療前向戶籍所在地鄉鎮市公所申請，經縣府核定後始得裝置',
  amount_max=KEEP, amount_unit='one_time',
  amount_note='每次補助最高 4 萬 4,000 元，自核准年度起 5 年內不得再次申請；活動假牙維修費每年最高 6,600 元（不在此限）'),
 420: dict(  # 苗栗縣政府社會處「申辦須知」→ 苗栗縣中低收入老人補助裝置假牙（上版 114-10-30）附件；⚠ 非標「115年度」，為現行修正版
  url='https://webws.miaoli.gov.tw/Download.ashx?u=LzAwMS9VcGxvYWQvNDEwL3JlbGZpbGUvOTQ2OC80MDY0My9jZjUzZWViYy00ZTU1LTQ5NTUtYmYwZC1iZjU3NGYwYzUwNTgucGRm&n=MTE05bm05Lit5L2O5pS25YWl6ICB5Lq66KOc5Yqp6KOd572u5YGH54mZ5a%2bm5pa96KiI55Wr5L%2bu5q2jLTExNDEwMzAucGRm',
  excerpt='苗栗縣政府辦理中低收入老人補助裝置假牙實施計畫（114年10月30日府社老字第1140235625號函修正）：（二）補助對象獲本計畫補助，5年內最高補助金額不得逾新臺幣5萬元(假牙維修不在此限)。…六、申請時間：每年10月30日前受理申請。',
  period='每年 10/30 前受理申請；向戶籍所在地鄉鎮市公所提出申請',
  amount_max=50000, amount_unit='one_time',
  amount_note='5 年內最高補助金額不得逾 5 萬元（假牙維修不在此限，維修每年最高 6,600 元）'),
 422: dict(  # 南投縣政府衛生局（草屯鎮衛生所）「115年南投縣老人裝置假牙補助申請」頁；縣府 115 實施計畫未公開（衛生局只掛 109 年版）
  url='https://www.ntshb.gov.tw/center/form/Details?Parser=2%2C24%2C525%2C496%2C%2C%2C2688',
  excerpt='115年南投縣老人裝置假牙補助申請開始囉!只要您符合以下資格，經醫師評估後有需求，即可送件申請。 第一類：請送戶籍所在地鄉(鎮、市)公所 福利身分 (由公所查詢)設籍本縣年滿六十五歲以上或年滿五十五歲以上原住民 □低收入戶、中低收入戶者 □領有中低收入老人生活津貼者 □經政府全額補助收容安置者 □領有身心障礙生活補助者 □經各級政府補助身心障礙者日間照顧及住宿式照顧費用達 50%以上',
  period=NEUTRAL,
  amount_max=KEEP, amount_unit=KEEP, amount_note=KEEP),
 425: dict(  # 屏東縣政府便民服務整合申辦平台「中低收入老人假牙補助申請」（社會處老人福利頁所連）；頁面未載金額 → 金額不動
  url='https://onestop.pthg.gov.tw/eservice/apply_mode_directions2?itemId=648',
  excerpt='中低收入老人假牙補助申請 服務對象：設籍本縣年滿 65 歲以上或年滿 55 歲以上原住民，經醫師評估缺牙需裝置活動假牙，並符合下列條件之一者：(申請者同一顎已取得相同補助項目者須於滿五年以上，經評估有重新裝置必要，始得重新提出申請。但假牙維修費不在此限。)',
  period=NEUTRAL,
  amount_max=KEEP, amount_unit=KEEP, amount_note=KEEP),
 427: dict(  # 花蓮縣政府社會處「花蓮縣65歲以上長者假牙補助」（115/6/1 起，中低收長者為第二類）
  url='https://sa.hl.gov.tw/Detail_sp/1d9e430707144c7482f7aa8db508e4dd',
  excerpt='花蓮縣65歲以上長者假牙補助：二、受理申請時間 自115年6月1日起受理申請，至經費用罄為止。…2.服務對象獲本計畫補助，一般 65 歲以上長者5年內最高補助金額不得逾新臺幣5萬元，中低收長者5年內不得逾 新臺幣 5 萬 5,000 元、惟假牙維修不在此限。',
  period='115/6/1 起受理申請，至經費用罄為止；至牙科醫療院所口腔檢查後由院所送件，核定後才裝置',
  amount_max=55000, amount_unit='one_time',
  amount_note='中低收長者 5 年內最高補助不得逾 5 萬 5,000 元（假牙維修不在此限）'),
}

ids = sorted(NEW)
assert ids == sorted(OLD) == [413, 414, 419, 420, 422, 425, 427]
conn = psycopg2.connect(os.environ['DATABASE_URL']); cur = conn.cursor()
cur.execute('select id, name, source_url, application_period, amount_max, amount_unit, amount_note, source_excerpt '
            'from benefits where id = any(%s)', (ids,))
rows = {r[0]: r for r in cur.fetchall()}
assert set(rows) == set(ids), set(ids) - set(rows)
for i in ids:
    r = rows[i]
    assert r[1] == '中低收入老人假牙補助（地方明細）', (i, r[1])
    now = (r[2], r[3], r[4], r[5], md5(r[6]), md5(r[7]))
    assert now == OLD[i], (i, 'DB 舊值已變動', now, OLD[i])

def plan(i):
    n = NEW[i]
    sets = {'source_url': n['url'], 'source_excerpt': n['excerpt'], 'application_period': n['period']}
    for k in ('amount_max', 'amount_unit', 'amount_note'):
        if n[k] is not KEEP:
            sets[k] = n[k]
    return sets

for i in ids:
    r, s = rows[i], plan(i)
    print(f'--- {i}')
    print('  url     :', r[2][:70], '→', s['source_url'][:70])
    if s['application_period'] != r[3]:
        print('  period  :', r[3], '→', s['application_period'])
    for k, idx in (('amount_max', 4), ('amount_unit', 5), ('amount_note', 6)):
        if k in s and s[k] != r[idx]:
            print(f'  {k:<8}:', str(r[idx])[:50], '→', s[k])
    print('  excerpt :', s['source_excerpt'][:60], '…')

if '--apply' not in sys.argv:
    print('(dry-run，未寫入；加 --apply 才寫)'); sys.exit()

cur.execute('create table benefits_before_w027_sources_20261119 as select * from benefits where id = any(%s)', (ids,))
for i in ids:
    s = plan(i)
    cols = ', '.join(f'{k}=%s' for k in s)
    cur.execute(f'update benefits set {cols}, last_verified_date=CURRENT_DATE, updated_at=now() where id=%s',
                (*s.values(), i))
    assert cur.rowcount == 1, i
conn.commit(); print('✅ updated', ids, '｜備份 benefits_before_w027_sources_20261119')
