"""C-6b：363「電動自行車購車補助（地方加碼）」名稱與來源不符 ⇒ 依原文改名、改描述與金額（比照 10-30 fix_ebike_flags Lonck 選 A）。
   原文：雲林縣政府新聞參考資料 115.02.13「雲林縣115年機車補助最高2.5萬元 二行程汰舊和換購電動機車加碼最多」
   🔴 原 amount_max 40,500 是「縣府 2.5 萬＋環境部＋經濟部約 15,500」合計 —— 經濟部那段已是 324 另一筆 ⇒ 本筆只記縣府 25,000。
   同網址的 339 已於 10-13 停用（同計畫重複），不復用。
   備份：benefits_before_c6b_3nocond_20261116（含 363 原始列）
   用法：python fix_363_rename_20261116.py [--apply]"""
import os, sys, psycopg2

URL = 'https://dsh.yunlin.gov.tw/News_Content.aspx?n=7200&s=581551&sms=9662'
NAME = '雲林縣 115 年度淘汰老舊機車及換、新購電動二輪車補助'
DESC = ('雲林縣 115 至 117 年淘汰老舊機車及換、新購電動二輪車補助計畫（環保局，115/2/13 起線上申請，各項目限額、額滿即停）：'
        '一般民眾換購電動機車 1.5 萬元、新購 1 萬元；中低收入戶換購電動機車最高 2.5 萬元；二行程機車回收報廢 5,000 元；換購微型電動二輪車 8,000 元。'
        '申請年度前 3 年未受縣府此項補助即可申請；多數項目補助金額逐年減少。另可自行向環境部（回收獎勵金）、抵換媒合平臺、經濟部產業發展署另外申請。'
        '詳見雲林縣機車定檢與污染管制資訊網 https://ylepb-rmei.easylife.net.tw/ 或洽 05-5526398。')
NOTE = '縣府補助：一般換購電動機車 15,000／新購 10,000／中低收換購 25,000／二行程報廢 5,000／換購微型電動二輪車 8,000；另加環境部、經濟部補助總計最高上看 40,500（經濟部部分見全國中央基準那筆）'
EX = ('雲林縣政府新聞參考資料 115.02.13 …公告115 至 117 年淘汰老舊機車及換、新購電動二輪車補助計畫…增加二行程機車完成回收與報廢補助為5,000元…換購微型電動二輪車補助8,000元選項。'
      '在電動機車部分，提高一般民眾換購與新購電動機車補助金額…分別補助1.5萬與1萬元。整體補助則以中低收入戶換購電動機車補助2.5萬元為最高，再加上環境部與經濟部額外補助 約15,500 元，則總補助金額最高上看4萬500元。'
      '…縣民只要在申請年度前3年…未受縣政府此項補助，就可提出申請。')

conn = psycopg2.connect(os.environ['DATABASE_URL']); cur = conn.cursor()
cur.execute('select name, source_url, amount_max from benefits where id=363'); n, u, a = cur.fetchone()
assert n == '電動自行車購車補助（地方加碼）' and u == URL and a == 40500, (n, u, a)
cur.execute("select id from benefits where replace(name,' ','')=replace(%s,' ','')", (NAME,)); assert cur.fetchone() is None
print(f'363：{n} → {NAME}；amount_max {a} → 25000')
if '--apply' not in sys.argv:
    print('(dry-run)'); sys.exit()
cur.execute('''update benefits set name=%s, description=%s, amount_min=5000, amount_max=25000, amount_unit='one_time', amount_note=%s,
               source_excerpt=%s, quota_limited=true, validity_status='valid_current', validity_checked_at=now(),
               validity_evidence='2026-11-16 讀環保局新聞稿 115.02.13：公告 115 至 117 年補助計畫，2/13 起受理',
               last_verified_date=current_date, updated_at=now() where id=363''', (NAME, DESC, NOTE, EX))
conn.commit(); print('✅ 363 改寫')
