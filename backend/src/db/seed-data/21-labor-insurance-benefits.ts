import type { SeedBenefit } from './types.js'

/** 全國統一制度，不分縣市 */
export const laborInsuranceBenefitsSeeds: SeedBenefit[] = [
  {
    categoryNumber: 21,
    name: '勞保給付權益（傷病／失能／老年年金）',
    agency: '勞動部勞工保險局',
    county: null,
    description:
      '在職勞工的勞保權益：(1) 傷病給付：住院期間可領平均日投保薪資 70%；(2) 失能給付：達終身無工作能力者可請領失能年金，公式為「平均月投保薪資 × 投保年資 × 1.55%」，最低保障每月 4,000 元；(3) 老年年金：保險年資滿 15 年、達法定請領年齡（113 年起為 64 歲）可請領。',
    searchGroup: '就業與勞工權益類',
    isTimeSensitive: false,
    applicationPeriod: '常態受理（達成就給付要件後即可申請）',
    notes: '建議在職勞工定期至勞保局網站試算未來可領金額，並確認投保薪資申報是否足額。',
    eligibilityConditions: { requiredFlags: ['has_labor_insurance'] },
    sourceUrl: 'https://www.bli.gov.tw/0004857.html',
    sourceExcerpt:
      '失能年金公式：平均月投保薪資 × 投保年資 × 1.55%，保底機制：如果算出來每個月不到 4,000 元，勞保局最少會發給 4,000 元。被保險人年滿 60 歲以上，保險年資合計滿 15 年，並辦理離職退保者，得請領老年年金給付……113 年提高為 64 歲。',
    lastVerifiedDate: '2026-07-28',
    locations: [
      {
        name: '勞動部勞工保險局',
        phone: '(02)2396-1266',
        website: 'https://www.bli.gov.tw/',
      },
    ],
  },
]
