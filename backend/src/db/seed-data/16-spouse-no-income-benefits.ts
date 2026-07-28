import type { SeedBenefit } from './types.js'

/** 全國統一制度，不分縣市——「二度就業婦女」是勞動部全國性計畫，非地方各自舉辦 */
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
    eligibilityConditions: { requiredFlags: ['spouse_no_income'] },
    sourceUrl: 'https://dep.mohw.gov.tw/DOSI/cp-308-601-102.html',
    sourceExcerpt:
      '職業訓練生活津貼……提供給非自願離職、登記求職，並安排全時職業訓練者……全時職業訓練要求訓練期間1個月以上，每週訓練日4日以上，每日訓練4小時以上，每月訓練時數達100小時以上……按月發給相當於離職前6個月平均月投保薪資60%，最長發給6個月。',
    lastVerifiedDate: '2026-07-28',
    documents: ['求職登記證明', '全時職業訓練錄取證明'],
    locations: [{ name: '各地公立就業服務站' }, { name: '勞動部勞工保險局（國民年金加保）', website: 'https://www.bli.gov.tw/' }],
  },
  {
    categoryNumber: 16,
    name: '二度就業婦女補助（婦女再就業計畫）',
    agency: '勞動部勞動力發展署',
    county: null,
    description:
      '勞動部自 112 年 9 月起推動「婦女再就業計畫」，協助因照顧家庭離開職場 180 日以上的婦女返回職場（全國統一制度，經各地公立就業服務機構執行，非地方各自舉辦）。措施包含：(1) 自主訓練獎勵：參與課程時數需至少 8 小時以上；(2) 再就業獎勵：就業每滿 30 日得請領獎勵金 1 萬元，最高發給 6 萬元；(3) 職場支持輔導獎勵：每人每月 5,000 元，最長 12 個月。',
    searchGroup: '就業與勞工權益類',
    isTimeSensitive: false,
    applicationPeriod: '常態受理',
    eligibilityConditions: { requiredFlags: ['spouse_no_income'] },
    sourceUrl: 'https://www.mol.gov.tw/1607/1632/1633/89893/post',
    sourceExcerpt:
      '勞動部自112年9月起推動「婦女再就業計畫」，運用個別化就業服務、「自主訓練獎勵」、「再就業獎勵」及「雇主工時調整獎勵」等措施，協助因照顧家庭離開職場180日以上的婦女返回職場……再就業獎勵：獎勵金於就業滿90日一次發給3萬元，修正為就業每滿30日得請領獎勵金1萬元，最高發給6萬元……職場支持輔導獎勵：獎勵金額由每人每月3千元提高為5千元，最長12個月。',
    lastVerifiedDate: '2026-07-28',
    documents: ['求職登記證明'],
    locations: [
      { name: '各地公立就業服務站' },
      { name: '台灣就業通婦女再就業專區', website: 'https://job.taiwanjobs.gov.tw/Internet/special2/woman/index.aspx' },
    ],
  },
]
