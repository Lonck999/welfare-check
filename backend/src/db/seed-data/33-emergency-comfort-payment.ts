import type { SeedBenefit } from './types.js'

const LAST_VERIFIED_DATE = '2026-07-28'
const SOURCE_URL = 'https://eysc.ey.gov.tw/Page/DAB11F5DBDC11168/3ccb55f0-60d5-4399-a8da-431843d17c93'
const SOURCE_EXCERPT =
  '急難救助的申請條件包括戶內人口死亡無力殮葬、遭受意外傷害或罹患重病致生活困難、負家庭主要生計責任者失業或其他原因無法工作等情形……縣市政府急難慰問金與中央急難救助（第4類）不同制度：門檻更低、核發更快，兩者可同時申請，惟具體門檻與金額由各地方政府自行訂定，本次搜尋未查得逐縣市清單。'

/** 縣市政府急難慰問金由地方政府各自訂定門檻與金額，全國無統一標準；本次搜尋未查得逐縣市確切數字 */
const nationalBase: SeedBenefit = {
  categoryNumber: 33,
  name: '縣市政府急難慰問金（全國概況）',
  agency: '各縣市政府社會處/局',
  county: null,
  description:
    '遭遇火災、重病、失業等突發困境時可向戶籍地政府申請急難慰問金，與第 4 類「急難救助」（中央急難紓困實施方案）為不同制度：門檻更低、核發更快，兩者可同時申請。惟具體申請門檻與金額由各地方政府自行訂定，本次搜尋未查得可信賴的逐縣市清單。',
  searchGroup: '時效性最高項目',
  isTimeSensitive: true,
  applicationPeriod: '常態受理，急迫個案通常可較快核發',
  notes: '⚠️ 搜尋過程中查到的是「端午節/年節慰問金」（發放對象通常為列冊低收入戶的節日性現金，如台北市單口低收入戶 1,500 元、其餘 2,000 元，高雄市第三類低收入戶 2,313 元），這與「急難慰問金」（因應突發困境的急難性質）是不同的兩種現金補助，不可混為一談。年節慰問金屬於本次未涵蓋的潛在新類別，建議未來另行查證後補入 SKILL.md。',
  eligibilityConditions: { requiredFlags: ['acute_hardship'] },
  sourceUrl: SOURCE_URL,
  sourceExcerpt: SOURCE_EXCERPT,
  lastVerifiedDate: LAST_VERIFIED_DATE,
  documents: ['申請書', '相關證明文件（依情況而定）'],
  locations: [{ name: '戶籍地政府社會處/局' }],
}

const UNCONFIRMED_NOTE = '本次搜尋未查得此縣市急難慰問金的具體申請門檻與金額，需依居住縣市另行洽詢社會處/局確認。'

const ALL_COUNTIES = [
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

const countyRows: SeedBenefit[] = ALL_COUNTIES.map((county) => ({
  categoryNumber: 33,
  name: '縣市政府急難慰問金（地方明細）',
  agency: `${county}政府社會處/局`,
  county,
  description: `${county}的急難慰問金方案：${UNCONFIRMED_NOTE}`,
  searchGroup: '時效性最高項目',
  isTimeSensitive: true,
  applicationPeriod: '常態受理',
  notes: '⚠️ ' + UNCONFIRMED_NOTE,
  eligibilityConditions: { requiredFlags: ['acute_hardship'], counties: [county] },
  sourceUrl: SOURCE_URL,
  sourceExcerpt: SOURCE_EXCERPT,
  lastVerifiedDate: LAST_VERIFIED_DATE,
  locations: [{ name: `${county}政府社會處/局` }],
}))

export const emergencyComfortPaymentSeeds: SeedBenefit[] = [nationalBase, ...countyRows]
