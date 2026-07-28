import type { SeedBenefit } from './types.js'

/** 中央「特殊境遇家庭扶助條例」訂定全國統一基準，地方政府執行時項目/金額可能略有差異 */
export const specialCircumstanceFamilySeeds: SeedBenefit[] = [
  {
    categoryNumber: 3,
    name: '特殊境遇婦女/家庭扶助',
    agency: '衛生福利部（特殊境遇家庭扶助條例）',
    county: null,
    description:
      '家庭總收入按人口平均每人每月未超過最低生活費 2.5 倍及臺灣地區平均每人每月消費支出 1.5 倍，且家庭財產未超過中央公告一定金額，並符合以下情形之一：配偶死亡或失蹤、因配偶惡意遺棄或受虐待經判決離婚、遭受家庭暴力、未婚懷孕婦女懷胎 3 個月以上至分娩 2 個月內等。補助項目：緊急生活扶助、子女生活津貼（每名子女每月補助當年度最低工資 1/10，每年申請一次）、子女教育補助、傷病醫療補助（醫療費用逾 3 萬元，最高補助 70%，1 年最高補助 12 萬元）、兒童托育津貼（6 歲以下子女讀私立幼托機構，每名每月補助 1,500 元）、法律訴訟補助、創業貸款補助。',
    searchGroup: '時效性最高項目',
    isTimeSensitive: false,
    applicationPeriod: '常態受理',
    notes: '⚠️ 各縣市對此扶助的實際補助內容與金額有一定差異，本次僅查得中央法規規定的基準框架，精確金額需依居住縣市另行洽詢社會局確認。',
    eligibilityConditions: { requiredFlags: ['special_circumstance_family'] },
    sourceUrl: 'https://www.sfaa.gov.tw/SFAA/Pages/Detail.aspx?nodeid=99&pid=404',
    sourceExcerpt:
      '特殊境遇家庭指申請人其家庭總收入按全家人口平均分配，每人每月未超過政府當年公布最低生活費二點五倍及臺灣地區平均每人每月消費支出一點五倍……符合資格的情形包括：配偶死亡或失蹤、因配偶惡意遺棄或受虐待經判決離婚、家庭暴力受害、未婚懷孕婦女懷胎三個月以上至分娩二個月內等……子女生活津貼每一名子女或孫子女每月補助當年度最低工資之十分之一……兒童托育津貼為6歲以下子女讀私立幼托機構，每名子女每月補助1,500元。',
    lastVerifiedDate: '2026-07-28',
    documents: ['離婚/家暴/未婚懷孕等身分證明', '財力證明', '戶籍謄本'],
    locations: [{ name: '戶籍地政府社會局' }],
  },
]
