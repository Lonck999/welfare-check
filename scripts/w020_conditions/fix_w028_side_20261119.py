"""W-028 子代理順帶點出的 6 件事中「原文明確、有前例」的部分（2026-11-19，只做 dry-run 準備，待 Lonck 審）。
報告：~/.hermes/cache/welfare_w027_20261119/w028_side_report.md（逐件結論、原文句、建議）

  停用（重複；比照 599↔1003、296↔675、10-29 原民假牙「縣市只是窗口，只留全國一筆」、479／482 地方明細占位列）：
    553 新北「體外受精人工生殖技術補助」＝ 318 國健署全國方案（新北頁只是轉述、申請走國健署特約機構；且是舊版 44 歲(含)）
    410 新北「中低收入老人假牙補助（地方明細）」＝ 642 同一頁內容（社會局「中、低收入老人補助裝置假牙」逐字相同）
    505 臺南「低收入戶家庭生活扶助」（常見問答頁 113-06-03）＝ 501 社會局「低收入戶家庭生活補助」專頁（115-10-14）
    491 南投「縣市政府急難慰問金（地方明細）」＝ 754 南投急難救助（來源原本指到原民處申請表）
  改寫（名稱／描述／來源換成現行官方原文；條件不動）：
    501 臺南：名稱「低收入戶」→「低收入戶家庭生活補助」，描述與金額照專頁
    519 臺南天然災害：source_url 從 114 年 0121 地震專頁換成社會局「天然災害救助」頁（115-02-11 修改）
    543 新北帶狀疱疹疫苗：source_url 從 114 年舊新聞換成衛生局 115/5/26「9 月 1 日起擴大」新聞，描述改成 115 年版
    642 新北假牙：source_excerpt 換成原文；application_period「20天」是處理期限 → 改中性句（比照 W-027 C）
  🔴 不在本腳本（要 Lonck 決定）：775 嘉義市川資／1001 新北環保葬的 counties 語意、318 ageMax、754 金額上限、486 嘉義市
用法：python fix_w028_side_20261119.py [--apply]   （預設 dry-run）
"""
import json, os, sys, psycopg2
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from eligibility_guard import assert_substantive

T = '2026-11-19 W-028 順帶'
BACKUP = 'benefits_before_w028_side_20261119'

DEACT = {
 553: f'{T} 讀原文：與 318 重複 —— 新北市衛生局頁講的就是國民健康署全國「體外受精(俗稱試管嬰兒)人工生殖技術補助方案」'
      '（「申請方式：由上述特約機構至國民健康署指定之資訊系統，辦理申請人資格審查及費用申請作業」），新北沒有自辦加碼；'
      '且為舊版（「妻年齡為44歲(含)以下」），國健署現行頁（2026/03/31 更新、3.0 方案「妻年齡為未滿45歲」）已由 318 收錄'
      '（比照 10-29 原民假牙「縣市只是窗口，只留全國一筆」）',
 410: f'{T} 讀原文：與 642 重複 —— 同為新北市社會局「中、低收入老人補助裝置假牙」，福利補助自己查頁（410）與申辦E服務頁（642）'
      '「補助資格」「補助限制」「補助標準」逐字相同；642 描述完整、有線上申辦，410 為「（地方明細）」占位名稱、'
      'source_excerpt 為非官方彙整文字（「最高可達55,000元」與原文「最高補助4萬4,000元」不符）（比照 296↔675）',
 505: f'{T} 讀原文：與 501 重複 —— 505 來源為社會局常見問答「符合低收入戶者，提供哪些扶助?」（修改 113-06-03），'
      '其「(三)低收入戶家庭生活補助 1. 第一款：每人每月發給家庭生活補助費 11,918元。2. 第二款：每戶每月發給家庭生活補助費 6,825元」'
      '就是 501 社會局「低收入戶家庭生活補助」專頁（修改 115-10-14）同一項；FAQ 其他各項另有 502／503 等列（比照 599↔1003）',
 491: f'{T} 讀原文：與 754 重複 —— 491 是「縣市政府急難慰問金（地方明細）」占位列，原 source_url 是原民處「原住民族急難救助申請表」'
      '（「救助對象為設籍本縣非原住民鄉(鎮、市)，並具有原住民身分者」，不是本項）；南投對一般民眾的地方急難救助'
      '（《南投縣辦理民眾急難救助實施要點》「凡設籍本縣之居民，具有社會救助法第二十一條情形之一者，依本要點給予急難救助」、'
      '開放資料 CSV「急難救助」）已由 754 收錄（比照 479／482 地方明細占位列停用、599 重複停用）',
}

