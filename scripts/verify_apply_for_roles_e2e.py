"""W-024 回歸（2026-10-30）：問卷的「也幫家人找」（applyForRoles）必須真的生效。
   🔴 validateAnswers() 漏了 applyForRoles ⇒ 65 筆只能為家人申請的福利從 9/25 起對任何人都看不到，且不報錯。
   斷言（都跟資料內容無關，只跟「這個開關有沒有作用」有關）：
     ① 勾 family 的人看到的「只能為家人申請」項目 ≥ 1（分母是臺中＋全國的 family-only 項目）
     ② 沒勾的人看到 0 筆 family-only（P4：沒要幫家人找就只給自身）
     ③ 勾了比沒勾多 —— 開關必須改變結果
   雙向驗過：把 check.ts 的 applyForRoles 那行拿掉 ⇒ ① ③ 紅；還原 ⇒ 綠。"""
import json, os, subprocess, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
env = dict(os.environ)
envf = ROOT / 'backend' / '.env'
if envf.exists():
    for line in envf.read_text().splitlines():
        if '=' in line and not line.lstrip().startswith('#'):
            k, v = line.split('=', 1); env.setdefault(k.strip(), v.strip().strip('"').strip("'"))
r = subprocess.run(['npx', 'tsx', 'scripts/w024_apply_for_roles_probe.ts'], cwd=ROOT / 'backend', env=env,
                   capture_output=True, text=True, timeout=180)
line = [l for l in r.stdout.splitlines() if l.startswith('{')]
if r.returncode != 0 or not line:
    print('🔴 probe 失敗', r.returncode, r.stderr[-800:]); sys.exit(1)
d = json.loads(line[-1])
scoped = set(d['scoped']); w = set(d['withFamily']); wo = set(d['without'])
fails = []
if len(scoped) < 5:
    fails.append(f'分母只有 {len(scoped)} 筆 family-only 項目（10-30 時 ≥ 5）—— 先查 benefit_applicants 是不是被改掉')
seen_w, seen_wo = scoped & w, scoped & wo
print(f'臺中家長（有 10 歲子女、低收）：family-only 項目 {len(scoped)} 筆；勾幫家人找 → 看到 {len(seen_w)}；沒勾 → 看到 {len(seen_wo)}')
if not seen_w:
    fails.append('勾了「幫家人找」卻一筆 family-only 都看不到 —— applyForRoles 沒傳進比對（W-024）')
if seen_wo:
    fails.append(f'沒勾「幫家人找」卻看到 family-only {sorted(seen_wo)[:5]} —— P4 篩選失效')
if len(w) <= len(wo):
    fails.append(f'勾與不勾結果一樣多（{len(w)} vs {len(wo)}）—— 開關沒有作用')
if fails:
    print('🔴 FAIL'); [print('  ', f) for f in fails]; sys.exit(1)
print('✅ PASS'); sys.exit(0)
