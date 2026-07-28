import type { SeedBenefit } from './types.js'

/** 全國統一制度，不分縣市 */
export const fscFinancialServicesSeeds: SeedBenefit[] = [
  {
    categoryNumber: 57,
    name: '金管會金融優惠與消費者保護服務',
    agency: '金融監督管理委員會',
    county: null,
    description:
      '(1) 微型保險：為經濟弱勢者提供低保費、低保額的基本人身保障，適用對象包含全年綜合所得未超過免稅額+標準扣除額+薪資特別扣除額合計數者、原住民、漁民等，投保年齡 15～75 足歲；(2) 金融消費評議中心：免費協助處理銀行/保險/證券消費爭議（不含純債務協商、投資績效爭議），不需上法院；(3) 信用卡/無擔保貸款債務協商：與銀行公會合辦的前置協商機制，避免強制執行。',
    searchGroup: '一般性優惠與便民服務',
    isTimeSensitive: false,
    applicationPeriod: '常態受理',
    notes: '金融消費評議中心不受理純債務協商案件，債務協商需另洽銀行公會的前置協商機制。',
    sourceUrl: 'https://www.ib.gov.tw/ch/home.jsp?id=210&parentpath=0%2C8',
    sourceExcerpt:
      '微型保險是指保險業為經濟弱勢者提供因應特定風險基本保障的保險商品……經濟弱勢者或特定身分者，指符合下列條件之一者：無配偶且全年綜合所得總額不超過財政部公告當年度規定之綜合所得稅免稅額、標準扣除額及薪資所得特別扣除額之合計數者或其家庭成員……投保年齡為15足歲～75歲。',
    lastVerifiedDate: '2026-07-28',
    locations: [
      {
        name: '財團法人金融消費評議中心',
        website: 'https://www.tii.org.tw/tii/comsumer/center/',
      },
      {
        name: '金融監督管理委員會保險局',
        website: 'https://www.ib.gov.tw/',
      },
    ],
  },
]
