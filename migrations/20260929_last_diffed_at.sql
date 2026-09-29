-- 比對輪替欄位（階段 C-3 續）
-- 2026-09-29　規劃：02-Projects/welfare-check階段C-手動更新流程工具化.md
--
-- 🔴 實測發現的 bug：連跑兩次 `welfare_monthly_diff.py --limit 3`
--   挑到的是**完全相同的 3 筆** ⇒ **跑 100 次的覆蓋率跟跑 1 次一樣**。
--
--   真因：857 筆的 last_verified_date 全是同一天（C-1 那批重抓造成），
--   而 C-3 **刻意不推** last_verified_date（推了會讓「比對過但沒核准」
--   看起來像「資料已更新」）⇒ 排序鍵永遠不變。
--
-- 🔴 所以需要**兩個不同的日期**，它們回答不同的問題：
--
--   last_verified_date  這筆資料的**內容**被確認過的日期
--                       → 只有人工核准異動後才推（C-5）
--                       → 站上「每月更新一次」講的是這個
--
--   last_diffed_at      這筆**被比對腳本檢查過**的時間
--                       → 比對就推，不管有沒有異動、有沒有核准
--                       → 只用來決定「下次先跑誰」
--
-- ⚠️ 合成一個欄位的話，兩種情況會混在一起：
--   「檢查過、沒異動」與「檢查過、有異動但還沒核准」
--   前者資料是新的，後者資料還是舊的 —— 不可以都算成「已驗證」。

BEGIN;

ALTER TABLE benefits ADD COLUMN IF NOT EXISTS last_diffed_at timestamptz;

COMMENT ON COLUMN benefits.last_diffed_at IS
  '上次被月更比對腳本檢查過的時間（不管有沒有異動）。'
  '🔴 與 last_verified_date 不同：那個是「內容被確認過」，'
  '只有人工核准後才推；這個只用來決定下次先跑誰。'
  'NULL = 從來沒被比對過（🔴 這批要最優先）。';

-- 🔴 NULL 要排在最前面（從沒比對過的優先），所以索引用 NULLS FIRST
CREATE INDEX IF NOT EXISTS benefits_last_diffed_idx
  ON benefits (last_diffed_at ASC NULLS FIRST, id ASC);

COMMIT;
