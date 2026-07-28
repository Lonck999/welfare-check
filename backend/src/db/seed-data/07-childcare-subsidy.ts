import type { SeedBenefit } from './types.js'

const BASE_SOURCE_URL = 'https://www.businessweekly.com.tw/careers/blog/3021035'
const BASE_SOURCE_EXCERPT =
  '2026托育補助在2024有過補助制度調整，公共托育的補助為每月7,000元，而準公共托育的補助為每月1萬3,000元……完全取消排富：全國家庭皆可申請，不再受所得稅率限制。'
const ADDON_SOURCE_EXCERPT =
  '台北市：第1胎準公共補助加碼8000元/月；第2胎以上朝全面免負擔調整。新北市：保母加碼2000元/月；準公共托嬰中心加碼3000元/月。桃園市：準公共保母加碼1000元/月；準公共托嬰中心加碼2000元/月。台中市：符合條件送托準公共托嬰中心加碼1400元/月。台南市：中央補助為主，地方加碼以弱勢家庭為優先。高雄市：中央補助為主，第2胎以上由市府另設增額方案。新竹市：保母／托嬰中心加碼1000～3000元（依機構類型不等）。其他縣市：以中央補助為主，部分鄉鎮有額外加碼。'
const LAST_VERIFIED_DATE = '2026-07-28'

/** 中央基準（全國統一）：公托 7,000／準公托 13,000 元，已取消排富 */
const nationalBase: SeedBenefit = {
  categoryNumber: 7,
  name: '育兒與托育補助（中央基準）',
  agency: '衛生福利部社會及家庭署',
  county: null,
  description:
    '有 18 歲以下子女者：公共托育每月補助 7,000 元、準公共托育每月補助 13,000 元（中央統一金額，已完全取消排富，全國家庭皆可申請）。2026 年起，滿 2 歲仍留在原托育處未入園者可續領托育補助至 3 歲。',
  searchGroup: '現金與生活補助類',
  isTimeSensitive: false,
  applicationPeriod: '常態受理',
  eligibilityConditions: { requiresChildUnder: 18 },
  sourceUrl: BASE_SOURCE_URL,
  sourceExcerpt: BASE_SOURCE_EXCERPT,
  lastVerifiedDate: LAST_VERIFIED_DATE,
  documents: ['托育契約', '戶籍資料'],
  locations: [{ name: '衛生福利部社會及家庭署托育媒合平台', website: 'https://ap.mohw.gov.tw/babyhome/' }],
}

interface CountyAddon {
  county: string
  addonDescription: string
  confirmed: boolean
}

const COUNTY_ADDONS: CountyAddon[] = [
  { county: '臺北市', addonDescription: '第 1 胎準公共托育補助加碼 8,000 元/月；第 2 胎以上朝全面免負擔方向調整。', confirmed: true },
  { county: '新北市', addonDescription: '保母加碼 2,000 元/月；準公共托嬰中心加碼 3,000 元/月。', confirmed: true },
  { county: '桃園市', addonDescription: '準公共保母加碼 1,000 元/月；準公共托嬰中心加碼 2,000 元/月。', confirmed: true },
  { county: '臺中市', addonDescription: '符合條件送托準公共托嬰中心加碼 1,400 元/月。', confirmed: true },
  { county: '臺南市', addonDescription: '中央補助為主，地方加碼以弱勢家庭為優先，具體金額本次未查得，需洽台南市社會局確認。', confirmed: false },
  { county: '高雄市', addonDescription: '中央補助為主，第 2 胎以上由市府另設增額方案，具體金額本次未查得，需洽高雄市社會局確認。', confirmed: false },
  { county: '新竹市', addonDescription: '保母/托嬰中心加碼 1,000～3,000 元（依機構類型不等）。', confirmed: true },
  { county: '基隆市', addonDescription: '本次搜尋未查得具體地方加碼金額，以中央補助為主，部分鄉鎮可能另有加碼。', confirmed: false },
  { county: '嘉義市', addonDescription: '本次搜尋未查得具體地方加碼金額，以中央補助為主，部分鄉鎮可能另有加碼。', confirmed: false },
  { county: '宜蘭縣', addonDescription: '本次搜尋未查得具體地方加碼金額，以中央補助為主，部分鄉鎮可能另有加碼。', confirmed: false },
  { county: '新竹縣', addonDescription: '本次搜尋未查得具體地方加碼金額，以中央補助為主，部分鄉鎮可能另有加碼。', confirmed: false },
  { county: '苗栗縣', addonDescription: '本次搜尋未查得具體地方加碼金額，以中央補助為主，部分鄉鎮可能另有加碼。', confirmed: false },
  { county: '彰化縣', addonDescription: '本次搜尋未查得具體地方加碼金額，以中央補助為主，部分鄉鎮可能另有加碼。', confirmed: false },
  { county: '南投縣', addonDescription: '本次搜尋未查得具體地方加碼金額，以中央補助為主，部分鄉鎮可能另有加碼。', confirmed: false },
  { county: '雲林縣', addonDescription: '本次搜尋未查得具體地方加碼金額，以中央補助為主，部分鄉鎮可能另有加碼。', confirmed: false },
  { county: '嘉義縣', addonDescription: '本次搜尋未查得具體地方加碼金額，以中央補助為主，部分鄉鎮可能另有加碼。', confirmed: false },
  { county: '屏東縣', addonDescription: '本次搜尋未查得具體地方加碼金額，以中央補助為主，部分鄉鎮可能另有加碼。', confirmed: false },
  { county: '臺東縣', addonDescription: '本次搜尋未查得具體地方加碼金額，以中央補助為主，部分鄉鎮可能另有加碼。', confirmed: false },
  { county: '花蓮縣', addonDescription: '本次搜尋未查得具體地方加碼金額，以中央補助為主，部分鄉鎮可能另有加碼。', confirmed: false },
  { county: '澎湖縣', addonDescription: '本次搜尋未查得具體地方加碼金額，以中央補助為主，部分鄉鎮可能另有加碼。', confirmed: false },
  { county: '金門縣', addonDescription: '本次搜尋未查得具體地方加碼金額，以中央補助為主，部分鄉鎮可能另有加碼。', confirmed: false },
  { county: '連江縣', addonDescription: '本次搜尋未查得具體地方加碼金額，以中央補助為主，部分鄉鎮可能另有加碼。', confirmed: false },
]

const countyAddonRows: SeedBenefit[] = COUNTY_ADDONS.map((addon) => ({
  categoryNumber: 7,
  name: '育兒與托育補助（地方加碼）',
  agency: `${addon.county}政府社會局`,
  county: addon.county,
  description: `在中央基準（公托 7,000／準公托 13,000 元）之上，${addon.county}的地方加碼情形：${addon.addonDescription}`,
  searchGroup: '現金與生活補助類',
  isTimeSensitive: false,
  applicationPeriod: '常態受理',
  notes: addon.confirmed
    ? undefined
    : '⚠️ 此縣市地方加碼金額本次未查得明確數字，不可視為「無加碼」，需依居住縣市另行向社會局確認最新公告。',
  eligibilityConditions: { requiresChildUnder: 18, counties: [addon.county] },
  sourceUrl: BASE_SOURCE_URL,
  sourceExcerpt: ADDON_SOURCE_EXCERPT,
  lastVerifiedDate: LAST_VERIFIED_DATE,
  locations: [{ name: `${addon.county}政府社會局` }],
}))

export const childcareSubsidySeeds: SeedBenefit[] = [nationalBase, ...countyAddonRows]
