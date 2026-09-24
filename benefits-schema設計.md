# benefits schema 擴充設計（P1~P4 承諾）

> 2026-09-24。🔴 **這是設計稿，還沒動資料庫** —— 確認後才執行。
> 目的：讓 `benefits` 表撐得起四個產品承諾。

---

## 現況盤點（實查，非估計）

| 承諾 | 需要什麼 | 現在有什麼 | 缺口 |
|---|---|---|---|
| P1 分析能領什麼 | 資格條件 | `eligibility_conditions` **491/499** ✅ | 🔶 342 筆描述是空殼 |
| P2-① 成功率 | 資格確定性 | 同上，鍵齊全 ✅ | 🔶 需算出「確定/可能」 |
| P2-② 期限近 | 截止日 | `is_time_sensitive` 布林，**152 筆全 true** | 🔴 **無 `deadline_date`** |
| P2-③ 金額大 | 可領金額 | 埋在描述文字裡（174/499 找得到數字） | 🔴 **無欄位** |
| P3 文件/地點 | 應備文件 | `benefit_documents` **58/499**（12%） | 🔶 覆蓋率低 |
| P3 去哪申請 | 地點 | `benefit_locations` **499/499** ✅ | — |
| P4 自身>配偶>家人 | 申請人角色 | 🔴 描述提到配偶僅 **11 筆**、家人 **18 筆** | 🔴 **資料不存在** |

---

## 🔴 兩個必須先講清楚的事實

### ① 74% 是「常態受理」—— 沒有期限可排

`application_period` 實際解析（499 筆）：

```
常態受理      370  (74%)   ← 沒有截止日
依公告         94  (19%)   ← 期限未定
事件觸發       30   (6%)   ← 出生後 N 個月、離職後 2 年…
每年固定月份    7   (1%)
有明確迄日      5   (1%)   ← 🔴 只有這些排得出「快到期」
解析不出來     26   (5%)
```

⚠️ **意思是：你排第二順位的「期限近」，對 74% 的補助不適用。**

🔴 但「事件觸發」那 30 筆**最該提醒**（新生兒出生後 3~6 個月、
喪葬給付 5 年內、離職後 2 年內）—— 它們的期限**綁在使用者的人生事件上**，
不是固定日期，**必須從問卷答案推算**。

### ② P4 的資料根本不存在

描述文字裡提到配偶只有 11 筆、家人 18 筆 ——
**不是欄位沒設計，是這件事從來沒被記錄過。**

⚠️ 而問卷已經問了配偶 29 次、家人 23 次 ——
**問了卻無處對應**，這是目前最大的落差。

---

## 設計：新增 7 個欄位 + 1 張表

### A. `benefits` 新增欄位

```sql
-- ① P2-③ 金額（排序用）
amount_min          integer      -- 最低可領金額（元）
amount_max          integer      -- 最高可領金額（元）
amount_unit         text         -- 'one_time' 一次 | 'monthly' 每月 | 'yearly' 每年
                                 -- | 'percent' 比例減免 | 'unlimited' 核實支付
amount_note         text         -- 🔴 金額算不出來時寫原因，不可留空白假裝沒有

-- ② P2-② 期限（排序用）
deadline_type       text         -- 'always' 常態 | 'fixed' 固定迄日
                                 -- | 'annual' 每年固定月份 | 'event' 事件觸發
                                 -- | 'announced' 依公告 | 'unknown' 解析不出
deadline_date       date         -- 只有 deadline_type='fixed' 才有值
deadline_rule       jsonb        -- event/annual 的規則，例：
                                 -- {"trigger":"childbirth","within_months":6}
                                 -- {"months":[10,11]}

-- ③ P2-① 成功率（排序用）
effort_level        smallint     -- 1 線上即可 / 2 需備文件 / 3 需臨櫃或審查
                                 -- 🔴 NULL = 未評估，不可預設 1
```

### B. 新表 `benefit_applicants`（P4）

🔴 **不能放在 `benefits` 的單一欄位** ——
同一個補助常常「本人可申請、配偶也可申請」，是一對多。

```sql
CREATE TABLE benefit_applicants (
  id           serial PRIMARY KEY,
  benefit_id   integer NOT NULL REFERENCES benefits(id) ON DELETE CASCADE,
  role         text NOT NULL,   -- 'self' 本人 | 'spouse' 配偶
                                -- | 'household' 與配偶共同 | 'family' 為家人申請
  relation     text,            -- family 時：'parent'/'child'/'sibling'/'other'
  note         text,            -- 條件（例：「限未成年子女」）
  UNIQUE (benefit_id, role, relation)
);
```

**P4 的排序** = 依 `role` 分組：`self` → `household` → `spouse` → `family`

---

## 🔴 排序規則（Lonck 2026-09-24 定案）

```
成功率高  >  期限近  >  金額大  >  加權
```

實作對應：

| 順位 | 依據 | 排序方式 |
|---|---|---|
| 1 | **資格確定性** | 問卷答案完全符合 `eligibility_conditions` → 最前 |
| 1b | **名額風險** | ⚠️ 「經費用罄即止」「名額有限」往前（待確認要不要納入） |
| 2 | **期限** | `fixed` 依 `deadline_date` 近的優先；`event` 依問卷事件推算 |
| 3 | **金額** | `amount_max` 大的優先（跨 unit 需換算成年化） |
| 4 | 加權 | 前三項打平時的綜合分數 |

⚠️ **74% 是常態受理 → 第 2 順位對多數項目無作用**，
實際上大部分排序會落在「資格確定性 → 金額」。

---

## 遷移步驟（每步可回滾）

```
① ALTER TABLE 加欄位（全部 NULL，不影響現有 157 筆實質內容）
② 從 application_period 反解 deadline_type（95% 可解析）
③ 從 description 反解金額 → amount_min/max（174 筆找得到數字）
④ 建 benefit_applicants 表（空的，之後隨抓取填入）
⑤ 寫 verify_benefits_schema.py：欄位存在、型別正確、
   deadline_type 只有六種合法值、amount_min<=amount_max
```

🔴 **不做的事**：
- 不動現有欄位（`is_time_sensitive` 保留，之後由 `deadline_type` 取代）
- 不刪任何資料
- **不填猜測值** —— 解析不出來就留 NULL 並在 `amount_note` 記原因

---

## 待確認

1. **「名額有限」要不要納入第 1 順位？**（你先前選 C 但還沒定案）
2. `effort_level` 怎麼評？（線上/臨櫃可從 e 政府申辦服務資料判斷）
