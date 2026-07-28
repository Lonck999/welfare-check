import type { SeedBenefit } from './types.js'

/** 全國統一制度，不分縣市 */
export const farmerFisherBenefitsSeeds: SeedBenefit[] = [
  {
    categoryNumber: 43,
    name: '農業部老農/漁民補助',
    agency: '農業部／勞動部勞工保險局',
    county: null,
    description:
      '老農津貼：農保或漁會甲類會員年資合計滿 15 年、年滿 65 歲當月即可申請（未滿 15 年但滿 6 個月以上可領半額）。排富規定：農業所得以外個人綜合所得總額門檻 60 萬元、個人土地房屋財產價值門檻 1,025 萬元（不含唯一自住房屋）。另有農民職業災害保險提供從農職災保障。',
    searchGroup: '特殊身分族群類',
    isTimeSensitive: false,
    applicationPeriod: '年滿 65 歲當月起可申請，核准後次月開始發放',
    notes:
      '⚠️ 搜尋當時找到「調漲至每月 10,000 元」為政策研議中的預估金額，實際生效金額與時間請以農業部/勞保局最新公告為準，不可直接引用未確認數字給使用者。',
    eligibilityConditions: { requiredIdentities: ['農民', '漁民'], ageMin: 65 },
    sourceUrl: 'https://www.bli.gov.tw/0017558.html',
    sourceExcerpt:
      '農民參加農保年資合計15年以上，或漁民參加漁會甲類會員之年資合計15年以上（……加保年資合計6個月以上未滿15年者，得領取半額津貼）。排富規定：個人綜合所得稅各類所得總額門檻由50萬元調整至60萬元；個人所有土地及房屋財產價值門檻由500萬元調整至1,025萬元；刪除唯一自住房屋扣除額上限。',
    lastVerifiedDate: '2026-07-28',
    documents: ['農保或漁會甲類會員證明', '身分證', '金融機構帳戶存摺影本'],
    locations: [
      { name: '戶籍所在地基層農會（老農津貼）' },
      { name: '戶籍所在地區漁會（漁民）' },
    ],
  },
]