EDIT = {
 501: dict(
   old_url='https://sab.tainan.gov.tw/News_Content.aspx?n=21390&s=4378483',
   url='https://sab.tainan.gov.tw/News_Content.aspx?n=21390&s=4378483',
   name='低收入戶家庭生活補助',
   desc=('臺南市列冊低收入戶家庭生活補助：第一款每人每月 11,918 元；第二款每戶每月 6,825 元。'
         '由社會局逕撥入低收入戶指定之郵政（農會）帳戶；洽戶籍所在地區公所社會（政）課。'),
   amount=(6825, 11918, 'monthly', '第一款每人每月 11,918 元；第二款每戶每月 6,825 元（固定發給，非連續區間）'),
   ex=('臺南市政府社會局「低收入戶家庭生活補助」（修改時間 115-10-14）六、服務內容：1.第一款：每人每月發給家庭生活補助費11,918元。'
       '2.第二款：每戶每月發給家庭生活補助費6,825元。七、服務對象：本市列冊之低收入戶'),
   status='valid_current', evidence=f'{T} 讀原文：專頁修改時間 115-10-14，列 115 年度最低生活費公告',
 ),
 519: dict(
   old_url='https://www.tainan.gov.tw/News.aspx?n=44000',
   url='https://sab.tainan.gov.tw/News_Content.aspx?n=21215&s=4779869',
   name='天然災害救助',
   desc=('臺南市天然災害救助（《臺南市災害救助辦法》114/12/17 發布）：本國國民於臺南市轄區內遭受水、火、雹、風、旱、地震或其他災害，'
         '致損害重大影響生活者——死亡救助、失蹤救助每人 20 萬元；重傷救助每人 10 萬元；安遷救助（住屋毀損達不堪居住程度，'
         '須災害發生時已在現址設籍並實際居住）戶內人口每人 2 萬元、以 5 人為限；住戶淹水（50 公分以上）、住屋土石流救助每戶 1 萬 5,000 元'
         '（已核安遷救助者不另發）。災害發生後 30 日內向災害發生地區公所申請，災情嚴重時得公告延長。'),
   period='災害發生後 30 日內向災害發生地區公所申請；災情嚴重時主管機關得公告延長', dl='event',
   ex=('臺南市政府社會局「天然災害救助」（修改時間 115-02-11）：1. 死亡救助…每人發給新臺幣20萬元。2. 失蹤救助…每人發給新臺幣 20萬元。'
       '3. 重傷救助…每人發給新臺幣10萬元。4. 安遷救助：災害發生時已在現址辦妥戶籍登記，並實際居住於現址者…戶內人口每人發給新臺幣 2萬元，以五口為限。'
       '5. 住戶淹水救助：因災害致住屋淹水達 50公分以上者。每戶發給新臺幣15,000元。｜《臺南市災害救助辦法》（114年12月17日發布）'
       '第三條 本國國民於本市轄區內遭受水、火、雹、風…或其他災害，致損害重大影響生活者，予以災害救助。'
       '第八條 申請災害救助者，應於災害發生後三十日內…向災害發生地執行機關提出。（https://sab.tainan.gov.tw/News_Content.aspx?n=21235&s=4780930）'),
   status='valid_current', evidence=f'{T} 換現行來源：社會局頁修改 115-02-11；辦法 114-12-17 發布（舊來源是 114 年 0121 地震專案頁）',
 ),
 543: dict(
   old_url='https://www.health.ntpc.gov.tw/basic/?mode=detail&node=14223',
   url=('https://www.health.ntpc.gov.tw/news/%E5%85%AD%E9%83%BD%E6%9C%80%E5%84%AA%EF%BC%81%E6%96%B0%E5%8C%97%E5%B8%829%E6%9C%881'
        '%E6%97%A5%E8%B5%B7%E6%93%B4%E5%A4%A7%E5%85%A8%E9%A1%8D%E8%A3%9C%E5%8A%A9%E5%B8%B6%E7%8B%80%E7%96%B1%E7%96%B9%E7%96%AB%E8%8B%97%E6%A2%9D%E4%BB%B62026052613'),
   desc=('新北市帶狀疱疹疫苗全額補助（115 年 9 月 1 日起擴大）：設籍新北市且滿 65 歲（原住民 55 歲）以上之低收入戶或中低收入戶，'
         '全額補助接種 2 劑（完整 2 劑費用約 1 萬 6,000 元），不再限高風險疾病。攜健保 IC 卡及低收／中低收入戶證明'
         '（原住民 55 歲以上另附戶口名簿或戶籍謄本；持「新北市中低收入老人生活津貼證明書」不符合）至新北市 29 區衛生所預約接種。'),
   ex=('新北市衛生局「六都最優！新北市9月1日起擴大全額補助帶狀疱疹疫苗條件」（115/5/26）：自9月1日起，擴大至設籍新北市65歲(原住民55歲)以上'
       '低收/中低收入戶者全額補助接種2劑帶狀疱疹疫苗…符合資格市民請攜帶健保卡、低收/中低收證明等資料至本市29區衛生所免費接種。'
       '｜板橋區衛生所「115年度新北市接種帶狀皰疹疫苗擴大接種對象」(一)實施期間 : 自115年9月1日起 (二)實施對象 : 設籍新北市且滿65歲(原住民55歲)以上之低收或中低收入戶者'
       '…※ 註1 : 如為<新北市中低收入老人生活津貼證明書>不符合接種資格'),
   status='valid_current', evidence=f'{T} 換現行來源：衛生局 115/5/26 新聞「自9月1日起擴大」＋板橋區衛生所 115 年度頁（舊來源是 114/9/24 版、限高風險疾病）',
 ),
 642: dict(
   old_url='https://service.ntpc.gov.tw/eservice/CaseData.action?itemId=110063',
   url='https://service.ntpc.gov.tw/eservice/CaseData.action?itemId=110063',
   period='官方頁未載受理期間；事前申請制，須經市府第一階段審核通知後才能開始製作假牙（處理期限 20 天）',
   ex=('新北市政府申辦E服務「中、低收入老人補助裝置假牙」申請說明：補助資格 1. 設籍本市年滿55歲以上原住民或年滿60歲以上列冊本市之低收入戶，'
       '經醫師評估缺牙需裝置假牙者。2. 設籍本市年滿55歲以上原住民或年滿65歲以上老人，經醫師評估缺牙需裝置假牙，且同時符合下列條件之一者：'
       '(1) 中低收入戶…四、服務對象獲本計畫補助(含活動及固定假牙)，5年內最高補助金額不得逾新臺幣4萬 4,000元(假牙維修不在此限)。｜處理期限：20天'),
   evidence=f'{T} 讀原文：「20天」是處理期限不是受理期間；410 與本筆重複已停用',
 ),
}

