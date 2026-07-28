import type { SeedBenefit } from './types.js'
import { ALL_22_COUNTIES } from './counties.js'

const LAST_VERIFIED_DATE = '2026-07-28'

/** 全國統一制度，不分縣市；地方仲介費補助因縣市而異（詳見縣市明細列） */
export const foreignCaregiverSeeds: SeedBenefit[] = [
  {
    categoryNumber: 27,
    name: '外籍家庭看護工申請',
    agency: '衛生福利部／勞動部勞動力發展署',
    county: null,
    description:
      '申請聘僱外籍家庭看護工原則須經巴氏量表評估失能程度，但自 2025 年 8 月 1 日起，80 歲以上者、70～79 歲第二期以上癌症患者、已連續使用長照服務（居家/日間/家庭喘息）滿 6 個月者、經診斷輕度以上失智（CDR ≥ 1）者、極重度身心障礙或特定病況者（如全癱臥床、24 小時使用呼吸器或維生設備、植物人狀態）可免評估申請。巴氏量表由醫院開立，費用約 300～1,900 元（各醫院收費不同）。2026 年基本工資調整為 29,500 元後，雇主健保費負擔調整為 1,428 元、勞工負擔 458 元。',
    searchGroup: '醫療與健康類',
    isTimeSensitive: false,
    applicationPeriod: '常態受理',
    eligibilityConditions: { requiredFlags: ['severe_disability_or_dementia'] },
    sourceUrl: 'https://mimd.com.tw/blog/foreign-caregiver-2025-barthel-exemption',
    sourceExcerpt:
      'Starting from August 1, 2025, individuals aged 80 and above, as well as those aged 70-79 with stage 2 cancer or above, can apply to hire foreign domestic care workers without a Barthel Scale assessment. Other groups that can apply without the Barthel Scale include: Those using long-term care services…continuously for 6 months or more; Those diagnosed with dementia at mild level or above (CDR score ≥1)……Following the 2026 basic wage adjustment to 29,500 Taiwan dollars, the employer\'s health insurance contribution for foreign care workers has been adjusted to 1,428 yuan, and the worker\'s contribution to 458 yuan.',
    lastVerifiedDate: LAST_VERIFIED_DATE,
    documents: ['巴氏量表評估報告（或免評估證明文件）', '身心障礙證明/長照使用證明（適用免評估者）'],
    locations: [
      { name: '衛生福利部', website: 'https://www.mohw.gov.tw/' },
      { name: '勞動部勞動力發展署（跨國勞動力管理）', website: 'https://www.wda.gov.tw/' },
    ],
  },
  {
    categoryNumber: 27,
    name: '中低收入戶外籍看護薪資補助（全國統一）',
    agency: '勞動部勞動力發展署',
    county: null,
    description:
      '經濟弱勢雇主（符合低收入戶/中低收入戶/領取中低收入老人生活津貼/領取身心障礙者生活補助費資格者）聘僱外籍看護工可免繳就業安定費（每季由勞動部自動比對資格，符合者直接減免每月 2,000 元安定費，免自行申請）。過去曾有薪資補助每月 3,000 元、最長 3 年、最高 108,000 元，惟該波受理僅限 111/8/10～114/8/9 有效聘僱期間者，應於 114/8/11 前提出申請，目前是否仍開放新申請需另行確認。',
    searchGroup: '醫療與健康類',
    isTimeSensitive: false,
    applicationPeriod: '就業安定費減免為常態性自動比對；薪資補助（如仍開放）依當年度公告期程受理',
    notes: '⚠️ 薪資補助方案的申請期限資訊已知的是舊制截止日 114/8/11，是否已有新一期方案本次搜尋未查得明確資料，需洽勞動部勞動力發展署確認目前是否仍可申請。',
    eligibilityConditions: { incomeThreshold: 'mid_low_income', requiredFlags: ['has_foreign_caregiver'] },
    sourceUrl: 'https://laws.mol.gov.tw/FLAW/FLAWDAT0202.aspx?id=FL099446',
    sourceExcerpt:
      '經濟弱勢雇主（符合低收入戶、中低收入戶、領取中低收入老人生活津貼或領取身心障礙者生活補助費資格者）可免繳納就業安定費。目前一般雇主外籍看護費用補助已終止，只有經濟弱勢雇主每月補助3,000元，最多補助3年，外籍看護費用補助最高108,000元，有效聘僱期間為111年8月10日至114年8月9日之間者，應於114年8月11日前提出申請……符合弱勢資格的雇主，勞動部每季會自動比對，符合者直接減免每月2,000元的安定費。',
    lastVerifiedDate: LAST_VERIFIED_DATE,
    documents: ['低收入戶/中低收入戶/身障或老人津貼證明'],
    locations: [{ name: '勞動部勞動力發展署', website: 'https://www.wda.gov.tw/' }],
  },
]

const CAREGIVER_UNCONFIRMED_NOTE = '本次搜尋未查得此縣市聘雇外籍看護仲介費補助的具體金額與資格門檻，需依居住縣市另行洽詢社會局確認。'

const countyRows: SeedBenefit[] = ALL_22_COUNTIES.map((county) => ({
  categoryNumber: 27,
  name: '聘雇外籍看護仲介費補助（地方明細）',
  agency: `${county}政府社會局`,
  county,
  description: `${county}的聘雇外籍看護仲介費補助方案：${CAREGIVER_UNCONFIRMED_NOTE}`,
  searchGroup: '醫療與健康類',
  isTimeSensitive: false,
  applicationPeriod: '常態受理',
  notes: '⚠️ ' + CAREGIVER_UNCONFIRMED_NOTE,
  eligibilityConditions: { incomeThreshold: 'mid_low_income', counties: [county] },
  sourceUrl: 'https://mercycare.com.tw/21%E7%B8%A3%E5%B8%82%E7%9C%8B%E8%AD%B7%E8%A3%9C%E5%8A%A9%E4%B8%80%E8%A6%BD%E8%A1%A8',
  sourceExcerpt: '各縣市確實有看護補助措施，但仲介費補助部分未在既有整理表中詳細列出，需另行查證各縣市社會局最新公告。',
  lastVerifiedDate: LAST_VERIFIED_DATE,
  locations: [{ name: `${county}政府社會局` }],
}))

foreignCaregiverSeeds.push(...countyRows)
