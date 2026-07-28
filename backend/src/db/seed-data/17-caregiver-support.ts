import type { SeedBenefit } from './types.js'
import { ALL_22_COUNTIES } from './counties.js'

const LAST_VERIFIED_DATE = '2026-07-28'

/** 全國統一制度，不分縣市（縣市層級照顧者現金津貼需另行查詢） */
export const caregiverSupportSeeds: SeedBenefit[] = [
  {
    categoryNumber: 17,
    name: '照顧者支持（家庭照顧假/喘息服務）',
    agency: '勞動部／衛生福利部',
    county: null,
    description:
      '(1) 家庭照顧假：每年最多可請 7 天，可以「小時」為單位彈性請假，適用對象含直系親屬或配偶及其父母（父母、子女、配偶、公婆、岳父母），於家庭成員預防接種、罹患嚴重疾病、其他重大事故且須親自照顧時可申請；(2) 長照喘息服務：2026 年新制放寬，若被照顧者評估為重度失能（7～8 級），外籍看護短暫休假（如週末）時家屬可直接申請喘息服務，不再受限於「看護需請假 30 天以上」的舊規定，聘僱外籍看護與申請政府長照資源不再互斥。',
    searchGroup: '就業與勞工權益類',
    isTimeSensitive: false,
    applicationPeriod: '常態受理，家庭照顧假需即時檢附相關證明',
    notes: '⚠️ 縣市層級的照顧者現金津貼本次搜尋未查得統一標準，需依居住縣市另行洽詢社會局確認。長照喘息服務的補助額度詳見第 9 類。',
    eligibilityConditions: { requiredFlags: ['has_care_recipient'] },
    sourceUrl: 'https://www.businessweekly.com.tw/careers/blog/3020943',
    sourceExcerpt:
      '家庭照顧假每年最多可請7天，以「小時」為單位請假，不用一次請一整天……可照顧的對象包括直系親屬或配偶及其父母，如父母、子女、配偶、公婆、岳父母……若被照顧者經評估為重度失能（7-8 級），外籍看護短暫休假（如週末）時，家屬可直接申請喘息服務，無需受限於過去「看護需請假30天以上」的規定。',
    lastVerifiedDate: LAST_VERIFIED_DATE,
    documents: ['家庭成員患病/事故證明（家庭照顧假適用）', '失能評估證明（喘息服務適用）'],
    locations: [{ name: '1966 長照專線', phone: '1966' }],
  },
]

const CAREGIVER_ALLOWANCE_UNCONFIRMED_NOTE = '本次搜尋未查得此縣市家庭照顧者現金津貼的具體金額與資格門檻，需依居住縣市另行洽詢社會局確認。'

const countyRows: SeedBenefit[] = ALL_22_COUNTIES.map((county) => ({
  categoryNumber: 17,
  name: '照顧者現金津貼（地方明細）',
  agency: `${county}政府社會局`,
  county,
  description: `${county}的家庭照顧者現金津貼方案：${CAREGIVER_ALLOWANCE_UNCONFIRMED_NOTE}`,
  searchGroup: '就業與勞工權益類',
  isTimeSensitive: false,
  applicationPeriod: '常態受理',
  notes: '⚠️ ' + CAREGIVER_ALLOWANCE_UNCONFIRMED_NOTE,
  eligibilityConditions: { requiredFlags: ['has_care_recipient'], counties: [county] },
  sourceUrl: 'https://www.mohw.gov.tw/',
  sourceExcerpt: '各縣市社會局可能自辦家庭照顧者現金津貼或喘息服務加碼，惟本次搜尋未查得逐縣市清單，需另行查證。',
  lastVerifiedDate: LAST_VERIFIED_DATE,
  locations: [{ name: `${county}政府社會局` }],
}))

caregiverSupportSeeds.push(...countyRows)
