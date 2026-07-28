import type { SeedBenefit } from './types.js'

/** 全國統一資格門檻（低收入戶/中低收入戶/身心障礙），不分縣市；優惠內容依電信業者略有差異 */
export const telecomDiscountsSeeds: SeedBenefit[] = [
  {
    categoryNumber: 25,
    name: '通訊費優惠（NCC 弱勢族群電信方案）',
    agency: '國家通訊傳播委員會（NCC）',
    county: null,
    description:
      '持有效期內低收入戶/中低收入戶證明或身心障礙證明者，可向電信業者申辦弱勢族群優惠資費方案（如中華電信「暖心方案」）：優惠期 2 年，期滿仍持有證明可憑證續辦；行動方案月租費減收最高 200 元並加贈免費 Wi-Fi 上網；寬頻方案最高享牌告價 5 折優惠。依戶籍地址一證號限辦一門優惠。',
    searchGroup: '一般性優惠與便民服務',
    isTimeSensitive: false,
    applicationPeriod: '常態受理，優惠期 2 年，期滿可憑有效證明續辦',
    notes: '優惠內容依電信業者（中華電信/台灣大哥大/遠傳等）方案略有差異，此為中華電信「暖心方案」查證結果，其餘業者需另行查證各自資費內容。SKILL.md 另列「中低收入戶 電話費補助 減免」為獨立搜尋語句，本次多次搜尋皆指向同一個 NCC 電信業者優惠方案，未查得縣市政府另外提供的獨立現金電話費補助，判斷這是同一件事的不同措辭，非兩個不同的福利項目；若之後確認真有獨立的縣市電話費現金補助，需另外建檔。',
    eligibilityConditions: { incomeThreshold: 'mid_low_income' },
    sourceUrl: 'https://accessibility.cht.com.tw/home/accessibility/package.html',
    sourceExcerpt:
      '低/中低收入戶可以領有政府機關核發仍於效期內之低/中低收入戶證明（含在學子女），依戶籍地址一證號限辦一門優惠……低收入戶、中低收入戶者申請，優惠2年，期滿恢復牌告價，惟期滿仍具低收入戶、中低收入戶證明者，憑證可辦理續享2年優惠。',
    lastVerifiedDate: '2026-07-28',
    documents: ['低收入戶/中低收入戶證明或身心障礙證明（效期內）'],
    locations: [
      { name: '國家通訊傳播委員會', website: 'https://www.ncc.gov.tw/' },
      { name: '各電信業者門市（中華電信/台灣大哥大/遠傳等）' },
    ],
  },
]
