import { describe, expect, it } from 'vitest'
import { evaluateEligibility, UNSORTED_CONDITIONS_LABEL, type ApplicantProfile, type EligibilityConditions } from '../eligibility.js'

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

  // 🔴 2026-10-20 改規格（Lonck：「用推算的只能證明他今年的收入明年可以去申請」）：
  //    舊測試「推算是低收 ⇒ confirmed」就是 bug 本身 —— 推算只代表可以去申請列冊。
  it('所得門檻：中低收入戶條件下，已列冊低收入戶也算符合', () => {
    const conditions: EligibilityConditions = { incomeThreshold: 'mid_low_income' }
    const applicant: ApplicantProfile = { incomeThresholdResult: 'low_income', registeredLowIncome: 'low_income' }
    expect(evaluateEligibility(conditions, applicant).verdict).toBe('confirmed')
  })

  it('所得門檻：只有推算（沒答已列冊）⇒ 最高 possible，且說明要先列冊', () => {
    const conditions: EligibilityConditions = { incomeThreshold: 'mid_low_income' }
    const r = evaluateEligibility(conditions, { incomeThresholdResult: 'low_income', registeredLowIncome: 'unknown' })
    expect(r.verdict).toBe('possible')
    expect(r.missingConditions.join()).toContain('列冊')
  })

  it('所得門檻：答「都不是」但推算符合 ⇒ possible，提示可去申請列冊', () => {
    const r = evaluateEligibility({ incomeThreshold: 'low_income' }, { incomeThresholdResult: 'low_income', registeredLowIncome: 'none' })
    expect(r.verdict).toBe('possible')
    expect(r.missingConditions.join()).toContain('未列冊')
  })

  it('所得門檻：答「都不是」且推算也不符 ⇒ not_eligible', () => {
    const r = evaluateEligibility({ incomeThreshold: 'mid_low_income' }, { incomeThresholdResult: 'above_threshold', registeredLowIncome: 'none' })
    expect(r.verdict).toBe('not_eligible')
  })

  it('所得門檻：已列冊以答案為準 —— 推算超標也 confirmed（推算用的是去年所得）', () => {
    const r = evaluateEligibility({ incomeThreshold: 'mid_low_income' }, { incomeThresholdResult: 'above_threshold', registeredLowIncome: 'mid_low_income' })
    expect(r.verdict).toBe('confirmed')
  })

  it('所得門檻：已列冊中低收 不符合「限低收入戶」', () => {
    const r = evaluateEligibility({ incomeThreshold: 'low_income' }, { incomeThresholdResult: 'low_income', registeredLowIncome: 'mid_low_income' })
    expect(r.verdict).toBe('not_eligible')
  })

  it('認定類（incomeEstimateSufficient）：推算符合就 confirmed —— 申請列冊本身不需要已列冊', () => {
    const r = evaluateEligibility({ incomeThreshold: 'mid_low_income', incomeEstimateSufficient: true }, { incomeThresholdResult: 'mid_low_income', registeredLowIncome: 'none' })
    expect(r.verdict).toBe('confirmed')
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

  it('W-020：條件全空 → possible（條件尚未整理，不是人人可申請）', () => {
    const result = evaluateEligibility({}, {})
    expect(result.verdict).toBe('possible')
    expect(result.missingConditions).toContain(UNSORTED_CONDITIONS_LABEL)
  })

  it('W-020：只有縣市、居住縣市相符 → possible，不可 confirmed', () => {
    const result = evaluateEligibility({ counties: ['新竹市'] }, { age: 30, county: '新竹市' })
    expect(result.verdict).toBe('possible')
    expect(result.missingConditions).toEqual([UNSORTED_CONDITIONS_LABEL])
  })

  it('W-020：只有縣市、縣市不符 → 仍是 not_eligible（❌ 優先於 ⚠️）', () => {
    const result = evaluateEligibility({ counties: ['新竹市'] }, { age: 30, county: '臺南市' })
    expect(result.verdict).toBe('not_eligible')
  })

  it('W-020：_note 與 referenceData 不算條件', () => {
    const c = { counties: ['新竹市'], _note: '資格條件見官方頁', referenceData: { minLivingExpense: 1 } } as EligibilityConditions
    expect(evaluateEligibility(c, { county: '新竹市' }).verdict).toBe('possible')
  })

  it('openToAll：逐筆確認過人人可申請 → confirmed', () => {
    const result = evaluateEligibility({ counties: ['新竹市'], openToAll: true }, { county: '新竹市' })
    expect(result.verdict).toBe('confirmed')
  })

  it('ageMinByIdentity：60 歲原住民符合「65 歲以上（原住民 55）」', () => {
    const c: EligibilityConditions = { counties: ['新竹市'], ageMin: 65, ageMinByIdentity: { 原住民: 55 } }
    expect(evaluateEligibility(c, { age: 60, county: '新竹市', identities: ['原住民'] }).verdict).toBe('confirmed')
  })

  it('ageMinByIdentity：60 歲非原住民 → not_eligible（不可因為有特例就全面放寬）', () => {
    const c: EligibilityConditions = { counties: ['新竹市'], ageMin: 65, ageMinByIdentity: { 原住民: 55 } }
    expect(evaluateEligibility(c, { age: 60, county: '新竹市', identities: [] }).verdict).toBe('not_eligible')
  })

  it('uncheckedConditions：其他條件全符合也只能 possible，且原文照列', () => {
    const c: EligibilityConditions = { counties: ['新竹市'], ageMin: 65, uncheckedConditions: ['連續設籍本市滿 10 年'] }
    const r = evaluateEligibility(c, { age: 70, county: '新竹市' })
    expect(r.verdict).toBe('possible')
    expect(r.missingConditions).toEqual(['連續設籍本市滿 10 年'])
  })

  it('uncheckedConditions：年齡不符仍是 not_eligible（❌ 優先）', () => {
    const c: EligibilityConditions = { counties: ['新竹市'], ageMin: 65, uncheckedConditions: ['連續設籍本市滿 10 年'] }
    expect(evaluateEligibility(c, { age: 30, county: '新竹市' }).verdict).toBe('not_eligible')
  })

  it('只有 ageMinByIdentity 沒有 ageMin → 仍算條件未整理', () => {
    const c: EligibilityConditions = { counties: ['新竹市'], ageMinByIdentity: { 原住民: 55 } }
    expect(evaluateEligibility(c, { age: 70, county: '新竹市' }).missingConditions).toContain(UNSORTED_CONDITIONS_LABEL)
  })

  it('有實質條件且都符合 → 照舊 confirmed，不會被誤標成未整理', () => {
    const result = evaluateEligibility({ counties: ['新竹市'], ageMin: 65 }, { age: 70, county: '新竹市' })
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

  it('需自有住宅：租屋者（ownsHome=false）→ not_eligible，不會誤判成確定符合', () => {
    const conditions: EligibilityConditions = { requiresOwnedHome: true }
    const applicant: ApplicantProfile = { ownsHome: false }
    const result = evaluateEligibility(conditions, applicant)
    expect(result.verdict).toBe('not_eligible')
    expect(result.failedConditions).toContain('需自有住宅')
  })

  it('需自有住宅：有自有住宅 → confirmed', () => {
    const conditions: EligibilityConditions = { requiresOwnedHome: true }
    const applicant: ApplicantProfile = { ownsHome: true }
    expect(evaluateEligibility(conditions, applicant).verdict).toBe('confirmed')
  })
})

// 🔴 2026-10-20 Lonck 定 A：問卷有明問的「身障證明」「家裡有沒有小孩」，沒有＝不符合（不是可能符合）
describe('問卷明確作答過的條件 → 可以判不符合', () => {
  it('requiredFlags 身障證明：問卷答過且沒有 → not_eligible', () => {
    const c: EligibilityConditions = { requiredFlags: ['disability_certificate'] }
    const a: ApplicantProfile = { flags: ['general_public'], answeredFlags: ['disability_certificate'] }
    expect(evaluateEligibility(c, a).verdict).toBe('not_eligible')
  })
  it('requiredFlags 身障證明：問卷答過且有 → confirmed', () => {
    const c: EligibilityConditions = { requiredFlags: ['disability_certificate'] }
    const a: ApplicantProfile = { flags: ['disability_certificate'], answeredFlags: ['disability_certificate'] }
    expect(evaluateEligibility(c, a).verdict).toBe('confirmed')
  })
  it('沒問過（非同戶家人 profile 不帶 answeredFlags）→ 仍是 possible', () => {
    const c: EligibilityConditions = { requiredFlags: ['disability_certificate'] }
    expect(evaluateEligibility(c, { flags: [] }).verdict).toBe('possible')
  })
  it('其他旗標（戒菸意願）沒勾 → 仍是 possible，不受影響', () => {
    const c: EligibilityConditions = { requiredFlags: ['wants_to_quit_smoking'] }
    const a: ApplicantProfile = { flags: [], answeredFlags: ['disability_certificate'] }
    expect(evaluateEligibility(c, a).verdict).toBe('possible')
  })
  it('requiresChildUnder：家庭名單已作答且沒有小孩 → not_eligible', () => {
    const c: EligibilityConditions = { requiresChildUnder: 18 }
    expect(evaluateEligibility(c, { householdAnswered: true }).verdict).toBe('not_eligible')
  })
  it('requiresChildUnder：不知道家庭狀況 → possible', () => {
    const c: EligibilityConditions = { requiresChildUnder: 18 }
    expect(evaluateEligibility(c, {}).verdict).toBe('possible')
  })
})

// 2026-10-20 Lonck 定 A：問卷第 2a 題設籍年限
describe('設籍年限 minResidencyMonths', () => {
  const c: EligibilityConditions = { counties: ['新北市'], ageMin: 65, minResidencyMonths: 12 }
  it('設籍滿 12 個月 → confirmed', () => {
    expect(evaluateEligibility(c, { county: '新北市', age: 70, residencyMonths: 12 }).verdict).toBe('confirmed')
  })
  it('設籍 11 個月 → not_eligible', () => {
    expect(evaluateEligibility(c, { county: '新北市', age: 70, residencyMonths: 11 }).verdict).toBe('not_eligible')
  })
  it('沒回答 → possible，還缺寫出幾年', () => {
    const r = evaluateEligibility(c, { county: '新北市', age: 70 })
    expect(r.verdict).toBe('possible')
    expect(r.missingConditions.join()).toContain('設籍滿 1 年')
  })
  it('只靠工作縣市對上（戶籍在別縣市）→ not_eligible', () => {
    expect(evaluateEligibility(c, { county: '臺北市', workCounty: '新北市', age: 70, residencyMonths: 240 }).verdict).toBe('not_eligible')
  })
  it('只有設籍年限、沒有其他條件 → 仍算條件未整理（不可 confirmed）', () => {
    const r = evaluateEligibility({ counties: ['新北市'], minResidencyMonths: 12 }, { county: '新北市', residencyMonths: 24 })
    expect(r.verdict).toBe('possible')
  })
})
