import type { SeedBenefit } from './types.js'

/** 中央「天然災害救助辦法」為全國統一法源依據，各地方政府依此執行，不分縣市 */
export const naturalDisasterReliefSeeds: SeedBenefit[] = [
  {
    categoryNumber: 55,
    name: '天然災害救助',
    agency: '各地方政府社會處/局（依中央天然災害救助辦法執行）',
    county: null,
    description:
      '因水、火、風、雹、旱、地震及其他不可抗力天然災害致住屋毀損不堪居住者（限已辦戶籍登記並居住於現址），地方政府每戶發給最高 10 萬元（以戶內實際居住人口 5 人為限）。另有人員死亡/失蹤/重傷救助、安遷救助、住戶淹水救助、農漁業受災救助等項目。與「急難救助」不同制度，天然災害救助依住屋/農業損失程度核發。',
    searchGroup: '時效性最高項目',
    isTimeSensitive: true,
    applicationPeriod: '災害發生後依地方政府公告受理期間申請，通常有明確申請截止日',
    notes: '⚠️ 各項救助金額上限依中央辦法訂定基準，惟實際執行與加碼仍可能因地方政府財政狀況略有差異，建議事發後立即洽詢當地社會處確認金額與截止日期。',
    eligibilityConditions: { requiredFlags: ['recent_natural_disaster_damage'] },
    sourceUrl: 'https://www.gov.tw/News_Content_26_813626',
    sourceExcerpt:
      '本市轄內之人民於遭受水、火、風、雹、旱、地震及其他災害等不可抗力肇因之災害，致損害重大，影響生活者可申請救助……人民因災致住屋毀損達不堪居住程度者（限已辦戶籍登記並居住於現址），地方政府每戶發給最高10萬元（以戶內實際居住人口以5人為限）。',
    lastVerifiedDate: '2026-07-28',
    documents: ['房屋受損照片/證明', '戶籍謄本'],
    locations: [{ name: '戶籍地政府社會處/局' }],
  },
]
