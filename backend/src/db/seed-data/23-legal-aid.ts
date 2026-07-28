import type { SeedBenefit } from './types.js'

/** 全國統一制度，不分縣市（現場法律諮詢無資格限制，訴訟扶助才需財力審查） */
export const legalAidSeeds: SeedBenefit[] = [
  {
    categoryNumber: 23,
    name: '法律扶助（免費法律諮詢/訴訟扶助）',
    agency: '財團法人法律扶助基金會',
    county: null,
    description:
      '現場法律諮詢：任何人皆可申請，不需財力或案情審查，每次面談 20 分鐘，完全免費（費用由法扶基金會負擔律師諮詢費），需攜帶身分證件及相關案件資料。訴訟扶助（律師代理出庭）：需通過財力與案情雙軌審查，非任何人皆可申請。',
    searchGroup: '一般性優惠與便民服務',
    isTimeSensitive: false,
    applicationPeriod: '常態受理',
    notes: '常見誤解是「一定要低收入戶才能用」——電話/現場法律諮詢沒有身分限制，只有委任律師出庭的訴訟扶助才需要財力審查。',
    sourceUrl: 'https://www.laf.org.tw/service-legal-advice/1',
    sourceExcerpt:
      'Anyone in Taiwan can use the foundation\'s legal consultation service without needing to verify your financial situation or case details……Each consultation is limited to 20 minutes of face-to-face consultation with a professional lawyer……the consultation is completely free. For formal legal representation and court cases, applicants must pass a dual-track review examining both financial capacity and case merits.',
    lastVerifiedDate: '2026-07-28',
    documents: ['身分證件', '相關案件資料'],
    locations: [
      {
        name: '財團法人法律扶助基金會',
        phone: '412-8518',
        website: 'https://www.laf.org.tw/',
      },
    ],
  },
]
