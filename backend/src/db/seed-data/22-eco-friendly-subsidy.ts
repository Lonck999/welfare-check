import type { SeedBenefit } from './types.js'

const LAST_VERIFIED_DATE = '2026-07-28'
const ADDON_SOURCE_URL = 'https://www.businesstoday.com.tw/article/category/183030/post/202605250011/'
const ADDON_SOURCE_EXCERPT =
  '台北市：若為淘汰老舊二行程機車換購電動機車，最高可補助4萬9,300元（含中央單位補助）；若家中無須汰換的老舊機車，新購電動機車最高可補助3萬3,000元，若為中低及低收入戶再加碼補助1萬元。桃園市：針對婦幼族群、青壯年、原住民、中低收入戶等族群推出多元補助專案，2026年再新增「外送騎士」與「守望相助隊」兩大加碼方案，最高補助新臺幣4萬4,000元。新北市：若搭配經濟部7,000元補助及環境部3,300元獎勵金，並採取「雙汰舊」方案，單筆申請電動機車最高補助金額可達3萬9,600元。'

/** 中央基本補助全國統一；地方加碼因縣市而異（詳見縣市加碼列） */
const nationalBase: SeedBenefit = {
  categoryNumber: 22,
  name: '環保節能補助（電動機車購車補助，中央基準）',
  agency: '經濟部／環境部',
  county: null,
  description:
    '依「經濟部推動電動機車產業補助實施要點」（效期至 115 年 12 月 31 日止）：新購電動機車，重型/輕型每輛補助 7,000 元、小型輕型每輛補助 5,100 元；電池芯及負極材料/電解液/銅箔皆為國內產製者再加碼 3,000 元。老舊機車（出廠滿 10 年以上燃油機車）汰舊換新另有空氣污染減量補助（至少 1,000 元）、溫室氣體減量補助（1,500～2,000 元）、廢車回收金（300 元）。節能家電汰換補助另計，需另行查證當年度公告額度。',
  searchGroup: '一般性優惠與便民服務',
  isTimeSensitive: true,
  applicationPeriod: '中央電動機車補助效期至 115（2026）年 12 月 31 日止',
  eligibilityConditions: {},
  sourceUrl: ADDON_SOURCE_URL,
  sourceExcerpt:
    '根據「經濟部推動電動機車產業補助實施要點」，補助效期將至115年12月31日止……重型與輕型等級每輛補助7,000元；小型輕型等級每輛補助5,100元；電動機車所使用的電池芯及其負極材料、電解液、銅箔均為國內產製者，每輛額外補助新臺幣3,000元。',
  lastVerifiedDate: LAST_VERIFIED_DATE,
  documents: ['購車發票', '舊車報廢證明（汰舊換新適用）'],
  locations: [{ name: '經濟部', website: 'https://www.moea.gov.tw/' }, { name: '環境部', website: 'https://www.moenv.gov.tw/' }],
}

interface CountyAddon {
  county: string
  addonDescription: string
  confirmed: boolean
}

const CONFIRMED_ADDONS: CountyAddon[] = [
  {
    county: '臺北市',
    addonDescription:
      '淘汰老舊二行程機車換購電動機車，最高可補助 4 萬 9,300 元（含中央補助）；無須汰換老舊車者新購電動機車最高補助 3 萬 3,000 元，中低/低收入戶再加碼 1 萬元。',
    confirmed: true,
  },
  {
    county: '桃園市',
    addonDescription: '針對婦幼族群、青壯年、原住民、中低收入戶等推出多元補助專案，2026 年新增外送騎士/守望相助隊加碼方案，最高補助 4 萬 4,000 元。',
    confirmed: true,
  },
  {
    county: '新北市',
    addonDescription: '搭配經濟部 7,000 元補助及環境部 3,300 元獎勵金，採「雙汰舊」方案，單筆最高補助金額可達 3 萬 9,600 元。',
    confirmed: true,
  },
]

const UNCONFIRMED_NOTE =
  '本次搜尋未查得此縣市電動機車/老舊機車汰換的具體地方加碼金額，需依居住縣市另行查證環保局最新公告。'

const OTHER_COUNTIES = [
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
  ...CONFIRMED_ADDONS,
  ...OTHER_COUNTIES.map((county) => ({ county, addonDescription: UNCONFIRMED_NOTE, confirmed: false })),
].map((addon) => ({
  categoryNumber: 22,
  name: '環保節能補助（電動機車地方加碼）',
  agency: `${addon.county}政府環保局`,
  county: addon.county,
  description: `在中央基準之上，${addon.county}的地方加碼情形：${addon.addonDescription}`,
  searchGroup: '一般性優惠與便民服務',
  isTimeSensitive: true,
  applicationPeriod: '依各縣市當年度公告期程受理',
  notes: addon.confirmed ? undefined : '⚠️ ' + UNCONFIRMED_NOTE,
  eligibilityConditions: { counties: [addon.county] },
  sourceUrl: ADDON_SOURCE_URL,
  sourceExcerpt: ADDON_SOURCE_EXCERPT,
  lastVerifiedDate: LAST_VERIFIED_DATE,
  locations: [{ name: `${addon.county}政府環保局` }],
}))

