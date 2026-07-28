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

/** 流產假：全國統一（性別工作平等法），依懷孕週數分級，不分縣市 */
const miscarriageLeave: SeedBenefit = {
  categoryNumber: 2,
  name: '流產假（性別工作平等法）',
  agency: '勞動部（性別工作平等法第 15 條）',
  county: null,
  description:
    '依懷孕天數不同，流產假天數與薪資保障不同：懷孕 3 個月以上流產者可請流產假 4 週，年資半年以上者全薪、未滿半年者半薪；懷孕 2 個月以上未滿 3 個月流產者可請假 1 週（不支薪）；懷孕未滿 2 個月流產者可請假 5 天（不支薪）。20 週以下流產無勞保生育給付；20 週以上之引產、死產則可申請生育給付（見本類中央基準）。',
  searchGroup: '時效性最高項目',
  isTimeSensitive: true,
  applicationPeriod: '流產發生後應儘速向雇主申請流產假',
  notes: '⚠️ 各縣市流產後心理諮商補助本次搜尋未查得具體縣市清單，可優先參考第 24 類「15-45 歲青壯世代心理健康支持方案」（全國統一，3 次免費諮商，無戶籍限制），或另行洽詢居住縣市衛生局是否有專屬方案。',
  eligibilityConditions: { requiredFlags: ['miscarriage'] },
  sourceUrl: 'https://www.yourator.co/articles/616',
  sourceExcerpt:
    '根據懷孕天數不同，流產假天數也不同：懷孕3個月以上流產：4週；懷孕2個月以上未滿3個月流產：1週；懷孕未滿2個月流產：5天。薪資補助標準為：懷孕3個月以上流產：全薪（年資半年以上）、半薪（年資未滿半年）；懷孕2個月以上未滿3個月流產：不支薪；懷孕未滿2個月流產：不支薪。若是20週以下的流產，沒有勞保給付。20週以上的引產、死產，可以申請生育補助。',
  lastVerifiedDate: LAST_VERIFIED_DATE,
  documents: ['醫療診斷證明'],
  locations: [{ name: '任職公司人資單位' }, { name: '勞動部', website: 'https://www.mol.gov.tw/' }],
}

/** 孕產婦補助/坐月子（產後護理/坐月子中心費用補助）：與生育獎勵金是不同的縣市方案，需分開建檔 */
const POSTPARTUM_UNCONFIRMED_NOTE =
  '本次搜尋未查得此縣市孕產婦補助/坐月子相關方案的具體金額，各縣市申請資格常見規定：家庭身分（低收入戶/中低收入戶/特殊境遇家庭等）、戶籍條件（設籍地區/年限或新生兒出生登記限制）、申請時間（懷孕期間/產前或產後指定期限內），需依居住縣市另行洽詢社會局/民政處確認，此為與「生育獎勵金」不同的獨立方案，不可混為一談。'

const postpartumCareRows: SeedBenefit[] = [
  ...CONFIRMED_ADDONS.map((a) => a.county),
  ...OTHER_COUNTIES,
].map((county) => ({
  categoryNumber: 2,
  name: '孕產婦補助/坐月子補助（地方方案）',
  agency: `${county}政府社會局/民政處`,
  county,
  description: `${county}的孕產婦補助/坐月子相關方案：${POSTPARTUM_UNCONFIRMED_NOTE}`,
  searchGroup: '時效性最高項目',
  isTimeSensitive: true,
  applicationPeriod: '多依懷孕期間/產前或產後指定期限內申請，逾期可能不予受理',
  notes: '⚠️ ' + POSTPARTUM_UNCONFIRMED_NOTE,
  eligibilityConditions: { requiredFlags: ['pregnant_or_recent_birth'], counties: [county] },
  sourceUrl: 'https://www.yannigo.com/zt/yannigo/blog-detail/pregnancy/maternity-benefits/postpartum/',
  sourceExcerpt:
    '坐月子補助申請資格與方式依各縣市規定不同，主要包括家庭身分（低收入戶、中低收入戶、特殊境遇家庭等）、戶籍條件（部分補助設有設籍地區、設籍年限或新生兒出生登記限制）、申請時間（依規定於懷孕期間、產前或產後指定期限內提出申請）、準備文件（常見文件包含身分證明、戶籍資料、孕婦健康手冊、出生證明及存摺影本）等要點。',
  lastVerifiedDate: LAST_VERIFIED_DATE,
  locations: [{ name: `${county}政府社會局/民政處` }],
}))

export const maternityBenefitsSeeds: SeedBenefit[] = [
  nationalBase,
  ...countyAddonRows,
  miscarriageLeave,
  ...postpartumCareRows,
]
