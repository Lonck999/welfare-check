"""B 批 2 匯入的 6 筆（benefits 987–992，change_log 542–547）依原文編資格條件（2026-10-29）。
   匯入程式只寫 counties ⇒ 條件未整理 ⇒ 最高 possible（W-020）。這支依 p29/NN.txt 正文補條件。
   🔴「符合其一」一律放 uncheckedConditions（引擎只做 AND）。
   🔴 對象是子女的（991、992）用 requiresChildUnder，不用 ageMax —— 申請人（profile 的 self）是家長，ageMax 會把家長刷掉。
   🔴 987 不套 recent_natural_disaster_damage：原文是「鳳凰颱風期間曾淹水」的建物，不是問卷問的「近期受災」，硬套會刷掉該看到的人。
   用法：python batch_import542_20261029.py [--apply]"""
import json, sys, psycopg2
D = '2026-10-29'
X = {
 987: ({"counties": ["宜蘭縣"], "requiresOwnedHome": True, "uncheckedConditions": [
          "建築物於鳳凰颱風期間有 50 公分以上淹水紀錄之合法建築物",
          "設置寬度及高度 90 公分以上之防水閘門（板）；同一門牌限 2 處；經費用罄為止"]},
       '宜蘭縣水利資源處「115~116年度防水閘門(板)補助計畫」'),
 988: ({"counties": ["宜蘭縣"], "ageMin": 55, "requiredIdentities": ["原住民"], "uncheckedConditions": [
          "經牙醫評估有裝置假牙需求；5 年內（含本年度）曾獲本計畫補助者合計不得逾 4 萬元",
          "115 年度申請期限 10/31"]},
       '宜蘭縣原民處 115 年度原住民族長者裝置假牙實施計畫：一、補助資格（設籍宜蘭縣、年滿 55 歲、原住民身份）'),
 989: ({"counties": ["臺東縣"], "requiresOwnedHome": True, "uncheckedConditions": [
          "設置於臺東縣轄區合法私有建築物之屋頂型太陽光電，且於 111/1/1–115/10/31 取得設備登記之設置者",
          "依收件順序補助至經費用罄"]},
       '臺東縣府新聞「鼓勵屋頂設置太陽光電…放寬申請補助資格」'),
 990: ({"counties": ["臺東縣"], "ageMin": 55, "requiredIdentities": ["原住民"], "uncheckedConditions": [
          "經牙醫評估有裝置假牙需求",
          "116 年度方案 115/11/1 起受理"]},
       '臺東縣原民處「原住民族長者假牙補助」：55 歲以上原住民'),
 991: ({"counties": ["澎湖縣"], "requiresChildUnder": 18, "uncheckedConditions": [
          "兒少（未滿 18 歲）須符合其一：低收／中低收、困苦失依或緊急生活扶助、保護個案、機構或寄養安置、特境家庭未滿 6 歲、早產兒、因懷孕生育遭遇困境、罕病或重大傷病、其他經評估有必要",
          "住院／醫療結束日起 6 個月內向戶籍地鄉市公所申請"]},
       '澎湖縣政府辦理弱勢兒童及少年醫療補助審查核發作業規定 二、補助對象'),
 992: ({"counties": ["澎湖縣"], "requiresChildUnder": 7, "uncheckedConditions": [
          "設籍且居住本縣之 6 個月至 6 歲兒童，家長因謀職、就醫、職業訓練或其他非可預期之突發事件需臨時托育",
          "托育後 3 個月內申請；計畫至 115/12/31"]},
       '澎湖縣政府 115 年度兒童臨時托育服務實施計畫'),
}
conn = psycopg2.connect(dbname='welfare_check'); cur = conn.cursor()
cur.execute('select id, county, eligibility_conditions from benefits where id = any(%s)', (list(X),))
old = {r[0]: (r[1], r[2]) for r in cur.fetchall()}; assert set(old) == set(X), set(X) - set(old)
for bid, (ec, src) in X.items():
    county, o = old[bid]; assert o.get('counties') == [county] == ec['counties'], (bid, county, o)
    ec = dict(ec); ec['_source'] = f'C-6 B 批 2 {D} 依官方原文編條件：{src}'
    print(bid, json.dumps({k: v for k, v in ec.items() if not k.startswith('_')}, ensure_ascii=False)[:150])
    if '--apply' in sys.argv:
        cur.execute('update benefits set eligibility_conditions=%s, updated_at=now() where id=%s', (json.dumps(ec, ensure_ascii=False), bid))
if '--apply' in sys.argv:
    conn.commit(); print('✅ 已寫入', len(X))
else:
    print('(dry-run)', len(X))
