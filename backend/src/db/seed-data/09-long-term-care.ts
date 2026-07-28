import type { SeedBenefit } from './types.js'

/** 中央長照制度，全國統一標準，不分縣市 */
export const longTermCareSeeds: SeedBenefit[] = [
  {
    categoryNumber: 9,
    name: '長期照顧（長照3.0）',
    agency: '衛生福利部',
    county: null,
    description:
      '長照 3.0 自 2025 年 9 月起分階段施行至 2026 年，擴大服務對象：65 歲以上失能者、55 歲以上失能原住民、50 歲以上失智症者（2026 起放寬至 49 歲以下）、各年齡層身心障礙者。補助項目依失能等級：照顧及專業服務每月補助 10,020～36,180 元；喘息服務依等級每年補助 32,340～48,510 元；輔具及居家無障礙環境改善每 3 年最高補助 40,000 元；交通接送服務依居住地分區每次 1,680～2,400 元不等。',
    searchGroup: '醫療與健康類',
    isTimeSensitive: false,
    applicationPeriod: '常態受理',
    eligibilityConditions: { requiredFlags: ['has_disability_or_dementia_member'] },
    sourceUrl: 'https://www.cw.com.tw/article/5138682',
    sourceExcerpt:
      '長照補助不限年齡，但需符合下列其中一種資格：65歲以上失能者、55歲以上失能原住民、50歲以上失智症者（2026起放寬至49歲以下）、各年齡層身心障礙者……照顧及專業服務每月補助10,020元至36,180元、喘息服務依等級每年補助32,340元至48,510元、輔具及居家無障礙環境改善每3年最高補助40,000元、交通及接送服務根據居住地分區為1,680元至2,400元不等。',
    lastVerifiedDate: '2026-07-28',
    documents: ['身心障礙證明/失能評估文件（如適用）'],
    locations: [{ name: '1966 長照專線', phone: '1966' }, { name: '衛生福利部', website: 'https://www.mohw.gov.tw/' }],
  },
]
