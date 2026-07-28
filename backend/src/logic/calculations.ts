/**
 * 對應 SKILL.md 第二步「預審計算」的公式，純函式、不依賴資料庫或外部服務，
 * 方便單元測試與之後在階段 3 資格比對邏輯裡重複使用。
 */

const MS_PER_DAY = 1000 * 60 * 60 * 24

/** 依出生年月日計算實際年齡（實歲，以 asOf 為基準日） */
export function calculateAge(birthDate: Date, asOf: Date): number {
  let age = asOf.getFullYear() - birthDate.getFullYear()
  const monthDiff = asOf.getMonth() - birthDate.getMonth()
  const beforeBirthdayThisYear =
    monthDiff < 0 || (monthDiff === 0 && asOf.getDate() < birthDate.getDate())
  if (beforeBirthdayThisYear) age -= 1
  return age
}

/** 距離滿 targetAge 歲的天數；已超過門檻回傳負數 */
export function daysUntilAge(birthDate: Date, targetAge: number, asOf: Date): number {
  const targetBirthday = new Date(birthDate)
  targetBirthday.setFullYear(birthDate.getFullYear() + targetAge)
  return Math.round((targetBirthday.getTime() - asOf.getTime()) / MS_PER_DAY)
}

/** 距離滿 targetAge 歲的年數（無條件捨去，已超過回傳負數） */
export function yearsUntilAge(birthDate: Date, targetAge: number, asOf: Date): number {
  return targetAge - calculateAge(birthDate, asOf)
}

export interface HouseholdMemberFinance {
  /** 該成員去年綜合所得稅核定所得 */
  annualIncome: number
  /** 該成員動產（存款＋有價證券＋自用車輛以外之車輛市值等） */
  assets: number
}

/**
 * C. 家庭總收入／人均月所得
 * 公式：（應計算人口年收入合計）÷ 人數 ÷ 12
 * members 必須只包含「應計算人口」（同戶號成員），排除判斷交由呼叫端在組成 members 前完成。
 */
export function calculatePerCapitaMonthlyIncome(members: HouseholdMemberFinance[]): number {
  if (members.length === 0) throw new Error('members must not be empty')
  const totalAnnualIncome = members.reduce((sum, m) => sum + m.annualIncome, 0)
  return totalAnnualIncome / members.length / 12
}

/**
 * D. 人均動產
 * 公式：（應計算人口動產合計）÷ 人數
 */
export function calculatePerCapitaAssets(members: HouseholdMemberFinance[]): number {
  if (members.length === 0) throw new Error('members must not be empty')
  const totalAssets = members.reduce((sum, m) => sum + m.assets, 0)
  return totalAssets / members.length
}

export type IncomeThresholdResult = 'low_income' | 'mid_low_income' | 'above_threshold'

/**
 * E. 比對當地當年度門檻（所得部分）
 * 低收入戶：人均月所得 ≦ 最低生活費
 * 中低收入戶：人均月所得 ≦ 最低生活費 × 1.5
 */
export function evaluateIncomeThreshold(
  perCapitaMonthlyIncome: number,
  minLivingExpense: number,
): IncomeThresholdResult {
  if (perCapitaMonthlyIncome <= minLivingExpense) return 'low_income'
  if (perCapitaMonthlyIncome <= minLivingExpense * 1.5) return 'mid_low_income'
  return 'above_threshold'
}

/**
 * E. 比對當地當年度門檻（動產部分）
 * 預設每人 15 萬元，各縣市可能略有差異，故開放帶入 assetLimit 覆寫。
 */
export function meetsAssetThreshold(perCapitaAssets: number, assetLimit = 150_000): boolean {
  return perCapitaAssets <= assetLimit
}
