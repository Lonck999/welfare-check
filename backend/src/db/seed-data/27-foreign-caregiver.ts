import type { SeedBenefit } from './types.js'

/** 全國統一制度，不分縣市 */
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
    notes: '⚠️ 各縣市聘雇外籍看護仲介費補助、中低收入戶外籍看護費用補助本次搜尋未查得統一標準，需另依居住縣市查證地方政府社會局公告。',
    eligibilityConditions: { requiredFlags: ['severe_disability_or_dementia'] },
    sourceUrl: 'https://mimd.com.tw/blog/foreign-caregiver-2025-barthel-exemption',
    sourceExcerpt:
      'Starting from August 1, 2025, individuals aged 80 and above, as well as those aged 70-79 with stage 2 cancer or above, can apply to hire foreign domestic care workers without a Barthel Scale assessment. Other groups that can apply without the Barthel Scale include: Those using long-term care services…continuously for 6 months or more; Those diagnosed with dementia at mild level or above (CDR score ≥1)……Following the 2026 basic wage adjustment to 29,500 Taiwan dollars, the employer\'s health insurance contribution for foreign care workers has been adjusted to 1,428 yuan, and the worker\'s contribution to 458 yuan.',
    lastVerifiedDate: '2026-07-28',
    documents: ['巴氏量表評估報告（或免評估證明文件）', '身心障礙證明/長照使用證明（適用免評估者）'],
    locations: [
      { name: '衛生福利部', website: 'https://www.mohw.gov.tw/' },
      { name: '勞動部勞動力發展署（跨國勞動力管理）', website: 'https://www.wda.gov.tw/' },
    ],
  },
]
