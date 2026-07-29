/**
 * 對應 SKILL.md 第一步「收集使用者資料」的完整 18 題（含子題）問卷資料形狀，
 * 以及把逐題結構化答案自動轉換成 ApplicantProfile／requiredFlags 的推導邏輯。
 *
 * 目的：取代原本 MVP 版本「使用者自己從一堆勾選項裡認出要勾什麼」的設計——
 * 逐題引導式問法本身就能推導出大部分 requiredFlags，不需要使用者自己知道
 * 「有戒菸意願」背後對應到哪個補助分類。只有極少數原本 18 題沒有直接對應的
 * 細節狀況（例如已聘僱外籍看護工、曾遭遇職業災害）才需要額外詢問。
 */

import { calculateAge, calculatePerCapitaAssets } from './calculations.js'
import type { ApplicantProfile } from './eligibility.js'

export interface HouseholdMember {
  relationship: string
  birthDate: string // YYYY-MM-DD
  registeredCounty?: string // Q6：設籍縣市
  sameHukou: boolean // Q6：是否同戶號（應計算人口）
  annualIncome?: number // Q8/Q9：僅同戶號成員需填
  assets?: number
  disabilityCard?: boolean // Q12
  catastrophicIllnessCard?: boolean // Q12
  rareDisease?: boolean // Q12
  chronicDisability?: string[] // Q12：'mobility' | 'cognitive' | 'self_care' | 'chronic_disease'
}

export type EmploymentStatus =
  | 'employed_insured' // 受僱員工（有公司加勞保）
  | 'employed_reduced_hours' // 受僱員工，因公司減班休息中
  | 'self_employed' // 自營作業者/接案/SOHO
  | 'unemployed_seeking' // 失業中（求職中）
  | 'unemployed_not_seeking' // 待業中（暫未求職）
  | 'retired'
  | 'homemaker'

export interface NonCohabitingFamilyMember {
  relationship: string
  birthDate: string
  county: string
  annualIncome: number
  assets: number
  isSinglePersonHousehold: boolean
}

/** 完整問卷答案，對應 SKILL.md 第 1～14b 題 */
export interface QuestionnaireAnswers {
  // Q1
  birthDate: string
  // Q2
  county: string
  district?: string
  // Q3（目前資格引擎不使用，僅為問卷完整性保留）
  gender?: 'male' | 'female' | 'other'
  // Q4
  maritalStatus: 'single' | 'married' | 'divorced' | 'widowed'
  // Q4a
  pregnantOrPostpartumSelf: boolean
  pregnantOrPostpartumSpouse: boolean
  miscarriageRecently: boolean
  familySpecialCircumstances: string[] // 'single_parent_custody' | 'domestic_violence' | 'unmarried_birth'
  // Q5/Q6
  householdMembers: HouseholdMember[]
  // Q7
  housingStatus: 'own' | 'rent' | 'borrow' | 'other'
  // Q8/Q9（本人）
  selfAnnualIncome: number
  selfAssets: number
  // Q10
  employmentStatus: EmploymentStatus
  // Q10a
  workCounty?: string
  // Q11（本人）
  selfDisabilityCard: boolean
  selfCatastrophicIllnessCard: boolean
  selfRareDisease: boolean
  selfRecentMajorSurgery: boolean
  // Q10 附加（原始 18 題沒有專門子題，併入就業狀況區塊）
  hasForeignCaregiver: boolean
  hadOccupationalInjury: boolean
  // Q13
  nonCohabitingFamily: NonCohabitingFamilyMember[]
  // Q14
  specialIdentities: string[] // IDENTITY_OPTIONS 的 value
  involuntaryUnemployment6mo: boolean
  majorMedicalExpense: boolean
  naturalDisasterDamage: boolean
  domesticViolenceOrTrafficking: boolean
  otherAcuteHardship: boolean
  // Q14a
  hasStartupIntent: boolean
  infertilityTreatmentNeeded: boolean
  wantsToQuitSmoking: boolean
  legalDisputeNeedsConsultation: boolean
  wantsAdultEducation: boolean // 原始 18 題無此子題，併入第 14a 題區塊詢問
  // Q14b
  isStudent: boolean
  developmentalDelayChild: boolean
}

function ageOf(birthDate: string, asOf: Date): number {
  return calculateAge(new Date(birthDate), asOf)
}

/** 應計算人口（本人＋同戶號家人）的收入/動產陣列，供 calculations.ts 既有函式使用 */
export function buildHouseholdFinances(answers: QuestionnaireAnswers) {
  const members = [
    { annualIncome: answers.selfAnnualIncome, assets: answers.selfAssets },
    ...answers.householdMembers
      .filter((m) => m.sameHukou)
      .map((m) => ({ annualIncome: m.annualIncome ?? 0, assets: m.assets ?? 0 })),
  ]
  return members
}

/** 從第 5/6 題的家庭成員名單（含本人）自動推算最年幼子女／最年長成員年齡，不需要另外問 */
function computeChildAndElderAges(answers: QuestionnaireAnswers, asOf: Date) {
  const allAges = [
    ageOf(answers.birthDate, asOf),
    ...answers.householdMembers.map((m) => ageOf(m.birthDate, asOf)),
  ]
  const childAges = allAges.filter((a) => a < 18)
  const elderAges = allAges.filter((a) => a >= 65)
  return {
    hasChildUnder: childAges.length > 0 ? Math.min(...childAges) : undefined,
    hasElderOver: elderAges.length > 0 ? Math.max(...elderAges) : undefined,
  }
}

