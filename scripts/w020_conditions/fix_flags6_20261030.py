"""FLAG 6 筆（業者對象 3、停辦過期 3）再讀原文後處理（2026-10-30，Lonck 選 A：照判準停用，但每筆先再讀一次原文確認）。
   🔴 再讀推翻了 1 筆：844 基隆老花眼鏡 —— 子代理只讀到 114 年版，但基隆市府有「115年度辦理老人老花眼鏡補助方式」
      （受理 115/1/1–12/31）⇒ **不停用，改寫成 115 年度並編條件**。
   停用 5：
     93  文化部實體書店補助：作業要點第三點「申請者須為已實際營運之實體書店，或與實體書店相關之國內立案獨資、合夥事業、法人或團體」（植根法律網轉載；文化部站被 Cloudflare 擋）
     321 數位發展部補助：申請須知「國內依法登記成立之獨資、合夥、有限合夥事業或公司，且行業分類須為 J582、J62、J63」
     802 勞工退休金年金保險：勞保局《捌、年金保險》「事業單位僱用勞工人數達 200 人以上，經工會同意…報請勞動部核准後實施」—— 雇主端制度
     842 基隆 COVID 死亡喪葬慰問金：頁面 2021/07/14 發布、2021/08/05 後未更新；經費來自已落日的紓困振興特別條例
     747 臺中原住民幼兒托教補助：中央法源「廢 原住民族委員會辦理原住民幼兒就讀幼兒園補助作業要點」113/08/21 廢止；
         來源是 2015 新聞，臺中開放資料（2026-04-01 更新）指向的 ipd 頁面讀不到內容 —— ⚠️ 若臺中仍以其他名義辦理，需另找來源新增
   用法：python fix_flags6_20261030.py [--apply]"""
import json, sys, psycopg2
K115 = 'https://www.klcg.gov.tw/tw/financial/2751-307843.html'
DEACT = {
 93:  '對象是業者：文化部推動實體書店發展補助作業要點第三點「申請者須為已實際營運之實體書店，或與實體書店相關之國內立案獨資、合夥事業、法人或團體」',
 321: '對象是業者：申請須知「國內依法登記成立之獨資、合夥、有限合夥事業或公司，且申請企業之行業分類須為 J582、J62、J63」',
 802: '對象是雇主：勞保局《年金保險》「事業單位僱用勞工人數達 200 人以上，經工會同意…報請勞動部核准後實施」，非民眾可申請',
 842: '已停辦：COVID-19 死亡喪葬慰問金，經費來自已落日之紓困振興特別條例；頁面 2021/08/05 後未更新',
 747: '已廢止：中央法源「原住民族委員會辦理原住民幼兒就讀幼兒園補助作業要點」113/08/21 廢止；來源為 2015 年新聞，查無臺中現行版本',
}
X844 = dict(
  name='基隆市 115 年度老人老花眼鏡補助',
  desc='基隆市設籍 4 個月以上、65 歲以上（原住民 55 歲以上）需配置老花眼鏡者，補助整副老花眼鏡每人最高 500 元，每年限申請一次、2 年內不得重複申請；購買後 3 個月內、最晚 12/5 前向戶籍地區公所社政課申請。受理 115/1/1–12/31。',
  cond={'counties': ['基隆市'], 'ageMin': 55, 'minResidencyMonths': 4,
        'uncheckedConditions': ['年滿 65 歲以上，原住民年滿 55 歲以上（非原住民 55–64 歲不符）',
                                '需配置老花眼鏡；每年限一次、2 年內不得重複申請',
                                '購買後 3 個月內申請，最晚 12/5；須台灣購買之收據或發票正本']},
  ex='基隆市政府115年度辦理老人老花眼鏡補助方式 受理期間：自115年1月1日起至115年12月31日止。受理地點：戶籍所在地各區公所(社政課)。補助對象及資格限制：設籍本市4個月以上，且年滿65歲以上老人或原住民滿55歲需配置老花眼鏡者。補助樣式及金額：補助整副老花眼鏡，每人最高補助新臺幣500元整，每年申請ㄧ次為限，2 年內不得重複申請補助。')
conn = psycopg2.connect(dbname='welfare_check'); cur = conn.cursor()
ids = list(DEACT) + [844]
cur.execute('select id, is_active, name from benefits where id = any(%s)', (ids,))
rows = {r[0]: r[1:] for r in cur.fetchall()}; assert set(rows) == set(ids)
for i in ids: assert rows[i][0] is True, (i, '已不是啟用中，停下來看')
for i, r in DEACT.items(): print('停用', i, rows[i][1], '｜', r[:40])
print('改寫 844', rows[844][1], '→', X844['name'])
if '--apply' in sys.argv:
    for i, r in DEACT.items():
        cur.execute("""update benefits set is_active=false, validity_status='deactivated', deactivated_at=now(),
                       deactivated_reason=%s, updated_at=now() where id=%s""", ('2026-10-30 FLAG 再讀原文（Lonck 選 A）：' + r, i))
        assert cur.rowcount == 1
    ec = {**X844['cond'], '_source': f'2026-10-30 FLAG 再讀原文找到 115 年版：{X844["ex"]}（{K115}）'}
    cur.execute('''update benefits set name=%s, description=%s, source_url=%s, source_excerpt=%s, amount_min=NULL, amount_max=500,
                   amount_unit='one_time', eligibility_conditions=%s, source_tier='official', validity_status='valid_current',
                   validity_checked_at=now(), last_verified_date=current_date, updated_at=now() where id=844''',
                (X844['name'], X844['desc'], K115, X844['ex'], json.dumps(ec, ensure_ascii=False)))
    assert cur.rowcount == 1
    conn.commit(); print('✅ 停用', len(DEACT), '改寫 1')
else:
    print('(dry-run)')
