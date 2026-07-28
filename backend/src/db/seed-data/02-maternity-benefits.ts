import type { SeedBenefit } from './types.js'

const LAST_VERIFIED_DATE = '2026-07-28'

/** 中央生育給付/陪產假/育嬰留停為全國統一；各縣市另有生育獎勵金金額不同（詳見 county 加碼列） */
const nationalBase: SeedBenefit = {
  categoryNumber: 2,
  name: '生育與孕產補助（中央基準：生育給付/陪產假/育嬰留停）',
  agency: '衛生福利部／勞動部勞工保險局',
  county: null,
  description:
    '「生育給付 PLUS」：2026 年 1 月 1 日起出生之新生兒，不論投保何種保險或有無保險，中央保證每胎普發 10 萬元（雙胞胎 20 萬元，依此類推）。另有勞保生育給付（依平均月投保薪資計算）；配偶懷孕或分娩時可申請陪產檢假與陪產假；父母雙方各自可申請育嬰留職停薪津貼（月領平均月投保薪資 60%，最長 6 個月/人）。',
    searchGroup: '時效性最高項目',
  isTimeSensitive: true,
  applicationPeriod: '常態受理，新生兒出生後應於一定期限內申請（依各項目規定，通常為出生後 60 日或數月內）',
  eligibilityConditions: { requiredFlags: ['pregnant_or_recent_birth'] },
  sourceUrl: 'https://www.mababy.com/knowledge-detail?id=16728',
  sourceExcerpt:
    '2026年起，政府實施「生育給付PLUS」，不論投保哪種保險，中央保證每胎領到10萬元。2026年1月1日起出生的新生兒，每胎發10萬元（雙胞胎20萬元，依此類推），不論父母是否有勞保或國保，一律普發。',
  lastVerifiedDate: LAST_VERIFIED_DATE,
  documents: ['出生證明', '戶籍謄本', '金融機構帳戶存摺影本'],
  locations: [{ name: '衛生福利部', website: 'https://www.mohw.gov.tw/' }, { name: '勞動部勞工保險局', website: 'https://www.bli.gov.tw/' }],
}

interface CountyAddon {
  county: string
  addonDescription: string
  confirmed: boolean
}

const CONFIRMED_ADDONS: CountyAddon[] = [
  {
    county: '臺北市',
    addonDescription: '生育獎勵金：第一胎 4 萬元、第二胎 4 萬 5,000 元、第三胎以上 5 萬元（依胎次遞增）。',
    confirmed: true,
  },
  {
    county: '桃園市',
    addonDescription: '生育獎勵金：第一胎 3 萬元、第二胎 4 萬元、第三胎以上 5 萬元，多胞胎另有加碼。',
    confirmed: true,
  },
  {
    county: '苗栗縣',
    addonDescription:
      '縣府生育獎勵金 2 萬元；部分鄉鎮另有獨立加碼（如通霄鎮地方單獨補助 9 萬元），加上中央 10 萬元與縣府 2 萬元，第一胎總額最高可達 21 萬元。鄉鎮加碼金額因鄉鎮而異，需另行確認戶籍所在鄉鎮公所公告。',
    confirmed: true,
  },
]

const UNCONFIRMED_NOTE =
  '本次搜尋未查得此縣市具體生育獎勵金金額，多數縣市要求新生兒出生後 3～6 個月內完成申請、逾期視同放棄，需依居住縣市另行洽詢戶政或社會局確認金額與申請期限。'

const OTHER_COUNTIES = [
  '新北市',
  '臺中市',
  '臺南市',
  '高雄市',
  '基隆市',
  '新竹市',
  '嘉義市',
  '宜蘭縣',
  '新竹縣',
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
  categoryNumber: 2,
  name: '生育獎勵金（地方加碼）',
  agency: `${addon.county}政府`,
  county: addon.county,
  description: `在中央「生育給付 PLUS」每胎 10 萬元之上，${addon.county}的生育獎勵金：${addon.addonDescription}`,
  searchGroup: '時效性最高項目',
  isTimeSensitive: true,
  applicationPeriod: '新生兒出生後 3～6 個月內申請（依各縣市規定，逾期視同放棄）',
  notes: addon.confirmed ? undefined : '⚠️ ' + UNCONFIRMED_NOTE,
  eligibilityConditions: { requiredFlags: ['pregnant_or_recent_birth'], counties: [addon.county] },
  sourceUrl: 'https://www.businessweekly.com.tw/careers/blog/3021085',
  sourceExcerpt:
    '發放金額依各縣市規定及胎次而定，例如台北市第一胎4萬元、第二胎4萬5000元、第三胎以上5萬元；桃園市第一胎3萬元、第二胎4萬元、第三胎以上5萬元，多胞胎另有加碼……例如苗栗通霄鎮地方單獨補助即有9萬元，加上縣府和中央的10萬元，以及苗栗縣府的2萬元，生育津貼第一胎總額可達21萬元。',
  lastVerifiedDate: LAST_VERIFIED_DATE,
  locations: [{ name: `${addon.county}政府戶政事務所/社會局` }],
}))

export const maternityBenefitsSeeds: SeedBenefit[] = [nationalBase, ...countyAddonRows]
