"""W-020 端對端對照：同一縣市、幾個「該看到 / 不該看到」的人打 /api/check，
   列出指定 benefit id 各落在哪一級（confirmed / possible / not_eligible / 不出現）。
   🔴 只驗正向沒有鑑別力（AGENTS §5.6）—— 一定要有「不該看到」的對照組。
   用法：python e2e_personas.py 高雄市 6,354,879,...   （後端要先在 :3000 跑）"""
import json, sys, urllib.request

county = sys.argv[1]
ids = [int(x) for x in sys.argv[2].split(',')]
API = 'http://localhost:3000/api/check'


def base(**kw):
    p = dict(birthDate='1996-05-01', county=county, gender='male', maritalStatus='single',
             householdMembers=[], housingStatus='own', selfAnnualIncome=900_000, selfAssets=2_000_000,
             employmentStatus='employed_insured', nonCohabitingFamily=[], specialIdentities=[],
             familySpecialCircumstances=[])
    p.update(kw)
    return p


PERSONAS = {
    '①30歲上班族(對照)': base(),
    '②70歲低收': base(birthDate='1956-01-01', selfAnnualIncome=0, selfAssets=0, employmentStatus='retired',
                       housingStatus='rent'),
    '③身障租屋': base(selfDisabilityCard=True, housingStatus='rent', selfAnnualIncome=200_000, selfAssets=50_000),
    '④單親低收有5歲子': base(maritalStatus='divorced', selfAnnualIncome=120_000, selfAssets=10_000,
                          housingStatus='rent', familySpecialCircumstances=['single_parent_custody'],
                          householdMembers=[dict(relationship='子女', birthDate='2021-03-01',
                                                 registeredCounty=county, sameHukou=True)]),
    '⑥70歲同②但已列冊低收': base(birthDate='1956-01-01', selfAnnualIncome=0, selfAssets=0, employmentStatus='retired',
                       housingStatus='rent', registeredLowIncome='low_income'),
    '⑤臺南人(縣市對照)': base(county='臺南市', birthDate='1956-01-01', selfAnnualIncome=0, selfAssets=0,
                          selfDisabilityCard=True, housingStatus='rent'),
}


def call(p):
    req = urllib.request.Request(API, data=json.dumps(p).encode(), headers={'Content-Type': 'application/json'})
    return json.load(urllib.request.urlopen(req, timeout=60))


def where(resp, bid):
    # 🔴 回傳只有 self.confirmed / self.possible；not_eligible 的不會出現 ⇒ '—'
    for tier in ('confirmed', 'possible'):
        for b in resp['self'].get(tier, []) or []:
            if b.get('id') == bid:
                return tier[:4]
    return '—'


out = {}
for name, p in PERSONAS.items():
    r = call(p)
    if 'self' not in r:
        print(name, '🔴 API 錯誤：', r); sys.exit(2)
    out[name] = {bid: where(r, bid) for bid in ids}
    out[name]['_counts'] = {k: len(r['self'].get(k, []) or []) for k in ('confirmed', 'possible')}

print('id   ' + ' | '.join(n[:8] for n in out))
for bid in ids:
    print(f'{bid:<5}' + ' | '.join(f'{out[n][bid]:<8}' for n in out))
print('計數 ' + ' | '.join(f"c{out[n]['_counts']['confirmed']}/p{out[n]['_counts']['possible']}" for n in out))
json.dump(out, open(f'/tmp/_tmp-e2e-{county}.json', 'w'), ensure_ascii=False, indent=1)
