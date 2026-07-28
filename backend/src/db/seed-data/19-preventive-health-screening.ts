import type { SeedBenefit } from './types.js'

/** 全國統一制度，不分縣市 */
export const preventiveHealthScreeningSeeds: SeedBenefit[] = [
  {
    categoryNumber: 19,
    name: '健保預防保健服務（四癌篩檢/成人健檢/老人健檢/流感疫苗）',
    agency: '衛生福利部國民健康署',
    county: null,
    description:
      '(1) 成人預防保健：2025 年起放寬至 30 歲以上、具中華民國國籍與健保身分者免費健檢，頻率依年齡層而異；(2) 四癌篩檢：口腔癌、子宮頸癌、乳癌、大腸癌免費篩檢；另有 45～74 歲（原住民 40 歲起）終身 1 次公費胃癌篩檢（糞便胃幽門螺旋桿菌檢測）與 45～79 歲（原住民 40 歲起）終身 1 次 B、C 型肝炎篩檢；(3) 65 歲以上長者：每年 1 次老人健康檢查、公費流感疫苗接種。',
    searchGroup: '醫療與健康類',
    isTimeSensitive: false,
    applicationPeriod: '常態受理，依年齡達到篩檢資格即可預約',
    notes: '⚠️ 老人健康檢查與公費流感疫苗的接種期間（通常流感疫苗有季節性開打期）本次搜尋未查得明確時間，需洽當地衛生所或國健署官網確認當年度接種期程。',
    eligibilityConditions: { ageMin: 30 },
    sourceUrl: 'https://edh.tw/articles/btgkwwk',
    sourceExcerpt:
      '2025年起成人免費健檢對象放寬至30歲，2026年將延續原有的補助，只要符合年齡資格，不需負擔檢查費……45歲～74歲民眾終身1次公費「糞便抗原檢測胃幽門螺旋桿菌」服務……45～79歲民眾（原住民提早至40歲）終身一次的「B、C型肝炎篩檢」。',
    lastVerifiedDate: '2026-07-28',
    documents: ['健保卡'],
    locations: [
      { name: '衛生福利部國民健康署', website: 'https://www.hpa.gov.tw/' },
      { name: '各縣市衛生所／健保特約院所' },
    ],
  },
]
