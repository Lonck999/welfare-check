import type { SeedBenefit } from './types.js'
import { ALL_22_COUNTIES } from './counties.js'

const LAST_VERIFIED_DATE = '2026-07-28'

/** 台電/台水為全國性事業機構，減免規則全國一致，不分縣市；瓦斯費補助因縣市/民營瓦斯行而異 */
export const utilityFeeReductionSeeds: SeedBenefit[] = [
  {
    categoryNumber: 20,
    name: '水電費減免（中低收入戶）',
    agency: '台灣電力公司／台灣自來水公司',
    county: null,
    description:
      `🔴 中央沒有「全國性低收入戶水電費減免」的規定，實際以各縣市自行辦理為主。

查證結果（2026-10-02）：
· 《社會救助法》第 16 條列舉的 7 項特殊項目救助為：產婦及嬰兒營養補助、托兒補助、教育補助、喪葬補助、居家服務、生育補助、其他必要之救助及服務 —— **不含水費、電費、瓦斯費**。且條文為「直轄市、縣（市）主管機關『得』視實際需要及財力提供」，各縣市可自行決定是否辦理。
· 台電依《電業法》第 52、53 條提供電價優惠的對象是**各級學校、社會福利機構、護理之家**，不含低收入戶家庭用電。
· 台灣自來水公司的水費減免為「用戶內線地下漏水減免」，營業章程亦無低收入戶減免。
· 常見流傳的「每月用電 110 度以下免收基本電費」為 101 年以前的電價級距（經濟部 101 年電價合理化方案已將第 1 級距由 110 度提高至 120 度），且其出處為 97 年台電研議中的社會關懷基金構想，並非現行制度。

✅ 實際可行的查詢方式：向**戶籍地公所或縣市政府社會局（處）**洽詢當地是否辦理水電費相關補助，或撥 1957 福利諮詢專線。
· 已查到的地方實例：臺北市對中低收入戶免收「分段加壓給水維護管理費」（每度 2.5 元，由臺北自來水事業處辦理，非台水公司）。`,
    searchGroup: '一般性優惠與便民服務',
    isTimeSensitive: false,
    applicationPeriod: '常態受理，取得低收入戶/中低收入戶資格後即可申請',
    notes: `⚠️ 本筆原描述引用的「對低收入戶用電優待辦法」經全國法規資料庫全文檢索**查無此法**；「110 度免收基本電費」為過時數字。已於 2026-10-02 改寫為「中央無全國性規定，依各縣市辦理」。
⚠️ 水電費減免屬各縣市自辦項目，有無與額度因縣市而異，須個別查證；瓦斯多為民營瓦斯行供應，更需洽當地。`,
    eligibilityConditions: { incomeThreshold: 'mid_low_income' },
    sourceUrl: 'https://law.moj.gov.tw/LawClass/LawSingle.aspx?pcode=D0050078&flno=16',
    sourceExcerpt:
      `《社會救助法》第 16 條：直轄市、縣（市）主管機關得視實際需要及財力，對設籍於該地之低收入戶或中低收入戶提供下列特殊項目救助及服務：一、產婦及嬰兒營養補助。二、托兒補助。三、教育補助。四、喪葬補助。五、居家服務。六、生育補助。七、其他必要之救助及服務。`,
    lastVerifiedDate: '2026-10-02',  // 🔴 本筆單獨查證，不沿用常數（22 筆瓦斯仍為 2026-07-28）
    documents: ['低收入戶/中低收入戶證明'],
    locations: [
      { name: '台灣電力公司', website: 'https://www.taipower.com.tw/' },
      { name: '台灣自來水公司', website: 'https://www.water.gov.tw/' },
      { name: '1957 福利諮詢專線', phone: '1957' },
    ],
  },
]

const GAS_UNCONFIRMED_NOTE = '本次搜尋未查得此縣市瓦斯費補助的具體金額與資格門檻，且瓦斯多為民營瓦斯行供應（非全國性事業機構），需依居住縣市另行洽詢社會局或當地瓦斯行確認。'

const gasCountyRows: SeedBenefit[] = ALL_22_COUNTIES.map((county) => ({
  categoryNumber: 20,
  name: '瓦斯費補助（地方明細）',
  agency: `${county}政府社會局`,
  county,
  description: `${county}的中低收入戶瓦斯費補助方案：${GAS_UNCONFIRMED_NOTE}`,
  searchGroup: '一般性優惠與便民服務',
  isTimeSensitive: false,
  applicationPeriod: '常態受理',
  notes: '⚠️ ' + GAS_UNCONFIRMED_NOTE,
  eligibilityConditions: { incomeThreshold: 'mid_low_income', counties: [county] },
  sourceUrl: 'https://www.mohw.gov.tw/',
  sourceExcerpt: '瓦斯費補助非台灣中油/台電等全國性事業統一辦理，各縣市及民營瓦斯行規定不同，需另行依居住縣市查證。',
  lastVerifiedDate: LAST_VERIFIED_DATE,
  locations: [{ name: `${county}政府社會局` }],
}))

utilityFeeReductionSeeds.push(...gasCountyRows)
