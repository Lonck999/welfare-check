import type { SeedBenefit } from './types.js'

/** 中央「急難紓困實施方案」為全國統一框架，不分縣市 */
export const emergencyReliefSeeds: SeedBenefit[] = [
  {
    categoryNumber: 4,
    name: '社會救助與現金補助（急難救助）',
    agency: '衛生福利部（急難紓困實施方案）',
    county: null,
    description:
      '戶內人口死亡無力殮葬、遭受意外傷害或罹患重病致生活困難、負家庭主要生計責任者失業或其他原因無法工作、財產或存款遭凍結無法運用、已申請福利項目尚未核准等情形，可申請急難救助，依情況核發 1～3 萬元；經認定為急迫個案者，訪視當下可先發放 5,000 元救助金。申請後 24 小時內會有訪視小組進行實地訪查。',
    searchGroup: '時效性最高項目',
    isTimeSensitive: true,
    applicationPeriod: '常態受理，急迫個案即時處理',
    eligibilityConditions: { requiredFlags: ['acute_hardship'] },
    sourceUrl: 'https://eysc.ey.gov.tw/Page/DAB11F5DBDC11168/3ccb55f0-60d5-4399-a8da-431843d17c93',
    sourceExcerpt:
      '急難救助的申請條件包括戶內人口死亡無力殮葬、遭受意外傷害或罹患重病致生活困難、負家庭主要生計責任者失業或其他原因無法工作、財產或存款遭凍結無法運用，以及已申請福利項目尚未核准等情形……衛福部現行的「急難紓困實施方案」針對不同情況發放1至3萬元的救助金，如屬急迫個案訪視時會先發5000元救助金。',
    lastVerifiedDate: '2026-07-28',
    documents: ['申請書', '相關證明文件（依情況而定，如死亡證明、醫療證明、失業證明等）'],
    locations: [{ name: '戶籍地政府社會處/局' }, { name: '1957 福利諮詢專線', phone: '1957' }],
  },
]
