"""W-028 前後對照：幾種人在幾個縣市看到多少 confirmed／possible，並列出 W-028 範圍內的 id 出現在哪。
用法：python w028_personas_20261119.py [port] > out.json"""
import json, sys, urllib.request
PORT = sys.argv[1] if len(sys.argv) > 1 else '3000'
W028 = set(json.load(open('/Users/lonck/.hermes/cache/welfare_w028_20261119/scope_ids.json')))

def person(county, birth, **kw):
    p = dict(birthDate=birth, county=county, gender='male', maritalStatus='single', householdMembers=[],
             housingStatus='rent', selfAnnualIncome=900_000, selfAssets=3_000_000, employmentStatus='employed_insured',
             nonCohabitingFamily=[], specialIdentities=[], familySpecialCircumstances=[], registeredLowIncome='none',
             selfDisabilityCard=False, residencyMonths=600)
    p.update(kw); return p

PERSONAS = {
    '30歲上班族': dict(birth='1996-01-01'),
    '70歲退休': dict(birth='1956-01-01', employmentStatus='retired', selfAnnualIncome=200_000),
    '40歲中低收身障': dict(birth='1986-01-01', registeredLowIncome='mid_low_income', selfDisabilityCard=True, selfAnnualIncome=100_000, employmentStatus='retired'),
}
out = {}
for county in ('新北市', '桃園市', '臺南市', '新竹市', '嘉義市'):
    for name, kw in PERSONAS.items():
        kw = dict(kw); birth = kw.pop('birth')
        r = json.load(urllib.request.urlopen(urllib.request.Request(f'http://localhost:{PORT}/api/check',
            data=json.dumps(person(county, birth, **kw)).encode(), headers={'Content-Type': 'application/json'}), timeout=60))
        if 'self' not in r:
            print('API error', county, name, r); sys.exit(2)
        s = r['self']
        out[f'{county}|{name}'] = {t: sorted(b['id'] for b in (s.get(t) or [])) for t in ('confirmed', 'possible')}
json.dump(out, sys.stdout, ensure_ascii=False)
