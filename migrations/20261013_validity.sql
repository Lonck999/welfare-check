-- 有效性檢查欄位（階段 C-6）
-- 2026-10-13　規劃：02-Projects/welfare-check階段C-手動更新流程工具化.md
--
-- Lonck 2026-10-13 定案：
--   A 官方來源＋頁面有 115 年度字樣或更新日期 → valid_current
--   B 官方來源＋頁面沒有廢止／停辦／已結束     → valid_unconfirmed（下一輪優先補查）
--   都不過 → 停用（不真刪，寫原因與日期）
--   抓不到：三種工具都失敗 → unreachable（本輪不判、保持啟用）；連續兩輪才停用
--
-- 🔴 last_verified_date 只代表「有人看過」，不代表「確認今年還有效」（W-014）
--    ⇒ 有效性用獨立欄位，不重用 last_verified_date。

BEGIN;

ALTER TABLE benefits ADD COLUMN IF NOT EXISTS validity_status text;
ALTER TABLE benefits ADD COLUMN IF NOT EXISTS validity_checked_at timestamptz;
ALTER TABLE benefits ADD COLUMN IF NOT EXISTS validity_evidence text;
ALTER TABLE benefits ADD COLUMN IF NOT EXISTS unreachable_streak smallint NOT NULL DEFAULT 0;
ALTER TABLE benefits ADD COLUMN IF NOT EXISTS deactivated_at timestamptz;
ALTER TABLE benefits ADD COLUMN IF NOT EXISTS deactivated_reason text;

ALTER TABLE benefits DROP CONSTRAINT IF EXISTS benefits_validity_status_chk;
ALTER TABLE benefits ADD CONSTRAINT benefits_validity_status_chk CHECK (
  validity_status IS NULL OR validity_status IN (
    'valid_current',      -- A：官方頁有今年度字樣／更新日期
    'valid_unconfirmed',  -- B：官方頁沒寫停辦，但沒確認到今年度
    'unreachable',        -- 三種工具都抓不到（本輪不判）
    'deactivated'         -- 已停用（is_active=false）
  ));

-- 🔴 停用必須有原因與日期 —— 不讓「為什麼不見了」變成查不到的事
ALTER TABLE benefits DROP CONSTRAINT IF EXISTS benefits_deactivation_reason_chk;
ALTER TABLE benefits ADD CONSTRAINT benefits_deactivation_reason_chk CHECK (
  validity_status IS DISTINCT FROM 'deactivated'
  OR (deactivated_at IS NOT NULL AND deactivated_reason IS NOT NULL
      AND is_active = false));

COMMENT ON COLUMN benefits.validity_status IS
  '有效性（C-6，2026-10-13）。NULL＝還沒檢查過。見 migration 註解的 A/B 判準。';
COMMENT ON COLUMN benefits.validity_evidence IS
  '判定依據的原文片段（例：「資料更新：115-09-30」「115年度」或「本補助已停辦」）';
COMMENT ON COLUMN benefits.unreachable_streak IS
  '連續幾輪三種工具都抓不到。>=2 才停用；抓到就歸零。';

COMMIT;
