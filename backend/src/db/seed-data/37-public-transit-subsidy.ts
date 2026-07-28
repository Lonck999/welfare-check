import type { SeedBenefit } from './types.js'

/** 全國統一制度（TPASS 2.0），依票證設定即可跨區使用，不需依縣市分別建檔 */
export const publicTransitSubsidySeeds: SeedBenefit[] = [
  {
    categoryNumber: 37,
    name: '公共運輸通勤補助（TPASS 定期票）',
    agency: '交通部',
    county: null,
    description:
      'TPASS 2.0 自 2025 年 1 月 14 日啟動，可搭乘公車、客運、台鐵、捷運、機場捷運、輕軌、自行車等公共運具，依居住地跨區設定即可用單一定期票通勤。持一般成人電子票證（悠遊卡、一卡通、愛金卡等）皆可設定，敬老卡/愛心卡等優惠票種不可設定。早鳥註冊可享 3 階段加碼回饋，最高 18～33% 總回饋或 50 元首購回饋金，回饋金於次月 25 日起開放領取，最遲須於開放領取日起 1 年內領取完畢。',
    searchGroup: '一般性優惠與便民服務',
    isTimeSensitive: false,
    applicationPeriod: '常態受理，早鳥註冊期間享額外回饋',
    notes: '跨縣市通勤者可直接用同一張定期票通勤，不需依居住縣市與工作地點縣市分別查詢不同方案，僅票價依所涵蓋的區域範圍而定。',
    sourceUrl: 'https://www.tpass.tw/',
    sourceExcerpt:
      'TPASS 2.0於2025年1月14日啟動，規劃一系列常客優惠與回饋方案，可搭乘公車、客運、台鐵、捷運、機場捷運、輕軌、自行車等公共運具……民眾可持自身原本的全票電子票證（悠遊卡、一卡通及愛金卡）去設定通勤定期票……如未領取可與後續月份回饋金併同領取，但最遲須於「開放領取日起1年內」領取完畢。',
    lastVerifiedDate: '2026-07-28',
    documents: ['一般成人電子票證（悠遊卡/一卡通/愛金卡）'],
    locations: [{ name: 'TPASS 定期票官方網站', website: 'https://www.tpass.tw/' }],
  },
]
