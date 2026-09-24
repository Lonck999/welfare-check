-- benefits schema 擴充（P1~P4 承諾）
-- 2026-09-24　設計稿：benefits-schema設計.md
--
-- 🔴 原則：
--   ① 只新增，不動既有欄位、不刪任何資料
--   ② 全部可為 NULL —— 解析不出來就留 NULL，不填猜測值
--   ③ CHECK 約束擋掉非法值（打錯字會立刻報錯，不會靜默存進去）

BEGIN;

-- ────────────────────────────────────────────
-- ① P2-③ 金額（排序用）
-- ────────────────────────────────────────────
ALTER TABLE benefits ADD COLUMN IF NOT EXISTS amount_min  integer;
ALTER TABLE benefits ADD COLUMN IF NOT EXISTS amount_max  integer;
ALTER TABLE benefits ADD COLUMN IF NOT EXISTS amount_unit text;
-- 🔴 金額算不出來時必須寫原因，不可留空白假裝沒有
ALTER TABLE benefits ADD COLUMN IF NOT EXISTS amount_note text;

ALTER TABLE benefits DROP CONSTRAINT IF EXISTS benefits_amount_unit_chk;
ALTER TABLE benefits ADD CONSTRAINT benefits_amount_unit_chk CHECK (
  amount_unit IS NULL OR amount_unit IN (
    'one_time',   -- 一次性給付
    'monthly',    -- 每月
    'yearly',     -- 每年
    'percent',    -- 比例減免（此時 amount_min/max 存百分比數字）
    'unlimited'   -- 核實支付／上限未定
  ));

ALTER TABLE benefits DROP CONSTRAINT IF EXISTS benefits_amount_range_chk;
ALTER TABLE benefits ADD CONSTRAINT benefits_amount_range_chk CHECK (
  amount_min IS NULL OR amount_max IS NULL OR amount_min <= amount_max);

-- ────────────────────────────────────────────
-- ② P2-② 期限（排序用）
-- 🔴 實測 499 筆：常態 370(74%)／依公告 94／事件 30／每年 7／固定迄日 5
--    ⇒ 一個 deadline_date 撐不起來，必須配 type + rule
-- ────────────────────────────────────────────
ALTER TABLE benefits ADD COLUMN IF NOT EXISTS deadline_type text;
ALTER TABLE benefits ADD COLUMN IF NOT EXISTS deadline_date date;
ALTER TABLE benefits ADD COLUMN IF NOT EXISTS deadline_rule jsonb;

ALTER TABLE benefits DROP CONSTRAINT IF EXISTS benefits_deadline_type_chk;
ALTER TABLE benefits ADD CONSTRAINT benefits_deadline_type_chk CHECK (
  deadline_type IS NULL OR deadline_type IN (
    'always',     -- 常態受理（沒有截止日）
    'fixed',      -- 有明確迄日 → deadline_date 有值
    'annual',     -- 每年固定月份 → deadline_rule {"months":[10,11]}
    'event',      -- 事件觸發 → {"trigger":"childbirth","within_months":6}
    'announced',  -- 依公告，期限未定
    'unknown'     -- 🔴 解析不出來，不可假裝是 always
  ));

-- 🔴 只有 fixed 才該有 deadline_date —— 防止「常態受理」被塞一個假日期
ALTER TABLE benefits DROP CONSTRAINT IF EXISTS benefits_deadline_date_chk;
ALTER TABLE benefits ADD CONSTRAINT benefits_deadline_date_chk CHECK (
  deadline_date IS NULL OR deadline_type = 'fixed');

-- ────────────────────────────────────────────
-- ③ P2-① 成功率：申請難度
-- 🔴 NULL = 未評估。不可預設 1，否則「沒查過」會被當成「很好申請」
-- ────────────────────────────────────────────
ALTER TABLE benefits ADD COLUMN IF NOT EXISTS effort_level smallint;
ALTER TABLE benefits DROP CONSTRAINT IF EXISTS benefits_effort_level_chk;
ALTER TABLE benefits ADD CONSTRAINT benefits_effort_level_chk CHECK (
  effort_level IS NULL OR effort_level BETWEEN 1 AND 3);

-- 名額風險（Lonck 2026-09-24 選 A：納入第 1 順位）
ALTER TABLE benefits ADD COLUMN IF NOT EXISTS quota_limited boolean;

-- ────────────────────────────────────────────
-- ④ P4 申請人角色（新表，一對多）
-- 🔴 不可塞進 benefits 單一欄位 —— 同一補助常「本人可申請、配偶也可申請」
-- ────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS benefit_applicants (
  id         serial PRIMARY KEY,
  benefit_id integer NOT NULL REFERENCES benefits(id) ON DELETE CASCADE,
  role       text NOT NULL CHECK (role IN (
               'self',       -- 本人
               'spouse',     -- 配偶
               'household',  -- 與配偶／全戶共同
               'family')),   -- 為家人申請
  relation   text CHECK (relation IS NULL OR relation IN (
               'parent','child','sibling','grandparent','other')),
  note       text,
  UNIQUE (benefit_id, role, relation)
);

CREATE INDEX IF NOT EXISTS benefit_applicants_benefit_idx
  ON benefit_applicants (benefit_id);

-- 排序常用索引
CREATE INDEX IF NOT EXISTS benefits_deadline_idx
  ON benefits (deadline_type, deadline_date);

COMMIT;
