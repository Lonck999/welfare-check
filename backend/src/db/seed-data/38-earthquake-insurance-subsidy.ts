import type { SeedBenefit } from './types.js'

/** 保費本身全國單一費率；中低收入戶保費補助方案因縣市而異（本次未查得具體金額清單） */
export const earthquakeInsuranceSubsidySeeds: SeedBenefit[] = [
  {
    categoryNumber: 38,
    name: '住宅地震基本保險保費補助',
    agency: '財團法人住宅地震保險基金／各縣市政府',
    county: null,
    description:
      '住宅地震基本保險採全國單一費率，每戶每年保費新臺幣 1,350 元（依保額 150 萬元計算，保額低於 150 萬元者按比例計算）。部分縣市對中低收入戶/弱勢家庭另有保費補助方案，惟本次搜尋未查得具體縣市清單與補助金額。',
    searchGroup: '住宅類',
    isTimeSensitive: false,
    applicationPeriod: '常態受理',
    notes: '⚠️ 各縣市中低收入戶地震保費補助本次搜尋未查得具體資料，需依居住縣市另行洽詢社會局或財團法人住宅地震保險基金確認是否有相關方案。',
    eligibilityConditions: { incomeThreshold: 'mid_low_income' },
    sourceUrl: 'https://www.treif.org.tw/',
    sourceExcerpt:
      '住宅地震基本保險採全國單一費率，每年保費新台幣1350元（每一戶按保額新台幣150萬元計算，保額低於150萬元者，按比例計算保費）。',
    lastVerifiedDate: '2026-07-28',
    locations: [{ name: '財團法人住宅地震保險基金', website: 'https://www.treif.org.tw/' }],
  },
]
