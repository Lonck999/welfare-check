import { describe, expect, it } from 'vitest'
import { evaluateEligibility, type ApplicantProfile, type EligibilityConditions } from '../eligibility.js'

describe('evaluateEligibility', () => {
  it('✅ 所有條件都滿足 → confirmed', () => {
    const conditions: EligibilityConditions = {
      ageMax: 40,
      requiresNoOwnedHome: true,
      counties: ['新北市'],
    }
    const applicant: ApplicantProfile = {
      age: 32,
      ownsHome: false,
      county: '新北市',
    }
    const result = evaluateEligibility(conditions, applicant)
    expect(result.verdict).toBe('confirmed')
    expect(result.missingConditions).toEqual([])
    expect(result.failedConditions).toEqual([])
  })

  it('❌ 年齡超過上限 → not_eligible，並列出是哪個條件不符合', () => {
    const conditions: EligibilityConditions = { ageMax: 40 }
    const applicant: ApplicantProfile = { age: 41 }
    const result = evaluateEligibility(conditions, applicant)
    expect(result.verdict).toBe('not_eligible')
    expect(result.failedConditions).toContain('年齡範圍')
  })

  it('⚠️ 缺少資料（未填年齡）→ possible，並列出缺少哪個條件', () => {
    const conditions: EligibilityConditions = { ageMax: 40 }
    const applicant: ApplicantProfile = {}
    const result = evaluateEligibility(conditions, applicant)
    expect(result.verdict).toBe('possible')
    expect(result.missingConditions).toContain('年齡範圍')
  })

  it('身分別條件：符合其中一項即可', () => {
    const conditions: EligibilityConditions = { requiredIdentities: ['原住民', '新住民'] }
    const applicant: ApplicantProfile = { identities: ['新住民'] }
    expect(evaluateEligibility(conditions, applicant).verdict).toBe('confirmed')
  })

  it('身分別條件：都不符合 → not_eligible', () => {
    const conditions: EligibilityConditions = { requiredIdentities: ['原住民', '新住民'] }
    const applicant: ApplicantProfile = { identities: ['客家人'] }
    expect(evaluateEligibility(conditions, applicant).verdict).toBe('not_eligible')
  })

  it('所得門檻：中低收入戶條件下，低收入戶身分也算符合', () => {
    const conditions: EligibilityConditions = { incomeThreshold: 'mid_low_income' }
    const applicant: ApplicantProfile = { incomeThresholdResult: 'low_income' }
    expect(evaluateEligibility(conditions, applicant).verdict).toBe('confirmed')
  })

  it('所得門檻：超過門檻者一律不符合', () => {
    const conditions: EligibilityConditions = { incomeThreshold: 'mid_low_income' }
    const applicant: ApplicantProfile = { incomeThresholdResult: 'above_threshold' }
    expect(evaluateEligibility(conditions, applicant).verdict).toBe('not_eligible')
  })

  it('同時有缺資料與不符合條件時，優先判定為 not_eligible（❌ 優先於 ⚠️）', () => {
    const conditions: EligibilityConditions = { ageMax: 40, requiresNoOwnedHome: true }
    const applicant: ApplicantProfile = { age: 45 } // ownsHome 未填，但年齡已經確定不符合
    const result = evaluateEligibility(conditions, applicant)
    expect(result.verdict).toBe('not_eligible')
  })

  it('沒有任何條件限制 → 一定 confirmed（例如人人可申請的優惠）', () => {
    const result = evaluateEligibility({}, {})
    expect(result.verdict).toBe('confirmed')
  })

  it('⚠️ 旗標條件沒勾 → possible（不確定，讓使用者自己確認），而非直接濾掉', () => {
    const conditions: EligibilityConditions = { requiredFlags: ['wants_to_quit_smoking'] }
    const applicant: ApplicantProfile = { flags: [] }
    const result = evaluateEligibility(conditions, applicant)
    expect(result.verdict).toBe('possible')
    expect(result.missingConditions).toContain('有戒菸意願')
  })

  it('✅ 旗標條件有勾 → confirmed', () => {
    const conditions: EligibilityConditions = { requiredFlags: ['wants_to_quit_smoking'] }
    const applicant: ApplicantProfile = { flags: ['wants_to_quit_smoking'] }
    expect(evaluateEligibility(conditions, applicant).verdict).toBe('confirmed')
  })

  it('旗標沒勾但其他條件確定不符合 → 仍是 not_eligible（❌ 優先於 ⚠️）', () => {
    const conditions: EligibilityConditions = { ageMax: 40, requiredFlags: ['wants_to_quit_smoking'] }
    const applicant: ApplicantProfile = { age: 45, flags: [] }
    expect(evaluateEligibility(conditions, applicant).verdict).toBe('not_eligible')
  })
})
