#!/usr/bin/env python3
"""回歸 W-022：沒有任何特殊身分的「普通人」，在 22 縣市只能看到白名單內的 confirmed。

🔴 起因（2026-10-20）：條件只編了一部分（例：身障攤販貸款只編 ageMin 20）的項目，
   對任何人都判「確定符合」—— 普通人 3 人 × 22 縣市查出 63 筆，逐筆對原文後只有 8 筆是對的。
🔴 這支用「症狀」守，不用關鍵字：新匯入的資料只要讓普通人多看到一筆 confirmed，就會紅。
   要放行新的一筆 → 先讀原文確認「真的人人可申請」，再加進 ALLOWED 並寫理由。

連本機 welfare_check 資料庫（backend/.env）。跑法：python verify_ordinary_person_confirmed.py
"""
import json, os, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ALLOWED = {
    6: '低收／中低收認定本身（申請列冊）—— 22 歲失業者收入推算符合，可去申請',
    23: '勞保給付權益：有加勞保即適用',
    25: '勞退自願提繳：受僱勞工即可',
    40: '成人預防保健：30 歲以上具健保身分',
    92: '文化幣：13–22 歲',
    198: '產業人才投資方案：15 歲以上在職勞工',
    322: '運動幣：登記抽籤，人人可登記',
    371: '15–45 歲心理諮商：無縣市限制',
    374: '離島居民航空票價補貼（金門）：辦法第 3 條唯一條件＝設籍離島，counties 已限金門（2026-10-29 讀原文放行）',
    375: '離島居民航空票價補貼（連江）：同上，counties 已限連江（2026-10-29 讀原文放行）',
}
EXPECTED_CALLS = 66

env = dict(os.environ)
envf = ROOT / 'backend' / '.env'
if envf.exists():
    for line in envf.read_text().splitlines():
        if '=' in line and not line.lstrip().startswith('#'):
            k, v = line.split('=', 1); env.setdefault(k.strip(), v.strip().strip('"'))
if not env.get('DATABASE_URL'):
    print('⏭️ 跳過：沒有 DATABASE_URL —— 這不算通過'); sys.exit(2)

r = subprocess.run(['npx', 'tsx', 'scripts/w022_ordinary_probe.ts'], cwd=ROOT / 'backend', env=env,
                   capture_output=True, text=True, timeout=170)
if r.returncode != 0:
    print('🔴 探針執行失敗\n', r.stderr[-1500:]); sys.exit(1)
line = [l for l in r.stdout.splitlines() if l.startswith('{')][-1]
d = json.loads(line)
fails = []
if d['calls'] != EXPECTED_CALLS:
    fails.append(f"查詢次數 {d['calls']} ≠ {EXPECTED_CALLS}（分母變了，結果不可信）")
extra = {int(k): v for k, v in d['confirmed'].items() if int(k) not in ALLOWED}
for bid, v in sorted(extra.items()):
    fails.append(f"#{bid} {v['name']} 對普通人 confirmed（{','.join(v['personas'])}／{len(v['counties'])} 縣市）")
# 反向：白名單裡的至少要出現一次，否則代表探針的人設壞了（例如送錯欄位、全部變 possible）
missing = [bid for bid in ALLOWED if str(bid) not in d['confirmed']]
if len(missing) == len(ALLOWED):
    fails.append('白名單一筆都沒出現 —— 探針人設或引擎壞了（全部變 possible 也會讓這支假綠）')

print(f"普通人 {d['calls']} 次查詢，confirmed {len(d['confirmed'])} 筆（白名單 {len(ALLOWED)}，命中 {len(ALLOWED) - len(missing)}）")
if fails:
    print('🔴 FAIL'); [print('  ', f) for f in fails]; sys.exit(1)
print('✅ PASS'); sys.exit(0)
