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
  {
    categoryNumber: 30,
    name: '文化部推動實體書店發展補助（澄清：非個人閱讀補助）',
    agency: '文化部',
    county: null,
    description:
      '⚠️ 重要澄清：SKILL.md 原描述的「文化部閱讀補助 書店」實為「文化部推動實體書店發展補助作業」，申請對象是**實際營運之實體書店或相關立案獨資/合夥事業/法人團體**，補助書店的特色發展、數位提升、閱讀推廣計畫、國際交流等，並非提供給一般民眾個人的閱讀/購書補助。申請期程為每年 10～11 月，至文化部獎補助資訊網線上申請。個人讀者若尋找「買書折抵/閱讀補助」，本次搜尋未查得專屬個人適用的方案，可能需另行查證圖書館借閱或其他管道。',
    searchGroup: '一般性優惠與便民服務',
    isTimeSensitive: true,
    applicationPeriod: '每年 10～11 月受理申請（適用書店經營者，非個人）',
    notes: '此項目的申請對象是書店/機構，不是個人使用者，若使用者詢問「個人閱讀補助」，此項目不適用，需誠實告知並說明查無個人適用方案。',
    sourceUrl: 'https://www.moc.gov.tw/News_Content.aspx?n=105&s=186301',
    sourceExcerpt:
      '文化部推動實體書店發展補助：補助目的是發揮實體書店文化及知識平臺功能，促進實體書店整體發展。申請對象為實際營運之實體書店，或與實體書店相關之國內立案獨資、合夥事業、法人或團體……申請期程為每年10至11月，請於期限內至文化部獎補助資訊網進行線上申請。',
    lastVerifiedDate: '2026-07-28',
    locations: [{ name: '文化部獎補助資訊網', website: 'https://grants.moc.gov.tw/Web/' }],
  },
]
