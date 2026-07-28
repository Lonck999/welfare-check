import {
  pgTable,
  serial,
  integer,
  text,
  varchar,
  boolean,
  jsonb,
  timestamp,
  date,
} from 'drizzle-orm/pg-core'

/**
 * 福利/補助項目主表。
 * category_number 對應 SKILL.md 第三步搜索清單的編號（1～58...），
 * 保留該編號只是為了資料溯源方便對照，網站本身的資格比對不依賴這個編號。
 */
export const benefits = pgTable('benefits', {
  id: serial('id').primaryKey(),
  categoryNumber: integer('category_number'), // 對應 SKILL.md 舊編號，可為 null（網站新建的項目）
  name: varchar('name', { length: 200 }).notNull(),
  agency: varchar('agency', { length: 200 }).notNull(), // 主管機關
  // 金額/門檻依縣市而定的類別（如租金補貼、低收入戶認定），每個縣市各存一筆row，此欄位存該縣市名稱；
  // 全國統一、不分縣市的類別則為 null。
  county: varchar('county', { length: 20 }),
  description: text('description').notNull(), // 補助內容簡述
  searchGroup: varchar('search_group', { length: 50 }), // 對應「搜尋執行順序」11 組之一
  isTimeSensitive: boolean('is_time_sensitive').notNull().default(false), // 有截止期限/候補制/名額有限
  applicationPeriod: text('application_period'), // 常態受理 / 每年 X 月開放 / 特定期間
  notes: text('notes'), // 備註、加分條件

  // 資格條件：階段 3 才會把政策文字轉成結構化判斷邏輯，
  // 這裡先用 JSONB 存放彈性的條件參數（年齡上下限、收入門檻、地區限制、身分別等），
  // 供程式碼的規則引擎讀取解讀，不在資料庫層面強制欄位結構。
  eligibilityConditions: jsonb('eligibility_conditions'),

  // 來源依據（網站化規劃第四節要求）
  sourceUrl: text('source_url').notNull(),
  sourceExcerpt: text('source_excerpt').notNull(), // 從官方頁面擷取、支撐內容的原文片段
  lastVerifiedDate: date('last_verified_date').notNull(),

  isActive: boolean('is_active').notNull().default(true), // false = 疑似已下架，保留歷史但不再顯示給使用者

  createdAt: timestamp('created_at').notNull().defaultNow(),
  updatedAt: timestamp('updated_at').notNull().defaultNow(),
})

/** 每項福利所需文件（一對多） */
export const benefitDocuments = pgTable('benefit_documents', {
  id: serial('id').primaryKey(),
  benefitId: integer('benefit_id')
    .notNull()
    .references(() => benefits.id, { onDelete: 'cascade' }),
  documentName: varchar('document_name', { length: 200 }).notNull(),
  obtainLocation: text('obtain_location'), // 去哪裡取得這份文件
})

/** 每項福利的申請地點（一對多，可能有多個承辦窗口） */
export const benefitLocations = pgTable('benefit_locations', {
  id: serial('id').primaryKey(),
  benefitId: integer('benefit_id')
    .notNull()
    .references(() => benefits.id, { onDelete: 'cascade' }),
  name: varchar('name', { length: 200 }).notNull(), // 機構名稱
  address: text('address'),
  phone: varchar('phone', { length: 50 }),
  website: text('website'),
})

/**
 * 每月批次更新的異動紀錄（網站化規劃第四節「6. 版本紀錄」）。
 * 一筆代表一次「找差異」的結果，approvedAt 為 null 代表尚未人工核准寫入 benefits 表。
 */
export const benefitChangeLog = pgTable('benefit_change_log', {
  id: serial('id').primaryKey(),
  benefitId: integer('benefit_id').references(() => benefits.id, {
    onDelete: 'set null',
  }), // 新增候選項目時可能還沒有對應的 benefit id
  changeType: varchar('change_type', { length: 30 }).notNull(), // 'amount_update' | 'new_candidate' | 'suspected_discontinued'
  fieldName: varchar('field_name', { length: 100 }), // 異動的欄位名稱（amount_update 適用）
  oldValue: text('old_value'),
  newValue: text('new_value'),
  sourceUrl: text('source_url').notNull(),
  sourceExcerpt: text('source_excerpt').notNull(),
  detectedAt: timestamp('detected_at').notNull().defaultNow(),
  reviewedBy: varchar('reviewed_by', { length: 100 }), // 核准者
  approvedAt: timestamp('approved_at'), // null = 尚待人工審核
})
