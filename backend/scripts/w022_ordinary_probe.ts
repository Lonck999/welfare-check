/**
 * W-022 回歸（2026-10-20）：「普通人」查 22 縣市，confirmed 只能出現白名單裡的項目。
 * 用 Fastify inject，不開 port。輸出一行 JSON 給 verify_ordinary_person_confirmed.py 讀。
 *   npx tsx scripts/w022_ordinary_probe.ts（在 backend/ 下）
 */
import Fastify from 'fastify'
import { registerCheckRoute } from '../src/routes/check.js'

const COUNTIES = ['臺北市', '新北市', '桃園市', '臺中市', '臺南市', '高雄市', '基隆市', '新竹市', '嘉義市', '新竹縣', '苗栗縣',
  '彰化縣', '南投縣', '雲林縣', '嘉義縣', '屏東縣', '宜蘭縣', '花蓮縣', '臺東縣', '澎湖縣', '金門縣', '連江縣']

const base = {
  birthDate: '1996-05-01', gender: 'male', maritalStatus: 'single', householdMembers: [] as unknown[], housingStatus: 'own',
  selfAnnualIncome: 900_000, selfAssets: 2_000_000, employmentStatus: 'employed_insured', nonCohabitingFamily: [],
  specialIdentities: [], familySpecialCircumstances: [], registeredLowIncome: 'none', residencyMonths: 360,
}
const PERSONAS: Record<string, Record<string, unknown>> = {
  '30男有房上班': base,
  '45女租屋上班': { ...base, birthDate: '1981-03-01', gender: 'female', housingStatus: 'rent', maritalStatus: 'married',
    householdMembers: [{ relationship: '配偶', birthDate: '1980-01-01', sameHukou: true, annualIncome: 800_000 }] },
  '22男租屋失業': { ...base, birthDate: '2004-02-01', housingStatus: 'rent', employmentStatus: 'unemployed_seeking',
    selfAnnualIncome: 300_000, selfAssets: 100_000 },
}

const app = Fastify({ logger: false })
await registerCheckRoute(app)
const out: Record<string, { name: string; personas: string[]; counties: string[] }> = {}
let calls = 0
for (const county of COUNTIES) {
  for (const [pname, p] of Object.entries(PERSONAS)) {
    const res = await app.inject({ method: 'POST', url: '/api/check', payload: { ...p, county } })
    const body = res.json()
    if (!body.self) throw new Error(`${county}/${pname}: ${res.body}`)
    calls++
    for (const b of body.self.confirmed) {
      const e = (out[b.id] ??= { name: b.name, personas: [], counties: [] })
      if (!e.personas.includes(pname)) e.personas.push(pname)
      if (!e.counties.includes(county)) e.counties.push(county)
    }
  }
}
await app.close()
console.log(JSON.stringify({ calls, confirmed: out }))
process.exit(0)
