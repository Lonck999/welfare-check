import type { FastifyInstance } from 'fastify'
import { and, eq, isNull, or } from 'drizzle-orm'
import { db } from '../db/client.js'
import { benefits, benefitDocuments, benefitLocations } from '../db/schema.js'
import { ALL_22_COUNTIES } from '../db/seed-data/counties.js'
import { calculateAge, calculatePerCapitaAssets, calculatePerCapitaMonthlyIncome, evaluateIncomeThreshold } from '../logic/calculations.js'
import { evaluateEligibility, type ApplicantProfile, type EligibilityConditions } from '../logic/eligibility.js'
import { IDENTITY_OPTIONS } from '../logic/profile-mapping.js'
import {
  buildApplicantProfile,
  buildHouseholdFinances,
  type QuestionnaireAnswers,
} from '../logic/questionnaire.js'

function isValidDateString(value: unknown): value is string {
  return typeof value === 'string' && /^\d{4}-\d{2}-\d{2}$/.test(value) && !Number.isNaN(Date.parse(value))
}

/** 寬鬆驗證：只擋會讓後續計算掛掉的必要欄位，其餘缺漏欄位一律當作「無」處理，不擋整個請求 */
function validateAnswers(body: unknown): QuestionnaireAnswers {
  if (typeof body !== 'object' || body === null) throw new Error('請求格式錯誤')
  const b = body as Record<string, unknown>

  if (!isValidDateString(b.birthDate)) throw new Error('出生年月日（第 1 題）格式須為 YYYY-MM-DD')
  if (typeof b.county !== 'string' || !ALL_22_COUNTIES.includes(b.county)) {
    throw new Error('居住縣市（第 2 題）不在 22 縣市清單內')
  }
  if (b.workCounty !== undefined && b.workCounty !== '' && !ALL_22_COUNTIES.includes(b.workCounty as string)) {
    throw new Error('工作地點縣市（第 10a 題）不在 22 縣市清單內')
  }
  if (!['own', 'rent', 'borrow', 'other'].includes(b.housingStatus as string)) {
    throw new Error('住宅狀況（第 7 題）必填')
  }
  if (
    !['employed_insured', 'employed_reduced_hours', 'self_employed', 'unemployed_seeking', 'unemployed_not_seeking', 'retired', 'homemaker'].includes(
      b.employmentStatus as string,
    )
  ) {
    throw new Error('就業身分（第 10 題）必填')
  }
  if (!Array.isArray(b.householdMembers)) throw new Error('家庭成員名單（第 5/6 題）格式錯誤')
  for (const m of b.householdMembers as unknown[]) {
    const member = m as Record<string, unknown>
    if (!isValidDateString(member.birthDate)) throw new Error('家庭成員出生年月日（第 5 題）格式須為 YYYY-MM-DD')
    if (typeof member.relationship !== 'string' || !member.relationship) throw new Error('家庭成員關係（第 5 題）必填')
  }
  if (!Array.isArray(b.nonCohabitingFamily)) throw new Error('非同戶籍家人資料（第 13 題）格式錯誤')
  for (const m of b.nonCohabitingFamily as unknown[]) {
    const member = m as Record<string, unknown>
    if (!isValidDateString(member.birthDate)) throw new Error('非同戶籍家人出生年月日（第 13 題）格式須為 YYYY-MM-DD')
    if (typeof member.county !== 'string' || !ALL_22_COUNTIES.includes(member.county)) {
      throw new Error('非同戶籍家人戶籍縣市（第 13 題）不在 22 縣市清單內')
    }
  }

  return {
    birthDate: b.birthDate as string,
    county: b.county as string,
    district: typeof b.district === 'string' ? b.district : undefined,
    gender: b.gender as QuestionnaireAnswers['gender'],
    maritalStatus: (b.maritalStatus as QuestionnaireAnswers['maritalStatus']) ?? 'single',
    pregnantOrPostpartumSelf: Boolean(b.pregnantOrPostpartumSelf),
    pregnantOrPostpartumSpouse: Boolean(b.pregnantOrPostpartumSpouse),
    miscarriageRecently: Boolean(b.miscarriageRecently),
    familySpecialCircumstances: Array.isArray(b.familySpecialCircumstances) ? (b.familySpecialCircumstances as string[]) : [],
    householdMembers: (b.householdMembers as QuestionnaireAnswers['householdMembers']).map((m) => ({
      relationship: m.relationship,
      birthDate: m.birthDate,
      registeredCounty: m.registeredCounty,
      sameHukou: Boolean(m.sameHukou),
      annualIncome: typeof m.annualIncome === 'number' ? m.annualIncome : undefined,
      assets: typeof m.assets === 'number' ? m.assets : undefined,
      disabilityCard: Boolean(m.disabilityCard),
      catastrophicIllnessCard: Boolean(m.catastrophicIllnessCard),
      rareDisease: Boolean(m.rareDisease),
      chronicDisability: Array.isArray(m.chronicDisability) ? m.chronicDisability : [],
    })),
    housingStatus: b.housingStatus as QuestionnaireAnswers['housingStatus'],
    selfAnnualIncome: typeof b.selfAnnualIncome === 'number' ? b.selfAnnualIncome : 0,
    selfAssets: typeof b.selfAssets === 'number' ? b.selfAssets : 0,
    employmentStatus: b.employmentStatus as QuestionnaireAnswers['employmentStatus'],
    workCounty: b.workCounty === '' ? undefined : (b.workCounty as string | undefined),
    selfDisabilityCard: Boolean(b.selfDisabilityCard),
    selfCatastrophicIllnessCard: Boolean(b.selfCatastrophicIllnessCard),
    selfRareDisease: Boolean(b.selfRareDisease),
    selfRecentMajorSurgery: Boolean(b.selfRecentMajorSurgery),
    hasForeignCaregiver: Boolean(b.hasForeignCaregiver),
    hadOccupationalInjury: Boolean(b.hadOccupationalInjury),
    nonCohabitingFamily: (b.nonCohabitingFamily as QuestionnaireAnswers['nonCohabitingFamily']).map((m) => ({
      relationship: m.relationship,
      birthDate: m.birthDate,
      county: m.county,
      annualIncome: typeof m.annualIncome === 'number' ? m.annualIncome : 0,
      assets: typeof m.assets === 'number' ? m.assets : 0,
      isSinglePersonHousehold: Boolean(m.isSinglePersonHousehold),
    })),
    specialIdentities: Array.isArray(b.specialIdentities) ? (b.specialIdentities as string[]) : [],
    involuntaryUnemployment6mo: Boolean(b.involuntaryUnemployment6mo),
    majorMedicalExpense: Boolean(b.majorMedicalExpense),
    naturalDisasterDamage: Boolean(b.naturalDisasterDamage),
    domesticViolenceOrTrafficking: Boolean(b.domesticViolenceOrTrafficking),
    otherAcuteHardship: Boolean(b.otherAcuteHardship),
    hasStartupIntent: Boolean(b.hasStartupIntent),
    infertilityTreatmentNeeded: Boolean(b.infertilityTreatmentNeeded),
    wantsToQuitSmoking: Boolean(b.wantsToQuitSmoking),
    legalDisputeNeedsConsultation: Boolean(b.legalDisputeNeedsConsultation),
    wantsAdultEducation: Boolean(b.wantsAdultEducation),
    isStudent: Boolean(b.isStudent),
    developmentalDelayChild: Boolean(b.developmentalDelayChild),
  }
}

