-- 異動審核：駁回也要留紀錄（階段 C-5）
-- 2026-10-13　規劃：02-Projects/welfare-check階段C-手動更新流程工具化.md
-- Lonck 2026-10-13 選 A：加「駁回時間」，駁回的紀錄保留不刪。
--
-- 🔴 為什麼不能只靠 approved_at：
--   approved_at IS NULL 原本＝「待審」。駁回的如果也留 NULL，
--   「還沒看」與「看過、不要」在資料庫裡長得一模一樣 ——
--   而且下個月比對會把同一個錯誤再記一次，他要再審一遍。
--
-- 🔴 三種狀態，互斥：
--   待審    approved_at IS NULL AND rejected_at IS NULL
--   已核准  approved_at IS NOT NULL
--   已駁回  rejected_at IS NOT NULL
--   ⇒ 兩個同時有值是不可能的狀態，用 CHECK 擋下，不靠程式自律。

BEGIN;

ALTER TABLE benefit_change_log
  ADD COLUMN IF NOT EXISTS rejected_at timestamp;

COMMENT ON COLUMN benefit_change_log.rejected_at IS
  '人工駁回的時間。🔴 與 approved_at 互斥（CHECK）。'
  '駁回的紀錄不刪：月更比對遇到「同一筆、同欄位、同新值、同佐證」'
  '會略過，避免同一個錯誤每個月重審。';

ALTER TABLE benefit_change_log
  DROP CONSTRAINT IF EXISTS benefit_change_log_decision_chk;
ALTER TABLE benefit_change_log
  ADD CONSTRAINT benefit_change_log_decision_chk
  CHECK (approved_at IS NULL OR rejected_at IS NULL);

-- 待審索引改成「兩個都 NULL」才算待審
DROP INDEX IF EXISTS benefit_change_log_pending_idx;
CREATE INDEX benefit_change_log_pending_idx
  ON benefit_change_log (id)
  WHERE approved_at IS NULL AND rejected_at IS NULL;

COMMIT;
