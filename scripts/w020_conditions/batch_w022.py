"""W-022：「普通人」（無身障／非低收／無特殊身分）在 22 縣市看到的 confirmed 共 63 筆，逐筆對原文判：
   該不該對普通人 confirmed？不該 ⇒ 補上少編的條件。
   判讀依據：DB description（匯入時抓的官方頁摘錄）；537 另讀臺南社會局實施計畫 PDF。
   🔴 刻意保留 confirmed 的（普通人真的可以申請）：6 認定、23 勞保、25 自提、40 健檢 30+、92 文化幣、
      198 產業人才投資、322 運動幣、371 心理諮商 —— 不動。
   用法：python batch_w022.py [--apply]"""
import json, sys, psycopg2
D = '2026-10-20'
DIS = 'disability_certificate'

# (要加的條件, 要移除的鍵, 依據)
X = {
 # ── 只編了一個條件、原文還有別的限制 ──
 537: ({"requiredFlags": [DIS], "ageMin": 18, "uncheckedConditions": [
          "可實際從事經營；購買或承租公有公共場所零售商店或攤販未滿 2 年",
          "家庭總收入人均未達最低生活費 2.5 倍；未曾接受政府同性質補貼"]}, ['ageMin'],
       '臺南市身障者購買或承租商店攤販低利貸款或租金補貼實施計畫 §三（PDF）：成年、領有身障證明…'),
 32:  ({"uncheckedConditions": ["已向公立就業服務機構辦理求職登記，14 日內未能推介就業"]}, [],
       'description：辦理求職登記 14 日內未能推介就業'),
 94:  ({"uncheckedConditions": ["於自有建築物屋頂新設太陽光電設備（114/1/1 起取得設備登記），屋頂面積 1,000 平方公尺以下"]}, [],
       'description：私有建築物屋頂設置太陽光電、114/1/1 起取得設備登記'),
 97:  ({"uncheckedConditions": ["個人年所得 200 萬元以內；借款人限貸 1 次"]}, [],
       'description：未滿 50 歲、個人年所得 200 萬元以內'),
 100: ({"uncheckedConditions": ["定期開辦：2026 年度受理期間 2025/12/15～2026/1/2（已截止，請留意下年度公告）",
                                "未請領老年給付或終身無工作能力之失能給付"]}, [],
       'description：2026 年度受理期間 2025/12/15～2026/1/2'),
 101: ({"uncheckedConditions": ["求職者經公立就業服務機構推介參加「職場學習及再適應計畫」"]}, [],
       'description：經公立就業服務機構推介入職'),
 127: ({"uncheckedConditions": ["家庭成員未接受政府其他住宅補貼；家庭所得、財產符合規定",
                                "承租處須為合法住宅（排除頂加、違建）"]}, [],
       'description：家庭成員均未接受政府其他住宅相關補貼、2026 起承租處須為合法住宅'),
 317: ({"uncheckedConditions": ["保險有效期間，被保險人本人或其父母、配偶、子女死亡"]}, [],
       'description：勞保家屬死亡給付／國保被保險人死亡'),
 372: ({"uncheckedConditions": ["屋齡 30 年以上合法建築物（結構嚴重損毀須拆除者不適用）"]}, [],
       'description：屋齡 30 年以上合法建築物'),
 128: ({"ageMax": 45, "uncheckedConditions": [
          "須先獲中央 300 億租金補貼核定",
          "未滿 40 歲單身青年，或 45 歲以下已婚青年家庭（子女 0–12 歲另加碼）"]}, [],
       'description：臺北幸福租 —— 未滿 40 歲單身青年／45 歲以下已婚青年家庭'),
 129: ({"uncheckedConditions": ["新北市青年租金補貼（市府自辦，青年留居租屋），年齡與所得條件見官方頁"]}, [],
       'description：新北市青年租金補貼'),
 150: ({"uncheckedConditions": ["家庭年所得低於 145 萬、人均月所得不超過 62,125 元、不動產低於 708 萬、動產低於 471 萬（國家住都中心興辦）"]}, [],
       'description：國家住都中心直接興辦部分的基本資格'),
}
# 社會住宅地方入口：原文都是「所得、財產低於當地公告標準＋無自有住宅」，description 只是入口連結
for bid in (151, 152, 153, 154, 155, 156, 158, 159, 160, 161, 162, 163, 164, 165, 169, 170, 172):
    X[bid] = ({"uncheckedConditions": ["成年；家庭所得、財產低於當地公告標準（多比照低收／中低收認定，見官方頁）"]}, [],
              'description／入口頁：地方社會住宅多比照當地低收入戶／中低收入戶認定標準（見 150）')

