import type { SeedBenefit } from './types.js'

/** 台電/台水為全國性事業機構，減免規則全國一致，不分縣市 */
export const utilityFeeReductionSeeds: SeedBenefit[] = [
  {
    categoryNumber: 20,
    name: '水電費減免（中低收入戶）',
    agency: '台灣電力公司／台灣自來水公司',
    county: null,
    description:
      '取得低收入戶/中低收入戶證明後，可向台電申請每月用電 110 度以下免收基本電費；向台水申請減免基本水費。多數情況由戶籍地公所核定低收入戶資格後自動通報台電/台水辦理減免，亦可自行持證明至台電/台水服務中心申請。瓦斯費補助則因各縣市/瓦斯行而異，需另行查證。',
    searchGroup: '一般性優惠與便民服務',
    isTimeSensitive: false,
    applicationPeriod: '常態受理，取得低收入戶/中低收入戶資格後即可申請',
    notes: '⚠️ 瓦斯費補助非台灣中油/台電等全國性事業統一辦理，各縣市及民營瓦斯行規定不同，需另行依居住縣市查證。',
    eligibilityConditions: { incomeThreshold: 'mid_low_income' },
    sourceUrl: 'https://getgrant.tw/grants/mohw-lowincome-utility-reduce',
    sourceExcerpt:
      '各地方政府及台電、台水公司提供低收入戶水電費減免，台電每月用電110度以下免收基本電費，台水減免基本水費……申請流程包括：至戶籍地公所取得低收入戶證明，然後至台電/台水服務中心申請減免，或公所代為通報自動減免。申請洽詢可撥打1957。',
    lastVerifiedDate: '2026-07-28',
    documents: ['低收入戶/中低收入戶證明'],
    locations: [
      { name: '台灣電力公司', website: 'https://www.taipower.com.tw/' },
      { name: '台灣自來水公司', website: 'https://www.water.gov.tw/' },
      { name: '1957 福利諮詢專線', phone: '1957' },
    ],
  },
]
