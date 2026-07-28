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

export const elderlyOtherBenefitsSeeds: SeedBenefit[] = [nationalBase, ...countyAddonRows]
