import type { SeedBenefit } from './types.js'
import { ALL_22_COUNTIES } from './counties.js'

const LAST_VERIFIED_DATE = '2026-07-28'

/** 全國統一制度，不分縣市（工作地點縣市勞工局另有各自加碼補助，需另行查詢） */
export const employmentSubsidySeeds: SeedBenefit[] = [
  {
    categoryNumber: 11,
    name: '就業補助（產業人才投資方案）',
    agency: '勞動部勞動力發展署',
    county: null,
    description:
      '年滿 15 歲、具就業保險/勞工保險/農民健康保險被保險人身分之在職勞工可申請。2025 年度起補助總額度由 3 年 7 萬元提升至 3 年 10 萬元，一般申請「部分補助」按訓練單位收費 80%；特定對象（生活扶助戶有工作能力者、原住民、身心障礙者、中高齡者、獨力負擔家計者、中低收入戶、65 歲以上者）可獲全額補助。免事先申請，結訓合格後由訓練單位填寫申請書送審，核對資料後 2 個月內撥款至個人帳戶。',
    searchGroup: '就業與勞工權益類',
    isTimeSensitive: false,
    applicationPeriod: '常態受理（課程結訓後由訓練單位代為申請撥款）',
    notes: '⚠️ 減班休息勞工再充電計畫（訓練生活津貼）與產業創新人才海外培訓計畫的具體金額本次搜尋未查得，需洽勞動部勞動力發展署確認。另工作地點縣市勞工局的地方加碼補助需依工作地點另行查詢，非本項全國統一制度涵蓋範圍。',
    eligibilityConditions: { requiredFlags: ['is_employed_or_insured'] },
    sourceUrl: 'https://bewithnene.tw/jobstraining/',
    sourceExcerpt:
      '申請人需年滿15歲以上，具就業保險、勞工保險或農民健康保險被保險人身分之在職勞工……自114年度（2025年）起，補助金額由3年內7萬元提升至3年10萬元。一般民眾申請「部分補助」，按照訓練單位的收費標準，補助課程80%費用……特定對象勞工（包含生活扶助戶中有工作能力者、原住民、身心障礙者、中高齡者、獨力負擔家計者）、中低收入戶、六十五歲以上者等，符合補助全額訓練費用。',
    lastVerifiedDate: LAST_VERIFIED_DATE,
    documents: ['勞保/就保/農保投保證明'],
    locations: [{ name: '台灣就業通在職訓練網', website: 'https://www.taiwanjobs.gov.tw/' }],
  },
]

const LABOR_BUREAU_UNCONFIRMED_NOTE =
  '本次搜尋未查得此工作地點縣市勞工局的具體加碼補助項目與金額，各縣市勞工局多有自辦的職訓/求職/創業等補助，性質類似第 12 類「地方政府專屬補助」，需依工作地點縣市另行查證當地勞工局公告，本項清單無法窮舉所有地方方案。'

const countyRows: SeedBenefit[] = ALL_22_COUNTIES.map((county) => ({
  categoryNumber: 11,
  name: '工作地點縣市勞工局補助（地方明細）',
  agency: `${county}政府勞工局`,
  county,
  description: `${county}勞工局的地方補助方案：${LABOR_BUREAU_UNCONFIRMED_NOTE}`,
  searchGroup: '就業與勞工權益類',
  isTimeSensitive: false,
  applicationPeriod: '常態受理',
  notes: '⚠️ ' + LABOR_BUREAU_UNCONFIRMED_NOTE,
  eligibilityConditions: { requiredFlags: ['is_employed_or_insured'], counties: [county] },
  sourceUrl: 'https://www.wda.gov.tw/',
  sourceExcerpt: '各縣市勞工局多有自辦職訓/求職/創業等補助方案，惟本次搜尋未查得逐縣市清單，需另行查證。',
  lastVerifiedDate: LAST_VERIFIED_DATE,
  locations: [{ name: `${county}政府勞工局` }],
}))

employmentSubsidySeeds.push(...countyRows)
