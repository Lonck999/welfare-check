import type { SeedBenefit } from './types.js'

/** 全國統一制度，不分縣市 */
export const militaryFamilyBenefitsSeeds: SeedBenefit[] = [
  {
    categoryNumber: 56,
    name: '現役軍人與軍眷福利',
    agency: '國防部',
    county: null,
    description:
      '(1) 軍人子女教育補助：上校（含）以下支領退休俸/贍養金/生活補助之人員，其在臺就讀公立學校（國小至大學）之子女可申請補助，於註冊後 3 個月內檢附申請書、戶籍謄本（首次申請）及高中以上學費繳費收據申請；(2) 軍人保險給付：死亡給付、失能給付、育嬰留職停薪津貼（前 6 個月按平均投保薪資 60% 加發薪資補助 20%）；(3) 其他福利：結婚補助（2 個月薪俸）、父母/配偶喪葬補助（5 個月薪俸）、子女喪葬補助（3 個月薪俸）、休假撫慰金。',
    searchGroup: '特殊身分族群類',
    isTimeSensitive: true,
    applicationPeriod: '子女教育補助須於註冊後 3 個月內申請，逾期不予受理',
    eligibilityConditions: { requiredIdentities: ['現役軍人'] },
    sourceUrl: 'https://rdrc.mnd.gov.tw/EditPage/?PageID=1ea3a378-9a87-454c-a3f1-d65ceada9707',
    sourceExcerpt:
      '支領退休俸、贍養金或生活補助達上校（含）以下人員，其在臺灣地區就學之子女，就讀政府立案之國小至大學可申請教育補助……應於註冊後3個月內申請，檢附申請書、戶籍謄本（限首次申請）及高中以上學雜費繳費收據……育嬰留職停薪津貼按留職停薪日前6個月平均投保薪資60%計算，並由預算另加發20%薪資補助。',
    lastVerifiedDate: '2026-07-28',
    documents: ['申請書', '戶籍謄本（首次申請）', '高中以上學費繳費收據（教育補助適用）'],
    locations: [
      { name: '所屬部隊人事單位' },
      { name: '國防部福利事業管理處', website: 'https://www.gwsm.gov.tw/' },
    ],
  },
]