# ── 「工作地點縣市勞工局補助」：22 筆原本一律編成 requiredFlags[is_employed_or_insured]（＝有工作就 confirmed），
#    實際每縣市內容完全不同（失業者／青年／低收／工讀生／訴訟）—— 錯編，逐筆改成原文 ──
LAB = {
 200: ({"uncheckedConditions": ["失業者（中高齡或就業保險被保險人），失業期間連續達 3 個月以上"]}, '失業者…連續達 3 個月以上'),
 201: ({"uncheckedConditions": ["補助對象見官方頁（description 只抓到金額）"]}, '只有金額'),
 202: ({"uncheckedConditions": ["初次尋職青年，參加就業促進活動後申請「初次尋職青年就業穩定計畫」"]}, '初次尋職青年就業穩定計畫'),
 203: ({"requiredIdentities": ["低收入戶或中低收入戶"], "uncheckedConditions": ["或參加本市社勞政聯合促進就業服務計畫者"]}, '本市列冊低收入戶、中低收入戶或參加…者'),
 204: ({"ageMin": 18, "ageMax": 29, "uncheckedConditions": ["其他條件見官方頁"]}, '年滿 18 歲至 29 歲'),
 206: ({"requiredFlags": ["is_student"], "uncheckedConditions": ["本人設籍新竹市；低收／中低收入戶家庭子女或本人列冊等特定對象（暑期工讀計畫）"]}, '暑期工讀，低收／中低收家庭子女'),
 208: ({"uncheckedConditions": ["補助對象見官方頁（description 只抓到獎勵金額）"]}, '只有金額'),
 209: ({"uncheckedConditions": ["補助內容見官方頁（description 未取得）"]}, '未取得'),
 210: ({"requiredIdentities": ["低收入戶或中低收入戶"], "uncheckedConditions": ["有工作能力未就業，經社工結合就業服務人員推介就業"]}, '本縣列冊低／中低收入戶有工作能力未就業'),
 211: ({"ageMin": 18, "ageMax": 45, "uncheckedConditions": ["設籍本縣；未在學且 112/1/1 後初次於本縣尋職就業（留鄉青年）等；連續受僱同一雇主滿 30 日並參加勞保"]}, '設籍本縣 18–45 歲青年'),
 213: ({"uncheckedConditions": ["勞資爭議訴訟（依法院實際徵收金額補助裁判費等）"]}, '法院徵收金額…補助'),
 215: ({"uncheckedConditions": ["內容未取得（抓取工具限制），請洽屏東縣政府"]}, '未取得'),
 217: ({"uncheckedConditions": ["設籍並實際居住本縣、最近一年居住國內超過 183 天；項目與對象見官方頁（同頁含低收入戶產婦營養補助等多項）"]}, '多項混在同一頁'),
 219: ({"requiredFlags": ["unemployed"], "uncheckedConditions": ["非自願離職失業勞工（設籍本縣滿 1 年並累積滿 6 年），子女就讀私立大專校院"]}, '非自願離職失業勞工，子女就讀私立大專'),
}
for bid, (add, why) in LAB.items():
    X[bid] = (add, ['requiredFlags'], f'description：{why}（原 is_employed_or_insured 為錯編）')

# 「本次搜尋未查得」的占位列：不是一項福利，是「查不到」的註記 —— 不可 confirmed
PLACEHOLDER = [130, 131, 132, 133, 134, 135, 136, 142, 148, 205, 220]
for bid in PLACEHOLDER:
    X[bid] = ({"uncheckedConditions": ["🔴 此縣市尚未查得具體方案（本筆是待查註記，不是已確認的福利），請洽當地主管機關"]},
              ['requiredFlags'] if bid in (205, 220) else [], 'description：本次搜尋未查得此縣市具體方案')

# 207 嘉義市：補助對象是「工會組織」—— 法人，不是個人福利（Lonck 09-28：網站給一般民眾，不會有法人）
DEACTIVATE = {207: '補助對象為依工會法成立之基層工會及聯合工會組織（法人），非個人福利 —— W-022 2026-10-20'}

conn = psycopg2.connect(dbname='welfare_check'); cur = conn.cursor()
ids = list(X) + list(DEACTIVATE)
cur.execute('select id, name, description, eligibility_conditions from benefits where id = any(%s) and is_active', (ids,))
rows = {r[0]: r[1:] for r in cur.fetchall()}
assert set(rows) == set(ids), set(ids) - set(rows)
for bid in PLACEHOLDER:
    assert '未查得' in (rows[bid][1] or ''), (bid, '不是占位列')
assert '工會' in rows[207][1]
for bid, (add, drop, src) in sorted(X.items()):
    name, desc, ec = rows[bid]
    ec = dict(ec or {})
    for k in drop:
        ec.pop(k, None)
    for k, v in add.items():
        if k == 'uncheckedConditions':
            ec[k] = list(ec.get(k, [])) + [u for u in v if u not in ec.get(k, [])]
        else:
            ec[k] = v
    ec['_w022'] = f'{D} {src}'
    print(bid, name[:20], '→', json.dumps({k: v for k, v in add.items()}, ensure_ascii=False)[:110])
    if '--apply' in sys.argv:
        cur.execute('update benefits set eligibility_conditions=%s, updated_at=now() where id=%s',
                    (json.dumps(ec, ensure_ascii=False), bid))
for bid, why in DEACTIVATE.items():
    print(bid, rows[bid][0], '→ 停用：', why)
    if '--apply' in sys.argv:
        cur.execute("update benefits set is_active=false, validity_status='deactivated', deactivated_at=now(), "
                    "deactivated_reason=%s, updated_at=now() where id=%s", (why, bid))
if '--apply' in sys.argv:
    conn.commit(); print('✅ 已寫入', len(X), '筆、停用', len(DEACTIVATE), '筆')
else:
    print('(dry-run)', len(X), '+', len(DEACTIVATE))
