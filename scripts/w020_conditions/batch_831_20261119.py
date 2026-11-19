"""C-6b（2026-11-19）：831 雲林縣鄉親專案 —— Lonck 選「收」（走公所申請、縣府合作，對民眾來說跟政府福利一樣）。

依原文（信華慈善基金會「急難救助實施要點（雲林縣鄉親專案）」113/11/18 生效 PDF ＋ 補助說明 PDF，皆掛在雲林社會處 n=21841 頁）：
  - 對象：戶籍設籍 183 天以上且實際居住雲林縣；因疾病、重大傷害等緊急事件致家庭生活困難
  - 事故發生 3 個月內申請、同戶一年一次；經公所初審 → 基金會審核；經費用完為止
  - 急難救助一次 5,000～20,000；急難醫療：中低收醫療費 5,000～30,000 補 80%（上限 2 萬）／非中低收但人均未達最低生活費 1.5 倍、10,000～50,000 補 70%（上限 1 萬）
條件寫法比照 830 雲林急難救助（acute_hardship＋unchecked）。
🔴 「115 年之後專案預算，前一年 12 月 25 日公佈」—— 115 年度有沒有延續**未查到** ⇒ validity_status 維持 valid_unconfirmed。
用法：python batch_831_20261119.py [--apply]
"""
import json, os, sys, psycopg2
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from eligibility_guard import assert_substantive

PAGE = 'https://social.yunlin.gov.tw/cl.aspx?n=21841'
TAG = 'C-6b 2026-11-19（Lonck 選收：民間基金會出錢、經公所申請與縣府合作）'
EX = ('財團法人台北市信華慈善基金會急難救助實施要點（雲林縣鄉親專案）自 113 年 11 月 18 日生效：二、救助對象 ★戶籍設籍 183 天以上，且實際居住在(雲林縣內鄉親)'
      ' 個案因疾病或重大傷害等緊急災難事件，造成家庭之生活困難…三、(二)限事故發生三個月內進行申請，其事故發生家庭年度僅能申請一次為原則。'
      '四、(一)…向公所提出申請，經公所/本會評估案家實際狀況…一次性急難救助 5,000-20000 元。'
      '急難醫療：1.…最近三個月內所花費之醫療費用累計達新台幣三萬元以下/五千元以上者為限。(中低收入戶之傷、病患者) '
      '2.…五萬元以下/一萬元以上者為限。(患嚴重傷、病，家庭總收入平均未達當年度每人每月最低生活費一點五倍…) 第一項第一款補助80% (補助上限2萬元) 第一項第二款補助70% (補助上限1萬元)'
      '｜七、113 年度預算/50 萬、114 年度預算/50 萬；115 年之後專案預算，前一年 12 月 25 日公佈。')
COND = {'counties': ['雲林縣'], 'minResidencyMonths': 6, 'requiredFlags': ['acute_hardship'],
        'uncheckedConditions': [
            '戶籍設籍 183 天以上且實際居住雲林縣',
            '因疾病、重大傷害、天災、意外、家庭變故、死亡等緊急事件致家庭生活陷困；事故發生 3 個月內申請，同戶一年一次',
            '急難醫療：中低收入戶醫療費近 3 個月累計 5,000～30,000 元；或非中低收但家庭人均未達最低生活費 1.5 倍、醫療費 10,000～50,000 元',
            '經鄉鎮市公所初審、基金會審核；經費用完為止（每年 12 月 15 日前送達）'],
        '_source': f'{TAG}：{EX}（{PAGE}）'}
assert_substantive(COND, label='831')
DESC = ('雲林縣鄉親專案（急難救助／急難醫療）：由財團法人台北市信華慈善基金會出資、與雲林縣政府及各鄉鎮市公所合作，'
        '補強縣府急難救助與醫療補助門檻較嚴的部分（非中低收的邊緣戶也可申請）。對象為設籍 183 天以上且實際居住雲林的鄉親，'
        '遭逢疾病、重大傷害、天災、家庭變故等急難致生活困難，事故 3 個月內向戶籍地公所申請，同戶一年一次。'
        '急難救助一次 5,000～20,000 元；急難醫療：中低收入戶醫療費 5,000～30,000 元補 80%（上限 2 萬）、'
        '非中低收但家庭人均未達最低生活費 1.5 倍者醫療費 10,000～50,000 元補 70%（上限 1 萬）。經費用完為止。')

conn = psycopg2.connect(os.environ['DATABASE_URL']); cur = conn.cursor()
cur.execute('select name, eligibility_conditions from benefits where id=831')
n, ec = cur.fetchone()
assert n == '雲林縣鄉親專案(急難救助/急難醫療)' and set(ec) == {'_note', 'counties'}, (n, ec)
print('831 新鍵：', sorted(COND))
if '--apply' not in sys.argv:
    print('(dry-run)'); sys.exit()
cur.execute('create table benefits_before_c6b_831_20261119 as select * from benefits where id=831')
cur.execute('''update benefits set agency=%s, description=%s, eligibility_conditions=%s::jsonb, source_excerpt=%s,
               amount_max=20000, amount_unit='one_time',
               amount_note='急難救助一次 5,000～20,000；急難醫療中低收補 80%%（上限 2 萬）／非中低收補 70%%（上限 1 萬）',
               application_period='事故發生 3 個月內向戶籍地公所申請；每年 12 月 15 日前送達；經費用完為止',
               deadline_type='event', quota_limited=true, last_verified_date=CURRENT_DATE, validity_checked_at=now(),
               validity_evidence=%s, updated_at=now() where id=831''',
            ('財團法人台北市信華慈善基金會（與雲林縣政府、鄉鎮市公所合作）', DESC, json.dumps(COND, ensure_ascii=False), EX,
             '2026-11-19 讀實施要點 PDF（113/11/18 生效）＋補助說明 PDF；115 年度預算是否延續未查到'))
conn.commit(); print('✅ 831 已寫入')
