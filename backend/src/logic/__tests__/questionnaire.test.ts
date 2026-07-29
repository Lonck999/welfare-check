import { describe, expect, it } from 'vitest'
import { buildApplicantProfile, deriveFlags, type QuestionnaireAnswers } from '../questionnaire.js'

function baseAnswers(overrides: Partial<QuestionnaireAnswers> = {}): QuestionnaireAnswers {
  return {
    birthDate: '1990-05-15',
    county: '臺北市',
    maritalStatus: 'single',
    pregnantOrPostpartumSelf: false,
    pregnantOrPostpartumSpouse: false,
    miscarriageRecently: false,
    familySpecialCircumstances: [],
    householdMembers: [],
    housingStatus: 'rent',
    selfAnnualIncome: 300000,
    selfAssets: 100000,
    employmentStatus: 'employed_insured',
    selfDisabilityCard: false,
    selfCatastrophicIllnessCard: false,
    selfRareDisease: false,
    selfRecentMajorSurgery: false,
    hasForeignCaregiver: false,
    hadOccupationalInjury: false,
    nonCohabitingFamily: [],
    specialIdentities: [],
    involuntaryUnemployment6mo: false,
    majorMedicalExpense: false,
    naturalDisasterDamage: false,
    domesticViolenceOrTrafficking: false,
    otherAcuteHardship: false,
    hasStartupIntent: false,
    infertilityTreatmentNeeded: false,
    wantsToQuitSmoking: false,
    legalDisputeNeedsConsultation: false,
    wantsAdultEducation: false,
    isStudent: false,
    developmentalDelayChild: false,
    ...overrides,
  }
}

describe('deriveFlags', () => {
  it('一般狀況只會有 general_public 加上就業相關旗標', () => {
    const flags = deriveFlags(baseAnswers())
    expect(flags).toContain('general_public')
    expect(flags).toContain('is_employed_or_insured')
    expect(flags).toContain('has_labor_insurance')
    expect(flags).not.toContain('acute_hardship')
  })

  it('懷孕中 → pregnant_or_recent_birth', () => {
    const flags = deriveFlags(baseAnswers({ pregnantOrPostpartumSelf: true }))
    expect(flags).toContain('pregnant_or_recent_birth')
  })

  it('本人或成員有身心障礙手冊 → 同時帶出多個相關旗標', () => {
    const flags = deriveFlags(baseAnswers({ selfDisabilityCard: true }))
    expect(flags).toContain('disability_certificate')
    expect(flags).toContain('has_disability_or_dementia_member')
    expect(flags).toContain('has_care_recipient')
    expect(flags).toContain('has_dependents_or_ltc_needs')
  })

  it('家庭成員生活自理困難 → severe_disability_or_dementia', () => {
    const flags = deriveFlags(
      baseAnswers({
        householdMembers: [
          { relationship: '母親', birthDate: '1950-01-01', sameHukou: false, chronicDisability: ['self_care'] },
        ],
      }),
    )
    expect(flags).toContain('severe_disability_or_dementia')
  })

  it('失業求職中 → unemployed，待業中(未求職) → 不算 unemployed', () => {
    expect(deriveFlags(baseAnswers({ employmentStatus: 'unemployed_seeking' }))).toContain('unemployed')
    expect(deriveFlags(baseAnswers({ employmentStatus: 'unemployed_not_seeking' }))).not.toContain('unemployed')
  })

  it('同戶配偶年收入為 0 → spouse_no_income', () => {
    const flags = deriveFlags(
      baseAnswers({
        householdMembers: [{ relationship: '配偶', birthDate: '1991-01-01', sameHukou: true, annualIncome: 0 }],
      }),
    )
    expect(flags).toContain('spouse_no_income')
  })

  it('配偶有收入則不會有 spouse_no_income', () => {
    const flags = deriveFlags(
      baseAnswers({
        householdMembers: [{ relationship: '配偶', birthDate: '1991-01-01', sameHukou: true, annualIncome: 500000 }],
      }),
    )
    expect(flags).not.toContain('spouse_no_income')
  })

  it('第 14a 題各項目個別對應各自旗標', () => {
    const flags = deriveFlags(
      baseAnswers({
        hasStartupIntent: true,
        infertilityTreatmentNeeded: true,
        wantsToQuitSmoking: true,
        legalDisputeNeedsConsultation: true,
        wantsAdultEducation: true,
      }),
    )
    expect(flags).toEqual(
      expect.arrayContaining([
        'has_startup_intent',
        'infertility_treatment_needed',
        'wants_to_quit_smoking',
        'legal_dispute_or_consultation_needed',
        'returning_to_education',
      ]),
    )
  })

  it('急難情形任一項成立 → acute_hardship', () => {
    expect(deriveFlags(baseAnswers({ majorMedicalExpense: true }))).toContain('acute_hardship')
    expect(deriveFlags(baseAnswers({ naturalDisasterDamage: true }))).toContain('recent_natural_disaster_damage')
  })
})

describe('buildApplicantProfile', () => {
  const asOf = new Date('2026-07-29')

  it('依第 5 題家庭成員名單自動算出最年幼子女與最年長成員年齡，不需要另外問', () => {
    const profile = buildApplicantProfile(
      baseAnswers({
        householdMembers: [
          { relationship: '子女', birthDate: '2020-01-01', sameHukou: true },
          { relationship: '母親', birthDate: '1950-01-01', sameHukou: false },
        ],
      }),
      'above_threshold',
      asOf,
    )
    expect(profile.hasChildUnder).toBe(6)
    expect(profile.hasElderOver).toBe(76)
  })

  it('沒有子女或長者時，兩個欄位皆為 undefined', () => {
    const profile = buildApplicantProfile(baseAnswers(), 'above_threshold', asOf)
    expect(profile.hasChildUnder).toBeUndefined()
    expect(profile.hasElderOver).toBeUndefined()
  })

  it('住宅狀況為 own 時 ownsHome 為 true，其餘皆為 false', () => {
    expect(buildApplicantProfile(baseAnswers({ housingStatus: 'own' }), 'above_threshold', asOf).ownsHome).toBe(true)
    expect(buildApplicantProfile(baseAnswers({ housingStatus: 'rent' }), 'above_threshold', asOf).ownsHome).toBe(false)
    expect(buildApplicantProfile(baseAnswers({ housingStatus: 'borrow' }), 'above_threshold', asOf).ownsHome).toBe(false)
  })

  it('人均動產計算包含本人與同戶號家人，不含不同戶號家人', () => {
    const profile = buildApplicantProfile(
      baseAnswers({
        selfAssets: 100000,
        householdMembers: [
          { relationship: '配偶', birthDate: '1991-01-01', sameHukou: true, assets: 200000 },
          { relationship: '母親', birthDate: '1950-01-01', sameHukou: false, assets: 9999999 },
        ],
      }),
      'above_threshold',
      asOf,
    )
    expect(profile.perCapitaAssets).toBe(150000) // (100000+200000)/2，不計入不同戶號的母親
  })
})
