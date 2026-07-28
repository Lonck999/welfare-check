import type { SeedBenefit } from './types.js'

/** 全國統一制度，不分縣市 */
export const overseasCommunityBenefitsSeeds: SeedBenefit[] = [
  {
    categoryNumber: 51,
    name: '僑委會補助（僑生獎助學金）',
    agency: '僑務委員會',
    county: null,
    description:
      '傑出僑生獎學金/學行優良僑生獎學金：適用大專院校二年級以上（五專四年級以上）僑生，上一學年學業總平均 80 分以上、操行兩學期均達甲等（80 分）以上（碩博士生不得申請）；就讀中等以上學校二、三年級者，上一學年學業總平均 85 分以上且無受警告以上處分亦可申請。依香港澳門居民來臺就學辦法在學之港澳學生符合前述資格者亦可申請。',
    searchGroup: '特殊身分族群類',
    isTimeSensitive: false,
    applicationPeriod: '每學年由學校審查後統一造冊送僑委會核定',
    eligibilityConditions: { requiredIdentities: ['僑民', '僑生'] },
    sourceUrl: 'https://www.ocac.gov.tw/OCAC/Pages/VDetail.aspx?nodeid=4496&pid=56984536',
    sourceExcerpt:
      '傑出僑生獎學金及學行優良僑生獎學金的申請資格為：就讀大專院校二年級以上（五年制專科學校四年級以上），其上一學年學業總平均成績在八十分以上，操行兩學期均列甲等（八十分）以上。但碩、博士班研究生不得申請。',
    lastVerifiedDate: '2026-07-28',
    documents: ['前一學年學業成績單', '在學證明'],
    locations: [
      { name: '就讀學校（初審後轉送僑委會）' },
      { name: '僑委會獎學金申請系統', website: 'https://scholarship.ocac.gov.tw/' },
    ],
  },
]
