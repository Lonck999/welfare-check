/**
 * W-023 回歸（2026-10-20）：county='全國' 的項目，任何縣市查都要撈得到；別縣市的項目不可混進來。
 * 🔴 9/25 national-scope.test.ts 只測引擎（evaluateEligibility），DB 撈資料那層只撈 county IS NULL
 *    ⇒ 引擎測試全綠，而 24 筆「全國」從來沒被任何人看到過。所以這支走 /api/check 端對端。
 * 用 Fastify inject，不開 port。輸出一行 JSON 給 verify_national_items_visible.py 讀。
 */
import Fastify from 'fastify'
import { registerCheckRoute } from '../src/routes/check.js'
import { db } from '../src/db/client.js'
import { benefits } from '../src/db/schema.js'
import { and, eq } from 'drizzle-orm'

const base = {
  birthDate: '1996-05-01', gender: 'male', maritalStatus: 'single', householdMembers: [] as unknown[], housingStatus: 'own',
  selfAnnualIncome: 900_000, selfAssets: 2_000_000, employmentStatus: 'employed_insured', nonCohabitingFamily: [],
  specialIdentities: [], familySpecialCircumstances: [], registeredLowIncome: 'none', residencyMonths: 360,
}
const national = (await db.select({ id: benefits.id }).from(benefits)
  .where(and(eq(benefits.isActive, true), eq(benefits.county, '全國')))).map((r) => r.id)
const tainanOnly = (await db.select({ id: benefits.id }).from(benefits)
  .where(and(eq(benefits.isActive, true), eq(benefits.county, '臺南市')))).map((r) => r.id)

const app = Fastify({ logger: false }); await registerCheckRoute(app)
const out: Record<string, { seen: number[]; foreign: number[] }> = {}
for (const county of ['臺北市', '連江縣']) {
  const b = (await app.inject({ method: 'POST', url: '/api/check', payload: { ...base, county } })).json()
  const ids = new Set<number>([...b.self.confirmed, ...b.self.possible].map((x: { id: number }) => x.id))
  out[county] = { seen: national.filter((i) => ids.has(i)), foreign: tainanOnly.filter((i) => ids.has(i)) }
}
console.log(JSON.stringify({ national, out }))
process.exit(0)
