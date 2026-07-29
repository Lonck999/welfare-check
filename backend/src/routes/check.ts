import type { FastifyInstance } from 'fastify'
import { and, eq, isNull, or } from 'drizzle-orm'
import { db } from '../db/client.js'
import { benefits, benefitDocuments, benefitLocations } from '../db/schema.js'
import { ALL_22_COUNTIES } from '../db/seed-data/counties.js'
import {
  calculateAge,
  calculatePerCapitaMonthlyIncome,
  calculatePerCapitaAssets,
  evaluateIncomeThreshold,
} from '../logic/calculations.js'
import {
  evaluateEligibility,
  type ApplicantProfile,
  type EligibilityConditions,
} from '../logic/eligibility.js'
import { FLAG_OPTIONS, IDENTITY_OPTIONS, IMPLICIT_FLAGS } from '../logic/profile-mapping.js'

interface HouseholdMemberInput {
  annualIncome: number
  assets: number
}

interface CheckRequestBody {
  birthDate: string // YYYY-MM-DD
  county: string
  workCounty?: string
  ownsHome: boolean
  householdMembers: HouseholdMemberInput[] // 應計算人口，至少含本人 1 筆
  youngestChildAge?: number
  oldestElderAge?: number
  identities?: string[]
  flags?: string[]
}

function isValidDateString(value: unknown): value is string {
  return typeof value === 'string' && /^\d{4}-\d{2}-\d{2}$/.test(value) && !Number.isNaN(Date.parse(value))
}

function validateBody(body: unknown): CheckRequestBody {
  if (typeof body !== 'object' || body === null) throw new Error('請求格式錯誤')
  const b = body as Record<string, unknown>

  if (!isValidDateString(b.birthDate)) throw new Error('出生年月日格式須為 YYYY-MM-DD')
  if (typeof b.county !== 'string' || !ALL_22_COUNTIES.includes(b.county)) {
    throw new Error('居住縣市不在 22 縣市清單內')
  }
  if (b.workCounty !== undefined && !ALL_22_COUNTIES.includes(b.workCounty as string)) {
    throw new Error('工作地點縣市不在 22 縣市清單內')
  }
  if (typeof b.ownsHome !== 'boolean') throw new Error('請填寫是否有自有住宅')
  if (!Array.isArray(b.householdMembers) || b.householdMembers.length === 0) {
    throw new Error('至少需要一筆應計算人口的收入/財產資料（本人）')
  }
  for (const m of b.householdMembers as unknown[]) {
    if (
      typeof m !== 'object' ||
      m === null ||
      typeof (m as Record<string, unknown>).annualIncome !== 'number' ||
      typeof (m as Record<string, unknown>).assets !== 'number'
    ) {
      throw new Error('應計算人口的 annualIncome/assets 必須是數字')
    }
  }

  return {
    birthDate: b.birthDate as string,
    county: b.county as string,
    workCounty: b.workCounty as string | undefined,
    ownsHome: b.ownsHome as boolean,
    householdMembers: b.householdMembers as HouseholdMemberInput[],
    youngestChildAge: typeof b.youngestChildAge === 'number' ? b.youngestChildAge : undefined,
    oldestElderAge: typeof b.oldestElderAge === 'number' ? b.oldestElderAge : undefined,
    identities: Array.isArray(b.identities) ? (b.identities as string[]) : [],
    flags: Array.isArray(b.flags) ? (b.flags as string[]) : [],
  }
}

interface BenefitResult {
  id: number
  categoryNumber: number | null
  name: string
  agency: string
  county: string | null
  description: string
  isTimeSensitive: boolean
  applicationPeriod: string | null
  notes: string | null
  sourceUrl: string
  missingConditions: string[]
  documents: string[]
  locations: Array<{ name: string; address: string | null; phone: string | null; website: string | null }>
  lastVerifiedDate: string
  sourceExcerpt: string
}

