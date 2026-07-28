/**
 * 資格比對規則引擎。
 *
 * 對應 SKILL.md 第四步的三級比對：✅ 確定符合 / ⚠️ 可能符合 / ❌ 不符合。
 * 條件用 EligibilityConditions（存在 benefits.eligibilityConditions JSONB 欄位）描述，
 * 刻意只涵蓋 58 大類裡最常見的條件形狀（年齡、所得門檻、動產門檻、身分別、地區、是否有自有住宅、
 * 是否有未成年子女／65 歲以上成員、其他布林旗標），不追求一開始就窮舉所有政策細節。
 * 遇到目前形狀覆蓋不到的複雜資格（例如某些排富條款的特殊排除項），
 * 先用 customFlags 搭配問卷欄位擴充，真的無法用旗標表達時再回頭擴充這裡的型別。
 */

import type { IncomeThresholdResult } from './calculations.js'

export interface EligibilityConditions {
  ageMin?: number
  ageMax?: number
  /** 'low_income' 只允許低收入戶；'mid_low_income' 允許低收入戶或中低收入戶 */
  incomeThreshold?: 'low_income' | 'mid_low_income'
  maxPerCapitaAssets?: number
  /** 符合其中之一即可 */
  requiredIdentities?: string[]
  requiresChildUnder?: number
  requiresElderOver?: number
  /** 居住或工作縣市須為其中之一；不填代表不限地區 */
  counties?: string[]
  requiresNoOwnedHome?: boolean
  /** 其他布林旗標式條件，例如 'pregnant'、'disability_card'、'time_sensitive_deadline_confirmed' */
  requiredFlags?: string[]
  /**
   * 縣市層級的門檻參考數值（目前只有「低收入戶/中低收入戶認定」這類本身就是門檻定義的項目會填）。
   * evaluateEligibility() 不會讀取這裡的數字做比對——實際比對邏輯是用 calculations.ts 的
   * evaluateIncomeThreshold(perCapitaMonthlyIncome, minLivingExpense) 在收集完使用者資料後另外計算。
   * 這裡純粹是把官方公告數字存進資料庫供查詢/顯示/未來計算引用，避免寫死在程式碼裡。
   */
  referenceData?: {
    minLivingExpense?: number // 每人每月最低生活費
    realEstateLimit?: number // 家庭不動產限額
  }
}

export interface ApplicantProfile {
  age?: number
  county?: string
  workCounty?: string
  incomeThresholdResult?: IncomeThresholdResult
  perCapitaAssets?: number
  identities?: string[]
  hasChildUnder?: number // 家中最年幼子女的年齡，undefined 代表沒有子女資料
  hasElderOver?: number // 家中最年長成員的年齡
  ownsHome?: boolean
  flags?: string[]
}

export type EligibilityVerdict = 'confirmed' | 'possible' | 'not_eligible'

export interface EligibilityResult {
  verdict: EligibilityVerdict
  /** verdict === 'possible' 時，列出還缺哪些資料才能判定 */
  missingConditions: string[]
  /** verdict === 'not_eligible' 時，列出是哪個條件不符合 */
  failedConditions: string[]
}

type ConditionCheck = 'satisfied' | 'failed' | 'missing_data'

function checkAgeRange(conditions: EligibilityConditions, applicant: ApplicantProfile): ConditionCheck {
  if (conditions.ageMin === undefined && conditions.ageMax === undefined) return 'satisfied'
  if (applicant.age === undefined) return 'missing_data'
  if (conditions.ageMin !== undefined && applicant.age < conditions.ageMin) return 'failed'
  if (conditions.ageMax !== undefined && applicant.age > conditions.ageMax) return 'failed'
  return 'satisfied'
}

function checkIncomeThreshold(
  conditions: EligibilityConditions,
  applicant: ApplicantProfile,
): ConditionCheck {
  if (!conditions.incomeThreshold) return 'satisfied'
  if (!applicant.incomeThresholdResult) return 'missing_data'
  if (applicant.incomeThresholdResult === 'above_threshold') return 'failed'
  if (conditions.incomeThreshold === 'low_income' && applicant.incomeThresholdResult !== 'low_income') {
    return 'failed'
  }
  return 'satisfied'
}

