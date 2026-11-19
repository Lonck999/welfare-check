"""W-028 FLAG：不是民眾可申請的福利 8 筆停用（2026-11-19 Lonck「照建議做」—— 回覆的是 d5474c8 那輪「剩 20 筆照建議處理嗎」）。
原因原文取自 ~/.hermes/cache/welfare_w028_20261119/g*_report.md。674 松年大學有 55 歲資格、屬老人福利，不在此列。
用法：python deactivate_w028_nonwelfare_20261119.py [--apply]"""
import os, sys, psycopg2
P = '2026-11-19 W-028 FLAG 讀原文（Lonck 照建議停用）：不是民眾可申請的福利 —— '
R = {
 593: '課程招生入口：新北原住民族部落大學「關於部大」辦學理念／課程類別頁，無任何補助；原值「先至部大官網註冊後線上報名」',
 588: '課程招生入口：社區大學「以提升人民現代公民素養…之終身學習機構」「每年招生二期」',
 590: '課程招生入口：施政成果頁「新北市民免費數位課程…透過新北市數位樂學網–數位學院查詢」',
 591: '單一課程報名頁：ezlearn 課程「新北動健康-樂活有氧」（A11509221、報名費 300、已關閉報名）',
 709: '一般公共服務：消費爭議申訴（「向本府消費者服務中心提出申訴」）',
 712: '通報表單：《桃園市社區(疑似)精神病患通報/轉介單(民眾版)》替他人通報、由衛生局派案，非申請人可申請之福利',
 554: '已核定案件的請款程序：原住民修繕住宅補助(請款階段)，對象「經市府審查符合補助規定…函文通知之申請人」（申請入口是 555）',
 632: '已核定案件的請款程序：都市更新整建維護補助請款作業(第一期、第二期)，應備「核定(准)函」',
}
c = psycopg2.connect(os.environ['DATABASE_URL']); cur = c.cursor()
cur.execute('select id, is_active from benefits where id = any(%s)', (list(R),))
st = dict(cur.fetchall()); assert set(st) == set(R) and all(st.values()), st
cur.execute('select is_active from benefits where id=555'); assert cur.fetchone()[0]   # 修繕補助申請入口仍在
print('將停用', sorted(R))
if '--apply' not in sys.argv: print('(dry-run)'); sys.exit()
cur.execute('create table benefits_before_w028_nonwelfare_20261119 as select * from benefits where id = any(%s)', (list(R),))
for i, r in R.items():
    cur.execute("update benefits set is_active=false, deactivated_at=now(), deactivated_reason=%s, validity_status='deactivated', updated_at=now() where id=%s", (P + r, i))
c.commit(); print('✅ 停用', sorted(R))
