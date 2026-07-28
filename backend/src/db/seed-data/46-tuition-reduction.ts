import type { SeedBenefit } from './types.js'

/** 全國統一制度，不分縣市 */
export const tuitionReductionSeeds: SeedBenefit[] = [
  {
    categoryNumber: 46,
    name: '教育部學費減免與就學貸款',
    agency: '教育部',
    county: null,
    description:
      '「拉近公私立學校學雜費差距方案」持續擴大實施：私立大專學生每人每年補助 3.5 萬元學雜費差額；高中職全面免學費；家庭年所得未達 70 萬元者學費全免、未達 148 萬元者減半，由教育部直接撥款到校自動扣減，學生免自行申請墊款。就學貸款依家庭年所得高低決定利息由誰負擔，家中 2 名以上子女就讀高中以上者多可獲免息優惠；另有「疫後就學貸款補助方案」可折抵 1 學期貸款本金或 1 年還款本息。',
    searchGroup: '教育類',
    isTimeSensitive: false,
    applicationPeriod: '每學期開學前後受理（依各校生輔組公告時間為準）',
    notes: '各校申請期限與細節略有差異，需洽就讀學校學務處生活輔導組確認。',
    eligibilityConditions: { requiredFlags: ['is_student'] },
    sourceUrl: 'https://faqs.tw/student-subsidy-guide',
    sourceExcerpt:
      '2024年起行政院推動「拉近公私立學校學雜費差距方案」，2026年持續擴大實施……減免私立大專學雜費（政府補助私立大學生每人每年3.5萬元）、高中高職全面免學費……只要家裡有2個小孩讀高中以上，基本上都能過件，且享有免息優惠。',
    lastVerifiedDate: '2026-07-28',
    documents: ['學生證/在學證明', '家庭年所得證明（依學校要求）'],
    locations: [{ name: '就讀學校學務處生活輔導組' }, { name: '教育部', website: 'https://www.edu.tw/' }],
  },
]
