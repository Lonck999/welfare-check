import type { SeedBenefit } from './types.js'

/** 全國統一制度，不分縣市 */
export const digitalDevelopmentSubsidySeeds: SeedBenefit[] = [
  {
    categoryNumber: 52,
    name: '數位發展部補助',
    agency: '數位發展部數位產業署',
    county: null,
    description:
      '數位發展部數位產業署「DIGITAL+ 數位創新補助平台計畫」提供數位服務創新補助計畫，扶植數位轉型與創新應用，適用對象以企業/團體為主。',
    searchGroup: '一般性優惠與便民服務',
    isTimeSensitive: false,
    applicationPeriod: '依平台公告受理期程',
    notes:
      '⚠️ 重要澄清：SKILL.md 原描述的「數位學習券」實為教育部「終身學習券」（新生券每張折抵 1,500 元、舊生券每張折抵 1,000 元，另有館所通行票，適用社區大學/樂齡大學課程，年滿 6 歲、具中華民國國籍即可申請，2026 年登記時間為 5/1～5/21），並非數位發展部主管業務，屬第 46 類教育補助範疇的相關項目，建議之後把「終身學習券」移至第 46 類或另建獨立類別，避免主管機關張冠李戴。數位發展部本身對一般民眾（尤其偏鄉數位機會中心）的直接補助項目，本次搜尋未查得具體個人適用方案，需另行查證。',
    sourceUrl: 'https://digiplus.adi.gov.tw/assets/aux_application_note.pdf',
    sourceExcerpt: '數位發展部數位產業署 DIGITAL+數位創新補助平台計畫【數位服務創新補助計畫】申請須知。',
    lastVerifiedDate: '2026-07-28',
    locations: [{ name: '數位發展部數位產業署', website: 'https://www.moda.gov.tw/' }],
  },
]
