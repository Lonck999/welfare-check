/**
 * 前端填表欄位 ↔ ApplicantProfile/requiredFlags 對照表。
 *
 * 對應 eligibility.ts 檔頭註解提到的「待辦」：56 大類 seed 資料裡的 requiredFlags 是用
 * 自由字串表達（例如 'pregnant_or_recent_birth'、'disability_certificate'），這裡把目前
 * seed-data/*.ts 實際用到的旗標值全部收斂成一份清單，搭配中文說明，前端表單直接依此清單
 * 產生複選項，避免前端自己發明字串跟資料庫裡的值對不上。
 *
 * 新增 seed 資料使用到新的 requiredFlags 值時，務必回頭在這裡補上對應項目，
 * 否則前端永遠無法勾選出那個旗標，該福利項目會一直卡在「缺資料」（⚠️ 可能符合）。
 */

export interface FlagOption {
  value: string
  label: string
}

export const FLAG_OPTIONS: FlagOption[] = [
  { value: 'pregnant_or_recent_birth', label: '本人或配偶懷孕中／產後 12 個月內' },
  { value: 'miscarriage', label: '近 1 年內有流產／小產' },
  { value: 'special_circumstance_family', label: '特殊境遇家庭（單親監護權／喪偶未成年子女／家暴／未婚生子）' },
  { value: 'acute_hardship', label: '近期急難情形（非自願離職、重大傷病、天災、家暴等突發困境）' },
  { value: 'catastrophic_illness', label: '持有健保重大傷病卡' },
  { value: 'disability_certificate', label: '本人或同戶家人領有身心障礙手冊／證明' },
  { value: 'has_disability_or_dementia_member', label: '家中有失能／失智／行動不便需照顧的成員' },
  { value: 'severe_disability_or_dementia', label: '家中有嚴重失能／失智成員（達巴氏量表聘僱外籍看護工等級）' },
  { value: 'has_foreign_caregiver', label: '已聘僱外籍看護工' },
  { value: 'has_care_recipient', label: '需請家庭照顧假或喘息服務照顧家人' },
  { value: 'is_employed_or_insured', label: '目前為受僱員工或已加保勞健保' },
  { value: 'is_employed', label: '目前有工作' },
  { value: 'unemployed', label: '目前失業中或 6 個月內非自願離職' },
  { value: 'has_labor_insurance', label: '有加保勞工保險' },
  { value: 'has_labor_insurance_or_national_pension', label: '有加保勞保或國民年金' },
  { value: 'enrolled_national_pension', label: '有加保國民年金' },
  { value: 'occupational_injury', label: '曾遭遇職業災害' },
  { value: 'has_startup_intent', label: '有創業意願或正在籌備創業計畫' },
  { value: 'has_dependents_or_ltc_needs', label: '有扶養需長期照顧的親屬' },
  { value: 'spouse_no_income', label: '配偶目前無工作／無收入' },
  { value: 'infertility_treatment_needed', label: '有不孕症／人工生殖需求' },
  { value: 'wants_to_quit_smoking', label: '有戒菸意願' },
  { value: 'returning_to_education', label: '想重返學校進修（回流教育／成人進修）' },
  { value: 'is_student', label: '本人、配偶或子女為國中以上在學學生' },
  {
    value: 'developmental_delay_suspected_or_diagnosed',
    label: '家中有未滿 6 歲子女有發展遲緩疑似或已診斷情形',
  },
  { value: 'recent_natural_disaster_damage', label: '近期遭遇風災／震災／水災導致房屋或財產受損' },
  { value: 'rare_disease_certificate', label: '本人或同戶家人領有罕見疾病證明' },
  { value: 'legal_dispute_or_consultation_needed', label: '目前有法律糾紛或需要法律諮詢（租屋、勞資、婚姻等）' },
]

export interface IdentityOption {
  value: string
  label: string
}

/** 對應 SKILL.md 第 14 題特殊身分（僑民/僑生因需求相近，仍拆兩個獨立勾選項） */
export const IDENTITY_OPTIONS: IdentityOption[] = [
  { value: '原住民', label: '原住民' },
  { value: '新住民', label: '新住民（外籍配偶）' },
  { value: '客家人', label: '客家人（設籍客家文化重點發展區或自我認定）' },
  { value: '退伍軍人', label: '退伍軍人（本人或同戶家人）' },
  { value: '現役軍人', label: '現役軍人（本人或同戶家人）' },
  { value: '農民', label: '農民（本人或同戶家人，含老農津貼領取者）' },
  { value: '漁民', label: '漁民（本人或同戶家人）' },
  { value: '僑民', label: '僑民' },
  { value: '僑生', label: '僑生' },
]

/** 全體使用者一律成立，不需要前端勾選，由後端自動補上 */
export const IMPLICIT_FLAGS = ['general_public']
