import type { SeedBenefit } from './types.js'

/** 全國統一制度，不分縣市（縣市低收入戶喪葬補助費需另行查詢） */
export const funeralSubsidySeeds: SeedBenefit[] = [
  {
    categoryNumber: 31,
    name: '喪葬補助（勞保/國民年金）',
    agency: '勞動部勞工保險局',
    county: null,
    description:
      '(1) 勞保喪葬津貼：被保險人於保險有效期間，父母、配偶或子女死亡時得請領家屬死亡給付喪葬津貼，按死亡當月起前 6 個月平均月投保薪資計算，有遺屬者發給 5 個月、無遺屬者發給 10 個月（最高級距情況下約 45.8 萬元）；(2) 國民年金喪葬給付：25～65 歲強制加保之國民年金被保險人死亡，喪葬津貼為 91,410 元，應自死亡之日起 5 年內申請，逾期不予給付。',
    searchGroup: '一般性優惠與便民服務',
    isTimeSensitive: true,
    applicationPeriod: '國民年金喪葬給付須於死亡之日起 5 年內申請，逾期不給付；勞保喪葬津貼建議儘速申請',
    notes: '⚠️ 縣市低收入戶喪葬補助費本次搜尋未查得統一標準，需依居住縣市另行查證社會局公告。',
    eligibilityConditions: { requiredFlags: ['has_labor_insurance_or_national_pension'] },
    sourceUrl: 'https://www.faqs.tw/funeral-subsidy-guide',
    sourceExcerpt:
      '被保險人於保險有效期間，若其父母、配偶或子女死亡時，得請領家屬死亡給付喪葬津貼……若有遺屬，按被保險人死亡當月起前6個月之平均月投保薪資計算，發給喪葬津貼5個月；若無遺屬，發給喪葬津貼10個月……國保喪葬津貼為91,410元……應自被保險人死亡之日起5年內提出喪葬津貼之申請，否則將不給付。',
    lastVerifiedDate: '2026-07-28',
    documents: ['死亡證明', '戶籍謄本', '與被保險人關係證明', '金融機構帳戶存摺影本'],
    locations: [{ name: '勞動部勞工保險局', website: 'https://www.bli.gov.tw/' }],
  },
]
