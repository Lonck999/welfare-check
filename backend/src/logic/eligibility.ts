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
import { FLAG_OPTIONS } from './profile-mapping.js'

const FLAG_LABELS = new Map(FLAG_OPTIONS.map((f) => [f.value, f.label]))

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
  /** 需要本人（或申請人）名下有自有住宅，例如老屋修繕/太陽能屋頂型補助——申請人須為房屋所有權人 */
  requiresOwnedHome?: boolean
  /** 其他布林旗標式條件，例如 'pregnant'、'disability_card'、'time_sensitive_deadline_confirmed' */
  requiredFlags?: string[]
  /**
   * 明確標記「真的人人可申請」（逐筆從官方原文確認過才可設）。
   * 🔴 沒設這個、又沒有任何實質條件的項目 → 一律 possible（W-020）：
   *    那代表「條件還沒整理」，不是「沒有條件」。
   */
  openToAll?: boolean
  /**
   * 特定身分的年齡下限另計（W-020 補條件時加）：例如老人福利「65 歲以上，原住民 55 歲以上」
   * ⇒ { ageMin: 65, ageMinByIdentity: { 原住民: 55 } }。申請人有該身分時取較低者。
   */
  ageMinByIdentity?: Record<string, number>
  /**
   * 官方原文寫了、但問卷問不到的條件（設籍滿 N 年、個人所得未達 X、醫療自付達 Y…）。
   * 🔴 每一條都會原文照列進 missingConditions ⇒ 這筆最高只能是 possible，不可能 confirmed。
   *    寫在這裡＝「我們知道有這條、但無法替使用者判斷」，不是「沒有這條」。
   */
  uncheckedConditions?: string[]
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
  /**
   * 問卷「有明確問過」的旗標（2026-10-20 Lonck 定 A）。
   * 這些旗標沒出現在 flags ＝ 使用者答了「沒有」，requiredFlags 要它 ⇒ failed（不是 missing）。
   * 🔴 只放問卷有直接題目的（身障證明）。其他旗標仍維持「沒勾＝不確定」，
   *    理由見 missingRequiredFlagLabels 的註解。非同戶家人的 profile 不設（沒問過他們）。
   */
  answeredFlags?: string[]
  /**
   * 家庭成員名單已作答、且非同戶家人裡沒有未滿 18 歲者 ⇒ hasChildUnder 為 undefined 代表「沒有小孩」，
   * requiresChildUnder ⇒ failed（不是 missing_data）。未設＝不知道。
   */
  householdAnswered?: boolean
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

/** 申請人適用的年齡下限：有 ageMinByIdentity 對應身分時取較低者 */
export function effectiveAgeMin(conditions: EligibilityConditions, applicant: ApplicantProfile): number | undefined {
  let min = conditions.ageMin
  for (const [identity, age] of Object.entries(conditions.ageMinByIdentity ?? {})) {
    if ((applicant.identities ?? []).includes(identity)) min = min === undefined ? age : Math.min(min, age)
  }
  return min
}

function checkAgeRange(conditions: EligibilityConditions, applicant: ApplicantProfile): ConditionCheck {
  if (conditions.ageMin === undefined && conditions.ageMax === undefined) return 'satisfied'
  if (applicant.age === undefined) return 'missing_data'
  const ageMin = effectiveAgeMin(conditions, applicant)
  if (ageMin !== undefined && applicant.age < ageMin) return 'failed'
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
  if (applicant.hasChildUnder === undefined) return applicant.householdAnswered ? 'failed' : 'missing_data'
  return applicant.hasChildUnder < conditions.requiresChildUnder ? 'satisfied' : 'failed'
}

function checkElderOver(conditions: EligibilityConditions, applicant: ApplicantProfile): ConditionCheck {
  if (conditions.requiresElderOver === undefined) return 'satisfied'
  if (applicant.hasElderOver === undefined) return 'missing_data'
  return applicant.hasElderOver >= conditions.requiresElderOver ? 'satisfied' : 'failed'
}

