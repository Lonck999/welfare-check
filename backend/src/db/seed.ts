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
