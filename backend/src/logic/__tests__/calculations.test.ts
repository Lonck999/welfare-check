import { describe, expect, it } from 'vitest'
import {
  calculateAge,
  calculatePerCapitaAssets,
  calculatePerCapitaMonthlyIncome,
  daysUntilAge,
  evaluateIncomeThreshold,
  meetsAssetThreshold,
  yearsUntilAge,
} from '../calculations.js'

describe('calculateAge', () => {
  it('計算已過生日的年齡', () => {
    expect(calculateAge(new Date('1988-08-16'), new Date('2026-07-28'))).toBe(37)
  })

  it('計算尚未到生日的年齡（今年生日還沒到，要少一歲）', () => {
    expect(calculateAge(new Date('1988-08-16'), new Date('2026-07-27'))).toBe(37)
    expect(calculateAge(new Date('1990-12-01'), new Date('2026-07-28'))).toBe(35)
  })

  it('生日當天滿歲', () => {
    expect(calculateAge(new Date('1990-07-28'), new Date('2026-07-28'))).toBe(36)
  })
})

describe('daysUntilAge / yearsUntilAge', () => {
  it('尚未滿 40 歲時回傳正數天數/年數', () => {
    const birth = new Date('1990-07-28')
    const today = new Date('2026-07-28') // 剛滿 36 歲
    expect(yearsUntilAge(birth, 40, today)).toBe(4)
    expect(daysUntilAge(birth, 40, today)).toBeGreaterThan(0)
  })

  it('已超過門檻年齡時回傳負數', () => {
    const birth = new Date('1960-01-01')
    const today = new Date('2026-07-28') // 已 66 歲，早就過了 65 歲門檻
    expect(yearsUntilAge(birth, 65, today)).toBeLessThan(0)
    expect(daysUntilAge(birth, 65, today)).toBeLessThan(0)
  })
})

describe('calculatePerCapitaMonthlyIncome', () => {
  it('依公式計算人均月所得', () => {
    const members = [
      { annualIncome: 480_000, assets: 0 },
      { annualIncome: 0, assets: 0 },
    ]
    // (480000 + 0) / 2 / 12 = 20000
    expect(calculatePerCapitaMonthlyIncome(members)).toBe(20_000)
  })

  it('空陣列要丟錯誤，避免除以零被靜默吃掉', () => {
    expect(() => calculatePerCapitaMonthlyIncome([])).toThrow()
  })
})

describe('calculatePerCapitaAssets', () => {
  it('依公式計算人均動產', () => {
    const members = [
      { annualIncome: 0, assets: 300_000 },
      { annualIncome: 0, assets: 100_000 },
    ]
    expect(calculatePerCapitaAssets(members)).toBe(200_000)
  })
})

describe('evaluateIncomeThreshold', () => {
  const minLivingExpense = 18_000

  it('人均月所得低於等於最低生活費 → 低收入戶', () => {
    expect(evaluateIncomeThreshold(18_000, minLivingExpense)).toBe('low_income')
    expect(evaluateIncomeThreshold(10_000, minLivingExpense)).toBe('low_income')
  })

  it('介於 1 倍到 1.5 倍之間 → 中低收入戶', () => {
    expect(evaluateIncomeThreshold(18_001, minLivingExpense)).toBe('mid_low_income')
    expect(evaluateIncomeThreshold(27_000, minLivingExpense)).toBe('mid_low_income')
  })

  it('超過 1.5 倍 → 超過門檻', () => {
    expect(evaluateIncomeThreshold(27_001, minLivingExpense)).toBe('above_threshold')
  })
})

describe('meetsAssetThreshold', () => {
  it('預設 15 萬元門檻', () => {
    expect(meetsAssetThreshold(150_000)).toBe(true)
    expect(meetsAssetThreshold(150_001)).toBe(false)
  })

  it('可傳入自訂門檻（部分縣市不同）', () => {
    expect(meetsAssetThreshold(200_000, 250_000)).toBe(true)
  })
})
