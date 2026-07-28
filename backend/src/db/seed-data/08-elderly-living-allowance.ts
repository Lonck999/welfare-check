import type { SeedBenefit } from './types.js'

/** 中央法規統一訂定基準金額，地方政府可能加碼（詳見 notes），非每縣市完全獨立數字 */
export const elderlyLivingAllowanceSeeds: SeedBenefit[] = [
  {
    categoryNumber: 8,
    name: '老人福利（中低收入老人生活津貼）',
    agency: '衛生福利部（中低收入老人生活津貼發給辦法）',
    county: null,
    description:
      '65 歲以上、實際居住戶籍地、最近一年居住國內超過 183 日者：家庭人均月所得未達最低生活費 1.5 倍者（含列冊低收入戶/中低收入戶），每人每月發給 8,329 元；達 1.5 倍但未達 2.5 倍者，每人每月發給 4,164 元。財產限制：全家人口存款、投資及有價證券合計，單一申請人未超過 250 萬元，每增加一人限額增加 25 萬元。',
    searchGroup: '現金與生活補助類',
    isTimeSensitive: false,
    applicationPeriod: '常態受理',
    notes: '⚠️ 此為中央統一基準金額，各縣市在不動產評估標準上可能有差異、部分縣市另有加碼措施（如重陽禮金等，屬第 18 類另計），精確金額仍需依居住縣市洽詢當地社會局確認。',
    eligibilityConditions: { ageMin: 65, incomeThreshold: 'mid_low_income' },
    sourceUrl: 'https://law.moj.gov.tw/LawClass/LawAll.aspx?pcode=D0050045',
    sourceExcerpt:
      '申請人需年滿65歲，實際居住於戶籍所在地，且最近一年居住國內超過183日……家庭總收入按全家人口平均分配，每人每月未超過最低生活費標準的2.5倍……列冊低收入戶、中低收入戶及未達最低生活費1.5倍者，每人每月發給8,329元；達最低生活費1.5倍但未達2.5倍者，每人每月發給4,164元。',
    lastVerifiedDate: '2026-07-28',
    documents: ['戶籍謄本', '財力證明'],
    locations: [{ name: '戶籍地政府社會局' }],
  },
]
