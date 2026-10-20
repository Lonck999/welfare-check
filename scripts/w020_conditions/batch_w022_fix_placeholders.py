"""W-022 更正（2026-10-20 16:2x）：batch_w022.py 把 11 筆標成「待查註記，不是福利」是錯的。
   那 11 筆的 description 寫「本次搜尋未查得」，但它們自己的 source_url 讀下去，9 筆有具體方案。
   🔴 根因同 AGENTS §5.7：看到描述說「沒有」，就信了描述，沒打開原始來源。
   每筆依 curl 讀到的來源正文重編；name／description 仍是舊的（另列待修）。
   用法：python batch_w022_fix_placeholders.py [--apply]"""
import json, sys, psycopg2
D = '2026-10-20'
OLD = '🔴 此縣市尚未查得具體方案（本筆是待查註記，不是已確認的福利），請洽當地主管機關'
X = {
 130: ({"requiredIdentities": ["原住民"], "requiresNoOwnedHome": True, "ageMin": 18, "uncheckedConditions": [
          "來源頁實為「116 年度桃園市原住民族租金補貼」：設籍本市之原住民、承租本市房屋",
          "家庭成員人均月所得低於最低生活費 3 倍（115 年度 51,558 元）；不得重複接受其他住宅補助"]},
       '桃園市原住民族租金補貼公告 二、申請條件'),
 131: ({"requiresNoOwnedHome": True, "uncheckedConditions": [
          "來源頁實為「臺中市住宅租金補貼增額補助」：本市租金補貼計畫戶數外之複審合格戶（每戶每月最高 4,000 元）",
          "且具特殊條件之一：65 歲以上、重大災害災民、原住民、重大傷病、特殊境遇家庭、身心障礙、列冊低收入戶、20–40 歲青年"]},
       '臺中市都發局租金補貼增額補助作業規範 三、四'),
 132: ({"requiredIdentities": ["原住民"], "requiresNoOwnedHome": True, "ageMin": 18, "minResidencyMonths": 4, "uncheckedConditions": [
          "來源頁實為「115 年度臺南市原住民住宅租金補貼」（115/9/1–10/31 受理，市區每月最高 3,800）",
          "家庭所得、財產符合規定；不得重複領取其他同性質租金補貼"]},
       '臺南市新聞稿 115-08-07：成年且設籍滿 4 個月以上之原住民'),
 133: ({"requiresNoOwnedHome": True, "uncheckedConditions": [
          "來源頁實為「高雄市增額租金補貼」申請系統（115/1/1–12/31 受理）；資格條件見官方公告（申請系統頁未列條件）"]},
       '高雄市增額租金補貼申請系統首頁'),
 134: ({"ageMin": 65, "requiresNoOwnedHome": True, "minResidencyMonths": 3, "uncheckedConditions": [
          "來源頁實為「基隆市中低收入老人租賃房屋租金補助」：須領有本市中低收入老人生活津貼",
          "租賃非三親等親屬所有之合法房屋，租期自申請日起剩 4 個月以上；未獲政府同性質補助"]},
       '基隆市中低收入老人租賃房屋租金補助作業辦法 第二條'),
 135: ({"ageMax": 39, "requiresNoOwnedHome": True, "uncheckedConditions": [
          "來源頁實為「新竹市加碼青年租金補貼」：設籍並實際租屋於新竹市",
          "須為中央 300 億租金補貼「第三級」核定戶（家庭成員 1 人且未滿 40 歲、無經濟或社會弱勢身分）；市府加碼每年 7,000 元"]},
       '新竹市青年發展中心「加碼青年租金補貼」三、加碼補貼對象及條件'),
 136: ({"ageMin": 18, "ageMax": 45, "requiresNoOwnedHome": True, "uncheckedConditions": [
          "來源頁實為「嘉義市青年租屋加碼補助計畫」：設籍且實際租屋於本市 18–45 歲青年",
          "須為內政部 115 年 300 億中央擴大租金補貼核定戶；每戶每月最高加碼 500 元，免另行申請"]},
       '嘉義市勞青處「青年租屋加碼補助計畫」補助對象及條件'),
 142: ({"uncheckedConditions": [
          "🔴 官方來源頁讀不到（雲林縣政府網站以 Cloudflare 阻擋自動讀取，2026-10-20），內容未確認，請洽雲林縣政府"]},
       'dsh.yunlin.gov.tw 回 Cloudflare 封鎖頁'),
 148: ({"ageMin": 20, "requiresNoOwnedHome": True, "uncheckedConditions": [
          "🔴 來源頁是 107 年（2018）的金門加碼租金補貼新聞，現行是否仍辦理未確認",
          "當年條件：有配偶／單身與直系親屬同戶／單身滿 40 歲；家庭年收入不超過 93 萬、人均月收入 38,973 元以下；動產 60 萬、不動產 405 萬以下"]},
       '金門縣政府新聞「照顧租屋族群 縣府延續加碼租金補貼」上版 107-07-25'),
 205: ({"uncheckedConditions": [
          "來源頁實為「115 年度協助雇主辦理工作場所性騷擾被害人心理諮商補助」",
          "設籍本市或勞務提供地於本市之職場性騷擾案件申訴人或被害人（或提供／轉介心理諮商之雇主）"]},
       '基隆市法制及勞動處 115 年度職場性騷擾被害人心理諮商補助'),
 220: ({"requiredFlags": ["disability_certificate"], "uncheckedConditions": [
          "來源頁實為「連江縣身心障礙者久任職場津貼」：設籍本縣，經本縣身障職業重建服務窗口轉介就業",
          "於本縣同一事業單位工作滿 2 年（5,000 元）或滿 3 年（10,000 元）；每年 7/1–8/30 申請"]},
       '連江縣身心障礙者久任職場津貼補助實施要點 二、三、五'),
}
conn = psycopg2.connect(dbname='welfare_check'); cur = conn.cursor()
cur.execute('select id, eligibility_conditions from benefits where id = any(%s) and is_active', (list(X),))
old = dict(cur.fetchall()); assert set(old) == set(X), set(X) - set(old)
for bid, (add, src) in sorted(X.items()):
    ec = dict(old[bid] or {})
    uc = [u for u in ec.get('uncheckedConditions', []) if u != OLD]
    assert len(uc) == len(ec.get('uncheckedConditions', [])) - 1, (bid, '找不到上一版寫錯的占位句')
    for k, v in add.items():
        ec[k] = uc + v if k == 'uncheckedConditions' else v
    ec['_w022'] = f'{D} 更正：上一版誤標待查註記；依來源頁正文：{src}'
    print(bid, json.dumps({k: v for k, v in add.items() if k != 'uncheckedConditions'}, ensure_ascii=False), '|', add['uncheckedConditions'][0][:40])
    if '--apply' in sys.argv:
        cur.execute('update benefits set eligibility_conditions=%s, updated_at=now() where id=%s', (json.dumps(ec, ensure_ascii=False), bid))
if '--apply' in sys.argv:
    conn.commit(); print('✅ 已寫入', len(X))
else:
    print('(dry-run)', len(X))
