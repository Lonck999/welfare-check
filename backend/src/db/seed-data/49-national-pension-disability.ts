import type { SeedBenefit } from './types.js'

/** 全國統一制度，不分縣市 */
export const nationalPensionDisabilitySeeds: SeedBenefit[] = [
  {
    categoryNumber: 49,
    name: '國民年金身心障礙年金',
    agency: '勞動部勞工保險局（國民年金組）',
    county: null,
    description:
      '領有身心障礙證明/手冊且有參加國民年金者，符合國民年金法第 35 條規定者每月可領身心障礙基本保證年金 5,437 元（自 2024 年 1 月起）；若計算後之年金給付低於 5,437 元且無欠繳保費等排除情形，最低保障發給 5,437 元至死亡為止。障礙類別及等級符合法定「視為無工作能力」者免經工作能力評估，其餘需經指定醫療機構綜合評量。',
    searchGroup: '現金與生活補助類',
    isTimeSensitive: false,
    applicationPeriod: '常態受理',
    eligibilityConditions: {
      requiredFlags: ['disability_certificate', 'enrolled_national_pension'],
    },
    sourceUrl: 'https://www.bli.gov.tw/0017725.html',
    sourceExcerpt:
      '符合國民年金法第35條規定之被保險人，可每月領取5,437元的身心障礙基本保證年金（自2024年1月起生效）。如果月給付金額低於5,437元，且不符合特定情況（如有欠缴保险费或正在领取其他社会福利津贴），則按月發給基本保障5,437元至死亡為止。',
    lastVerifiedDate: '2026-07-28',
    documents: ['身心障礙證明或手冊影本', '申請書', '本人金融機構帳戶存摺影本'],
    locations: [
      {
        name: '勞動部勞工保險局國民年金組',
        website: 'https://www.bli.gov.tw/',
      },
    ],
  },
]