function checkPerCapitaAssets(
  conditions: EligibilityConditions,
  applicant: ApplicantProfile,
): ConditionCheck {
  if (conditions.maxPerCapitaAssets === undefined) return 'satisfied'
  if (applicant.perCapitaAssets === undefined) return 'missing_data'
  return applicant.perCapitaAssets <= conditions.maxPerCapitaAssets ? 'satisfied' : 'failed'
}

function checkIdentities(conditions: EligibilityConditions, applicant: ApplicantProfile): ConditionCheck {
  if (!conditions.requiredIdentities || conditions.requiredIdentities.length === 0) return 'satisfied'
  if (!applicant.identities) return 'missing_data'
  const matched = conditions.requiredIdentities.some((id) => applicant.identities!.includes(id))
  return matched ? 'satisfied' : 'failed'
}

function checkChildUnder(conditions: EligibilityConditions, applicant: ApplicantProfile): ConditionCheck {
  if (conditions.requiresChildUnder === undefined) return 'satisfied'
  if (applicant.hasChildUnder === undefined) return 'missing_data'
  return applicant.hasChildUnder < conditions.requiresChildUnder ? 'satisfied' : 'failed'
}

function checkElderOver(conditions: EligibilityConditions, applicant: ApplicantProfile): ConditionCheck {
  if (conditions.requiresElderOver === undefined) return 'satisfied'
  if (applicant.hasElderOver === undefined) return 'missing_data'
  return applicant.hasElderOver >= conditions.requiresElderOver ? 'satisfied' : 'failed'
}

function checkCounties(conditions: EligibilityConditions, applicant: ApplicantProfile): ConditionCheck {
  if (!conditions.counties || conditions.counties.length === 0) return 'satisfied'
  if (!applicant.county && !applicant.workCounty) return 'missing_data'
  const matched = conditions.counties.some(
    (c) => c === applicant.county || c === applicant.workCounty,
  )
  return matched ? 'satisfied' : 'failed'
}

function checkNoOwnedHome(conditions: EligibilityConditions, applicant: ApplicantProfile): ConditionCheck {
  if (!conditions.requiresNoOwnedHome) return 'satisfied'
  if (applicant.ownsHome === undefined) return 'missing_data'
  return applicant.ownsHome === false ? 'satisfied' : 'failed'
}

function checkRequiredFlags(conditions: EligibilityConditions, applicant: ApplicantProfile): ConditionCheck {
  if (!conditions.requiredFlags || conditions.requiredFlags.length === 0) return 'satisfied'
  if (!applicant.flags) return 'missing_data'
  const allPresent = conditions.requiredFlags.every((flag) => applicant.flags!.includes(flag))
  return allPresent ? 'satisfied' : 'failed'
}

const CHECKS: Array<{
  label: string
  check: (conditions: EligibilityConditions, applicant: ApplicantProfile) => ConditionCheck
}> = [
  { label: '年齡範圍', check: checkAgeRange },
  { label: '所得門檻', check: checkIncomeThreshold },
  { label: '人均動產門檻', check: checkPerCapitaAssets },
  { label: '身分別', check: checkIdentities },
  { label: '未成年子女年齡', check: checkChildUnder },
  { label: '長者年齡', check: checkElderOver },
  { label: '居住/工作縣市', check: checkCounties },
  { label: '無自有住宅', check: checkNoOwnedHome },
  { label: '其他條件旗標', check: checkRequiredFlags },
]

/** 依 SKILL.md 第四步的三級邏輯評估單一福利項目 */
export function evaluateEligibility(
  conditions: EligibilityConditions,
  applicant: ApplicantProfile,
): EligibilityResult {
  const missingConditions: string[] = []
  const failedConditions: string[] = []

  for (const { label, check } of CHECKS) {
    const result = check(conditions, applicant)
    if (result === 'failed') failedConditions.push(label)
    if (result === 'missing_data') missingConditions.push(label)
  }

  if (failedConditions.length > 0) {
    return { verdict: 'not_eligible', missingConditions: [], failedConditions }
  }
  if (missingConditions.length > 0) {
    return { verdict: 'possible', missingConditions, failedConditions: [] }
  }
  return { verdict: 'confirmed', missingConditions: [], failedConditions: [] }
}
