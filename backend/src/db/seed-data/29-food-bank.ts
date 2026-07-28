import type { SeedBenefit } from './types.js'

const SOURCE_URL = 'https://www.society.taichung.gov.tw/136190/post'
const SOURCE_EXCERPT =
  '以台中市為例，食物銀行受助戶資格需為實際居住於該市的家戶，並符合下列情形之一：主要負擔家計者因急難事由，且有就讀高中職以下子女，生活陷困；領有政府社會福利補助，生活仍陷困；或其他因素經社工員評估確實急需食物銀行濟助。'
const LAST_VERIFIED_DATE = '2026-07-28'

/** 食物銀行由地方政府社會局各自設立與核定資格，全國無統一標準 */
const nationalBase: SeedBenefit = {
  categoryNumber: 29,
  name: '食物銀行/實物給付補助（全國概況）',
  agency: '各縣市政府社會局',
  county: null,
  description:
    '食物銀行由地方政府社會局各自設立與核定發放對象，並非中央統一制度。以台中市為例：受助戶須實際居住於該市，並符合以下情形之一——主要負擔家計者因急難事由且有就讀高中職以下子女、生活陷困；領有政府社會福利補助但生活仍陷困；或經社工員評估確實急需濟助。多數縣市有類似機制，但認定標準與物資內容因地而異。',
  searchGroup: '一般性優惠與便民服務',
  isTimeSensitive: false,
  applicationPeriod: '常態受理，經社工評估後核定',
  eligibilityConditions: { requiredFlags: ['acute_hardship'] },
  sourceUrl: SOURCE_URL,
  sourceExcerpt: SOURCE_EXCERPT,
  lastVerifiedDate: LAST_VERIFIED_DATE,
  documents: ['低收入戶/中低收入戶證明或社工評估報告'],
  locations: [{ name: '戶籍地政府社會局' }],
}

const CONFIRMED_TAICHUNG: SeedBenefit = {
  categoryNumber: 29,
  name: '食物銀行（地方明細）',
  agency: '臺中市政府社會局',
  county: '臺中市',
  description:
    '受助戶須實際居住於臺中市，並符合以下情形之一：主要負擔家計者因急難事由且有就讀高中職以下子女、生活陷困；領有政府社會福利補助但生活仍陷困；或經社工員評估確實急需食物銀行濟助。',
  searchGroup: '一般性優惠與便民服務',
  isTimeSensitive: false,
  applicationPeriod: '常態受理，經社工評估後核定',
  eligibilityConditions: { requiredFlags: ['acute_hardship'], counties: ['臺中市'] },
  sourceUrl: SOURCE_URL,
  sourceExcerpt: SOURCE_EXCERPT,
  lastVerifiedDate: LAST_VERIFIED_DATE,
  documents: ['低收入戶/中低收入戶證明或社工評估報告'],
  locations: [{ name: '臺中市政府社會局', website: 'https://www.society.taichung.gov.tw/' }],
}

const OTHER_COUNTIES = [
  '臺北市',
  '新北市',
  '桃園市',
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

const UNCONFIRMED_NOTE = '本次搜尋未查得此縣市食物銀行的具體受助資格與物資內容，需依居住縣市另行洽詢社會局確認。'

const countyRows: SeedBenefit[] = OTHER_COUNTIES.map((county) => ({
  categoryNumber: 29,
  name: '食物銀行（地方明細）',
  agency: `${county}政府社會局`,
  county,
  description: `${county}的食物銀行方案：${UNCONFIRMED_NOTE}`,
  searchGroup: '一般性優惠與便民服務',
  isTimeSensitive: false,
  applicationPeriod: '常態受理，經社工評估後核定',
  notes: '⚠️ ' + UNCONFIRMED_NOTE,
  eligibilityConditions: { requiredFlags: ['acute_hardship'], counties: [county] },
  sourceUrl: SOURCE_URL,
  sourceExcerpt: SOURCE_EXCERPT,
  lastVerifiedDate: LAST_VERIFIED_DATE,
  locations: [{ name: `${county}政府社會局` }],
}))

export const foodBankSeeds: SeedBenefit[] = [nationalBase, CONFIRMED_TAICHUNG, ...countyRows]
