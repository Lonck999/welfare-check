"""C-6b ②：假牙「65 歲（原住民 55）」端對端對照。
   四個人 × 每筆假牙所在縣市，打 /api/check，列出該筆落在哪一級。
   🔴 一定要有「不該看到」的人（60 歲非原住民、非列冊）—— 只驗正向沒有鑑別力（AGENTS §5.6）。
   用法：python e2e_denture_age.py [port] > out.txt   （後端先跑在該 port，預設 3001）"""
import json, sys, urllib.request

PORT = sys.argv[1] if len(sys.argv) > 1 else '3001'
API = f'http://localhost:{PORT}/api/check'
ROWS = {409: '臺北市', 410: '新北市', 411: '桃園市', 412: '臺中市', 413: '臺南市', 414: '高雄市', 415: '基隆市',
        417: '嘉義市', 419: '新竹縣', 420: '苗栗縣', 421: '彰化縣', 422: '南投縣', 423: '雲林縣', 425: '屏東縣',
        427: '花蓮縣', 428: '澎湖縣', 430: '連江縣'}


def person(county, birth, idents, reg, income, assets):
    return dict(birthDate=birth, county=county, gender='male', maritalStatus='single', householdMembers=[],
                housingStatus='rent', selfAnnualIncome=income, selfAssets=assets, employmentStatus='retired',
                nonCohabitingFamily=[], specialIdentities=idents, familySpecialCircumstances=[],
                registeredLowIncome=reg)


PERSONAS = {
    'A 60歲原住民低收': ('1966-01-01', ['原住民'], 'low_income', 0, 0),
    'B 60歲非原住民低收': ('1966-01-01', [], 'low_income', 0, 0),
    'C 60歲非原住民一般': ('1966-01-01', [], 'none', 900_000, 3_000_000),
    'D 70歲一般(非列冊)': ('1956-01-01', [], 'none', 900_000, 3_000_000),
}


def where(resp, bid):
    for tier in ('confirmed', 'possible'):
        for b in resp['self'].get(tier, []) or []:
            if b.get('id') == bid:
                return tier[:4]
    return '—'


out = {}
for bid, county in ROWS.items():
    out[bid] = {}
    for name, args in PERSONAS.items():
        req = urllib.request.Request(API, data=json.dumps(person(county, *args)).encode(),
                                     headers={'Content-Type': 'application/json'})
        r = json.load(urllib.request.urlopen(req, timeout=60))
        if 'self' not in r:
            print('🔴 API 錯誤', bid, name, r); sys.exit(2)
        out[bid][name] = where(r, bid)
print('id   縣市   ' + ' | '.join(n for n in PERSONAS))
for bid, county in ROWS.items():
    print(f'{bid:<4} {county} ' + ' | '.join(f'{out[bid][n]:<6}' for n in PERSONAS))