export async function registerCheckRoute(app: FastifyInstance) {
  app.get('/api/form-options', async () => ({
    counties: ALL_22_COUNTIES,
    flags: FLAG_OPTIONS,
    identities: IDENTITY_OPTIONS,
  }))

  app.post('/api/check', async (request, reply) => {
    let body: CheckRequestBody
    try {
      body = validateBody(request.body)
    } catch (err) {
      reply.code(400)
      return { error: err instanceof Error ? err.message : '請求格式錯誤' }
    }

    const asOf = new Date()
    const age = calculateAge(new Date(body.birthDate), asOf)
    const perCapitaMonthlyIncome = calculatePerCapitaMonthlyIncome(body.householdMembers)
    const perCapitaAssets = calculatePerCapitaAssets(body.householdMembers)

    // 依居住縣市查第 1 類「低收入戶/中低收入戶認定」的官方門檻數字（見 01-low-income-threshold.ts）
    const [thresholdRow] = await db
      .select()
      .from(benefits)
      .where(and(eq(benefits.categoryNumber, 1), eq(benefits.county, body.county)))
      .limit(1)

    if (!thresholdRow) {
      reply.code(500)
      return { error: `找不到 ${body.county} 的低收入戶認定門檻資料，請確認資料庫已完成建檔` }
    }
    const referenceData = (thresholdRow.eligibilityConditions as EligibilityConditions | null)
      ?.referenceData
    const minLivingExpense = referenceData?.minLivingExpense
    if (minLivingExpense === undefined) {
      reply.code(500)
      return { error: `${body.county} 的最低生活費資料缺漏` }
    }

    const incomeThresholdResult = evaluateIncomeThreshold(perCapitaMonthlyIncome, minLivingExpense)

    const profile: ApplicantProfile = {
      age,
      county: body.county,
      workCounty: body.workCounty,
      incomeThresholdResult,
      perCapitaAssets,
      identities: body.identities,
      hasChildUnder: body.youngestChildAge,
      hasElderOver: body.oldestElderAge,
      ownsHome: body.ownsHome,
      flags: [...(body.flags ?? []), ...IMPLICIT_FLAGS],
    }

    const allBenefits = await db
      .select()
      .from(benefits)
      .where(
        and(
          eq(benefits.isActive, true),
          or(isNull(benefits.county), eq(benefits.county, body.county), eq(benefits.county, body.workCounty ?? '')),
        ),
      )

    const confirmed: BenefitResult[] = []
    const possible: BenefitResult[] = []
    const relevantIds: number[] = []

    for (const benefit of allBenefits) {
      const conditions = (benefit.eligibilityConditions as EligibilityConditions | null) ?? {}
      const result = evaluateEligibility(conditions, profile)
      if (result.verdict === 'not_eligible') continue

      relevantIds.push(benefit.id)
      const entry: BenefitResult = {
        id: benefit.id,
        categoryNumber: benefit.categoryNumber,
        name: benefit.name,
        agency: benefit.agency,
        county: benefit.county,
        description: benefit.description,
        isTimeSensitive: benefit.isTimeSensitive,
        applicationPeriod: benefit.applicationPeriod,
        notes: benefit.notes,
        sourceUrl: benefit.sourceUrl,
        sourceExcerpt: benefit.sourceExcerpt,
        lastVerifiedDate: benefit.lastVerifiedDate,
        missingConditions: result.missingConditions,
        documents: [],
        locations: [],
      }
      if (result.verdict === 'confirmed') confirmed.push(entry)
      else possible.push(entry)
    }

    if (relevantIds.length > 0) {
      const [documents, locations] = await Promise.all([
        db.select().from(benefitDocuments),
        db.select().from(benefitLocations),
      ])
      const documentsByBenefit = new Map<number, string[]>()
      for (const doc of documents) {
        if (!relevantIds.includes(doc.benefitId)) continue
        const list = documentsByBenefit.get(doc.benefitId) ?? []
        list.push(doc.documentName)
        documentsByBenefit.set(doc.benefitId, list)
      }
      const locationsByBenefit = new Map<number, BenefitResult['locations']>()
      for (const loc of locations) {
        if (!relevantIds.includes(loc.benefitId)) continue
        const list = locationsByBenefit.get(loc.benefitId) ?? []
        list.push({ name: loc.name, address: loc.address, phone: loc.phone, website: loc.website })
        locationsByBenefit.set(loc.benefitId, list)
      }
      for (const entry of [...confirmed, ...possible]) {
        entry.documents = documentsByBenefit.get(entry.id) ?? []
        entry.locations = locationsByBenefit.get(entry.id) ?? []
      }
    }

    // 時效性項目優先排在前面，對應 SKILL.md 注意事項「有截止期限者優先列出」
    const sortByUrgency = (a: BenefitResult, b: BenefitResult) => Number(b.isTimeSensitive) - Number(a.isTimeSensitive)
    confirmed.sort(sortByUrgency)
    possible.sort(sortByUrgency)

    // 資料更新日期：取顯示結果中「最舊」的查證日期，讓使用者知道最需要留意的資料落差上限，
    // 而不是用最新一筆掩蓋掉其他項目可能更久沒查證的事實。
    const allVerifiedDates = [...confirmed, ...possible].map((b) => b.lastVerifiedDate)
    const oldestVerifiedDate =
      allVerifiedDates.length > 0 ? allVerifiedDates.reduce((oldest, d) => (d < oldest ? d : oldest)) : null

    return {
      computed: {
        age,
        perCapitaMonthlyIncome: Math.round(perCapitaMonthlyIncome),
        perCapitaAssets: Math.round(perCapitaAssets),
        minLivingExpense,
        incomeThresholdResult,
      },
      generatedAt: asOf.toISOString().slice(0, 10),
      oldestVerifiedDate,
      confirmed,
      possible,
    }
  })
}
