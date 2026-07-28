import type { SeedBenefit } from './types.js'

/** 全國統一制度，不分縣市（二度就業縣市加碼需另行查詢） */
export const spouseNoIncomeBenefitsSeeds: SeedBenefit[] = [
  {
    categoryNumber: 16,
    name: '配偶無收入相關補助',
    agency: '勞動部勞工保險局',
    county: null,
    description:
      '無職業配偶依法應強制參加國民年金，以免老年年金與身心障礙年金年資中斷（詳見第 32 類）。若配偶為非自願離職，2 年內於公立就業服務機構辦理求職登記並安排全時職業訓練（訓練期 1 個月以上、每週至少 4 訓練日、每日 4 小時以上、每月至少 100 小時）者，可申請職業訓練生活津貼，按離職前 6 個月平均月投保薪資 60% 按月發給（扶養眷屬者加發 20%），最長補助 6 個月。',
    searchGroup: '就業與勞工權益類',
    isTimeSensitive: false,
    applicationPeriod: '離職後 2 年內辦理求職登記並安排全時職業訓練',
    notes: '⚠️ 二度就業婦女職業訓練補助（縣市層級）本次搜尋未查得統一標準，需依居住縣市另行查證。',
    eligibilityConditions: { requiredFlags: ['spouse_no_income'] },
    sourceUrl: 'https://dep.mohw.gov.tw/DOSI/cp-308-601-102.html',
    sourceExcerpt:
      '職業訓練生活津貼……提供給非自願離職、登記求職，並安排全時職業訓練者……全時職業訓練要求訓練期間1個月以上，每週訓練日4日以上，每日訓練4小時以上，每月訓練時數達100小時以上……按月發給相當於離職前6個月平均月投保薪資60%，最長發給6個月。',
    lastVerifiedDate: '2026-07-28',
    documents: ['求職登記證明', '全時職業訓練錄取證明'],
    locations: [{ name: '各地公立就業服務站' }, { name: '勞動部勞工保險局（國民年金加保）', website: 'https://www.bli.gov.tw/' }],
  },
]
