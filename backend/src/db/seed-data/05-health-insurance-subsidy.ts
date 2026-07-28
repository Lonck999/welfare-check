import type { SeedBenefit } from './types.js'

const BASE_SOURCE_URL = 'https://cava.tw/topic/news/263638'
const BASE_SOURCE_EXCERPT =
  '中低收入戶的健保費補助為健保自付保費補助1/2，但18歲以下兒童少年及70歲以上老人參加全民健康保險應自付之保險費全額補助……台灣並沒有「全國統一65歲以上免繳健保費」制度，而是由各縣市依照財政能力與社福政策，自行規劃補助方案。2026年起，更有部分縣市加碼實施65歲以上健保費全額代繳，每月最高補助約826元。例如南投、台東等縣市推出長者健保費補助，新竹市也宣布將加入。'
const LAST_VERIFIED_DATE = '2026-07-28'

/** 中低收入戶部分為全國統一（50%/100%），但一般長者（65歲以上不限身分）的健保費補助確實因縣市而異 */
const nationalBase: SeedBenefit = {
  categoryNumber: 5,
  name: '醫療與健保補助（中低收入戶健保費補助，中央基準）',
  agency: '衛生福利部中央健康保險署',
  county: null,
  description:
    '中低收入戶：健保自付保費補助 1/2；18 歲以下兒童少年及 70 歲以上老人應自付之保險費全額補助（此為全國統一標準）。另外，部分縣市自 2026 年起針對「65 歲以上一般長者」（不限中低收入戶身分）加碼實施健保費全額代繳，每月最高補助約 826 元，此為地方自辦方案，非全國統一。',
  searchGroup: '醫療與健康類',
  isTimeSensitive: false,
  applicationPeriod: '常態受理',
  eligibilityConditions: { incomeThreshold: 'mid_low_income' },
  sourceUrl: BASE_SOURCE_URL,
  sourceExcerpt: BASE_SOURCE_EXCERPT,
  lastVerifiedDate: LAST_VERIFIED_DATE,
  documents: ['低收入戶/中低收入戶證明或身分證明'],
  locations: [{ name: '衛生福利部中央健康保險署', website: 'https://www.nhi.gov.tw/' }],
}

interface CountyAddon {
  county: string
  addonDescription: string
  confirmed: boolean
}

const CONFIRMED_65_FULL_SUBSIDY: string[] = ['南投縣', '臺東縣', '新竹市']

const OTHER_COUNTIES = [
  '臺北市',
  '新北市',
  '桃園市',
  '臺中市',
  '臺南市',
  '高雄市',
  '基隆市',
  '嘉義市',
  '宜蘭縣',
  '新竹縣',
  '苗栗縣',
  '彰化縣',
  '雲林縣',
  '嘉義縣',
  '屏東縣',
  '花蓮縣',
  '澎湖縣',
  '金門縣',
  '連江縣',
]

const countyAddons: CountyAddon[] = [
  ...CONFIRMED_65_FULL_SUBSIDY.map((county) => ({
    county,
    addonDescription: '2026 年起加碼實施 65 歲以上一般長者（不限中低收入戶身分）健保費全額代繳，每月最高補助約 826 元。',
    confirmed: true,
  })),
  ...OTHER_COUNTIES.map((county) => ({
    county,
    addonDescription: '本次搜尋未查得此縣市是否有 65 歲以上一般長者健保費全額代繳方案，需依居住縣市另行查證衛生局/社會局最新公告。',
    confirmed: false,
  })),
]

const countyAddonRows: SeedBenefit[] = countyAddons.map((addon) => ({
  categoryNumber: 5,
  name: '醫療與健保補助（65歲以上健保費地方加碼）',
  agency: `${addon.county}政府衛生局/社會局`,
  county: addon.county,
  description: `${addon.county}的地方加碼情形：${addon.addonDescription}`,
  searchGroup: '醫療與健康類',
  isTimeSensitive: false,
  applicationPeriod: '常態受理',
  notes: addon.confirmed ? undefined : '⚠️ ' + addon.addonDescription,
  eligibilityConditions: { ageMin: 65, counties: [addon.county] },
  sourceUrl: BASE_SOURCE_URL,
  sourceExcerpt: BASE_SOURCE_EXCERPT,
  lastVerifiedDate: LAST_VERIFIED_DATE,
  locations: [{ name: `${addon.county}政府衛生局/社會局` }],
}))

/** 健保重大傷病卡：全國統一制度，不分縣市 */
const catastrophicIllnessCard: SeedBenefit = {
  categoryNumber: 5,
  name: '健保重大傷病卡（免部分負擔）',
  agency: '衛生福利部中央健康保險署',
  county: null,
  description:
    '重大傷病項目共計 30 大類疾病，包括癌症、洗腎、失智、罕見疾病、嚴重精神病、自體免疫疾病等。領有重大傷病證明者，因該證明所載傷病就醫時免門急住診自行負擔費用（僅限與申請疾病類別相關的治療，非重大傷病相關的就醫項目仍需自行負擔部分負擔費用）。證明有效期 3～5 年，依疾病類型而定，到期需重新申請。',
  searchGroup: '醫療與健康類',
  isTimeSensitive: false,
  applicationPeriod: '常態受理，證明到期前應重新申請以免權益中斷',
  notes: '⚠️ 免部分負擔僅限與重大傷病證明所載疾病相關的治療項目，非該疾病相關的就醫仍需自付部分負擔，並非「持卡全部免費」。',
  eligibilityConditions: { requiredFlags: ['catastrophic_illness'] },
  sourceUrl: 'https://www.nhi.gov.tw/ch/cp-6089-0c619-2957-1.html',
  sourceExcerpt:
    '重大傷病項目共計30大項，包括癌症、洗腎、失智、罕見疾病、嚴重精神病等……保險對象因重大傷病就醫時，免門急住診自行負擔費用……只有和重大傷病證明所載之傷病相關的治療，該次就醫可免部分負擔……有效期3-5年，具體期限視疾病類型而定。',
  lastVerifiedDate: LAST_VERIFIED_DATE,
  documents: ['重大傷病診斷證明文件（依疾病類別而定）'],
  locations: [{ name: '衛生福利部中央健康保險署（分區業務組）', website: 'https://www.nhi.gov.tw/' }],
}

export const healthInsuranceSubsidySeeds: SeedBenefit[] = [nationalBase, ...countyAddonRows, catastrophicIllnessCard]
