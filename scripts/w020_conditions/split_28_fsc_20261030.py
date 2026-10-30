"""28「金管會金融優惠與消費者保護服務」拆成三筆（2026-10-30 Lonck 選 A），各依官方原文。
   原 28 把三件事包成一筆，source 只對應微型保險 ⇒
     28  → 改寫為「微型保險」（保險局「推動微型保險」頁，原 source，更新 2025-09-22）
     新增 金融消費評議（財團法人金融消費評議中心「如何申請」）
     新增 消費者債務清理條例前置協商（金管會銀行局「消費者債務清理條例之前置協商說明」）
   三筆都是常設制度、頁面無 115 年度字樣 ⇒ validity_status = valid_unconfirmed（判準 B）。
   條件都是「符合其一」或「有爭議／有債務」這類引擎問不到的 ⇒ 全放 uncheckedConditions，不設 openToAll。
   用法：python split_28_fsc_20261030.py [--apply]"""
import json, sys, psycopg2
IB  = 'https://www.ib.gov.tw/ch/home.jsp?id=210&parentpath=0%2C8'
FOI = 'https://www.foi.org.tw/article.aspx?Arti=44&Lang=1'
BK  = 'https://www.banking.gov.tw/ch/home.jsp?id=742&websitelink=artwebsite.jsp&parentpath=0,674,717,740'
MICRO = dict(
  name='微型保險（經濟弱勢與特定身分者低保費人身保險）',
  desc='金管會推動之微型保險：提供經濟弱勢或特定身分者一年期定期壽險、傷害險及傷害醫療險，保費低；累計保額上限壽險 50 萬、傷害險 50 萬、傷害醫療 3 萬。可個人投保、透過代理投保單位集體投保，或由團體（如社福團體、地方政府）為成員投保。',
  cond={'uncheckedConditions': ['符合其一（本人或家庭成員）：全年綜合所得總額不超過免稅額＋標準扣除額＋薪資特別扣除額合計數（無配偶者或夫妻合計）；原住民；漁民或漁業從業人；農保被保險人；社福慈善團體服務對象；工作所得補助方案對象；特殊境遇家庭、低收或中低收入戶；身心障礙者；領中低收入老人生活津貼者；新住民；其他經主管機關認可之經濟弱勢或特定身分者',
                                '向保險公司個人投保，或透過代理投保單位／團體投保']},
  ex='推動微型保險 二、微型保險簡介：微型保險係提供經濟弱勢或特定身分者基本人身保險保障…(一) 可投保微型保險之資格包含：無配偶且全年綜合所得總額不超過財政部公告當年度規定之綜合所得稅免稅額、標準扣除額及薪資所得特別扣除額之合計數者或其家庭成員…具有原住民身分法規定之原住民身分…符合身心障礙者權益保障法定義之身心障礙者…符合新住民基本法第二條第一項第一款規定者或其家庭成員。(二) 保險金額：個別被保險人累計投保微型人壽保險之保險金額不得超過新臺幣50萬元，累計投保微型傷害保險之保險金額不得超過新臺幣50萬元，累計投保微型傷害醫療保險之保險金額不得超過新臺幣3萬元。')
