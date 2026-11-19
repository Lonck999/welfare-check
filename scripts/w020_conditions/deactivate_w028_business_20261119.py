"""W-028 FLAG：對象是業者／團體 6 筆停用（2026-11-19 Lonck 選「照前例停用」，前例 93／321）。原因原文取自 g*_report.md。
用法：python deactivate_w028_business_20261119.py [--apply]"""
import os, sys, psycopg2
P = '2026-11-19 W-028 FLAG 讀原文（Lonck 選停用，比照 93／321）：對象是業者／團體：'
R = {
 572: '新北「原住民創業及所營事業信用保證融資貸款」申請對象「本市原住民個人、機構、法人或團體所營事業」，須已辦公司／商業／合作社登記且設於本市滿 3 個月',
 549: '新北創新創業信用保證融資貸款利息補貼：「得以公司或商業名義申請」、「登記於本市未滿五年之公司或商業」',
 586: '協助民間推動都市更新補助：申請對象為「都市更新會」（團體）',
 609: '動力漁船補助保險費：「補助本市100噸以下動力漁船申辦漁船保險的保費負擔」，依總噸位補助、須漁業執照與船舶檢查證書（補助對象是船／漁業經營者）',
 576: '社區綠美學競賽材料補助：「由各申請單位備齊書面資料…向當地所屬區公所提出申請」（社區單位）',
 577: '環境綠美學苗木申請：「受理對象：機關、學校、社區管理委員會、里辦公處及公司行號。(一般民眾不提供申請服務)」',
}
c = psycopg2.connect(os.environ['DATABASE_URL']); cur = c.cursor()
cur.execute('select id, is_active from benefits where id = any(%s)', (list(R),))
st = dict(cur.fetchall()); assert set(st) == set(R) and all(st.values()), st
print('將停用', sorted(R))
if '--apply' not in sys.argv: print('(dry-run)'); sys.exit()
cur.execute('create table benefits_before_w028_business_20261119 as select * from benefits where id = any(%s)', (list(R),))
for i, r in R.items():
    cur.execute("update benefits set is_active=false, deactivated_at=now(), deactivated_reason=%s, validity_status='deactivated', updated_at=now() where id=%s", (P + r, i))
c.commit(); print('✅ 停用', sorted(R))
