import type { SeedBenefit } from './types.js'

/** 全國統一制度，不分縣市 */
export const childVaccinationSeeds: SeedBenefit[] = [
  {
    categoryNumber: 48,
    name: '兒童公費疫苗與預防保健',
    agency: '衛生福利部疾病管制署／國民健康署',
    county: null,
    description:
      '未滿 7 歲兒童依現行兒童預防接種時程接種公費疫苗，包含出生 24 小時內 B 型肝炎第 1 劑、卡介苗（約 5 個月大）、五合一疫苗、1 歲時公費水痘疫苗第 1 劑等；接種時程與細節詳列於「兒童健康手冊」。合約院所同時提供健兒門診與健康手冊相關檢查項目。腸病毒 71 型、輪狀病毒、公費以外流感疫苗等屬自費項目。',
    searchGroup: '醫療與健康類',
    isTimeSensitive: false,
    applicationPeriod: '依兒童健康手冊時程常態受理',
    notes: '⚠️ 兒童牙齒塗氟/口腔檢查補助本次搜尋未查得明確全國統一資訊，多數縣市有牙齒塗氟服務但細節需另洽當地衛生所確認，可能屬縣市層級補助，需另建檔查證。',
    eligibilityConditions: { requiresChildUnder: 7 },
    sourceUrl: 'https://www.cdc.gov.tw/Category/Page/TxRW-x3WzvPhvEtxM628GA',
    sourceExcerpt:
      '現行兒童預防接種時程表（兒童常規疫苗）……常見的公費疫苗包括卡介苗（通常在新生兒滿5個月時施打）、B型肝炎（出生24小時內第1劑）……水痘疫苗（1歲時公費提供第一劑）。',
    lastVerifiedDate: '2026-07-28',
    documents: ['兒童健康手冊', '兒童健保卡'],
    locations: [
      { name: '衛生福利部疾病管制署', website: 'https://www.cdc.gov.tw/' },
      { name: '各縣市合約診所與衛生所' },
    ],
  },
]
