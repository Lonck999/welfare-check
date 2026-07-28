import type { SeedBenefit } from './types.js'

/**
 * 115 年度（2026年）各直轄市/縣市最低生活費及不動產限額。
 * 來源：臺北市政府社會局公告（與衛福部社會救助及社工司公告一致，全國僅分 8 組數值，
 * 6 個直轄市各自一組＋臺灣省一組（多數縣市共用）＋福建省一組（金門、連江）），
 * 非每個縣市都有獨立數字，此為官方制度本身如此，並非本專案簡化。
 */
const SOURCE_URL = 'https://service.docms.gov.taipei/attachments/115-income-limit.pdf'
const SOURCE_EXCERPT =
  '※各直轄市、縣(市)最低生活費及不動產限額※ 115 年度(1/1~12/31)：臺北市 20,744／837萬、新北市 17,750／472萬、桃園市 17,186／470萬、臺中市 16,431／386萬、臺南市 15,515／385萬、高雄市 16,970／397萬、臺灣省 15,515／385萬、福建省(金門縣、連江縣) 15,173／307萬'
const LAST_VERIFIED_DATE = '2026-07-28'

interface Group {
  counties: string[]
  minLivingExpense: number
  realEstateLimit: number
}

const GROUPS: Group[] = [
  { counties: ['臺北市'], minLivingExpense: 20_744, realEstateLimit: 8_370_000 },
  { counties: ['新北市'], minLivingExpense: 17_750, realEstateLimit: 4_720_000 },
  { counties: ['桃園市'], minLivingExpense: 17_186, realEstateLimit: 4_700_000 },
  { counties: ['臺中市'], minLivingExpense: 16_431, realEstateLimit: 3_860_000 },
  { counties: ['臺南市'], minLivingExpense: 15_515, realEstateLimit: 3_850_000 },
  { counties: ['高雄市'], minLivingExpense: 16_970, realEstateLimit: 3_970_000 },
  {
    // 臺灣省：其餘省轄市／縣，皆適用同一數值
    counties: [
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
    ],
    minLivingExpense: 15_515,
    realEstateLimit: 3_850_000,
  },
  {
    // 福建省：金門、連江
    counties: ['金門縣', '連江縣'],
    minLivingExpense: 15_173,
    realEstateLimit: 3_070_000,
  },
]

export const lowIncomeThresholdSeeds: SeedBenefit[] = GROUPS.flatMap((group) =>
  group.counties.map(
    (county): SeedBenefit => ({
      categoryNumber: 1,
      name: '低收入戶 / 中低收入戶認定',
      agency: `${county}政府社會局`,
      county,
      description:
        `115 年度（2026年）${county}最低生活費為每人每月 ${group.minLivingExpense.toLocaleString()} 元，` +
        `家庭不動產限額 ${(group.realEstateLimit / 10_000).toLocaleString()} 萬元。` +
        `應計算人口人均月所得 ≦ 最低生活費 → 低收入戶；≦ 最低生活費 × 1.5 → 中低收入戶。`,
      searchGroup: '資格認定基礎',
      isTimeSensitive: false,
      applicationPeriod: '常態受理',
      notes: '動產（存款/有價證券/車輛）門檻另計，各縣市規定略有差異，需另行查詢當地公告。',
      eligibilityConditions: {
        counties: [county],
        referenceData: {
          minLivingExpense: group.minLivingExpense,
          realEstateLimit: group.realEstateLimit,
        },
      },
      sourceUrl: SOURCE_URL,
      sourceExcerpt: SOURCE_EXCERPT,
      lastVerifiedDate: LAST_VERIFIED_DATE,
      locations: [
        {
          name: `${county}政府社會局`,
          website: 'https://dep.mohw.gov.tw/dosaasw/',
        },
      ],
    }),
  ),
)
