import type { SeedBenefit } from './types.js'

const BASE_SOURCE_URL = 'https://www.faqs.tw/disability-subsidy'
const BASE_SOURCE_EXCERPT =
  '2026年身心障礙生活補助每月最高8,836元：極重度8,836元、重度8,499元、中度5,065元、輕度4,872元（中央公告基準金額）。'
const LAST_VERIFIED_DATE = '2026-07-28'

/** 中央法規訂定基本金額；地方政府執行時常有加碼，金額不完全統一 */
const nationalBase: SeedBenefit = {
  categoryNumber: 6,
  name: '身心障礙補助（生活補助費，中央基準）',
  agency: '衛生福利部（身心障礙者生活補助費發給辦法）',
  county: null,
  description:
    '領有身心障礙手冊或證明、實際居住戶籍地直轄市/縣市滿 183 日以上、未經政府補助安置於機構者，且符合低收入戶/中低收入戶或家庭總收入財產規定：2026 年中央基準金額為極重度 8,836 元、重度 8,499 元、中度 5,065 元、輕度 4,872 元（每人每月）。財產限制：動產第 1 人 200 萬元（每增 1 人加 25 萬元）、不動產未超過臺灣省不動產限額 2 倍（見第 1 類各縣市不動產限額）。',
  searchGroup: '醫療與健康類',
  isTimeSensitive: false,
  applicationPeriod: '常態受理',
  eligibilityConditions: { requiredFlags: ['disability_certificate'] },
  sourceUrl: BASE_SOURCE_URL,
  sourceExcerpt: BASE_SOURCE_EXCERPT,
  lastVerifiedDate: LAST_VERIFIED_DATE,
  documents: ['身心障礙手冊或證明', '財力證明'],
  locations: [{ name: '戶籍地政府社會局' }],
}

interface CountyAddon {
  county: string
  addonDescription: string
  confirmed: boolean
}

const CONFIRMED_NEW_TAIPEI: CountyAddon = {
  county: '新北市',
  addonDescription:
    '一般身心障礙中/重/極重度者每月補助 5,437 元、輕度者 4,049 元；列冊低收入戶且身心障礙中/重/極重度者每月補助 9,485 元、輕度者 5,437 元（皆高於中央基準金額）。',
  confirmed: true,
}

const UNCONFIRMED_NOTE =
  '本次搜尋未查得此縣市具體加碼金額，各地方政府每年可能調整加碼方案，需依居住縣市另行洽詢當地社會局確認，不可直接套用中央基準金額。'

const OTHER_COUNTIES = [
  '臺北市',
  '桃園市',
  '臺中市',
  '臺南市',
  '高雄市',
  '基隆市',
  '新竹市',
  '嘉義市',
  '宜蘭縣',
  '新竹縣',
  '苗栗縣',
  '彰化縣',
  '南投縣',
  '雲林縣',
  '嘉義縣',
  '屏東縣',
  '臺東縣',
  '花蓮縣',
  '澎湖縣',
  '金門縣',
  '連江縣',
]

const countyAddonRows: SeedBenefit[] = [
  CONFIRMED_NEW_TAIPEI,
  ...OTHER_COUNTIES.map((county) => ({ county, addonDescription: UNCONFIRMED_NOTE, confirmed: false })),
].map((addon) => ({
  categoryNumber: 6,
  name: '身心障礙補助（地方加碼）',
  agency: `${addon.county}政府社會局`,
  county: addon.county,
  description: `在中央基準之上，${addon.county}的地方加碼情形：${addon.addonDescription}`,
  searchGroup: '醫療與健康類',
  isTimeSensitive: false,
  applicationPeriod: '常態受理',
  notes: addon.confirmed ? undefined : '⚠️ ' + UNCONFIRMED_NOTE,
  eligibilityConditions: { requiredFlags: ['disability_certificate'], counties: [addon.county] },
  sourceUrl: BASE_SOURCE_URL,
  sourceExcerpt: BASE_SOURCE_EXCERPT,
  lastVerifiedDate: LAST_VERIFIED_DATE,
  locations: [{ name: `${addon.county}政府社會局` }],
}))

export const disabilityLivingAllowanceSeeds: SeedBenefit[] = [nationalBase, ...countyAddonRows]
