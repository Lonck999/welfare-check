"""W-027／W-028 收尾補丁（2026-11-19 20:0x）：
  ① 427 花蓮中低收老人假牙：換成現行來源後，跟 913「花蓮縣65歲以上長者假牙補助」**是同一個網址、同一個計畫**
     （115 年起一般長者與中低收長者合併為一個計畫，913 的條件兩軌都寫了）⇒ 427 停用，比照 296↔675、599↔1003 重複停用。
     913 的 amount_max 50,000 是一般長者上限；中低收長者 55,000 寫進 amount_note。
  ② 318 試管嬰兒補助 3.0：`ageMax: 45` 是「妻未滿 45 歲」——那是太太的年齡，引擎拿去比填問卷的人
     ⇒ 46 歲先生配 40 歲太太會被刷掉。比照 eligibility.ts 規範（只編申請人本人的條件；他人條件放 unchecked）：
     拿掉 ageMax，原文放 uncheckedConditions。
⚠️ ② 已撤回（同日 20:02）：拿掉 ageMax 後 318 對每個成年人都 possible（70 歲也看到試管嬰兒補助）——
   因為 `infertility_treatment_needed` 刻意不在 ANSWERED_FLAGS（questionnaire.ts:236「使用者可能沒想到要勾」），
   沒勾不會被刷掉。ageMax 45 是唯一擋住不相干的人的條件 ⇒ 已從備份表還原 318，待 Lonck 決定（KNOWN-ISSUES W-028）。
用法：python fix_w027_tail_20261119.py [--apply]
"""
import json, os, sys, psycopg2
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from eligibility_guard import assert_substantive

conn = psycopg2.connect(os.environ['DATABASE_URL']); cur = conn.cursor()
cur.execute('select id, source_url, is_active, eligibility_conditions, amount_note from benefits where id in (427, 913, 318)')
r = {i: (u, a, e, n) for i, u, a, e, n in cur.fetchall()}
assert r[427][0] == r[913][0] and r[427][1] and r[913][1], 'expect 427/913 same url, both active'
e318 = dict(r[318][2]); assert e318.get('ageMax') == 45, e318
del e318['ageMax']
e318['uncheckedConditions'] = list(e318.get('uncheckedConditions', [])) + ['受術妻未滿 45 歲（妻的年齡，不是填表人）']
e318['_source'] = (e318.get('_source', '') + '｜2026-11-19 W-028：原文「未滿45歲」是妻的年齡，引擎比的是填表人 ⇒ ageMax 移到 unchecked').lstrip('｜')
assert_substantive(e318, label='318')
note913 = '一般 65 歲以上長者 5 年內最高 5 萬元；中低收入戶等福利身分長者 5 年內最高 5 萬 5,000 元（假牙維修不在此限）'
print('停用 427（與 913 同網址同計畫）；318 鍵', sorted(k for k in e318 if not k.startswith('_')), '；913 amount_note →', note913)
if '--apply' not in sys.argv:
    print('(dry-run)'); sys.exit()
cur.execute('create table benefits_before_w027_tail_20261119 as select * from benefits where id in (427, 913, 318)')
cur.execute("""update benefits set is_active=false, deactivated_at=now(), validity_status='deactivated', updated_at=now(),
               deactivated_reason='2026-11-19 W-027 換現行來源後與 913 重複：同一頁（花蓮縣社會處「65歲以上長者假牙補助」），115 年起一般長者與中低收長者合為一個計畫，913 已收兩軌條件'
               where id=427""")
cur.execute('update benefits set amount_note=%s, updated_at=now() where id=913', (note913,))
cur.execute('update benefits set eligibility_conditions=%s::jsonb, updated_at=now() where id=318', (json.dumps(e318, ensure_ascii=False),))
conn.commit(); print('✅')