/** 依 Q10 就業身分推導對應旗標 */
function employmentFlags(status: EmploymentStatus): string[] {
  switch (status) {
    case 'employed_insured':
      return ['is_employed_or_insured', 'is_employed', 'has_labor_insurance']
    case 'employed_reduced_hours':
      return ['is_employed_or_insured', 'is_employed', 'has_labor_insurance']
    case 'self_employed':
      return ['is_employed_or_insured', 'is_employed', 'has_labor_insurance']
    case 'unemployed_seeking':
      return ['unemployed']
    case 'unemployed_not_seeking':
      return []
    case 'retired':
      return []
    case 'homemaker':
      return []
  }
}

/**
 * 把逐題答案自動轉換成 requiredFlags 用的旗標清單。
 * 對照 backend/src/logic/profile-mapping.ts 的 FLAG_OPTIONS：
 * 這裡涵蓋所有能從結構化答案直接推導的旗標；有些旗標（如 has_care_recipient）
 * 跟 has_disability_or_dementia_member 語意重疊，只要有一方成立就一起帶上，
 * 避免使用者因為「兩個旗標名稱看起來很像」而漏掉其中一個。
 */
export function deriveFlags(answers: QuestionnaireAnswers): string[] {
  const flags = new Set<string>(['general_public'])

  if (answers.pregnantOrPostpartumSelf || answers.pregnantOrPostpartumSpouse) flags.add('pregnant_or_recent_birth')
  if (answers.miscarriageRecently) flags.add('miscarriage')
  if (answers.familySpecialCircumstances.length > 0) flags.add('special_circumstance_family')

  const anyMemberDisabled = answers.householdMembers.some(
    (m) => m.disabilityCard || (m.chronicDisability && m.chronicDisability.length > 0),
  )
  if (answers.selfDisabilityCard || anyMemberDisabled) {
    flags.add('disability_certificate')
    flags.add('has_disability_or_dementia_member')
    flags.add('has_care_recipient')
    flags.add('has_dependents_or_ltc_needs')
  }
  const anySelfCareDifficulty = answers.householdMembers.some((m) => m.chronicDisability?.includes('self_care'))
  if (anySelfCareDifficulty) flags.add('severe_disability_or_dementia')

  if (answers.selfCatastrophicIllnessCard || answers.householdMembers.some((m) => m.catastrophicIllnessCard)) {
    flags.add('catastrophic_illness')
  }
  if (answers.selfRareDisease || answers.householdMembers.some((m) => m.rareDisease)) {
    flags.add('rare_disease_certificate')
  }
  if (answers.hasForeignCaregiver) flags.add('has_foreign_caregiver')
  if (answers.hadOccupationalInjury) flags.add('occupational_injury')

  for (const f of employmentFlags(answers.employmentStatus)) flags.add(f)
  const workingAgeNotCovered =
    answers.employmentStatus === 'unemployed_seeking' ||
    answers.employmentStatus === 'unemployed_not_seeking' ||
    answers.employmentStatus === 'retired' ||
    answers.employmentStatus === 'homemaker'
  if (workingAgeNotCovered) {
    // 原始 18 題沒有專門詢問國民年金加保狀況，用就業狀況做近似推斷（未被勞保覆蓋者多半應加保國民年金）
    flags.add('has_labor_insurance_or_national_pension')
    flags.add('enrolled_national_pension')
  }

  const spouse = answers.householdMembers.find((m) => m.relationship === '配偶' && m.sameHukou)
  if (spouse && (spouse.annualIncome ?? 0) === 0) flags.add('spouse_no_income')

  if (answers.hasStartupIntent) flags.add('has_startup_intent')
  if (answers.infertilityTreatmentNeeded) flags.add('infertility_treatment_needed')
  if (answers.wantsToQuitSmoking) flags.add('wants_to_quit_smoking')
  if (answers.legalDisputeNeedsConsultation) flags.add('legal_dispute_or_consultation_needed')
  if (answers.wantsAdultEducation) flags.add('returning_to_education')
  if (answers.isStudent) flags.add('is_student')
  if (answers.developmentalDelayChild) flags.add('developmental_delay_suspected_or_diagnosed')

  if (
    answers.involuntaryUnemployment6mo ||
    answers.majorMedicalExpense ||
    answers.domesticViolenceOrTrafficking ||
    answers.otherAcuteHardship
  ) {
    flags.add('acute_hardship')
  }
  if (answers.involuntaryUnemployment6mo) flags.add('unemployed')
  if (answers.naturalDisasterDamage) flags.add('recent_natural_disaster_damage')

  return [...flags]
}

/** 把逐題答案組成主要申請人（本人）的 ApplicantProfile，交給 evaluateEligibility 使用 */
export function buildApplicantProfile(
  answers: QuestionnaireAnswers,
  incomeThresholdResult: ApplicantProfile['incomeThresholdResult'],
  asOf: Date,
): ApplicantProfile {
  const finances = buildHouseholdFinances(answers)
  const { hasChildUnder, hasElderOver } = computeChildAndElderAges(answers, asOf)

  return {
    age: ageOf(answers.birthDate, asOf),
    county: answers.county,
    workCounty: answers.workCounty,
    incomeThresholdResult,
    perCapitaAssets: calculatePerCapitaAssets(finances),
    identities: answers.specialIdentities,
    hasChildUnder,
    hasElderOver,
    ownsHome: answers.housingStatus === 'own',
    flags: deriveFlags(answers),
  }
}
