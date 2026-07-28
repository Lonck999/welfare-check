import type { SeedBenefit } from './types.js'

/** 全國統一制度，不分縣市（低收入/中低收入戶部分由地方政府執行，制度依據為中央法規） */
export const newImmigrantFundSeeds: SeedBenefit[] = [
  {
    categoryNumber: 42,
    name: '新住民發展基金補助',
    agency: '內政部移民署',
    county: null,
    description:
      '服務對象為配偶屬外國人、無國籍人、大陸地區人民及港澳居民（含已入籍仍有輔導需要者）及其子女與同住親屬，提供生活適應輔導、通譯人才培訓、子女教育與獎助學金等服務。「設籍前新住民社會救助計畫」則由地方政府針對轄內核定列冊低收入戶、中低收入戶之設籍前新住民，提供生活扶助、醫療補助、急難救助等項目。',
    searchGroup: '特殊身分族群類',
    isTimeSensitive: false,
    applicationPeriod: '常態受理',
    notes: '⚠️ 具體補助金額本次搜尋未查得明確數字，需洽移民署或戶籍地社會局確認最新補助基準。',
    eligibilityConditions: { requiredIdentities: ['新住民'] },
    sourceUrl: 'https://www.immigration.gov.tw/5385/7445/7451/7508/',
    sourceExcerpt:
      '新住民發展基金的目的是結合各級政府及民間團體力量，加強協助臺灣地區人民之配偶為外國人、無國籍人、大陸地區人民及香港、澳門居民適應臺灣社會……服務對象包括臺灣地區人民之配偶為未入籍之外國人、無國籍人、大陸地區人民及香港或澳門居民，或已入籍為我國國民而仍有照顧輔導需要者，以及前述服務對象之子女及共同生活之親屬。',
    lastVerifiedDate: '2026-07-28',
    locations: [
      { name: '內政部移民署', website: 'https://www.immigration.gov.tw/' },
      { name: '戶籍地政府社會局（設籍前新住民社會救助）' },
    ],
  },
]
