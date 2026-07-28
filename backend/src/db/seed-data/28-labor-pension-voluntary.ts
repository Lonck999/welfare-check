import type { SeedBenefit } from './types.js'

/** 全國統一制度，不分縣市 */
export const laborPensionVoluntarySeeds: SeedBenefit[] = [
  {
    categoryNumber: 28,
    name: '勞工退休金自願提繳（節稅）',
    agency: '勞動部勞工保險局',
    county: null,
    description:
      '受僱勞工、受委任工作者、自營作業者可在每月工資 6% 範圍內自願提繳退休金至個人專戶，自提金額當年度不計入薪資所得課稅，可降低綜合所得稅級距。受僱勞工向雇主提出申請，雇主不得拒絕（2026 年 8 月 1 日起生效的施行細則修正規定）。',
    searchGroup: '就業與勞工權益類',
    isTimeSensitive: false,
    applicationPeriod: '常態受理，隨時可向雇主申請開始/調整自提比例',
    notes: '報稅時務必確認扣繳憑單薪資總額是否已扣除自願提繳金額，如有誤可洽稅捐機關更正；同時建議確認雇主是否足額提繳 6% 的法定提撥。',
    eligibilityConditions: { requiredFlags: ['is_employed'] },
    sourceUrl: 'https://money.udn.com/money/story/6710/9475422',
    sourceExcerpt:
      '依《勞工退休金條例》第14條規定，勞工、受委任工作者、實際從事勞動之雇主及自營作業者，得在每月工資、執行業務所得 6% 範圍內自願提繳退休金……受僱勞工如向雇主提出申請自願提繳退休金，雇主不得拒絕。',
    lastVerifiedDate: '2026-07-28',
    locations: [
      {
        name: '勞動部勞工保險局',
        phone: '(02)2396-1266',
        website: 'https://www.bli.gov.tw/',
      },
    ],
  },
]
