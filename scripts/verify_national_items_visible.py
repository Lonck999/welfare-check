#!/usr/bin/env python3
"""回歸 W-023：county='全國' 的項目要在任何縣市查得到；別縣市的項目不可混進來。

🔴 起因（2026-10-20）：/api/check 撈資料只撈 `county IS NULL` 與使用者縣市，
   而 9/25 補建的 21 筆全國制度、10/20 匯入的 3 筆衛福部方案都存成 county='全國'
   ⇒ 24 筆對**任何人**都看不到，且不報錯。9/25 的 national-scope.test.ts 只測引擎函式 → 全綠。
🔴 這支走 /api/check 端對端（Fastify inject，不開 port）：
   · 正向：臺北市、連江縣兩個人，「全國」項目至少要看到一半（10-20 實測 14/24；其餘被年齡、身分等條件判不符，例如勞保遺屬年金）
   · 反向：臺南市專屬項目一筆都不可出現
     ⚠️ 2026-10-20 實測：只拿掉 DB 篩選時這條仍綠 —— 引擎的 counties 判斷會再擋一次（雙重保險）。
        所以它守的是「DB 篩選＋引擎判斷都失效」，不是單獨守 DB 篩選；正向那條才是 W-023 的主斷言。

跑法：python verify_national_items_visible.py
"""
import json, os, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MIN_SEEN = 1
# 🔴 2026-10-29 改判準：原本是「至少看到一半（MIN_SEEN_RATIO 0.5）」—— 那個比例是 10-20 量出來的 14/24，
#    當時大部分全國項目沒有條件（W-020）⇒ 一律 possible ⇒ 誰都看得到。
#    10-29 W-020 B 依原文補了條件（遺屬年金只能為家人申請、老年年金要 65 歲…）⇒ 30 歲上班族合理地只剩 8/24，
#    比例判準就紅了，**而程式完全沒壞**（寫死的結論活得比它的證據久，AGENTS §5.5）。
#    W-023 的 bug 長相是「全國項目一筆都看不到」⇒ 改成兩條跟資料條件無關的斷言：
#    ① 每個縣市至少看到 1 筆全國項目 ② 同一個人換縣市，看到的全國項目必須完全相同（全國項目不該隨縣市變）。
#    雙向驗過：拿掉 check.ts 撈資料的 eq(county,'全國') ⇒ ① 紅；還原 ⇒ 綠。

env = dict(os.environ)
envf = ROOT / 'backend' / '.env'
if envf.exists():
    for line in envf.read_text().splitlines():
        if '=' in line and not line.lstrip().startswith('#'):
            k, v = line.split('=', 1); env.setdefault(k.strip(), v.strip().strip('"'))
if not env.get('DATABASE_URL'):
    print('⏭️ 跳過：沒有 DATABASE_URL —— 這不算通過'); sys.exit(2)

r = subprocess.run(['npx', 'tsx', 'scripts/w023_national_probe.ts'], cwd=ROOT / 'backend', env=env,
                   capture_output=True, text=True, timeout=120)
if r.returncode != 0:
    print('🔴 探針執行失敗\n', r.stderr[-1500:]); sys.exit(1)
d = json.loads([l for l in r.stdout.splitlines() if l.startswith('{')][-1])
fails = []
n = len(d['national'])
if n < 20:
    fails.append(f"資料庫 county='全國' 只有 {n} 筆（10-20 時 24 筆）—— 分母變了，先查是不是被改掉")
seen_sets = {}
for county, v in d['out'].items():
    seen = len(v['seen'])
    seen_sets[county] = set(v['seen'])
    print(f"{county}：全國項目看到 {seen}/{n}；臺南專屬混入 {len(v['foreign'])}")
    if seen < MIN_SEEN:
        fails.append(f"{county} 一筆全國項目都看不到（0/{n}）—— 撈資料的縣市篩選又漏了 '全國'")
    if v['foreign']:
        fails.append(f"{county} 看到臺南市專屬項目 {v['foreign'][:5]} —— 縣市篩選被拿掉了")
if len({frozenset(s) for s in seen_sets.values()}) > 1:
    fails.append(f"同一個人換縣市，看到的全國項目不同：{ {c: sorted(s) for c, s in seen_sets.items()} }")
if fails:
    print('🔴 FAIL'); [print('  ', f) for f in fails]; sys.exit(1)
print('✅ PASS'); sys.exit(0)
