-- benefits 來源等級欄位（階段 C-2）
-- 2026-09-29　規劃：02-Projects/welfare-check階段C-手動更新流程工具化.md
--
-- 🔴 為什麼需要它：857 筆裡有 192 筆的來源是**媒體或商業網站**
--   （businesstoday 32、faqs.tw 24、mercycare 22、city.gvm 22、
--     yannigo 22、businessweekly 20…）。
--
--   ⚠️ 不是說媒體一定錯 —— 媒體整理文常常比官網好讀、資訊也正確。
--   問題是**政策改了媒體不會回頭改文章，官網會**。
--   ⇒ 使用者有權知道這筆的依據是哪一種。
--
-- 🔴 這也是 W-001（165 筆佐證講別的縣市）的根因：
--   一篇媒體整理文同時談 22 個縣市 ⇒ 展開成 22 筆，
--   每筆都「有佐證」，但沒有一個縣市是對的。
--
-- 🔴 原則（沿用 20260924 那份）：
--   ① 只新增，不動既有欄位、不刪任何資料
--   ② 可為 NULL —— 判不出來就留 NULL，不填猜測值
--   ③ CHECK 約束擋掉非法值（打錯字立刻報錯，不會靜默存進去）

BEGIN;

ALTER TABLE benefits ADD COLUMN IF NOT EXISTS source_tier text;

ALTER TABLE benefits DROP CONSTRAINT IF EXISTS benefits_source_tier_chk;
ALTER TABLE benefits ADD CONSTRAINT benefits_source_tier_chk CHECK (
  source_tier IS NULL OR source_tier IN (
    'official',   -- 政府機關官網（.gov.tw / .gov.taipei / .edu.tw）
    'opendata',   -- 政府開放資料平台（data.gov.tw）—— 官方但非原始公告頁
    'ngo',        -- 民間團體、基金會（法扶會、罕病基金會…）
    'media',      -- 媒體、商業網站、整理型內容農場
    'unknown'     -- 判不出來（刻意留一個顯性值，跟 NULL「還沒判」區分）
  ));

COMMENT ON COLUMN benefits.source_tier IS
  '來源等級。🔴 official/opendata 才是可查證的權威來源；'
  'media 的內容可能正確但政策改了不會回頭改。'
  'NULL = 還沒分類（跟 unknown = 判過但判不出來 不同）。';

COMMIT;
