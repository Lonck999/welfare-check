import type { SeedBenefit } from './types.js'

/** 全國統一制度（衛福部方案），不限戶籍地縣市 */
export const mentalHealthCounselingSeeds: SeedBenefit[] = [
  {
    categoryNumber: 24,
    name: '心理諮商補助（15-45歲青壯世代心理健康支持方案）',
    agency: '衛生福利部',
    county: null,
    description:
      '衛福部自 113 年 8 月至 115 年 12 月辦理「15-45 歲青壯世代心理健康支持方案」，年滿 15～45 歲有心理諮商需求者可申請，每人補助 3 次免費心理諮商服務，無戶籍或居住地縣市限制，可選擇戶籍地外的合作機構。申請流程：查詢合作機構 → 聯繫機構預約 → 攜帶身分證明文件 → 至機構接受諮商。可上官網用「心理諮商合作機構查詢」或「通訊諮商合作機構查詢」依縣市篩選尚有名額的機構。補助期程至 2026 年 12 月 31 日止。',
    searchGroup: '一般性優惠與便民服務',
    isTimeSensitive: true,
    applicationPeriod: '方案期程至 2026/12/31 止，名額有限，需查詢合作機構是否還有名額',
    notes: '若曾有流產、家暴經歷或有照顧壓力，此方案同樣適用，不需額外符合其他資格條件；名額依合作機構而定，建議儘早查詢預約。',
    eligibilityConditions: { ageMin: 15, ageMax: 45 },
    sourceUrl: 'https://www.businessweekly.com.tw/focus/blog/3016202',
    sourceExcerpt:
      '衛生福利部自113年8月至115年12月辦理「15-45歲青壯世代心理健康支持方案」，15-45歲青壯世代可至指定執行機構，於方案執行期間內，補助每人3次免費心理諮商服務……年滿15歲至45歲有心理諮商需求者，無戶籍或居住地縣市限制，可以選擇戶籍地外的機構諮詢。',
    lastVerifiedDate: '2026-07-28',
    documents: ['身分證明文件'],
    locations: [{ name: '衛福部青壯世代心理健康支持方案官網' }],
  },
]
