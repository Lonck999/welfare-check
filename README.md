# 台灣社會福利補助查詢助手

一套整合在 Claude Code 的 Skill，透過逐步問答收集使用者基本資料，自動比對並列出所有可能符合資格的台灣政府福利補助項目。

---

## 安裝教學

### 前置需求

- 已安裝 [Claude Code](https://claude.ai/code)（v2.1 以上）
- 已登入 Anthropic 帳號

---

### 方法一：透過 Marketplace 安裝（推薦）

在 Claude Code 中依序執行以下兩個指令：

**第一步：加入 Marketplace**

```
/plugin marketplace add Lonck999/welfare-check
```

**第二步：安裝插件**

```
/plugin install welfare-check@Lonck999/welfare-check
```

**第三步：重新載入**

```
/reload-plugins
```

---

### 方法二：透過 ZIP 安裝

前往 [Releases 頁面](https://github.com/Lonck999/welfare-check/releases)，下載最新版本的 `.zip` 檔，然後在 Claude Code 中執行：

```
claude --plugin-url https://github.com/Lonck999/welfare-check/releases/latest/download/welfare-check.zip
```

---

### 確認安裝成功

執行以下指令，看到 `welfare-check` 出現在清單中即代表安裝成功：

```
/plugin list
```

---

## 使用方式

安裝完成後，在 Claude Code 中輸入：

```
/welfare-check
```

助手將逐題引導填寫資料，完成後輸出個人化的補助清單與申請步驟。

---

## 功能說明

- 透過 14 題問答，全面收集年齡、居住地、家庭成員、財產與健康狀況等資訊
- 自動計算人均月所得、動產總額，與當地低收入戶 / 中低收入戶門檻比對
- 使用即時網路搜尋查詢最新補助資訊，涵蓋 **40 大類**：
  - 低收入戶、中低收入戶生活補助
  - 生育、孕產、育兒托育補助
  - 老人福利與長期照顧
  - 身心障礙補助
  - 租金補貼與社會住宅
  - 勞工就業補助與勞保給付權益
  - 貸款類補助（青年創業、安心成家等）
  - 稅務減免（長照特別扣除額、扶養親屬申報）
  - 配偶無收入相關補助（國民年金、二度就業）
  - 照顧者支持（家庭照顧假、喘息服務）
  - 老人其他福利（重陽禮金、假牙補助、敬老卡）
  - 健保預防保健服務（四癌篩檢、成人健檢）
  - 水電費與通訊費減免
  - 環保節能補助（電動機車、節能家電）
  - 法律扶助與心理諮商補助
  - 居家修繕與無障礙環境改善
  - 地方政府加碼補助
- 每項補助標注 ✅ 確定符合 / ⚠️ 可能符合，並列出所需文件與申請地點
- 查詢完成後自動產生 **HTML 報告檔**（`welfare-result-YYYYMMDD.html`），可直接用瀏覽器開啟，包含可勾選的行動清單

---

## 資料來源

優先參考政府官方網站（gov.tw），所有補助資訊均附來源連結，確保資訊可信度。

---

## 問題回報

遇到問題或有建議，歡迎至 [Issues](https://github.com/Lonck999/welfare-check/issues) 回報。

---

## 授權

MIT License