export type Priority = 'urgent' | 'normal' | 'review'

export interface BenefitResult {
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
  sourceExcerpt: string
  lastVerifiedDate: string
  missingConditions: string[]
  documents: Array<{ name: string; obtainLocation: string | null }>
  locations: Array<{ name: string; address: string | null; phone: string | null; website: string | null }>
  priority: Priority
}

/** 依居住縣市查第 1 類「低收入戶/中低收入戶認定」的官方門檻數字（見 01-low-income-threshold.ts） */
async function getMinLivingExpense(county: string): Promise<number> {
  const [thresholdRow] = await db
    .select()
    .from(benefits)
    .where(and(eq(benefits.categoryNumber, 1), eq(benefits.county, county)))
    .limit(1)
  const referenceData = (thresholdRow?.eligibilityConditions as EligibilityConditions | null)?.referenceData
  const minLivingExpense = referenceData?.minLivingExpense
  if (minLivingExpense === undefined) throw new Error(`找不到 ${county} 的最低生活費資料，請確認資料庫已完成建檔`)
  return minLivingExpense
}

function computePriority(isTimeSensitive: boolean, verdict: 'confirmed' | 'possible'): Priority {
  if (isTimeSensitive) return 'urgent' // 🔴 有明確截止期限/候補制/名額有限，優先確認
  return verdict === 'confirmed' ? 'normal' : 'review' // 🟠 確定符合／🟡 需自行確認
}

const PRIORITY_ORDER: Record<Priority, number> = { urgent: 0, normal: 1, review: 2 }

