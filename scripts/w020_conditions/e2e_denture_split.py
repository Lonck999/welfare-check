"""C-6b 假牙一般長者拆分（1005 高雄／1006 嘉義市／1007 彰化）端對端。
   打 /api/check，比對「預期 vs 實際」。🔴 含負向對照：年齡不到、設籍不夠的人必須看不到（AGENTS §5.6）。
   用法：python e2e_denture_split.py [port]   （預設 3000）  ；全對 exit 0，有錯 exit 1"""
import json, sys, urllib.request

PORT = sys.argv[1] if len(sys.argv) > 1 else '3000'
API = f'http://localhost:{PORT}/api/check'


def person(county, birth, reg, residency, idents=()):
    p = dict(birthDate=birth, county=county, gender='male', maritalStatus='single', householdMembers=[],
             housingStatus='rent', selfAnnualIncome=900_000, selfAssets=3_000_000, employmentStatus='retired',
             nonCohabitingFamily=[], specialIdentities=list(idents), familySpecialCircumstances=[], registeredLowIncome=reg)
    if residency is not None:
        p['residencyMonths'] = residency
    return p


# (人物, 出生, 列冊, 設籍月) → {benefit_id: 預期}；poss＝看得到，—＝看不到
CASES = [
    ('60歲一般',           '1966-01-01', 'none', 600, {1005: '—',    1006: '—',    1007: '—',    1008: '—'}),
    ('70歲一般 設籍50年',  '1956-01-01', 'none', 600, {1005: 'poss', 1006: '—',    1007: 'poss', 1008: 'poss'}),
    ('80歲一般 設籍50年',  '1946-01-01', 'none', 600, {1005: 'poss', 1006: 'poss', 1007: 'poss', 1008: 'poss'}),
    ('80歲一般 設籍2年',   '1946-01-01', 'none', 24,  {1005: 'poss', 1006: '—',    1007: '—',    1008: 'poss'}),
    ('80歲一般 設籍4年',   '1946-01-01', 'none', 48,  {1005: 'poss', 1006: '—',    1007: 'poss', 1008: 'poss'}),
    ('80歲一般 未答設籍',  '1946-01-01', 'none', None, {1005: 'poss', 1006: 'poss', 1007: 'poss', 1008: 'poss'}),
    ('60歲原住民',         '1966-01-01', 'none', 600, {1005: '—',    1006: '—',    1007: '—',    1008: 'poss'}, ['原住民']),
]
COUNTY = {1005: '高雄市', 1006: '嘉義市', 1007: '彰化縣', 1008: '臺南市'}


def where(resp, bid):
    for tier in ('confirmed', 'possible'):
        for b in resp['self'].get(tier, []) or []:
            if b.get('id') == bid:
                return tier[:4]
    return '—'


bad = 0
for name, birth, reg, res, exp, *idn in CASES:
    row = []
    for bid, want in exp.items():
        req = urllib.request.Request(API, data=json.dumps(person(COUNTY[bid], birth, reg, res, *idn)).encode(),
                                     headers={'Content-Type': 'application/json'})
        r = json.load(urllib.request.urlopen(req, timeout=60))
        if 'self' not in r:
            print('🔴 API 錯誤', bid, name, r); sys.exit(2)
        got = where(r, bid)
        ok = got == want
        bad += not ok
        row.append(f'{bid}:{got}{"" if ok else f"≠{want}❌"}')
    print(f'{name:<14} ' + '  '.join(row))
print('全對' if not bad else f'🔴 {bad} 格不符'); sys.exit(1 if bad else 0)