/** 節能家電汰換補助：全國統一（中央常態性補助），不分縣市 */
const applianceSubsidy: SeedBenefit = {
  categoryNumber: 22,
  name: '節能家電汰換補助（冷氣/冰箱/除濕機）',
  agency: '經濟部能源署',
  county: null,
  description:
    '2026 年常態性中央補助品項僅限冷氣機、冰箱與除濕機：購買指定一級能效冷氣機及電冰箱之消費者可申請補助，每台最高補助 5,000 元。申請需準備身分證明文件、存簿照片、電費單照片、統一發票、產品保證書、廢四機回收聯單等文件，可線上上傳申請或填寫申請表以掛號方式郵寄至指定信箱。原則上從送出申請單到補助入帳約需 2 個月。',
  searchGroup: '一般性優惠與便民服務',
  isTimeSensitive: false,
  applicationPeriod: '常態受理，購買後應於指定期限內申請',
  eligibilityConditions: {},
  sourceUrl: 'https://www.businessweekly.com.tw/focus/blog/3020900',
  sourceExcerpt:
    '2026年常態性的中央補助品項，僅限冷氣、冰箱與除濕機……購買指定一級能效冷氣機及電冰箱之消費者可申請該補助，並須準備身分證明文件、存簿照片、電費單照片，以及統一發票、產品保證書、廢四機回收聯單等文件……原則上從送出申請單到補助入帳需要2個月。',
  lastVerifiedDate: LAST_VERIFIED_DATE,
  documents: ['身分證明文件', '存簿照片', '電費單照片', '統一發票', '產品保證書', '廢四機回收聯單'],
  locations: [{ name: '經濟部能源署', website: 'https://www.moeaea.gov.tw/' }],
}

/** 電動自行車購車補助：中央法規統一基準，地方加碼因縣市而異 */
const eBikeSourceUrl = 'https://uptogo.com.tw/%E6%B1%BD%E6%A9%9F%E8%BB%8A/%E9%9B%BB%E5%8B%95%E8%BB%8A/%E7%8F%BE%E5%9C%A8%E8%B2%B7%E9%9B%BB%E5%8B%95%E6%A9%9F%E8%BB%8A%E6%9C%89%E8%A3%9C%E5%8A%A9%E5%97%8E%EF%BC%9F/'
const eBikeSourceExcerpt =
  '新購電動自行車補助辦法……縣市環保局有加碼補助，效期延續至2026年，包含台北、新北等城市。新北市提供額外「雙汰舊加碼」補助每輛9,000元（限量1,000輛）與「早鳥加碼」補助每輛10,000元（限量4,500輛），期限至2026年12月31日止。每縣市汰舊換購補助均有名額限制，建議購買前先確認補助是否還有名額，依先到先得原則發放。'

const eBikeNationalBase: SeedBenefit = {
  categoryNumber: 22,
  name: '電動自行車購車補助（中央基準）',
  agency: '經濟部／環境部',
  county: null,
  description:
    '依「新購電動自行車補助辦法」，購買電動自行車（電輔車/電動輔助自行車）可申請中央補助，各縣市環保局另有加碼方案，多數縣市有名額限制，依先到先得原則發放，購買前應先確認補助名額是否還有剩餘。',
  searchGroup: '一般性優惠與便民服務',
  isTimeSensitive: true,
  applicationPeriod: '常態受理，惟各縣市加碼名額有限，額滿為止',
  notes: '⚠️ 中央基準的具體補助金額本次搜尋未查得明確數字，僅確認新北市有具體地方加碼金額，其餘縣市需另行查證環保局公告與剩餘名額。',
  eligibilityConditions: {},
  sourceUrl: eBikeSourceUrl,
  sourceExcerpt: eBikeSourceExcerpt,
  lastVerifiedDate: LAST_VERIFIED_DATE,
  documents: ['購車發票'],
  locations: [{ name: '經濟部', website: 'https://www.moea.gov.tw/' }, { name: '環境部', website: 'https://www.moenv.gov.tw/' }],
}

const EBIKE_CONFIRMED: CountyAddon[] = [
  {
    county: '新北市',
    addonDescription: '「雙汰舊加碼」每輛 9,000 元（限量 1,000 輛）；「早鳥加碼」每輛 10,000 元（限量 4,500 輛），期限至 2026 年 12 月 31 日止。',
    confirmed: true,
  },
]

const EBIKE_UNCONFIRMED_NOTE = '本次搜尋未查得此縣市電動自行車地方加碼的具體金額與名額，需依居住縣市另行查證環保局最新公告。'

const eBikeOtherCounties = [
  '臺北市',
  '桃園市',
  ...OTHER_COUNTIES,
]

const eBikeCountyRows: SeedBenefit[] = [
  ...EBIKE_CONFIRMED,
  ...eBikeOtherCounties.map((county) => ({ county, addonDescription: EBIKE_UNCONFIRMED_NOTE, confirmed: false })),
].map((addon) => ({
  categoryNumber: 22,
  name: '電動自行車購車補助（地方加碼）',
  agency: `${addon.county}政府環保局`,
  county: addon.county,
  description: `在中央基準之上，${addon.county}的地方加碼情形：${addon.addonDescription}`,
  searchGroup: '一般性優惠與便民服務',
  isTimeSensitive: true,
  applicationPeriod: '依各縣市當年度公告期程受理，額滿為止',
  notes: addon.confirmed ? undefined : '⚠️ ' + EBIKE_UNCONFIRMED_NOTE,
  eligibilityConditions: { counties: [addon.county] },
  sourceUrl: eBikeSourceUrl,
  sourceExcerpt: eBikeSourceExcerpt,
  lastVerifiedDate: LAST_VERIFIED_DATE,
  locations: [{ name: `${addon.county}政府環保局` }],
}))

export const ecoFriendlySubsidySeeds: SeedBenefit[] = [
  nationalBase,
  ...countyAddonRows,
  applianceSubsidy,
  eBikeNationalBase,
  ...eBikeCountyRows,
]