NEW = [
 dict(name='金融消費爭議評議（金融消費評議中心）', agency='財團法人金融消費評議中心（金管會指定）', url=FOI,
  desc='與銀行、保險、證券等金融服務業因商品或服務發生民事爭議時，先向該金融業者申訴（業者應於 30 日內處理回覆），不滿意可向金融消費評議中心申請評議，不必上法院。申訴專線 0800-789885，可線上申請。',
  cond={'uncheckedConditions': ['金融消費者與金融服務業之間有因商品或服務產生的民事爭議', '須先向金融服務業申訴，業者 30 日內未處理或不滿意處理結果才可申請評議', '有不受理情形（見評議中心「不受理的情形」）']},
  ex='如何申請：當金融消費者與金融服務業因商品或服務產生民事爭議時：第一步驟-向金融服務業申訴…金融服務業應於收受申訴之日起30日內為適當之處理，並將處理結果回覆給您。第二步驟-申請評議 (請注意是否有不受理之情形) 請電洽金融消費者申訴專線0800-789885…'),
 dict(name='消費者債務清理條例前置協商（信用卡、信貸等債務協商）', agency='金融監督管理委員會銀行局（向最大債權金融機構申請）', url=BK,
  desc='積欠銀行、信用卡公司等金融機構消費借貸、信用卡、現金卡或自用住宅借款債務，還款有困難者，可檢具申請文件及債權人清冊向最大債權金融機構申請前置協商，協商期間通知各債權金融機構停止催收，擬定清償方案。',
  cond={'uncheckedConditions': ['積欠任一家金融機構債務（消費借貸、自用住宅借款、信用卡、現金卡）', '五年內未從事營業活動，或僅從事小規模營業活動（營業額平均每月 20 萬元以下）之自然人', '向最大債權金融機構申請；民間債權不納入前置協商']},
  ex='消費者債務清理條例之前置協商說明 一、受理債務人範圍及條件…（五）五年內未從事營業活動或從事小規模營業活動之自然人，前述小規模營業指營業額平均每月新臺幣20萬元以下者。（六）必須有積欠任一家金融機構債權者。二、受理金融機構：最大債權金融機構…三、協商之債權範圍：因消費借貸、自用住宅借款、信用卡及現金卡契約而負之債務…'),
]
conn = psycopg2.connect(dbname='welfare_check'); cur = conn.cursor()
cur.execute('select is_active, name, source_url from benefits where id=28'); a, n, u = cur.fetchone()
assert a and n == '金管會金融優惠與消費者保護服務' and u == IB, (a, n, u)
for x in NEW:
    cur.execute("select id from benefits where replace(name,' ','')=replace(%s,' ','')", (x['name'],)); assert cur.fetchone() is None, x['name']
print('改寫 28 →', MICRO['name']); [print('新增 全國｜', x['name']) for x in NEW]
if '--apply' in sys.argv:
    ec = {**MICRO['cond'], '_source': f'2026-10-30 依原文拆分改寫（Lonck 選 A）：{MICRO["ex"]}（{IB}）'}
    cur.execute('''update benefits set name=%s, description=%s, source_excerpt=%s, eligibility_conditions=%s,
                   validity_status='valid_unconfirmed', validity_checked_at=now(), last_verified_date=current_date, updated_at=now()
                   where id=28''', (MICRO['name'], MICRO['desc'], MICRO['ex'], json.dumps(ec, ensure_ascii=False)))
    new_ids = []
    for x in NEW:
        ec = {'counties': ['全國'], **x['cond'], '_source': f'2026-10-30 自 28 拆出（Lonck 選 A）：{x["ex"]}（{x["url"]}）'}
        cur.execute("""INSERT INTO benefits (name, agency, county, description, search_group, eligibility_conditions, source_url, source_excerpt,
                         last_verified_date, is_active, deadline_type, application_period, source_tier, validity_status, validity_checked_at, validity_evidence)
                       VALUES (%s,%s,'全國',%s,'一般性優惠與便民服務',%s::jsonb,%s,%s,CURRENT_DATE,true,'always','常態受理','official','valid_unconfirmed',now(),%s)
                       RETURNING id""", (x['name'], x['agency'], x['desc'], json.dumps(ec, ensure_ascii=False), x['url'], x['ex'],
                                         '2026-10-30 讀官方原文（常設制度，頁面無 115 年度字樣 ⇒ 判準 B）；Lonck 選 A 拆分 28'))
        new_ids.append(cur.fetchone()[0])
    conn.commit(); print('✅ 改寫 28；新增', new_ids)
else:
    print('(dry-run)')
