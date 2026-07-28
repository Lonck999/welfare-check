import type { SeedBenefit } from './types.js'

const LAST_VERIFIED_DATE = '2026-07-28'
const SOURCE_URL = 'https://www.businesstoday.com.tw/article/category/183030/post/202607200021/'
const SOURCE_EXCERPT =
  '2026年重陽敬老禮金：統計22縣市，最少600元起跳，有的是1500元甚至5000元，最大方的就屬新竹縣，65歲以上長輩，每人發給敬老禮金1萬元。以六都來看，桃園市最大方，可領到2500元，台中市則是以2000元居次……雙北敬老卡點數已於今年7月同步從480點調升至600點……新竹市從800點提升至1200點，新竹縣則從500點加倍至1000點。台東縣每月發放高達1500點（1點1元）居全台之冠。'

/** 重陽禮金、假牙補助、敬老卡點數皆為地方政府自辦，因縣市而異，非全國統一 */
const nationalBase: SeedBenefit = {
  categoryNumber: 18,
  name: '老人其他福利（重陽禮金/敬老卡，全國概況）',
  agency: '衛生福利部（各縣市政府自辦）',
  county: null,
  description:
    '65 歲以上長者可領取地方政府自辦的重陽敬老禮金（每年農曆 9 月 9 日重陽節前後發放）與敬老卡（乘車點數，多為 1 點折抵 1 元，可用於公車/捷運/台鐵/計程車等）。金額與點數完全依縣市而定，最低約 600 元起，最高可達 1 萬元（新竹縣）；敬老卡點數多數縣市 480～1,200 點不等，臺東縣每月最高發放 1,500 點居冠。假牙補助多數縣市有提供中低收入老人假牙裝置補助，惟具體金額本次未逐一查得。',
  searchGroup: '現金與生活補助類',
  isTimeSensitive: true,
  applicationPeriod: '重陽禮金通常於每年重陽節（農曆 9 月 9 日）前後發放；敬老卡點數多為每年或每月定期核發',
  eligibilityConditions: { ageMin: 65 },
  sourceUrl: SOURCE_URL,
  sourceExcerpt: SOURCE_EXCERPT,
  lastVerifiedDate: LAST_VERIFIED_DATE,
  documents: ['身分證', '戶籍證明'],
  locations: [{ name: '戶籍地政府社會局' }],
}

interface CountyAddon {
  county: string
  addonDescription: string
  confirmed: boolean
}

const CONFIRMED_ADDONS: CountyAddon[] = [
  { county: '新竹縣', addonDescription: '重陽敬老禮金每人 1 萬元（全台最高），敬老卡點數 1,000 點。', confirmed: true },
  { county: '桃園市', addonDescription: '重陽敬老禮金 2,500 元（六都最高）。', confirmed: true },
  { county: '臺中市', addonDescription: '重陽敬老禮金 2,000 元。', confirmed: true },
  { county: '臺北市', addonDescription: '敬老卡點數 600 點（2026 年 7 月起自 480 點調升）。', confirmed: true },
  { county: '新北市', addonDescription: '敬老卡點數 600 點（2026 年 7 月起自 480 點調升）。', confirmed: true },
  { county: '新竹市', addonDescription: '敬老卡點數 1,200 點（2026 年 10 月起自 800 點調升）。', confirmed: true },
  { county: '臺東縣', addonDescription: '敬老卡點數每月 1,500 點（1 點 1 元），為全台最高。', confirmed: true },
]

const UNCONFIRMED_NOTE =
  '本次搜尋未查得此縣市具體重陽敬老禮金金額或敬老卡點數，全國最低約 600 元起跳，需依居住縣市另行查證社會局公告。'

const OTHER_COUNTIES = [
  '臺南市',
  '高雄市',
  '基隆市',
  '嘉義市',
  '宜蘭縣',
  '苗栗縣',
  '彰化縣',
  '南投縣',
  '雲林縣',
  '嘉義縣',
  '屏東縣',
  '花蓮縣',
  '澎湖縣',
  '金門縣',
  '連江縣',
]