/** 對單一 ApplicantProfile 跑完整資格比對，回傳 confirmed/possible 兩組（含所需文件與申請地點） */
async function evaluateAllBenefits(profile: ApplicantProfile, county: string, workCounty: string | undefined) {
  const allBenefits = await db
    .select()
    .from(benefits)
    .where(
      and(
        eq(benefits.isActive, true),
        or(isNull(benefits.county), eq(benefits.county, county), eq(benefits.county, workCounty ?? '')),
      ),
    )

  const results: Array<{ benefit: (typeof allBenefits)[number]; missingConditions: string[]; verdict: 'confirmed' | 'possible' }> = []
  const relevantIds: number[] = []

  for (const benefit of allBenefits) {
    const conditions = (benefit.eligibilityConditions as EligibilityConditions | null) ?? {}
    const result = evaluateEligibility(conditions, profile)
    if (result.verdict === 'not_eligible') continue
    relevantIds.push(benefit.id)
    results.push({ benefit, missingConditions: result.missingConditions, verdict: result.verdict as 'confirmed' | 'possible' })
  }

  const documentsByBenefit = new Map<number, Array<{ name: string; obtainLocation: string | null }>>()
  const locationsByBenefit = new Map<number, BenefitResult['locations']>()

  if (relevantIds.length > 0) {
    const [documents, locations] = await Promise.all([
      db.select().from(benefitDocuments),
      db.select().from(benefitLocations),
    ])
    for (const doc of documents) {
      if (!relevantIds.includes(doc.benefitId)) continue
      const list = documentsByBenefit.get(doc.benefitId) ?? []
      list.push({ name: doc.documentName, obtainLocation: doc.obtainLocation })
      documentsByBenefit.set(doc.benefitId, list)
    }
    for (const loc of locations) {
      if (!relevantIds.includes(loc.benefitId)) continue
      const list = locationsByBenefit.get(loc.benefitId) ?? []
      list.push({ name: loc.name, address: loc.address, phone: loc.phone, website: loc.website })
      locationsByBenefit.set(loc.benefitId, list)
    }
  }

  const confirmed: BenefitResult[] = []
  const possible: BenefitResult[] = []

  for (const { benefit, missingConditions, verdict } of results) {
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
      missingConditions,
      documents: documentsByBenefit.get(benefit.id) ?? [],
      locations: locationsByBenefit.get(benefit.id) ?? [],
      priority: computePriority(benefit.isTimeSensitive, verdict),
    }
    if (verdict === 'confirmed') confirmed.push(entry)
    else possible.push(entry)
  }

  const byPriority = (a: BenefitResult, b: BenefitResult) => PRIORITY_ORDER[a.priority] - PRIORITY_ORDER[b.priority]
  confirmed.sort(byPriority)
  possible.sort(byPriority)

  return { confirmed, possible }
}

export async function registerCheckRoute(app: FastifyInstance) {
  app.get('/api/form-options', async () => ({
    counties: ALL_22_COUNTIES,
    identities: IDENTITY_OPTIONS,
  }))

  app.post('/api/check', async (request, reply) => {
    let answers: QuestionnaireAnswers
    try {
      answers = validateAnswers(request.body)
    } catch (err) {
      reply.code(400)
      return { error: err instanceof Error ? err.message : '請求格式錯誤' }
    }

    const asOf = new Date()

    let minLivingExpense: number
    try {
      minLivingExpense = await getMinLivingExpense(answers.county)
    } catch (err) {
      reply.code(500)
      return { error: err instanceof Error ? err.message : '查詢失敗' }
    }

    const selfFinances = buildHouseholdFinances(answers)
    const perCapitaMonthlyIncome = calculatePerCapitaMonthlyIncome(selfFinances)
    const perCapitaAssets = calculatePerCapitaAssets(selfFinances)
    const incomeThresholdResult = evaluateIncomeThreshold(perCapitaMonthlyIncome, minLivingExpense)

    const selfProfile = buildApplicantProfile(answers, incomeThresholdResult, asOf)
    const self = await evaluateAllBenefits(selfProfile, answers.county, answers.workCounty)

    // 第 13 題：非同戶籍家人——依 SKILL.md 原始規格「依家人的戶籍縣市與年齡分別搜索」，
    // 只用戶籍縣市/年齡/（若為單人戶）所得動產做比對，其餘缺乏資料的條件一律列入⚠️可能符合，
    // 不虛構我們沒問過的資訊（身分別、自有住宅、特殊狀況旗標皆未收集，保持 undefined）。
    const familyMembers = []
    for (const member of answers.nonCohabitingFamily) {
      const age = calculateAge(new Date(member.birthDate), asOf)
      let memberIncomeThreshold: ApplicantProfile['incomeThresholdResult'] | undefined
      let memberPerCapitaAssets: number | undefined
      if (member.isSinglePersonHousehold) {
        try {
          const memberMinLivingExpense = await getMinLivingExpense(member.county)
          memberIncomeThreshold = evaluateIncomeThreshold(member.annualIncome / 12, memberMinLivingExpense)
          memberPerCapitaAssets = member.assets
        } catch {
          // 該縣市門檻查詢失敗時，略過所得比對，其餘條件仍照常評估
        }
      }
      const memberProfile: ApplicantProfile = {
        age,
        county: member.county,
        incomeThresholdResult: memberIncomeThreshold,
        perCapitaAssets: memberPerCapitaAssets,
      }
      const memberResult = await evaluateAllBenefits(memberProfile, member.county, undefined)
      familyMembers.push({
        relationship: member.relationship,
        county: member.county,
        age,
        ...memberResult,
      })
    }

    const allVerifiedDates = [...self.confirmed, ...self.possible].map((b) => b.lastVerifiedDate)
    const oldestVerifiedDate =
      allVerifiedDates.length > 0 ? allVerifiedDates.reduce((oldest, d) => (d < oldest ? d : oldest)) : null

    return {
      computed: {
        age: selfProfile.age,
        perCapitaMonthlyIncome: Math.round(perCapitaMonthlyIncome),
        perCapitaAssets: Math.round(perCapitaAssets),
        minLivingExpense,
        incomeThresholdResult,
      },
      generatedAt: asOf.toISOString().slice(0, 10),
      oldestVerifiedDate,
      self,
      familyMembers,
    }
  })
}
