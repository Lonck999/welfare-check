export interface IdentityOption {
  value: string
  label: string
}

export interface FormOptions {
  counties: string[]
  identities: IdentityOption[]
}

export interface HouseholdMember {
  relationship: string
  birthDate: string
  registeredCounty?: string
  sameHukou: boolean
  annualIncome?: number
  assets?: number
  disabilityCard?: boolean
  catastrophicIllnessCard?: boolean
  rareDisease?: boolean
  chronicDisability?: string[]
}

export type EmploymentStatus =
  | 'employed_insured'
  | 'employed_reduced_hours'
  | 'self_employed'
  | 'unemployed_seeking'
  | 'unemployed_not_seeking'
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

/**
 * 🔴 申請對象（P4 排序：self > household > spouse > family）
 *
 * ⚠️ 與 `benefit_applicants.role` 的值一一對應，**兩邊不可分岔**：
 *    問卷選了 'spouse'，比對時才找得到 role='spouse' 的補助。
 */
export type ApplyForRole = 'spouse' | 'household' | 'family'

export interface QuestionnaireAnswers {
  /**
   * 🔴 這次想幫誰找福利（P4：自身 > 配偶 > 家人）
   *
   * Lonck 2026-09-24 定的問法：
   *   先問「有沒有要幫家人申請」——
   *   · 答「沒有」→ 只找自身的，不再追問
   *   · 答「有」  → 才出現對象選擇（配偶／同住家人／未同住家人）
   *
   * ⚠️ 空陣列代表「只找自己」，不是「還沒回答」。
   */
  applyForRoles: ApplyForRole[]
  birthDate: string
  county: string
  district?: string
  gender?: 'male' | 'female' | 'other'
  maritalStatus: 'single' | 'married' | 'divorced' | 'widowed'
  pregnantOrPostpartumSelf: boolean
  pregnantOrPostpartumSpouse: boolean
  miscarriageRecently: boolean
  familySpecialCircumstances: string[]
  householdMembers: HouseholdMember[]
  housingStatus: 'own' | 'rent' | 'borrow' | 'other'
  selfAnnualIncome: number
  selfAssets: number
  employmentStatus: EmploymentStatus
  workCounty?: string
  selfDisabilityCard: boolean
  selfCatastrophicIllnessCard: boolean
  selfRareDisease: boolean
  selfRecentMajorSurgery: boolean
  hasForeignCaregiver: boolean
  hadOccupationalInjury: boolean
  nonCohabitingFamily: NonCohabitingFamilyMember[]
  specialIdentities: string[]
  involuntaryUnemployment6mo: boolean
  majorMedicalExpense: boolean
  naturalDisasterDamage: boolean
  domesticViolenceOrTrafficking: boolean
  otherAcuteHardship: boolean
  hasStartupIntent: boolean
  infertilityTreatmentNeeded: boolean
  wantsToQuitSmoking: boolean
  legalDisputeNeedsConsultation: boolean
  wantsAdultEducation: boolean
  isStudent: boolean
  developmentalDelayChild: boolean
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

export interface BenefitGroup {
  confirmed: BenefitResult[]
  possible: BenefitResult[]
}

export interface FamilyMemberResult extends BenefitGroup {
  relationship: string
  county: string
  age: number
}

export interface CheckResponse {
  computed: {
    age: number
    perCapitaMonthlyIncome: number
    perCapitaAssets: number
    minLivingExpense: number
    incomeThresholdResult: 'low_income' | 'mid_low_income' | 'above_threshold'
  }
  generatedAt: string
  oldestVerifiedDate: string | null
  self: BenefitGroup
  familyMembers: FamilyMemberResult[]
}

export interface ApiError {
  error: string
}
