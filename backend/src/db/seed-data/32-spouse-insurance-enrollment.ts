import type { SeedBenefit } from './types.js'

/** 全國統一制度，不分縣市 */
export const spouseInsuranceEnrollmentSeeds: SeedBenefit[] = [
  {
    categoryNumber: 32,
    name: '配偶健保／國民年金加保確認',
    agency: '衛生福利部中央健康保險署／勞動部勞工保險局',
    county: null,
    description:
      '無工作配偶須確認健保投保身分：無職業者僅能以「眷屬依附」身分加保於有工作的配偶、直系血親尊親屬或子女名下（依序：配偶→子女→孫子女皆無工作時，須自行至區公所以第六類被保險人身分加保）。同時，無職業配偶依法應強制參加國民年金，以免老年年金與身心障礙年金年資中斷。',
    searchGroup: '就業與勞工權益類',
    isTimeSensitive: false,
    applicationPeriod: '常態受理，身分異動（離職/待業）時應主動確認並辦理',
    notes: '若配偶有接案或兼職收入，應改以職業工會身分加保勞保／健保，不可再依附眷屬身分，以免影響給付權益。',
    eligibilityConditions: { requiredFlags: ['spouse_no_income'] },
    sourceUrl: 'https://www.nhi.gov.tw/ch/cp-4532-a6e73-2616-1.html',
    sourceExcerpt:
      '只有3種身分且無職業才可以眷屬身分依附被保險人加保：無職業之配偶及直系血親尊親屬（父母、(外)祖父母、(外)曾祖父母），以及未滿20歲或年滿20歲符合特定條件之子女、孫子女。若三者皆無工作，則需自行到區公所投保為第六類被保險人。',
    lastVerifiedDate: '2026-07-28',
    locations: [
      {
        name: '衛生福利部中央健康保險署',
        website: 'https://www.nhi.gov.tw/',
      },
      {
        name: '各地區公所（第六類被保險人加保）',
      },
    ],
  },
]