const countyAddonRows: SeedBenefit[] = [
  ...CONFIRMED_ADDONS,
  ...OTHER_COUNTIES.map((county) => ({ county, addonDescription: UNCONFIRMED_NOTE, confirmed: false })),
].map((addon) => ({
  categoryNumber: 18,
  name: '老人其他福利（重陽禮金/敬老卡，地方明細）',
  agency: `${addon.county}政府社會局`,
  county: addon.county,
  description: `${addon.county}的重陽禮金/敬老卡情形：${addon.addonDescription}`,
  searchGroup: '現金與生活補助類',
  isTimeSensitive: true,
  applicationPeriod: '重陽禮金約於每年重陽節前後發放，敬老卡點數依縣市規定核發週期不同',
  notes: addon.confirmed ? undefined : '⚠️ ' + UNCONFIRMED_NOTE,
  eligibilityConditions: { ageMin: 65, counties: [addon.county] },
  sourceUrl: SOURCE_URL,
  sourceExcerpt: SOURCE_EXCERPT,
  lastVerifiedDate: LAST_VERIFIED_DATE,
  locations: [{ name: `${addon.county}政府社會局` }],
}))

/** 假牙補助：衛福部中央補助已退場，改為各縣市自訂方案，因縣市而異 */
const DENTURE_SOURCE_URL = 'https://health.businessweekly.com.tw/article/ARTL003018345'
const DENTURE_SOURCE_EXCERPT =
  '2026假牙補助：衛福部補助退場，全台各縣市最新方案……假牙補助的常見申請資格包括65歲以上長者或55歲以上原住民，且需符合低收入戶、中低收入戶、領有身障證明、領老人生活津貼等條件之一。上下顎全口活動假牙最高可達55,000元（第1、2款對象）或44,000元（其他弱勢對象）；低收入戶65歲以上全口義齒最高40,000元；中低收入戶最高20,000元。申請流程原則為「先申請、後製作」，需攜帶身分證、健保卡及印章至合約牙醫診所進行口腔篩檢。'

const dentureNationalNote: SeedBenefit = {
  categoryNumber: 18,
  name: '中低收入老人假牙補助（全國概況）',
  agency: '各縣市政府衛生局/社會局',
  county: null,
  description:
    '衛福部中央統一補助已退場，改由各縣市政府自訂方案。常見申請資格：65 歲以上長者或 55 歲以上原住民，且符合低收入戶/中低收入戶/領有身障證明/領老人生活津貼其中之一。常見金額級距：全口活動假牙最高 55,000 元（第 1、2 款對象）或 44,000 元（其他弱勢對象）；低收入戶 65 歲以上全口義齒最高 40,000 元、中低收入戶最高 20,000 元，惟各縣市實際金額與資格門檻不同。申請原則為「先申請、後製作」，需攜帶身分證、健保卡及印章至合約牙醫診所口腔篩檢後才能製作假牙。',
  searchGroup: '現金與生活補助類',
  isTimeSensitive: false,
  applicationPeriod: '常態受理，須先申請核准後才能至合約診所製作假牙',
  eligibilityConditions: { ageMin: 65 },
  sourceUrl: DENTURE_SOURCE_URL,
  sourceExcerpt: DENTURE_SOURCE_EXCERPT,
  lastVerifiedDate: LAST_VERIFIED_DATE,
  documents: ['身分證', '健保卡', '印章', '低收入戶/中低收入戶/身障證明（依資格別）'],
  locations: [{ name: '戶籍地政府衛生局/社會局' }, { name: '合約牙醫診所' }],
}

const DENTURE_UNCONFIRMED_NOTE = '本次搜尋未查得此縣市假牙補助的具體金額與資格門檻，需依居住縣市另行洽詢衛生局/社會局確認。'

