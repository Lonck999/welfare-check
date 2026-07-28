import type { SeedBenefit } from './types.js'

const LAST_VERIFIED_DATE = '2026-07-28'

/** 中央「300億元擴大租金補貼」為全國統一方案，非依縣市各自訂價；地方另有自辦加碼方案 */
const nationalBase: SeedBenefit = {
  categoryNumber: 10,
  name: '租金補貼（300億元中央擴大租金補貼，中央基準）',
  agency: '內政部國土管理署',
  county: null,
  description:
    '2026 年持續辦理「300 億元中央擴大租金補貼」，每戶每月補貼 2,000～8,000 元，依身分等級（第一級：家庭 2 人以上且有低收入戶身分／家庭 3 人以上且有中低收入戶身分，餘為一般申請）核定金額。20～40 歲單身者、結婚 2 年內新婚家庭、育有未成年子女家庭及經濟/社會弱勢可享 1.2～1.8 倍加碼。基本資格：家庭成員均未接受政府其他住宅相關補貼、申請人及家人均無自有住宅。2026 年起新申請案承租處須為合法住宅，排除頂樓加蓋與違章建築。受理期間 2026/1/1 上午 9 點至 2026/12/31 下午 5 點，隨到隨辦。',
  searchGroup: '住宅類',
  isTimeSensitive: false,
  applicationPeriod: '2026/1/1～2026/12/31，隨到隨辦（每年會重新公告下一年度受理期間）',
  notes:
    '社會住宅的「目前空戶/候補梯次」屬即時性資訊，本資料庫不存這類會隨時過期的內容；但主管機關、申請入口網站與基本資格門檻是穩定資訊，已在本類別另建社會住宅相關列（見下方 socialHousingRows），確保使用者至少查得到「該去哪裡查、資格門檻是什麼」，不會因為即時資料無法存檔就完全查不到這項福利。',
  eligibilityConditions: { requiresNoOwnedHome: true },
  sourceUrl: 'https://woman.udn.com/woman/story/123165/9236540',
  sourceExcerpt:
    '行政院推出的「300億元中央擴大租金補貼」2026年持續辦理，每月補助金額介於2000元至8000元不等……中央針對20～40歲單身者、結婚2年內的新婚家庭、育有未成年子女家庭及經濟或社會弱勢，提供金額加碼補助1.2-1.8倍……受理申請期間為2026/01/01上午9點至2026/12/31下午5點止。',
  lastVerifiedDate: LAST_VERIFIED_DATE,
  documents: ['租賃契約', '房屋為合法住宅之證明（非頂樓加蓋/違章建築）'],
  locations: [{ name: '內政部國土管理署 300億元中央擴大租金補貼專區', website: 'https://www.cpami.gov.tw/' }],
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
      '「臺北幸福租－民間租屋租金加碼補貼」：未滿 40 歲單身青年在中央每月 3,600 元補助上再加碼 1,000 元（合計 4,600 元）；45 歲以下已婚青年家庭中央 7,500 元再加碼 2,500 元。市府加碼採累計制，另按育有 0～12 歲已出生子女（不含胎兒）每人每月再加碼 1,000 元，子女數無上限。',
    confirmed: true,
  },
  {
    county: '新北市',
    addonDescription:
      '另立獨立方案「新北市青年租金補貼」，非中央方案的加碼，而是新北市政府自辦的青年留居租屋補助，114 年度開放時間為 2025/10/1～2026/12/31。',
    confirmed: true,
  },
]

const UNCONFIRMED_NOTE =
  '本次搜尋未查得此縣市具體地方加碼方案或金額，需依居住縣市另行洽詢當地都發局/住宅發展單位確認是否有自辦租屋補貼方案。'

