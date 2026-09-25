import { describe, it, expect } from 'vitest'
import { evaluateEligibility } from '../eligibility.js'
import type { ApplicantProfile, EligibilityConditions } from '../eligibility.js'

/**
 * 🔴 這支測的是 2026-09-25 修的兩個「會靜默給錯答案」的 bug。
 *    ⚠️ 修完時 40 個既有測試全綠 —— 因為沒有一個測到這兩個行為。
 *       「全綠」在這裡完全不構成證據。
 */

const BASE: ApplicantProfile = {
  county: '新北市',
  age: 33,
}

describe('🔴 counties: ["全國"] 是萬用值，不是一個縣市', () => {
  it('全國層級的補助，任何縣市的人都符合', () => {
    const cond: EligibilityConditions = { counties: ['全國'] }
    for (const county of ['新北市', '臺北市', '澎湖縣', '連江縣']) {
      const r = evaluateEligibility(cond, { ...BASE, county })
      expect(r.verdict, `${county} 應該符合全國層級補助`).not.toBe('not_eligible')
    }
  })

  it('🔴 negative control：一般縣市條件仍然要擋', () => {
    const cond: EligibilityConditions = { counties: ['臺南市'] }
    const r = evaluateEligibility(cond, { ...BASE, county: '新北市' })
    expect(r.verdict).toBe('not_eligible')
  })

  it('「全國」和特定縣市並列時也要放行', () => {
    const cond: EligibilityConditions = { counties: ['全國', '臺南市'] }
    const r = evaluateEligibility(cond, { ...BASE, county: '花蓮縣' })
    expect(r.verdict).not.toBe('not_eligible')
  })

  it('沒填 counties 時不受影響（維持原行為）', () => {
    const r = evaluateEligibility({}, BASE)
    expect(r.verdict).not.toBe('not_eligible')
  })
})
