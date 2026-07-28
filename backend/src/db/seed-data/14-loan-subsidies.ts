import type { SeedBenefit } from './types.js'

/** 全國統一制度，不分縣市（皆為中央政策性貸款） */
export const loanSubsidiesSeeds: SeedBenefit[] = [
  {
    categoryNumber: 14,
    name: '青年安心成家購屋優惠貸款（新青安3.0）',
    agency: '內政部',
    county: null,
    description:
      '「新青安3.0」新制方案於 2026 年 8 月 1 日起上路，申請期間 2026 年 8 月 1 日至 2029 年 7 月 31 日。申請條件：未滿 50 歲、個人年所得 200 萬元以內，借款人限貸 1 次。',
    searchGroup: '稅務與貸款類',
    isTimeSensitive: true,
    applicationPeriod: '2026 年 8 月 1 日至 2029 年 7 月 31 日',
    eligibilityConditions: { ageMax: 50, requiresNoOwnedHome: true },
    sourceUrl: 'https://www.hbhousing.com.tw/news/detail.aspx?num=5278',
    sourceExcerpt:
      '行政院於2026年7月16日拍板「新青安3.0」新制方案，預計於2026年8月1日起開始正式上路，申請期間為自2026年8月1日至2029年7月31日。申請條件包括未滿50歲、個人年所得200萬以內，且借款人限貸1次。',
    lastVerifiedDate: '2026-07-28',
    locations: [{ name: '各承辦銀行（內政部公告名單）' }, { name: '內政部', website: 'https://www.moi.gov.tw/' }],
  },
  {
    categoryNumber: 14,
    name: '青年創業貸款',
    agency: '經濟部中小及新創企業署',
    county: null,
    description:
      '（原「青年創業及啟動金貸款」，官方名稱簡化為「青年創業貸款」）公司設立登記未滿 8 年即可申請（原規定為 5 年內，已放寬）。',
    searchGroup: '稅務與貸款類',
    isTimeSensitive: false,
    applicationPeriod: '常態受理',
    notes: '⚠️ 貸款額度、利率等細節本次搜尋未查得完整數字，需洽經濟部中小及新創企業署確認。',
    eligibilityConditions: { requiredFlags: ['has_startup_intent'] },
    sourceUrl: 'https://startup.sme.gov.tw/home/modules/funding/detail/?sId=15',
    sourceExcerpt:
      '官方全名從「青年創業及啟動金貸款」簡化為「青年創業貸款」，申請資格從原本的公司成立5年內放寬到設立登記未滿8年。',
    lastVerifiedDate: '2026-07-28',
    locations: [{ name: '經濟部中小及新創企業署', website: 'https://www.sme.gov.tw/' }],
  },
  {
    categoryNumber: 14,
    name: '微型創業鳳凰貸款',
    agency: '勞動部勞動力發展署',
    county: null,
    description:
      '員工人數少於 5 人（不含負責人）、3 年內參與政府立案創業課程 18 小時以上，最高貸款額度 200 萬元（已辦稅籍登記者最高 50 萬元）。前 3 年利息全額補貼，第 4 年起年息 1.5%。適用 45 歲以上或弱勢族群（含 20～45 歲之特定對象）。',
    searchGroup: '稅務與貸款類',
    isTimeSensitive: false,
    applicationPeriod: '常態受理',
    eligibilityConditions: { requiredFlags: ['has_startup_intent'] },
    sourceUrl: 'https://nextx.biz/youth-startup-loan-vs-grant/',
    sourceExcerpt:
      '申請資格要求員工人數小於5人（不含負責人）、3年內參與政府立案之創業課程18小時以上，最高貸款額度為200萬元（辦有稅籍登記者最高50萬元）。前3年利息全額補貼，第4年起年息1.5%。',
    lastVerifiedDate: '2026-07-28',
    locations: [{ name: '勞動部勞動力發展署', website: 'https://www.wda.gov.tw/' }],
  },
  {
    categoryNumber: 14,
    name: '勞工紓困貸款（勞保紓困貸款）',
    agency: '勞動部勞工保險局',
    county: null,
    description:
      '被保險人未請領老年給付、終身無工作能力之失能給付，或已領取但過去貸款已還清完畢者可申請，每人限申請 1 次（每期）。貸款額度最高 10 萬元，年利率 2.165%（每年 1 月、7 月第一個營業日公告調整）。2026 年度受理期間為 2025 年 12 月 15 日至 2026 年 1 月 2 日，屬定期開辦、有明確申請截止日的方案，須留意年度公告時程。',
    searchGroup: '稅務與貸款類',
    isTimeSensitive: true,
    applicationPeriod: '每年固定期間開辦（2026 年度為 2025/12/15～2026/1/2），逾期需等下一年度公告',
    eligibilityConditions: { requiredFlags: ['has_labor_insurance'] },
    sourceUrl: 'https://houseloan.tw/labor-insurance-loan/',
    sourceExcerpt:
      '申請2026年勞保紓困貸款，被保險人必須……未請領老年給付、終身無工作能力之失能給付……貸款額度：10萬元（實際核貸金額依個人條件審核）；年利率：2.165%……2026年度的勞保紓困貸款從2025年12月15日起開放申請，截止日期到2026年1月2日。',
    lastVerifiedDate: '2026-07-28',
    locations: [{ name: '勞動部勞工保險局', website: 'https://www.bli.gov.tw/' }],
  },
]
