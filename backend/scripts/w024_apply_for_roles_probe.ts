/**
 * W-024 回歸（2026-10-30）：問卷勾「也幫家人找」（applyForRoles）要真的傳進比對。
 * 🔴 validateAnswers() 逐欄重建答案物件，**漏了 applyForRoles** ⇒ 前端送什麼都變成 []，
 *    65 筆「只能為家人申請」的福利（托育、喪葬、子女補助…）從 9/25 起對任何人都看不到，且不報錯。
 *    P4 篩選的單元邏輯沒錯，錯在它根本收不到值 —— 所以這支走 /api/check 端對端。
 * 用 Fastify inject，不開 port。輸出一行 JSON 給 verify_apply_for_roles_e2e.py 讀。
 */
import Fastify from 'fastify'
import { registerCheckRoute } from '../src/routes/check.js'
import { db } from '../src/db/client.js'
import { benefits, benefitApplicants } from '../src/db/schema.js'
import { and, eq, inArray } from 'drizzle-orm'

const base = {
  birthDate: '1990-01-01', county: '臺中市', gender: 'female', maritalStatus: 'married',
  householdMembers: [{ relationship: '子女', birthDate: '2016-03-01', registeredCounty: '臺中市', sameHukou: true }],
  housingStatus: 'rent', selfAnnualIncome: 0, selfAssets: 0, employmentStatus: 'unemployed_seeking',
  nonCohabitingFamily: [], specialIdentities: [], familySpecialCircumstances: [], residencyMonths: 360,
}
// 只能為家人申請（有 role、但沒有 self）且 county 是臺中或全國的啟用項目 —— 分母
const roleRows = await db.select({ id: benefitApplicants.benefitId, role: benefitApplicants.role }).from(benefitApplicants)
const roles = new Map<number, Set<string>>()
for (const r of roleRows) { if (!roles.has(r.id)) roles.set(r.id, new Set()); roles.get(r.id)!.add(r.role) }
const familyOnly = [...roles].filter(([, s]) => !s.has('self') && s.has('family')).map(([id]) => id)
const scoped = (await db.select({ id: benefits.id, county: benefits.county }).from(benefits)
  .where(and(eq(benefits.isActive, true), inArray(benefits.id, familyOnly.length ? familyOnly : [-1]))))
  .filter((r) => r.county === '臺中市' || r.county === '全國' || r.county === null).map((r) => r.id)

const app = Fastify({ logger: false }); await registerCheckRoute(app)
const ids = async (applyForRoles: string[]) => {
  const b = (await app.inject({ method: 'POST', url: '/api/check', payload: { ...base, applyForRoles } })).json()
  return [...b.self.confirmed, ...b.self.possible].map((x: { id: number }) => x.id)
}
const withFamily = await ids(['family'])
const without = await ids([])
console.log(JSON.stringify({ scoped, withFamily, without }))
process.exit(0)
