import type { SeedBenefit } from './types.js'

/** 全國統一制度，不分縣市 */
export const culturePointsSeeds: SeedBenefit[] = [
  {
    categoryNumber: 30,
    name: '文化幣',
    agency: '文化部',
    county: null,
    description:
      '13～22 歲青年（出生於民國 93 年 1 月 1 日至 102 年 12 月 31 日之間）每人可領取 1,200 點文化幣（1 點=新臺幣 1 元），用於購買書籍、電影票、展演票券等文化體驗項目。2026 年文化幣自 2026 年 1 月 1 日上午 8 點起開放領用，使用期限至 2026 年 12 月 31 日。下載「文化幣 APP」註冊並完成個人資料驗證後即可領取，無手機者可申請紙本 QR-code 使用。',
    searchGroup: '一般性優惠與便民服務',
    isTimeSensitive: true,
    applicationPeriod: '2026 年 1 月 1 日起開放領用，使用期限至 2026 年 12 月 31 日',
    notes: '⚠️ 各縣市另有自辦的藝文體驗補助券，非文化部文化幣，需另依居住縣市查證是否有加碼措施。',
    eligibilityConditions: { ageMin: 13, ageMax: 22 },
    sourceUrl: 'https://udn.com/news/story/6885/9236575',
    sourceExcerpt:
      '符合13歲至22歲青年族群，需出生於民國93年(2004)1月1日至民國102年(2013)12月31日之間。每人發放1200點文化幣（1點等於新臺幣1元）。自2026年1月1日上午8點起，2026文化幣正式開放領用……使用期限至2026年12月31日。',
    lastVerifiedDate: '2026-07-28',
    documents: ['文化幣 APP 註冊（或申請紙本 QR-code）'],
    locations: [{ name: '文化部文化幣官方網站/APP' }],
  },
]