const OTHER_COUNTIES = [
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
  ...CONFIRMED_ADDONS,
  ...OTHER_COUNTIES.map((county) => ({ county, addonDescription: UNCONFIRMED_NOTE, confirmed: false })),
].map((addon) => ({
  categoryNumber: 10,
  name: '租金補貼（地方加碼/自辦方案）',
  agency: `${addon.county}政府都發局/住宅發展單位`,
  county: addon.county,
  description: `在中央「300億元擴大租金補貼」之上，${addon.county}的地方加碼/自辦方案：${addon.addonDescription}`,
  searchGroup: '住宅類',
  isTimeSensitive: false,
  applicationPeriod: '常態受理（各縣市自辦方案期程可能不同，需另行確認）',
  notes: addon.confirmed ? undefined : '⚠️ ' + UNCONFIRMED_NOTE,
  eligibilityConditions: { requiresNoOwnedHome: true, counties: [addon.county] },
  sourceUrl: 'https://city.gvm.com.tw/article/129396',
  sourceExcerpt:
    '台北市推出「臺北幸福租－民間租屋租金加碼補貼」方案，針對未滿40歲、設籍且租屋於台北市的單身青年，除了能領取中央每月3600元補貼外，北市府也再加碼1000元……「新北市青年租金補貼」是新北市政府為了鼓勵青年留在新北市定居、打拼，透過租屋補助的方式減輕新北市青年的租屋負擔，114年度開放時間為2025/10/1～2026/12/31。',
  lastVerifiedDate: LAST_VERIFIED_DATE,
  locations: [{ name: `${addon.county}政府都發局/住宅發展單位` }],
}))

/**
 * 社會住宅：只存「主管機關/申請入口網站/基本資格門檻」這類穩定資訊，
 * 刻意不存「目前有哪些空戶在招租」——那是每週都會變動的即時資料，
 * 存了很快就會過期誤導使用者。查詢當下若需要「現在有沒有空房」，
 * 仍需引導使用者自行到對應入口網站查詢，或在網站上另建即時抓取機制（非本次範圍）。
 */
const SOCIAL_HOUSING_SOURCE_URL = 'https://www.socialhousing.tw/'
const SOCIAL_HOUSING_SOURCE_EXCERPT =
  '安居好室（國家住宅及都市更新中心）：申請人需為成年國民或特殊條件未成年國民，於原承租規定直轄市/縣市設籍或就學/就業，於基隆市、臺北市、新北市及桃園市無自有住宅，家庭成員年所得低於145萬元、每人每月平均所得不超過62,125元、不動產價值低於708萬元、動產價值低於471萬元。線上申請平台：https://pms.hurc.org.tw/OnlineApply。台北市：安心樂租網；新北市/桃園市：住宅及都市更新中心；台中市：共好社會住宅；台南市：台南住宅網；高雄市：社會住宅資訊網。'

const nationalSocialHousingPlatform: SeedBenefit = {
  categoryNumber: 10,
  name: '社會住宅（全國申請入口：安居好室）',
  agency: '國家住宅及都市更新中心',
  county: null,
  description:
    '「安居好室」為國家住宅及都市更新中心直接興辦社會住宅的全國查詢與申請平台，可查詢跨縣市社會住宅資訊。國家住都中心直接興辦部分的基本資格：家庭成員年所得低於 145 萬元、每人每月平均所得不超過 62,125 元、不動產價值低於 708 萬元、動產價值低於 471 萬元，且申請人及家人於承租規定縣市無自有住宅。地方政府自行興辦的社會住宅則多比照當地低收入戶/中低收入戶認定標準（見第 1 類），資格門檻依縣市略有不同。',
  searchGroup: '住宅類',
  isTimeSensitive: false,
  applicationPeriod: '常態受理，實際可申請戶數依各案場招租梯次而定（即時資訊需至入口網站查詢）',
  notes: '⚠️ 本列僅提供查詢入口與一般資格門檻，實際「目前是否有空戶可申請」仍需至安居好室或各縣市社宅平台即時查詢，資料庫不保證即時可用性。',
  eligibilityConditions: { requiresNoOwnedHome: true },
  sourceUrl: SOCIAL_HOUSING_SOURCE_URL,
  sourceExcerpt: SOCIAL_HOUSING_SOURCE_EXCERPT,
  lastVerifiedDate: LAST_VERIFIED_DATE,
  documents: ['戶籍謄本', '所得與財產證明'],
  locations: [
    { name: '安居好室（全國社會住宅申請入口）', website: 'https://www.socialhousing.tw/' },
    { name: '線上申請系統', website: 'https://pms.hurc.org.tw/OnlineApply' },
  ],
}

