import type { SeedBenefit } from './types.js'

/** 全國統一資格與基準，不分縣市（各地社會局為執行窗口，實際核定金額仍以中央標準為準） */
export const earlyInterventionSeeds: SeedBenefit[] = [
  {
    categoryNumber: 47,
    name: '發展遲緩兒童早期療育補助',
    agency: '衛生福利部社會及家庭署',
    county: null,
    description:
      '6 歲以下兒童（含應屆小一新生、通過緩讀尚未入學者），領有身心障礙手冊證明，或經聯合評估醫院開立診斷證明/綜合評估報告書認定為疑似發展遲緩者，可申請療育訓練費與交通補助費：每人每月最高補助 4,000 元，低收入戶每人每月最高補助 6,000 元。',
    searchGroup: '時效性最高項目',
    isTimeSensitive: true,
    applicationPeriod: '常態受理，但療育有時效性，建議及早申請評估',
    notes: '若已知有發展遲緩疑似情形或正在評估中，應優先確認此項，早期療育有黃金治療期限制。',
    eligibilityConditions: { requiresChildUnder: 6, requiredFlags: ['developmental_delay_suspected_or_diagnosed'] },
    sourceUrl: 'https://dowcd.tycg.gov.tw/News_Content.aspx?n=16390&s=1178054',
    sourceExcerpt:
      '欲申請發展遲緩兒童療育費用補助，需符合以下兩項資格：六歲以下兒童（包括應屆小一新生以及通過緩讀尚未入學就讀者），以及具身心障礙兒童或疑似發展遲緩兒童身份……補助項目包括療育訓練費與交通補助費。每人每月最高補助金額為新臺幣4,000元整，低收入戶每人每月最高補助金額為新臺幣6,000元整。',
    lastVerifiedDate: '2026-07-28',
    documents: ['身心障礙手冊證明或聯合評估醫院診斷證明/綜合評估報告書'],
    locations: [{ name: '戶籍地政府社會局（早期療育通報轉介中心）' }],
  },
]
