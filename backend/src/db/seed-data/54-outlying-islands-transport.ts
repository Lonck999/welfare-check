import type { SeedBenefit } from './types.js'

const SOURCE_URL = 'https://law.moj.gov.tw/LawClass/LawAll.aspx?PCODE=K0090035'
const SOURCE_EXCERPT =
  '設籍於澎湖縣、金門縣、連江縣（馬祖）以及臺東縣蘭嶼鄉、綠島鄉的居民，搭乘國內定期航線班機往返其戶籍地時，可申請票價補貼。補貼額度：澎湖縣馬公機場航線及金門縣尚義機場航線為全額客運票價20%；連江縣南竿/北竿機場航線為30%；澎湖縣七美/望安機場及臺東縣蘭嶼/綠島機場航線為40%。'
const LAST_VERIFIED_DATE = '2026-07-28'

/** 依「離島地區居民航空票價補貼辦法」，此類福利本質上只適用於特定離島縣市，不適用全國22縣市清單 */
export const outlyingIslandsTransportSeeds: SeedBenefit[] = [
  {
    categoryNumber: 54,
    name: '離島居民航空票價補貼',
    agency: '交通部',
    county: '澎湖縣',
    description: '設籍澎湖縣居民搭乘馬公機場航線可獲全額客運票價 20% 補貼；七美、望安機場航線補貼比例提高至 40%。',
    searchGroup: '地方政府與其他非同戶籍',
    isTimeSensitive: false,
    applicationPeriod: '常態受理',
    eligibilityConditions: { counties: ['澎湖縣'] },
    sourceUrl: SOURCE_URL,
    sourceExcerpt: SOURCE_EXCERPT,
    lastVerifiedDate: LAST_VERIFIED_DATE,
    documents: ['戶籍證明'],
    locations: [{ name: '澎湖縣政府', website: 'https://www.penghu.gov.tw/' }],
  },
  {
    categoryNumber: 54,
    name: '離島居民航空票價補貼',
    agency: '交通部',
    county: '金門縣',
    description: '設籍金門縣居民搭乘尚義機場航線可獲全額客運票價 20% 補貼。',
    searchGroup: '地方政府與其他非同戶籍',
    isTimeSensitive: false,
    applicationPeriod: '常態受理',
    eligibilityConditions: { counties: ['金門縣'] },
    sourceUrl: SOURCE_URL,
    sourceExcerpt: SOURCE_EXCERPT,
    lastVerifiedDate: LAST_VERIFIED_DATE,
    documents: ['戶籍證明'],
    locations: [{ name: '金門縣政府', website: 'https://www.kinmen.gov.tw/' }],
  },
  {
    categoryNumber: 54,
    name: '離島居民航空票價補貼',
    agency: '交通部',
    county: '連江縣',
    description: '設籍連江縣（馬祖）居民搭乘南竿/北竿機場航線可獲全額客運票價 30% 補貼。',
    searchGroup: '地方政府與其他非同戶籍',
    isTimeSensitive: false,
    applicationPeriod: '常態受理',
    eligibilityConditions: { counties: ['連江縣'] },
    sourceUrl: SOURCE_URL,
    sourceExcerpt: SOURCE_EXCERPT,
    lastVerifiedDate: LAST_VERIFIED_DATE,
    documents: ['戶籍證明'],
    locations: [{ name: '連江縣政府', website: 'https://www.matsu.gov.tw/' }],
  },
  {
    categoryNumber: 54,
    name: '離島居民航空票價補貼（蘭嶼/綠島）',
    agency: '交通部',
    county: '臺東縣',
    description:
      '設籍臺東縣蘭嶼鄉、綠島鄉居民搭乘蘭嶼機場、綠島機場航線可獲全額客運票價 40% 補貼。另有船票資訊參考：台東至蘭嶼來回船票約 2,300 元、台東至綠島單程約 560 元/來回約 1,120 元；⚠️ 本次搜尋未查得船票價格是否有政府補助機制，僅為市價參考，需另行查證。',
    searchGroup: '地方政府與其他非同戶籍',
    isTimeSensitive: false,
    applicationPeriod: '常態受理',
    notes: '此補貼僅適用臺東縣「蘭嶼鄉、綠島鄉」設籍居民，非臺東縣全縣居民皆適用，查詢時需特別確認鄉鎮別。',
    eligibilityConditions: { counties: ['臺東縣'] },
    sourceUrl: SOURCE_URL,
    sourceExcerpt: SOURCE_EXCERPT,
    lastVerifiedDate: LAST_VERIFIED_DATE,
    documents: ['戶籍證明（蘭嶼鄉/綠島鄉）'],
    locations: [{ name: '臺東縣政府', website: 'https://www.taitung.gov.tw/' }],
  },
]