interface SocialHousingPortal {
  county: string
  portalName: string
  website?: string
  confirmed: boolean
}

const CONFIRMED_PORTALS: SocialHousingPortal[] = [
  { county: '臺北市', portalName: '臺北市政府安心樂租網', website: 'https://rent.thurc.org.taipei/', confirmed: true },
  { county: '新北市', portalName: '新北市住宅及都市更新中心', confirmed: true },
  { county: '桃園市', portalName: '桃園市住宅及都市更新中心', confirmed: true },
  { county: '臺中市', portalName: '臺中市共好社會住宅線上申請', website: 'https://17zu.taichung.gov.tw/portal/ApplyRent/ApplyRentList', confirmed: true },
  { county: '臺南市', portalName: '臺南住宅網', confirmed: true },
  { county: '高雄市', portalName: '高雄市社會住宅線上申請資訊網', website: 'https://shouse.kcg.gov.tw/DSB/', confirmed: true },
]

const UNCONFIRMED_PORTAL_NOTE =
  '本次搜尋未查得此縣市是否有獨立的社會住宅申請入口網站，建議優先使用全國性的「安居好室」平台查詢，或洽當地都發局/城鄉發展處確認是否有地方自辦社宅。'

const OTHER_COUNTIES_FOR_HOUSING = [
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

const socialHousingCountyRows: SeedBenefit[] = [
  ...CONFIRMED_PORTALS,
  ...OTHER_COUNTIES_FOR_HOUSING.map(
    (county): SocialHousingPortal => ({ county, portalName: '（無獨立入口，建議使用安居好室全國平台）', confirmed: false }),
  ),
].map((portal) => ({
  categoryNumber: 10,
  name: '社會住宅（地方申請入口）',
  agency: `${portal.county}政府都發局/住宅發展單位`,
  county: portal.county,
  description: portal.confirmed
    ? `${portal.county}的社會住宅可透過「${portal.portalName}」查詢與申請，另可搭配全國性「安居好室」平台跨縣市查詢。`
    : `${portal.county}：${UNCONFIRMED_PORTAL_NOTE}`,
  searchGroup: '住宅類',
  isTimeSensitive: false,
  applicationPeriod: '常態受理，實際可申請戶數依招租梯次而定（即時資訊需至入口網站查詢）',
  notes: portal.confirmed
    ? '⚠️ 目前是否有空戶可申請屬即時資訊，仍需至對應入口網站查詢，不保證資料庫資訊即時可用。'
    : '⚠️ ' + UNCONFIRMED_PORTAL_NOTE,
  eligibilityConditions: { requiresNoOwnedHome: true, counties: [portal.county] },
  sourceUrl: SOCIAL_HOUSING_SOURCE_URL,
  sourceExcerpt: SOCIAL_HOUSING_SOURCE_EXCERPT,
  lastVerifiedDate: LAST_VERIFIED_DATE,
  locations: portal.website
    ? [{ name: portal.portalName, website: portal.website }]
    : [{ name: portal.portalName || `${portal.county}政府都發局/住宅發展單位` }],
}))

export const rentSubsidySeeds: SeedBenefit[] = [
  nationalBase,
  ...countyAddonRows,
  nationalSocialHousingPlatform,
  ...socialHousingCountyRows,
]
