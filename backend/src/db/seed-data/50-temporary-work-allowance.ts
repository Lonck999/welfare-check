import type { SeedBenefit } from './types.js'

/** 全國統一制度，不分縣市 */
export const temporaryWorkAllowanceSeeds: SeedBenefit[] = [
  {
    categoryNumber: 50,
    name: '就業保險臨時工作津貼與求職關懷',
    agency: '勞動部勞動力發展署',
    county: null,
    description:
      '失業中且有工作能力與意願者，於公立就業服務機構辦理求職登記 14 日內未能推介就業，或有正當理由拒絕推介工作（薪資低於原投保薪資 60% 或工作地點距住家逾 30 公里），可申請臨時工作津貼，按中央主管機關公告時薪計算、每月不超過基本工資，最長 6 個月（2 年內合併領取同性質政府津貼合計不超過 6 個月）。適用對象包含獨力負擔家計者、中高齡者、身心障礙者、原住民、低收入/中低收入戶、長期失業者、二度就業婦女、家暴受害者、更生受保護人、職災勞工等。',
    searchGroup: '現金與生活補助類',
    isTimeSensitive: true,
    applicationPeriod: '常態受理，但每次核發最長 6 個月，2 年內合併領取上限 6 個月',
    eligibilityConditions: { requiredFlags: ['unemployed'] },
    sourceUrl: 'https://law.moj.gov.tw/LawClass/LawAll.aspx?pcode=N0090025',
    sourceExcerpt:
      '申請人須具工作能力及工作意願……非自願離職、就業服務法第24條第1項所列失業者（獨力負擔家計者、中高齡者、身心障礙者、原住民、低收入或中低收入戶有工作能力者、長期失業者、二度就業婦女、家暴受害者、更生受保護人、職災勞工等）……補助以中央主管機關公告之時薪計算，每月不超過基本工資，最長6個月，2年內合併領取同性質政府津貼合計不得超過6個月。',
    lastVerifiedDate: '2026-07-28',
    documents: ['身分證', '求職登記證明', '金融機構帳戶存摺影本'],
    locations: [{ name: '各地公立就業服務站（勞動力發展署所屬分署）', website: 'https://www.wda.gov.tw/' }],
  },
]