conn = psycopg2.connect(os.environ['DATABASE_URL']); cur = conn.cursor()
ids = sorted(set(DEACT) | set(EDIT))
cur.execute('select id, is_active, source_url, eligibility_conditions from benefits where id = any(%s)', (ids,))
rows = {i: (a, u, e) for i, a, u, e in cur.fetchall()}
assert set(rows) == set(ids), set(ids) - set(rows)
for i in ids:
    assert rows[i][0] is True, (i, '已不是啟用中，停下來看')
for i, x in EDIT.items():
    assert rows[i][1] == x['old_url'], (i, 'source_url 已不是預期舊值，停下來看', rows[i][1])
    # 條件不動；仍用引擎同一把尺確認保留下來的條件合格
    assert_substantive(rows[i][2], label=str(i))
# 停用的那筆，保留的那筆必須還在啟用中
KEEP = {553: 318, 410: 642, 505: 501, 491: 754}
cur.execute('select id, is_active from benefits where id = any(%s)', (list(KEEP.values()),))
alive = dict(cur.fetchall())
for d, k in KEEP.items():
    assert alive.get(k) is True, (d, k, '保留的那筆不是啟用中')
    print(f'停用 {d}（保留 {k}）')
for i, x in EDIT.items():
    print(f'改寫 {i}：欄位 {sorted(k for k in x if k not in ("old_url",))}' + ('' if x['url'] == x['old_url'] else f'；source_url → {x["url"][:80]}…'))
if '--apply' not in sys.argv:
    print('(dry-run，未寫入)'); sys.exit()

cur.execute(f'create table {BACKUP} as select * from benefits where id = any(%s)', (ids,))
for i, r in DEACT.items():
    cur.execute("update benefits set is_active=false, deactivated_at=now(), deactivated_reason=%s, validity_status='deactivated', updated_at=now() where id=%s", (r, i))
for i, x in EDIT.items():
    cur.execute('''update benefits set source_url=%s, source_excerpt=%s, last_verified_date=CURRENT_DATE, validity_checked_at=now(),
                   validity_evidence=%s, updated_at=now() where id=%s''', (x['url'], x['ex'], x['evidence'], i))
    if 'name' in x: cur.execute('update benefits set name=%s where id=%s', (x['name'], i))
    if 'desc' in x: cur.execute('update benefits set description=%s where id=%s', (x['desc'], i))
    if 'period' in x: cur.execute('update benefits set application_period=%s where id=%s', (x['period'], i))
    if 'dl' in x: cur.execute('update benefits set deadline_type=%s, deadline_date=null where id=%s', (x['dl'], i))
    if 'status' in x: cur.execute('update benefits set validity_status=%s where id=%s', (x['status'], i))
    if 'amount' in x:
        mn, mx, unit, note = x['amount']
        cur.execute('update benefits set amount_min=%s, amount_max=%s, amount_unit=%s, amount_note=%s where id=%s', (mn, mx, unit, note, i))
conn.commit(); print('✅ 停用', sorted(DEACT), '；改寫', sorted(EDIT), '；備份', BACKUP)
