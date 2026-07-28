import type { SeedBenefit } from './types.js'

/** 中央統一基準，全國適用；部分縣市另有加碼（詳見 notes），非每縣市金額不同 */
export const childcareSubsidySeeds: SeedBenefit[] = [
  {
    categoryNumber: 7,
    name: '育兒與托育補助',
    agency: '衛生福利部社會及家庭署',
    county: null,
    description:
      '有 18 歲以下子女者：公共托育每月補助 7,000 元、準公共托育每月補助 13,000 元（中央統一金額，已完全取消排富，全國家庭皆可申請）。2026 年起，滿 2 歲仍留在原托育處未入園者可續領托育補助至 3 歲。',
    searchGroup: '現金與生活補助類',
    isTimeSensitive: false,
    applicationPeriod: '常態受理',
    notes:
      '部分縣市另有地方加碼：保母/托嬰中心加碼 1,000～3,000 元（依機構類型不等）；台北市、新北市對準公共托育另有「友善托育補助」每月約增 2,000～6,000 元。基隆、宜蘭、苗栗、彰化、雲林、嘉義、屏東、花蓮、台東及外島等縣市目前多以中央補助為主，部分鄉鎮另有加碼。⚠️ 各縣市加碼金額本次未逐一查證，需依居住縣市另行確認衛福部托育媒合平台最新公告。',
    eligibilityConditions: { requiresChildUnder: 18 },
    sourceUrl: 'https://www.businessweekly.com.tw/careers/blog/3021035',
    sourceExcerpt:
      '2026托育補助在2024有過補助制度調整，公共托育的補助為每月7,000元，而準公共托育的補助為每月1萬3,000元……完全取消排富：全國家庭皆可申請，不再受所得稅率限制……加碼保母／托嬰中心1000～3000元（依機構類型不等）。部分縣市如台北市、新北市針對準公共托育另有加碼「友善托育補助」（每月約增2,000-6,000元不等）。',
    lastVerifiedDate: '2026-07-28',
    documents: ['托育契約', '戶籍資料'],
    locations: [{ name: '衛生福利部社會及家庭署托育媒合平台', website: 'https://ap.mohw.gov.tw/babyhome/' }],
  },
]
