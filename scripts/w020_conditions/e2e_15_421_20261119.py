"""C-6b 2026-11-19：15 雲林認定／421 彰化中低收老人假牙／1009 彰化身障(中)低收假牙 端對端。
   打 /api/check；🔴 含負向對照（不該看到的人必須看不到，AGENTS §5.6）。
   用法：python e2e_15_421_20261119.py [port]   全對 exit 0"""
import json, sys, urllib.request

PORT = sys.argv[1] if len(sys.argv) > 1 else '3000'
API = f'http://localhost:{PORT}/api/check'


def person(county, birth, reg, disab=False, income=900_000, idents=()):
    return dict(birthDate=birth, county=county, gender='male', maritalStatus='single', householdMembers=[],
                housingStatus='rent', selfAnnualIncome=income, selfAssets=0, employmentStatus='retired',
                nonCohabitingFamily=[], specialIdentities=list(idents), familySpecialCircumstances=[],
                registeredLowIncome=reg, selfDisabilityCard=disab, residencyMonths=600)


# (說明, 縣市, 出生, 列冊, 身障, 年收) → {id: 預期}   poss/conf＝看得到；—＝看不到
CASES = [
    ('彰化 40歲 中低收 有身障',   '彰化縣', '1986-01-01', 'mid_low_income', True,  100_000, {1009: 'poss', 421: '—'}),
    ('彰化 40歲 低收 有身障',     '彰化縣', '1986-01-01', 'low_income',     True,  100_000, {1009: 'poss', 421: '—'}),
    ('彰化 40歲 中低收 無身障',   '彰化縣', '1986-01-01', 'mid_low_income', False, 100_000, {1009: '—',    421: '—'}),
    ('彰化 40歲 未列冊 有身障',   '彰化縣', '1986-01-01', 'none',           True,  900_000, {1009: '—',    421: '—'}),
    ('彰化 70歲 中低收 有身障',   '彰化縣', '1956-01-01', 'mid_low_income', True,  100_000, {1009: '—',    421: 'poss'}),
    ('臺南 40歲 中低收 有身障',   '臺南市', '1986-01-01', 'mid_low_income', True,  100_000, {1009: '—'}),
    ('雲林 40歲 低所得 未列冊',   '雲林縣', '1986-01-01', 'none',           False, 60_000,  {15: 'poss'}),   # 有 unchecked（動產／不動產）⇒ 最高 possible，同 16 嘉義縣
    ('雲林 40歲 年收90萬',        '雲林縣', '1986-01-01', 'none',           False, 900_000, {15: '—'}),
    ('嘉義縣 40歲 低所得 未列冊', '嘉義縣', '1986-01-01', 'none',           False, 60_000,  {15: '—', 16: 'poss'}),   # 對照組：同一個人在嘉義縣看得到 16
]


def where(resp, bid):
    for tier in ('confirmed', 'possible'):
        for b in resp['self'].get(tier, []) or []:
            if b.get('id') == bid:
                return tier[:4]
    return '—'


bad = 0
for name, county, birth, reg, dis, inc, exp in CASES:
    req = urllib.request.Request(API, data=json.dumps(person(county, birth, reg, dis, inc)).encode(),
                                 headers={'Content-Type': 'application/json'})
    r = json.load(urllib.request.urlopen(req, timeout=60))
    if 'self' not in r:
        print('🔴 API 錯誤', name, r); sys.exit(2)
    row = []
    for bid, want in exp.items():
        got = where(r, bid)
        ok = got == want
        bad += not ok
        row.append(f'{bid}:{got}{"" if ok else f"≠{want}❌"}')
    print(f'{name:<18} ' + '  '.join(row))
print('全對' if not bad else f'🔴 {bad} 格不符'); sys.exit(1 if bad else 0)
