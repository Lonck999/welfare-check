export interface FlagOption {
  value: string
  label: string
}

export interface IdentityOption {
  value: string
  label: string
}

export interface FormOptions {
  counties: string[]
  flags: FlagOption[]
  identities: IdentityOption[]
}

export interface HouseholdMemberInput {
  annualIncome: number
  assets: number
}

export interface CheckRequestBody {
  birthDate: string
  county: string
  workCounty?: string
  ownsHome: boolean
  householdMembers: HouseholdMemberInput[]
  youngestChildAge?: number
  oldestElderAge?: number
  identities: string[]
  flags: string[]
}

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
  missingConditions: string[]
  documents: string[]
  locations: Array<{ name: string; address: string | null; phone: string | null; website: string | null }>
  lastVerifiedDate: string
  sourceExcerpt: string
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
  confirmed: BenefitResult[]
  possible: BenefitResult[]
}

export interface ApiError {
  error: string
}
