import type { SeedBenefit } from './types.js'

/** 中央法規訂定基本金額，地方政府執行時常見加碼（詳見 notes 與新北市範例），非每縣市完全獨立數字 */
export const disabilityLivingAllowanceSeeds: SeedBenefit[] = [
  {
    categoryNumber: 6,
    name: '身心障礙補助（生活補助費）',
    agency: '衛生福利部（身心障礙者生活補助費發給辦法）',
    county: null,
    description:
      '領有身心障礙手冊或證明、實際居住戶籍地直轄市/縣市滿 183 日以上、未經政府補助安置於機構者，且符合低收入戶/中低收入戶或家庭總收入財產規定：中央基本金額為極重度/重度/中度每人每月 4,700 元，輕度每人每月 3,500 元。財產限制：動產第 1 人 200 萬元（每增 1 人加 25 萬元）、不動產未超過臺灣省不動產限額 2 倍。',
    searchGroup: '醫療與健康類',
    isTimeSensitive: false,
    applicationPeriod: '常態受理',
    notes:
      '⚠️ 地方政府常有加碼，金額可能明顯高於中央基本金額（例如新北市：中重極重度每月 5,437 元、輕度 4,049 元；列冊低收入戶中重極重度每月 9,485 元、輕度 5,437 元）。精確金額需依居住縣市另行查證當地社會局公告，不可直接套用中央基本金額給使用者。',
    eligibilityConditions: { requiredFlags: ['disability_certificate'] },
    sourceUrl: 'https://www.figure.tw/life/disability-benefits-guide/',
    sourceExcerpt:
      '2026年中央公告的身心障礙生活補助最高每月8,711元。根據具體分類，極重度、重度及中度身心障礙者每人每月核發新臺幣四千七百元；輕度身心障礙者每人每月核發新臺幣三千五百元（基本金額），但不同地方政府可能有調整。例如在新北市，一般身心障礙中、重、極重度者每月補助新臺幣5,437元；輕度者每月補助新臺幣4,049元；列冊低收入戶且身心障礙中、重、極重度者每月補助新臺幣9,485元；輕度者每月補助新臺幣5,437元。',
    lastVerifiedDate: '2026-07-28',
    documents: ['身心障礙手冊或證明', '財力證明'],
    locations: [{ name: '戶籍地政府社會局' }],
  },
]
