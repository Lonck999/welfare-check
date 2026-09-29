-- 月更比對的執行紀錄（階段 C-3）
-- 2026-09-29　規劃：02-Projects/welfare-check階段C-手動更新流程工具化.md
--
-- 🔴 存在的理由（KNOWN-ISSUES W-002）：
--   `benefit_change_log` 只在**有異動時**才會寫入。
--   所以這兩種情況在資料庫裡長得一模一樣：
--     ① 真的跑了月更、逐筆比對、發現沒有異動
--     ② 根本沒跑，只是有人把 last_verified_date 批次 UPDATE 了
--
--   ⇒ 需要一個「不管有沒有異動都會留下」的痕跡。
--
-- ⚠️ 為什麼不塞進 benefit_change_log：
--   那張表的 source_url / source_excerpt 都是 NOT NULL
--   —— 那是**刻意的**（沒佐證就寫不進去）。
--   一次「跑過但沒異動」沒有對應的 URL 與原文，
--   硬塞會逼我們放寬 NOT NULL，等於把那道防線拆掉。
--
-- 🔴 與既有的 benefit_verification_progress 不同：
--   那張是**主題層級**的一次性盤點（25 筆，零程式在用）。
--   這張是**每次執行**的紀錄。

BEGIN;

CREATE TABLE IF NOT EXISTS verification_runs (
  id            bigserial PRIMARY KEY,

  -- 🔴 這次跑了哪些 —— 說不出範圍的話，「跑過」本身沒有意義
  scope         text        NOT NULL,   -- 例：'tier=official limit=50'
  target_count  integer     NOT NULL,   -- 這次預計處理幾筆

  -- 實際結果（🔴 四個數字要能加總回 target_count，否則就是「做了一半」）
  checked_count integer     NOT NULL DEFAULT 0,  -- 真的抓到頁面並比對過
  changed_count integer     NOT NULL DEFAULT 0,  -- 發現異動（已寫 change_log）
  unreachable_count integer NOT NULL DEFAULT 0,  -- 網址打不開
  skipped_count integer     NOT NULL DEFAULT 0,  -- 刻意跳過（已知抓不到的縣市等）

  started_at    timestamptz NOT NULL DEFAULT now(),
  finished_at   timestamptz,            -- NULL = 跑到一半掛了（🔴 這本身就是訊號）
  notes         text
);

COMMENT ON TABLE verification_runs IS
  '月更比對的執行紀錄。🔴 不管有沒有異動都要留一筆 —— '
  '否則「跑過沒異動」跟「根本沒跑」在資料庫裡分不出來（W-002）。';

COMMENT ON COLUMN verification_runs.finished_at IS
  'NULL = 這次跑到一半就中斷了。🔴 這不是遺漏，是訊號：'
  '有 started_at 沒 finished_at 代表那批結果不完整，不可當成「查過了」。';

CREATE INDEX IF NOT EXISTS verification_runs_started_idx
  ON verification_runs (started_at DESC);

-- 🔴 change_log 要能回溯到是哪一次跑出來的。
--    不然「這筆異動什麼時候發現的、當時的範圍是什麼」查不到。
ALTER TABLE benefit_change_log ADD COLUMN IF NOT EXISTS run_id bigint;

ALTER TABLE benefit_change_log
  DROP CONSTRAINT IF EXISTS benefit_change_log_run_id_fk;
ALTER TABLE benefit_change_log
  ADD CONSTRAINT benefit_change_log_run_id_fk
  FOREIGN KEY (run_id) REFERENCES verification_runs(id) ON DELETE SET NULL;

CREATE INDEX IF NOT EXISTS benefit_change_log_run_idx
  ON benefit_change_log (run_id);

-- 🔴 既有的 FK 全部沒有索引（KNOWN-ISSUES 的 ITAM 那條也踩過同一個）。
--    benefit_id 會被「這筆補助的異動史」查詢用到。
CREATE INDEX IF NOT EXISTS benefit_change_log_benefit_idx
  ON benefit_change_log (benefit_id);

-- 🔴 待審清單是 C-5 的主查詢：approved_at IS NULL 的那些。
CREATE INDEX IF NOT EXISTS benefit_change_log_pending_idx
  ON benefit_change_log (approved_at) WHERE approved_at IS NULL;

COMMIT;
