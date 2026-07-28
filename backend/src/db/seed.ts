/**
 * 資料建檔腳本：把 backend/src/db/seed-data/ 下每個檔案匯出的結構化資料寫入 Neon 資料庫。
 * 可重複執行（idempotent）：每次執行前，會先刪除同一批次要寫入的 categoryNumber 對應的舊資料，
 * 避免重跑造成重複列。
 *
 * 執行方式：cd backend && node --env-file=.env --import tsx src/db/seed.ts
 */
import { db } from './client.js'
import { benefits, benefitDocuments, benefitLocations } from './schema.js'
import { eq } from 'drizzle-orm'
import type { SeedBenefit } from './seed-data/types.js'
import { lowIncomeThresholdSeeds } from './seed-data/01-low-income-threshold.js'
import { laborInsuranceBenefitsSeeds } from './seed-data/21-labor-insurance-benefits.js'
import { laborPensionVoluntarySeeds } from './seed-data/28-labor-pension-voluntary.js'
import { spouseInsuranceEnrollmentSeeds } from './seed-data/32-spouse-insurance-enrollment.js'
import { nationalPensionDisabilitySeeds } from './seed-data/49-national-pension-disability.js'
import { fscFinancialServicesSeeds } from './seed-data/57-fsc-financial-services.js'
import { farmerFisherBenefitsSeeds } from './seed-data/43-farmer-fisher-benefits.js'
import { veteransAffairsBenefitsSeeds } from './seed-data/44-veterans-affairs-benefits.js'
import { tuitionReductionSeeds } from './seed-data/46-tuition-reduction.js'
import { temporaryWorkAllowanceSeeds } from './seed-data/50-temporary-work-allowance.js'
import { taxDeductionsSeeds } from './seed-data/15-tax-deductions.js'
import { indigenousAffairsBenefitsSeeds } from './seed-data/41-indigenous-affairs-benefits.js'
import { newImmigrantFundSeeds } from './seed-data/42-new-immigrant-fund.js'
import { hakkaAffairsBenefitsSeeds } from './seed-data/45-hakka-affairs-benefits.js'
import { overseasCommunityBenefitsSeeds } from './seed-data/51-overseas-community-benefits.js'
import { militaryFamilyBenefitsSeeds } from './seed-data/56-military-family-benefits.js'
import { preventiveHealthScreeningSeeds } from './seed-data/19-preventive-health-screening.js'
import { childVaccinationSeeds } from './seed-data/48-child-vaccination.js'
import { legalAidSeeds } from './seed-data/23-legal-aid.js'
import { smokingCessationSeeds } from './seed-data/36-smoking-cessation.js'
import { telecomDiscountsSeeds } from './seed-data/25-telecom-discounts.js'
import { utilityFeeReductionSeeds } from './seed-data/20-utility-fee-reduction.js'
import { foreignCaregiverSeeds } from './seed-data/27-foreign-caregiver.js'
import { culturePointsSeeds } from './seed-data/30-culture-points.js'
import { solarEnergySubsidySeeds } from './seed-data/40-solar-energy-subsidy.js'
import { rareDiseaseBenefitsSeeds } from './seed-data/58-rare-disease-benefits.js'
import { longTermCareSeeds } from './seed-data/09-long-term-care.js'
import { loanSubsidiesSeeds } from './seed-data/14-loan-subsidies.js'
import { middleAgedEmploymentSeeds } from './seed-data/34-middle-aged-employment.js'
import { earlyInterventionSeeds } from './seed-data/47-early-intervention.js'
import { naturalDisasterReliefSeeds } from './seed-data/55-natural-disaster-relief.js'
import { childcareSubsidySeeds } from './seed-data/07-childcare-subsidy.js'
import { rentSubsidySeeds } from './seed-data/10-rent-subsidy.js'
import { elderlyLivingAllowanceSeeds } from './seed-data/08-elderly-living-allowance.js'
import { disabilityLivingAllowanceSeeds } from './seed-data/06-disability-living-allowance.js'
import { emergencyReliefSeeds } from './seed-data/04-emergency-relief.js'
import { employmentSubsidySeeds } from './seed-data/11-employment-subsidy.js'
import { specialCircumstanceFamilySeeds } from './seed-data/03-special-circumstance-family.js'
import { healthInsuranceSubsidySeeds } from './seed-data/05-health-insurance-subsidy.js'
import { maternityBenefitsSeeds } from './seed-data/02-maternity-benefits.js'
import { spouseNoIncomeBenefitsSeeds } from './seed-data/16-spouse-no-income-benefits.js'
import { caregiverSupportSeeds } from './seed-data/17-caregiver-support.js'
import { funeralSubsidySeeds } from './seed-data/31-funeral-subsidy.js'
import { ivfSubsidySeeds } from './seed-data/35-ivf-subsidy.js'
import { adultEducationSeeds } from './seed-data/39-adult-education.js'
import { publicTransitSubsidySeeds } from './seed-data/37-public-transit-subsidy.js'
import { digitalDevelopmentSubsidySeeds } from './seed-data/52-digital-development-subsidy.js'
import { sportsAdministrationSubsidySeeds } from './seed-data/53-sports-administration-subsidy.js'
import { earthquakeInsuranceSubsidySeeds } from './seed-data/38-earthquake-insurance-subsidy.js'
import { ecoFriendlySubsidySeeds } from './seed-data/22-eco-friendly-subsidy.js'

