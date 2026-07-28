import type { SeedBenefit } from './types.js'

/** 全國統一制度，不分縣市（各地勞動力發展署分署為執行窗口） */
export const middleAgedEmploymentSeeds: SeedBenefit[] = [
  {
    categoryNumber: 34,
    name: '中高齡就業促進補助',
    agency: '勞動部勞動力發展署',
    county: null,
    description:
      '45 歲以上中高齡及高齡求職者參與「職場學習及再適應計畫」，經公立就業服務機構推介入職後，按基本時薪發給補助金（不超過每月基本工資），一般最長補助 3 個月、高齡者可延長至 6 個月，由雇主代為發放。雇主面：在職中高齡者訓練補助課程費用 70%，每雇主每年最高 50 萬元；雇主外部訓練課程補助同為 70%，與其他措施合計最高 50 萬元。雇主申請須於每年 12 月受理下一年度申請，訓練計畫上傳後 5 個工作日內檢具文件向所在地勞動力發展署分署申請。',
    searchGroup: '就業與勞工權益類',
    isTimeSensitive: false,
    applicationPeriod: '常態受理（求職者）；雇主訓練補助每年 12 月受理次年度申請',
    eligibilityConditions: { ageMin: 45 },
    sourceUrl: 'https://guide.1111.com.tw/article/job-hunting/45plus_employment_subsidy',
    sourceExcerpt:
      '針對45歲以上的中高齡及高齡求職者，填寫同意「參與職場學習及再適應計畫意願書」後，經公立就業服務機構推介入職者，可按照基本時薪發給補助金，且不超過每月基本工資，最長補助3個月，高齡者可延長至6個月……在職中高齡者訓練補助：補助70%的課程費用，每雇主每年最高可申請50萬元。',
    lastVerifiedDate: '2026-07-28',
    documents: ['求職登記證明', '參與職場學習及再適應計畫意願書'],
    locations: [{ name: '各地公立就業服務站（勞動力發展署所屬分署）', website: 'https://www.wda.gov.tw/' }],
  },
]
