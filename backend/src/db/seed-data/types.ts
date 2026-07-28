import type { EligibilityConditions } from '../../logic/eligibility.js'

/** 一筆 seed 資料對應 benefits 表一列，可選擇附帶所需文件與申請地點 */
export interface SeedBenefit {
  categoryNumber: number
  name: string
  agency: string
  county: string | null // null = 全國統一，不分縣市
  description: string
  searchGroup: string
  isTimeSensitive: boolean
  applicationPeriod: string
  notes?: string
  eligibilityConditions?: EligibilityConditions
  sourceUrl: string
  sourceExcerpt: string
  lastVerifiedDate: string // YYYY-MM-DD
  documents?: string[]
  locations?: Array<{ name: string; address?: string; phone?: string; website?: string }>
}
