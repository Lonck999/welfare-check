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

export interface QuestionnaireAnswers {
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
