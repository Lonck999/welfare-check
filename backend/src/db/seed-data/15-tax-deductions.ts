import type { SeedBenefit } from './types.js'

/** 全國統一稅制，不分縣市 */
export const taxDeductionsSeeds: SeedBenefit[] = [
  {
    categoryNumber: 15,
    name: '稅務減免（長照/扶養親屬/配偶）',
    agency: '財政部',
    county: null,
    description:
      '(1) 長期照顧特別扣除額：115 年度已由每人每年 12 萬元調升至 18 萬元，受扶養長輩若領有身心障礙證明可再疊加身心障礙特別扣除額 21.8 萬元，兩者合計最高可節省超過 39 萬元課稅額度；(2) 扶養親屬：每人扣除額 9.7 萬元，本人/配偶/受扶養直系尊親屬年滿 70 歲者免稅額提高至 14.55 萬元；(3) 配偶免稅額 9.7 萬元、有配偶者標準扣除額 26.2 萬元。',
    searchGroup: '稅務與貸款類',
    isTimeSensitive: true,
    applicationPeriod: '每年 5 月報稅季申報',
    notes: '每年報稅季前應提醒使用者確認扶養親屬是否符合列報條件（會影響親屬自身福利資格認定的家庭所得計算）。',
    eligibilityConditions: { requiredFlags: ['has_dependents_or_ltc_needs'] },
    sourceUrl: 'https://www.dentist2home.com/post/2026%E5%A0%B1%E7%A8%85%E5%BF%85%E7%9C%8B%EF%BC%81%E7%85%A7%E9%A1%A7%E5%A4%B1%E8%83%BD%E9%95%B7%E8%80%85%E5%8F%AF%E6%89%A318%E8%90%AC%EF%BC%81%E9%95%B7%E6%9C%9F%E7%85%A7%E9%A1%A7%E7%89%B9%E5%88%A5%E6%89%A3%E9%99%A4%E9%A1%8D%E7%94%B3%E5%A0%B1-%E6%87%B6%E4%BA%BA%E5%8C%85',
    sourceExcerpt:
      '長期照顧特別扣除額由每人12萬元大幅提高至18萬元，調幅達50％……搭配身心障礙特別扣除額21.8萬元，兩者合計最高可節省超過39萬元的課稅額度。免稅額為每人9.7萬元；70歲以上納稅義務人、配偶或受納稅義務人扶養之直系尊親屬14.55萬元；有配偶者標準扣除額26.2萬元。',
    lastVerifiedDate: '2026-07-28',
    locations: [{ name: '財政部各地區國稅局' }, { name: '財政部電子申報繳稅服務網', website: 'https://www.etax.nat.gov.tw/' }],
  },
]
