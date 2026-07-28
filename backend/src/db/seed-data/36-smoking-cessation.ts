import type { SeedBenefit } from './types.js'

/** 全國統一制度，不分縣市 */
export const smokingCessationSeeds: SeedBenefit[] = [
  {
    categoryNumber: 36,
    name: '戒菸補助（戒菸門診/戒菸專線）',
    agency: '衛生福利部國民健康署',
    county: null,
    description:
      '具健保身分、尼古丁成癮度分數達 4 分以上或平均每天吸菸 10 支以上者，可至健保特約院所接受戒菸治療服務，每年補助 2 個療程、每療程最多補助 8 週藥品，且須於同一醫事機構 90 天內完成；戒菸輔助用藥不收部分負擔費用。不適合用藥者（如孕婦、18 歲以下青少年）可改由衛教師提供衛教諮詢。免費戒菸專線 0800-636-363 提供電話諮詢陪伴戒菸。',
    searchGroup: '醫療與健康類',
    isTimeSensitive: false,
    applicationPeriod: '常態受理，每年可申請 2 個療程',
    notes: '⚠️ 縣市層級戒菸獎勵金（部分縣市另有加碼）本次搜尋未查得明確全國清單，需視使用者居住縣市另行查證。',
    eligibilityConditions: { requiredFlags: ['wants_to_quit_smoking'] },
    sourceUrl: 'https://www.hpa.gov.tw/Pages/Detail.aspx?nodeid=1812&pid=10193',
    sourceExcerpt:
      '符合健保身份且尼古丁成癮度分數達4分(含)以上，或平均每天吸10支菸以上者可接受戒菸治療服務……每年補助2個療程，每療程最多補助8週藥品，且每療程須於同一醫事機構於90天內完成……免費戒菸專線（0800-636363）。',
    lastVerifiedDate: '2026-07-28',
    documents: ['健保卡'],
    locations: [
      { name: '衛生福利部國民健康署', phone: '0800-636-363', website: 'https://www.hpa.gov.tw/' },
      { name: '健保特約戒菸門診院所' },
    ],
  },
]
