import type { SeedBenefit } from './types.js'

/** 全國統一制度，不分縣市 */
export const sportsAdministrationSubsidySeeds: SeedBenefit[] = [
  {
    categoryNumber: 53,
    name: '教育部體育署補助（運動幣/運動i台灣）',
    agency: '教育部體育署',
    county: null,
    description:
      '「運動幣」：政府補助 500 元運動消費金，可於合作店家使用，採登記抽籤制。「運動 i 臺灣 2.0 計畫」執行期程 111～116 年（2022～2027），推展縣市體育活動、地方特色運動、優化運動友善服務，主要補助對象為地方政府與全國性運動團體（非個人直接申請）。',
    searchGroup: '一般性優惠與便民服務',
    isTimeSensitive: true,
    applicationPeriod: '運動幣依當年度登記抽籤期程受理（非常態開放）',
    notes: '⚠️ 運動幣為抽籤制，中籤與否及每年開放期程需依教育部體育署/i運動資訊平台當年度公告確認，不保證每次登記皆可領取。',
    eligibilityConditions: { requiredFlags: ['general_public'] },
    sourceUrl: 'https://mrmad.com.tw/2026-sports-coin-registration',
    sourceExcerpt:
      '2026運動幣懶人包｜500元怎麼領？中籤結果出爐！怎麼用、使用時間、合作店家一次看……「運動i臺灣2.0計畫」執行期程為111年1月1日至116年12月31日（2022-2027年），施政方向包括推展縣市體育活動、強化質精量足運動專業人力、發展地方特色運動、優化運動友善服務。',
    lastVerifiedDate: '2026-07-28',
    documents: ['身分證件（登記用）'],
    locations: [{ name: 'i運動資訊平台', website: 'https://isports.sa.gov.tw/' }],
  },
]