const ALL_SEEDS: SeedBenefit[] = [
  ...lowIncomeThresholdSeeds,
  ...laborInsuranceBenefitsSeeds,
  ...laborPensionVoluntarySeeds,
  ...spouseInsuranceEnrollmentSeeds,
  ...nationalPensionDisabilitySeeds,
  ...fscFinancialServicesSeeds,
  ...farmerFisherBenefitsSeeds,
  ...veteransAffairsBenefitsSeeds,
  ...tuitionReductionSeeds,
  ...temporaryWorkAllowanceSeeds,
  ...taxDeductionsSeeds,
  ...indigenousAffairsBenefitsSeeds,
  ...newImmigrantFundSeeds,
  ...hakkaAffairsBenefitsSeeds,
  ...overseasCommunityBenefitsSeeds,
  ...militaryFamilyBenefitsSeeds,
  ...preventiveHealthScreeningSeeds,
  ...childVaccinationSeeds,
  ...legalAidSeeds,
  ...smokingCessationSeeds,
  ...telecomDiscountsSeeds,
  ...utilityFeeReductionSeeds,
  ...foreignCaregiverSeeds,
  ...culturePointsSeeds,
  ...solarEnergySubsidySeeds,
  ...rareDiseaseBenefitsSeeds,
  ...longTermCareSeeds,
  ...loanSubsidiesSeeds,
  ...middleAgedEmploymentSeeds,
  ...earlyInterventionSeeds,
  ...naturalDisasterReliefSeeds,
  ...childcareSubsidySeeds,
  ...rentSubsidySeeds,
  ...elderlyLivingAllowanceSeeds,
  ...disabilityLivingAllowanceSeeds,
  ...emergencyReliefSeeds,
  ...employmentSubsidySeeds,
  ...specialCircumstanceFamilySeeds,
  ...healthInsuranceSubsidySeeds,
  ...maternityBenefitsSeeds,
  ...spouseNoIncomeBenefitsSeeds,
  ...caregiverSupportSeeds,
  ...funeralSubsidySeeds,
  ...ivfSubsidySeeds,
  ...adultEducationSeeds,
  ...publicTransitSubsidySeeds,
  ...digitalDevelopmentSubsidySeeds,
  ...sportsAdministrationSubsidySeeds,
  ...earthquakeInsuranceSubsidySeeds,
  ...ecoFriendlySubsidySeeds,
]

async function run() {
  const categoryNumbers = [...new Set(ALL_SEEDS.map((s) => s.categoryNumber))]

  for (const categoryNumber of categoryNumbers) {
    const existing = await db
      .select({ id: benefits.id })
      .from(benefits)
      .where(eq(benefits.categoryNumber, categoryNumber))
    if (existing.length > 0) {
      await db.delete(benefits).where(eq(benefits.categoryNumber, categoryNumber))
      console.log(`已清除 category ${categoryNumber} 的舊資料（${existing.length} 筆）`)
    }
  }

  let inserted = 0
  for (const seed of ALL_SEEDS) {
    const [row] = await db
      .insert(benefits)
      .values({
        categoryNumber: seed.categoryNumber,
        name: seed.name,
        agency: seed.agency,
        county: seed.county,
        description: seed.description,
        searchGroup: seed.searchGroup,
        isTimeSensitive: seed.isTimeSensitive,
        applicationPeriod: seed.applicationPeriod,
        notes: seed.notes,
        eligibilityConditions: seed.eligibilityConditions,
        sourceUrl: seed.sourceUrl,
        sourceExcerpt: seed.sourceExcerpt,
        lastVerifiedDate: seed.lastVerifiedDate,
      })
      .returning({ id: benefits.id })

    if (seed.documents) {
      for (const documentName of seed.documents) {
        await db.insert(benefitDocuments).values({ benefitId: row.id, documentName })
      }
    }
    if (seed.locations) {
      for (const location of seed.locations) {
        await db.insert(benefitLocations).values({ benefitId: row.id, ...location })
      }
    }
    inserted += 1
  }

  console.log(`寫入完成，共 ${inserted} 筆 benefits 資料。`)
  process.exit(0)
}

run().catch((err) => {
  console.error(err)
  process.exit(1)
})
