"""W-022：找「條件編不完整」的項目 —— 讓一群「沒有任何特殊身分」的普通人查 22 縣市，
   收集他們的 confirmed。這些人該看到的只有「真的人人可申請」的福利；
   清單裡任何一筆不是，就代表那筆的條件少編了。
   🔴 用症狀找，不用關鍵字找：描述裡有「低收入戶另加 1 萬」不代表限低收（是加碼），
      關鍵字掃描會誤判；「普通人看到 confirmed」才是錯誤本身。
   輸出 /tmp/_tmp-w022-confirmed.json：{id: {name, personas:[...], counties:[...]}}
   用法：python w022_baseline_confirmed.py   （後端要先在 :3000）"""
import json, sys, urllib.request

COUNTIES = ['臺北市', '新北市', '桃園市', '臺中市', '臺南市', '高雄市', '基隆市', '新竹市', '嘉義市', '新竹縣', '苗栗縣',
            '彰化縣', '南投縣', '雲林縣', '嘉義縣', '屏東縣', '宜蘭縣', '花蓮縣', '臺東縣', '澎湖縣', '金門縣', '連江縣']
assert len(COUNTIES) == 22


def base(**kw):
    p = dict(birthDate='1996-05-01', gender='male', maritalStatus='single', householdMembers=[], housingStatus='own',
             selfAnnualIncome=900_000, selfAssets=2_000_000, employmentStatus='employed_insured', nonCohabitingFamily=[],
             specialIdentities=[], familySpecialCircumstances=[], registeredLowIncome='none', residencyMonths=360)
    p.update(kw)
    return p


# 三個「普通人」：刻意把各種身分都關掉，只變動年齡／性別／住房，讓年齡類與住房類的福利有機會出現
PERSONAS = {
    '30男有房上班': base(),
    '45女租屋上班': base(birthDate='1981-03-01', gender='female', housingStatus='rent', maritalStatus='married',
                      householdMembers=[dict(relationship='配偶', birthDate='1980-01-01', sameHukou=True, annualIncome=800_000)]),
    '22男租屋失業': base(birthDate='2004-02-01', housingStatus='rent', employmentStatus='unemployed_seeking', selfAnnualIncome=300_000,
                      selfAssets=100_000),
}


def call(p):
    req = urllib.request.Request('http://localhost:3000/api/check', data=json.dumps(p).encode(),
                                 headers={'Content-Type': 'application/json'})
    return json.load(urllib.request.urlopen(req, timeout=60))


out = {}
n_calls = 0
for county in COUNTIES:
    for pname, p in PERSONAS.items():
        r = call(dict(p, county=county))
        assert 'self' in r, r
        n_calls += 1
        for b in r['self']['confirmed']:
            e = out.setdefault(b['id'], {'name': b['name'], 'county': b.get('county'), 'personas': set(), 'counties': set()})
            e['personas'].add(pname); e['counties'].add(county)
for e in out.values():
    e['personas'] = sorted(e['personas']); e['counties'] = sorted(e['counties'])
json.dump(out, open('/tmp/_tmp-w022-confirmed.json', 'w'), ensure_ascii=False, indent=1)
print(f'{n_calls} 次查詢（22 縣市 × {len(PERSONAS)} 人），普通人 confirmed 不重複 {len(out)} 筆')
