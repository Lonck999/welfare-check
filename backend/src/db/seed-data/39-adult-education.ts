import type { SeedBenefit } from './types.js'

/** 全國統一制度，不分縣市（縣市成人基本教育補習班補助需另行查詢） */
export const adultEducationSeeds: SeedBenefit[] = [
  {
    categoryNumber: 39,
    name: '回流教育/成人進修補助',
    agency: '教育部',
    county: null,
    description:
      '在職或失業者重返學校就讀正規學制（學位班、學分班等）適用。私立大專校院學生：基本補助每學年 3.5 萬元，弱勢家庭學生另加碼 1.5～2 萬元，最高合計 5.5 萬元；資格：中華民國國籍、就讀國內學校、學士班（含後學士）或專科班在正規修業年限內學生。此與第 11 類「產業人才投資方案」不同，該方案適用職業訓練課程，本項適用學位班/學分班等正規學制。',
    searchGroup: '教育類',
    isTimeSensitive: false,
    applicationPeriod: '每學期開學前後受理',
    notes: '⚠️ 本次搜尋對「回流教育」專屬方案（區別於一般私立大專學費補助）的具體規定未查得明確資料，且查得資訊顯示身心障礙者扶養親屬就讀在職專班碩士班不適用回流教育認定，需洽教育部或所屬學校確認回流教育的確切定義與資格範圍。縣市層級成人基本教育補習班補助需依居住縣市另行查證。',
    eligibilityConditions: { requiredFlags: ['returning_to_education'] },
    sourceUrl: 'https://roo.cash/blog/college-subsidy-project-article/',
    sourceExcerpt:
      '2026年，私立大學基本補助35,000 TWD per academic year，學生從disadvantaged families可獲得additional 15,000-20,000 TWD，最高55,000 TWD……申請資格：中華民國國籍、國內學校在學學生、學士班或專科班在正規修業年限內學生。',
    lastVerifiedDate: '2026-07-28',
    documents: ['在學證明', '家庭經濟弱勢證明（如適用加碼）'],
    locations: [{ name: '教育部', website: 'https://www.edu.tw/' }, { name: '就讀學校學務處生活輔導組' }],
  },
]
