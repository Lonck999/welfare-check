import type { SeedBenefit } from './types.js'

/** 全國統一制度，不分縣市（各地榮民服務處為執行窗口，制度本身全國一致） */
export const veteransAffairsBenefitsSeeds: SeedBenefit[] = [
  {
    categoryNumber: 44,
    name: '退輔會補助（退伍軍人就業/就醫/子女教育）',
    agency: '國軍退除役官兵輔導委員會',
    county: null,
    description:
      '退伍軍人可申請「促進退除役官兵穩定就業津貼」（含推介就業穩定津貼、職業訓練訓後就業穩定津貼）、免費職業訓練（餐飲、資訊、精密機械、物業管理、機械維修等七大類課程）；公費就養榮民於退輔會所屬醫療機構住院可獲膳食費補助，特定保險身分或低收入戶另有病房費補助；眷屬可申請輪椅、助聽器、眼鏡、假牙等輔具補助。',
    searchGroup: '特殊身分族群類',
    isTimeSensitive: false,
    applicationPeriod: '常態受理',
    notes:
      '⚠️ 子女教育補助、安養補助的具體金額本次搜尋未查得明確數字，需洽當地榮民服務處或退輔會服務專線確認最新金額。',
    eligibilityConditions: { requiredIdentities: ['退伍軍人'] },
    sourceUrl: 'https://www.vac.gov.tw/lp-3097-1.html',
    sourceExcerpt:
      '促進退除役官兵穩定就業津貼……包括「職業訓練訓後就業穩定津貼」（post-training employment stabilization subsidy）和「推介就業穩定津貼」（referral employment stabilization subsidy），協助退除役官兵獲得穩定就業。',
    lastVerifiedDate: '2026-07-28',
    locations: [
      {
        name: '國軍退除役官兵輔導委員會（各地榮民服務處）',
        phone: '(02)2725-5700 / 0800-212-154 / 0800-212-510',
        website: 'https://www.vac.gov.tw/',
      },
    ],
  },
]
