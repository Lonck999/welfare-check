import type { SeedBenefit } from './types.js'

/** 全國統一制度，不分縣市 */
export const rareDiseaseBenefitsSeeds: SeedBenefit[] = [
  {
    categoryNumber: 58,
    name: '罕見疾病醫療與生活補助',
    agency: '衛生福利部國民健康署／財團法人罕見疾病基金會',
    county: null,
    description:
      '領有罕見疾病證明者，可透過罕見疾病基金會申請醫療補助、生育關懷補助、臨床試驗補助、安養補助、個人助理員補助、無障礙計程車補助等多項服務；另罕見疾病藥費由健保給付（孤兒藥）。基金會亦提供罕病防治宣導教育與病患社會資源轉介。',
    searchGroup: '醫療與健康類',
    isTimeSensitive: false,
    applicationPeriod: '常態受理',
    notes: '⚠️ 各項補助的具體金額本次搜尋未查得明確數字，需洽罕見疾病基金會確認最新補助基準與交通補助細節。',
    eligibilityConditions: { requiredFlags: ['rare_disease_certificate'] },
    sourceUrl: 'http://www.tfrd.org.tw/tfrd/service_b/main/category_id/1',
    sourceExcerpt:
      '基金會提供多項服務，包括罕病防治與宣導教育、罕病病患社會資源轉介、罕病病患相關醫療、生活急難及安養補助。具體服務項目包括醫療補助、生育關懷補助、臨床試驗補助、安養補助、個人助理員補助、無障礙計程車補助等。',
    lastVerifiedDate: '2026-07-28',
    documents: ['罕見疾病證明'],
    locations: [
      {
        name: '財團法人罕見疾病基金會',
        phone: '02-25210717 分機 168/112',
        website: 'https://www.tfrd.org.tw/',
      },
    ],
  },
]
