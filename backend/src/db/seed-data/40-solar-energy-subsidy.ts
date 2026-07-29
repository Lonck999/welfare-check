import type { SeedBenefit } from './types.js'

/** 中央基本獎勵全國統一，不分縣市；部分縣市另有地方加碼（需另行查證） */
export const solarEnergySubsidySeeds: SeedBenefit[] = [
  {
    categoryNumber: 40,
    name: '太陽能/綠能裝設補助（屋頂型光電獎勵）',
    agency: '經濟部能源署',
    county: null,
    description:
      '私有建築物屋頂設置太陽光電發電設備，於 114 年 1 月 1 日起取得主管機關核發設備登記文件、屋頂面積 1,000 平方公尺以下、使用符合台灣高效能太陽光電模組技術規範之新品設備，可申請基本獎勵：每瓩 3,000 元，同一幢建築物累計上限 30 萬元；採自發自用餘電躉售並加裝 ATS 者每瓩可達 2 萬元，上限 200 萬元。裝設後可將餘電售予台電獲得收益（餘電躉購）。依法令負有設置義務者（如特定工廠、用電大戶）不具申請資格。房屋所有人須為申請人，借住情況下須由屋主出面申請。',
    searchGroup: '一般性優惠與便民服務',
    isTimeSensitive: false,
    applicationPeriod: '常態受理',
    notes:
      '⚠️ 部分縣市（如台南、高雄）另有地方加碼補助，需依居住縣市另行查證各地方政府能源相關單位公告。另外，本次搜尋到的「儲能設備補助」實為「產業儲能設備設置補助要點」，適用對象為產業/企業級儲能系統，非一般家戶個人可申請的儲能設備補助，兩者不可混為一談；若使用者是一般民眾詢問住宅用儲能設備補助，本次搜尋未查得專屬個人申請的方案，需另行查證是否有住宅級儲能補助。',
    eligibilityConditions: { requiresOwnedHome: true },
    sourceUrl: 'https://www.solargarden.com.tw/press/2614',
    sourceExcerpt:
      '申請人須於私有建築物屋頂設置太陽光電發電設備……建築頂層面積須在1,000平方公尺以下，設備須為新品……2026年太陽光電基本獎勵為每瓩3,000元，上限30萬元；採自發自用餘電躉售並加裝ATS者每瓩可達2萬元，上限200萬元……依法令負有設置義務者（如特定工廠申請用地計畫、用電大戶等）不具申請資格。',
    lastVerifiedDate: '2026-07-28',
    documents: ['建物所有權證明', '設備登記文件'],
    locations: [{ name: '經濟部能源署', website: 'https://www.moeaea.gov.tw/' }],
  },
]
