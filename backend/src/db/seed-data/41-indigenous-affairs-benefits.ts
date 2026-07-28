import type { SeedBenefit } from './types.js'

/** 全國統一制度，不分縣市 */
export const indigenousAffairsBenefitsSeeds: SeedBenefit[] = [
  {
    categoryNumber: 41,
    name: '原住民族委員會補助（創業貸款/獎助學金/急難救助）',
    agency: '原住民族委員會',
    county: null,
    description:
      '(1) 原住民創業貸款：18～65 歲原住民、無信用不良紀錄，申請前 3 年內曾參加創業輔導課程 20 小時或 2 學分以上，開辦費/準備金最高 200 萬元，農林漁牧業週轉金最高 500 萬元或資本支出最高 5,000 萬元；(2) 大專校院原住民學生獎助學金：前一學期成績 70 分以上可申請獎學金每學期 3.2 萬元，60 分以上可申請一般助學金每學期 2 萬元，低收入戶學生每學期 3 萬元、中低收入戶學生每學期 2 萬元。',
    searchGroup: '特殊身分族群類',
    isTimeSensitive: false,
    applicationPeriod: '創業貸款常態受理；獎助學金每學期開學後受理',
    notes: '⚠️ 急難救助的具體申請資格與金額本次搜尋未查得明確數字，需洽原民會或戶籍地原住民族事務相關單位確認。',
    eligibilityConditions: { requiredIdentities: ['原住民'] },
    sourceUrl: 'https://cipgrant.fju.edu.tw/',
    sourceExcerpt:
      '前一學期學業成績達七十分以上者得申請獎學金新臺幣三萬二千元，成績達六十分以上者得申請一般助學金每學期新臺幣二萬元，低收入戶或中低收入戶學生則可申請低收入戶助學金每學期新臺幣三萬元或中低收入戶助學金每學期新臺幣二萬元。',
    lastVerifiedDate: '2026-07-28',
    documents: ['原住民身分證明', '在學證明/成績單（獎助學金）', '創業輔導課程證明（創業貸款）'],
    locations: [
      { name: '原住民族委員會', website: 'https://www.cip.gov.tw/' },
      { name: '原住民族委員會大專校院獎助學金申請系統', website: 'https://cipgrant.fju.edu.tw/' },
    ],
  },
]
