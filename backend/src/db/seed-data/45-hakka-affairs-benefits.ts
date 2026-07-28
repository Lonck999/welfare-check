import type { SeedBenefit } from './types.js'

/** 全國統一制度，不分縣市 */
export const hakkaAffairsBenefitsSeeds: SeedBenefit[] = [
  {
    categoryNumber: 45,
    name: '客委會補助（創業/文化/子女獎助學金）',
    agency: '客家委員會',
    county: null,
    description:
      '客委會提供客家青年創業輔導與「推展客家文化力補助」（地方創生、藝文生活、公共參與等面向的文化補助計畫），設籍客家文化重點發展區或自我認定為客家人者可申請。創業貸款部分與一般青年創業貸款制度相通（18～45 歲、自然人出資占比 20% 以上、3 年內受過創業輔導 20 小時或 2 學分）。',
    searchGroup: '特殊身分族群類',
    isTimeSensitive: false,
    applicationPeriod: '文化補助依客委會每年公告期程受理；創業貸款常態受理',
    notes: '⚠️ 客家子女才藝獎助學金的具體申請資格與金額本次搜尋未查得明確資料，需洽客委會或「客傳會獎補助系統」（grants.hpcf.tw）確認最新公告。',
    eligibilityConditions: { requiredIdentities: ['客家人'] },
    sourceUrl: 'https://youthfirst.yda.gov.tw/index.php/subject/content/1308',
    sourceExcerpt:
      '客家委員會「推展客家文化力補助」：地方創生、藝文生活、公共參與……申請青年創業貸款的代表人/負責人須年滿18歲至45歲，其以自然人之出資額應占該企業體實收資本額20%以上；須在3年內受過政府認可之單位開辦創業輔導相關課程至少20小時或取得2學分證明。',
    lastVerifiedDate: '2026-07-28',
    locations: [
      { name: '客家委員會', website: 'https://www.hakka.gov.tw/' },
      { name: '客傳會獎補助系統', website: 'https://grants.hpcf.tw/subsidy' },
    ],
  },
]
