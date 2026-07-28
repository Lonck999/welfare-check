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
    '⚠️ 社會住宅（含候補戶招租、預告公告）因涉及各縣市實際釋出戶數與梯次，屬即時性資訊，無法以固定資料庫欄位呈現，仍需在使用者查詢當下即時 WebSearch「{縣市} 社會住宅 招租公告」等關鍵字，不適合僅查資料庫。',
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

export const rentSubsidySeeds: SeedBenefit[] = [nationalBase, ...countyAddonRows]
