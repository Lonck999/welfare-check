import type { SeedBenefit } from './types.js'

/** 全國統一制度（不孕症試管嬰兒補助3.0），不分縣市；地方另有加碼需另行查詢 */
export const ivfSubsidySeeds: SeedBenefit[] = [
  {
    categoryNumber: 35,
    name: '人工生殖費用補助（不孕症試管嬰兒補助3.0）',
    agency: '衛生福利部國民健康署',
    county: null,
    description:
      '2025 年 11 月 1 日上路「不孕症試管嬰兒補助 3.0」新制：不孕夫妻至少一方具中華民國國籍且妻子未滿 45 歲即可申請（已放寬，不再要求中低收入戶資格）。非低收入戶/中低收入戶者：首次申請每胎最高 15 萬元，再次申請最高 10 萬元；低收入戶/中低收入戶者：每次補助上限 15 萬元，不限年齡與胎次。39 歲（含）以下最多補助 6 次，44 歲（含）以下最多補助 3 次。',
    searchGroup: '時效性最高項目',
    isTimeSensitive: true,
    applicationPeriod: '常態受理',
    notes:
      '⚠️ 若配偶超過 45 歲且有生育需求，應優先確認此項，時間急迫（超過 45 歲即不符資格）。此為 3.0 新制金額，與舊制（一般 15 萬/中低收入戶 20 萬）不同，SKILL.md 內文字需同步更新。地方加碼部分本次未逐一查證，需依居住縣市另行確認。另外，不孕症「檢查/診斷」費用部分本身即有健保給付（與試管嬰兒治療本身的政府補助是兩件事）；但目前人工協助生殖技術的政府補助範圍僅涵蓋「試管嬰兒（IVF）療程」，體內人工授精（IUI）不在補助範圍內，需向使用者說明清楚這個區別，避免誤以為所有人工生殖技術都有補助。',
    eligibilityConditions: { requiredFlags: ['infertility_treatment_needed'], ageMax: 45 },
    sourceUrl: 'https://www.ivftaiwan.tw/article-detail/195',
    sourceExcerpt:
      '非低收入戶及中低收入戶者，各胎首次申請試管嬰兒補助者，最高上限15萬元，再次申請者試管補助最高10萬元。中低收入戶或低收入戶之不孕夫妻：每次補助上限15萬元，不分年齡與胎次……39歲(含)以下最多補助6次，44歲(含)以下最多補助3次。衛生福利部於2025年11月1日正式上路「不孕症試管嬰兒補助3.0」新制度。',
    lastVerifiedDate: '2026-07-28',
    documents: ['不孕症診斷證明', '婚姻/國籍證明'],
    locations: [{ name: '衛生福利部國民健康署', website: 'https://www.hpa.gov.tw/' }],
  },
]