function checkCounties(conditions: EligibilityConditions, applicant: ApplicantProfile): ConditionCheck {
  if (!conditions.counties || conditions.counties.length === 0) return 'satisfied'
  // 🔴 「全國」是萬用值，不是一個縣市（2026-09-25 加）：
  //    全國統一制度（勞保老年年金、育兒津貼、國民年金保費補助…）
  //    存成 counties: ['全國']，任何縣市的居民都適用。
  //    ⚠️ 不加這條的話，那 21 筆會**永遠 failed** ——
  //    使用者少領到最多人能領的那幾項，而且完全沒有錯誤訊息。
  if (conditions.counties.includes('全國')) return 'satisfied'
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

function checkOwnedHome(conditions: EligibilityConditions, applicant: ApplicantProfile): ConditionCheck {
  if (!conditions.requiresOwnedHome) return 'satisfied'
  if (applicant.ownsHome === undefined) return 'missing_data'
  return applicant.ownsHome === true ? 'satisfied' : 'failed'
}

/**
 * 旗標條件刻意不會回傳 'failed'，只會是 'satisfied' 或 missing（缺哪幾個旗標）。
 *
 * 跟身分別（checkIdentities，使用者通常很清楚自己是不是原住民/退伍軍人）不同，
 * 這裡的旗標大多是使用者不見得會主動想到要勾的細節狀況（例如「有戒菸意願」
 * 「有不孕症/人工生殖需求」）。如果沒勾就直接判定不符合、從結果消失，
 * 使用者永遠不會知道有這個補助存在——這樣就違背了「幫使用者發現他不知道
 * 自己能申請的補助」這個核心價值。所以沒勾一律視為「不確定」，讓這類項目
 * 進「⚠️ 可能符合」列出還缺哪個旗標，由使用者自己判斷是否符合，而不是被系統
 * 直接篩掉。
 */
function missingRequiredFlagLabels(conditions: EligibilityConditions, applicant: ApplicantProfile): string[] {
  if (!conditions.requiredFlags || conditions.requiredFlags.length === 0) return []
  const presentFlags = applicant.flags ?? []
  const answered = applicant.answeredFlags ?? []
  return conditions.requiredFlags
    .filter((flag) => !presentFlags.includes(flag) && !answered.includes(flag))
    .map((flag) => FLAG_LABELS.get(flag) ?? flag)
}

/** 問卷明確問過、答案是「沒有」的必要旗標 ⇒ 不符合（W-020 第 2 批後 Lonck 定 A） */
function checkAnsweredFlags(conditions: EligibilityConditions, applicant: ApplicantProfile): ConditionCheck {
  if (!conditions.requiredFlags || conditions.requiredFlags.length === 0) return 'satisfied'
  const presentFlags = applicant.flags ?? []
  const answered = applicant.answeredFlags ?? []
  const deniedExplicitly = conditions.requiredFlags.some((f) => answered.includes(f) && !presentFlags.includes(f))
  return deniedExplicitly ? 'failed' : 'satisfied'
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
  { label: '需自有住宅', check: checkOwnedHome },
  { label: '身心障礙證明', check: checkAnsweredFlags },
]

/** 不算「資格條件」的鍵：地區只是篩選範圍、referenceData 不參與比對、_ 開頭是註記 */
const NON_SUBSTANTIVE_KEYS = new Set(['counties', 'referenceData', 'openToAll', 'ageMinByIdentity'])
export const UNSORTED_CONDITIONS_LABEL = '資格條件尚未整理（請見官方頁）'

/**
 * W-020：條件只有 counties（或全空）且沒標 openToAll ⇒ 條件尚未整理。
 * 以前這種項目沒有任何條件可以不符 ⇒ 對任何人都判 confirmed（30 歲上班族會看到「65 歲以上健保補助」）。
 */
export function hasUnsortedConditions(conditions: EligibilityConditions): boolean {
  if (conditions.openToAll === true) return false
  return !Object.keys(conditions).some(
    (k) => !k.startsWith('_') && !NON_SUBSTANTIVE_KEYS.has(k),
  )
}

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
  missingConditions.push(...missingRequiredFlagLabels(conditions, applicant))
  if (hasUnsortedConditions(conditions)) missingConditions.push(UNSORTED_CONDITIONS_LABEL)
  for (const u of conditions.uncheckedConditions ?? []) missingConditions.push(u)

  if (failedConditions.length > 0) {
    return { verdict: 'not_eligible', missingConditions: [], failedConditions }
  }
  if (missingConditions.length > 0) {
    return { verdict: 'possible', missingConditions, failedConditions: [] }
  }
  return { verdict: 'confirmed', missingConditions: [], failedConditions: [] }
}