const ALL_22_COUNTIES = [
  '臺北市',
  '新北市',
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

const dentureCountyRows: SeedBenefit[] = ALL_22_COUNTIES.map((county) => ({
  categoryNumber: 18,
  name: '中低收入老人假牙補助（地方明細）',
  agency: `${county}政府衛生局/社會局`,
  county,
  description: `${county}的假牙補助方案：${DENTURE_UNCONFIRMED_NOTE}`,
  searchGroup: '現金與生活補助類',
  isTimeSensitive: false,
  applicationPeriod: '常態受理，須先申請核准後才能至合約診所製作假牙',
  notes: '⚠️ ' + DENTURE_UNCONFIRMED_NOTE,
  eligibilityConditions: { ageMin: 65, counties: [county] },
  sourceUrl: DENTURE_SOURCE_URL,
  sourceExcerpt: DENTURE_SOURCE_EXCERPT,
  lastVerifiedDate: LAST_VERIFIED_DATE,
  locations: [{ name: `${county}政府衛生局/社會局` }],
}))

/** 身心障礙者愛心卡乘車優惠：因縣市而異，比照敬老卡點數制 */
const LOVE_CARD_SOURCE_URL = 'https://www.twneed.org/post/28.html'
const LOVE_CARD_SOURCE_EXCERPT =
  '多數縣市提供陪同身心障礙者搭乘大眾運輸時，陪伴者可享半價優惠（由陪伴卡扣點或自費儲值）。2026全台各縣市提供不同額度的月點數補助，台東每月1,500點最高、台中1,000點、雙北加碼至600點。'

const loveCardNationalNote: SeedBenefit = {
  categoryNumber: 18,
  name: '身心障礙者愛心卡乘車優惠（全國概況）',
  agency: '各縣市政府社會局',
  county: null,
  description:
    '領有身心障礙手冊/證明者可申請愛心卡，搭乘公車/捷運/台鐵享優惠或免費；陪同者（陪伴卡）搭乘時多可享半價優惠（由點數扣抵或自費儲值）。點數額度依縣市而定，比照敬老卡制度，臺東縣每月最高 1,500 點、臺中市 1,000 點、雙北 600 點。',
  searchGroup: '現金與生活補助類',
  isTimeSensitive: false,
  applicationPeriod: '常態受理',
  eligibilityConditions: { requiredFlags: ['disability_certificate'] },
  sourceUrl: LOVE_CARD_SOURCE_URL,
  sourceExcerpt: LOVE_CARD_SOURCE_EXCERPT,
  lastVerifiedDate: LAST_VERIFIED_DATE,
  documents: ['身心障礙手冊或證明'],
  locations: [{ name: '戶籍地政府社會局' }],
}

const LOVE_CARD_CONFIRMED: CountyAddon[] = [
  { county: '臺東縣', addonDescription: '愛心卡每月最高 1,500 點（比照敬老卡制度）。', confirmed: true },
  { county: '臺中市', addonDescription: '愛心卡每月 1,000 點。', confirmed: true },
  { county: '臺北市', addonDescription: '愛心卡每月 600 點。', confirmed: true },
  { county: '新北市', addonDescription: '愛心卡每月 600 點。', confirmed: true },
]

const LOVE_CARD_UNCONFIRMED_NOTE = '本次搜尋未查得此縣市愛心卡具體點數額度，需依居住縣市另行查證社會局公告。'

const loveCardOtherCounties = ALL_22_COUNTIES.filter(
  (c) => !LOVE_CARD_CONFIRMED.some((addon) => addon.county === c),
)

const loveCardCountyRows: SeedBenefit[] = [
  ...LOVE_CARD_CONFIRMED,
  ...loveCardOtherCounties.map((county) => ({ county, addonDescription: LOVE_CARD_UNCONFIRMED_NOTE, confirmed: false })),
].map((addon) => ({
  categoryNumber: 18,
  name: '身心障礙者愛心卡乘車優惠（地方明細）',
  agency: `${addon.county}政府社會局`,
  county: addon.county,
  description: `${addon.county}的愛心卡情形：${addon.addonDescription}`,
  searchGroup: '現金與生活補助類',
  isTimeSensitive: false,
  applicationPeriod: '常態受理',
  notes: addon.confirmed ? undefined : '⚠️ ' + LOVE_CARD_UNCONFIRMED_NOTE,
  eligibilityConditions: { requiredFlags: ['disability_certificate'], counties: [addon.county] },
  sourceUrl: LOVE_CARD_SOURCE_URL,
  sourceExcerpt: LOVE_CARD_SOURCE_EXCERPT,
  lastVerifiedDate: LAST_VERIFIED_DATE,
  locations: [{ name: `${addon.county}政府社會局` }],
}))

export const elderlyOtherBenefitsSeeds: SeedBenefit[] = [
  nationalBase,
  ...countyAddonRows,
  dentureNationalNote,
  ...dentureCountyRows,
  loveCardNationalNote,
  ...loveCardCountyRows,
]
