# welfare-check UI/UX 改版交接文件

> 建立日期：2026-08-02
> 用途：把「視覺風格重新打造」這件事的決策脈絡、已完成範圍、未完成事項交接給下一個接手的 session（Claude Code / IDE）
> 狀態：**首頁已改完並 commit 在 `dev`，但尚未 push、尚未部署、尚未實際截圖驗證**

---

## 一、這次改版要解決什麼

原本首頁的視覺是「高飽和橘紅色滿版 hero（`--hero-solid: #ee461c`）＋ 手刻 SVG 圖示」，風格偏遊戲／娛樂感。

問題在於：**這個網站的使用者要填的是收入、財產、身心障礙證明、家人的病況**。在那種情境下，跳動活潑的視覺會顯得輕浮，跟「照顧、安心、被接住」的情緒需求對不上。

因此改版方向定為「柔和照顧感」：米白底 ＋ 鼠尾草綠輔色 ＋ 扁平無描邊插畫 ＋ 有機波浪分隔色塊。

### 參考來源演進（供理解決策脈絡）

| 階段 | 參考對象 | 結論 |
|------|---------|------|
| 初版提案 | Rainbow Friends（韓國遊戲角色網站） | **否決**。娛樂品牌語彙，與福利查詢的情緒需求不合 |
| 第二版 | be kids（韓國托兒所網站） | **採用結構**：波浪分隔、圓形柔色底圖示、襯線標題、圓角膠囊按鈕。但不照抄其綠色主導配色，也不能只畫小孩（本站涵蓋長者／身障者／退伍軍人／農漁民／學生） |
| 主視覺 | Amore Mall 2022 活動 banner（韓國扁平向量插畫） | **採用畫風**：扁平、無描邊、低飽和、多人物場景。注意該圖是商業廣告物料，只借鑑風格，未直接使用 |

### 使用者明確做過的決策

- 插畫形式：**情境場景插畫（無固定吉祥物角色）**
- 插畫產出方式：AI 生成後再調整（實際上最終採用 Gemini 生成的 PNG，未轉向量）
- 圖片格式：**不限 SVG**，可接受點陣圖
- 柔和度：維持目前 mockup 的程度（不再更柔、也不再更克制）
- 主色調：**米白底 ＋ 鼠尾草綠輔色**（不採用 be kids 的綠色主導，也不沿用原本的焦糖橘）
- 各頁面背景**不再使用深色**

---

## 二、色票系統（已寫入 `frontend/src/style.css`）

```css
--bg: #f9f5e9;          /* 米白底 — 見下方警告，不可隨手改 */
--surface: #ffffff;
--cream-deep: #f2ead9;  /* 頁尾底色 */

--sage-100: #dfe9d4;    /* 淺色帶狀區塊 */
--sage-200: #c8dbb8;    /* 圖示次要色 */
--sage-500: #7d9b6a;    /* 波浪色塊、圖示主色 */
--sage-700: #4f6a41;    /* 按鈕、連結、accent */

--text: #665b4d;
--text-h: #2a2019;
--border: #e2dac7;

--accent: #4f6a41;      /* = sage-700 */

--confirmed: #3b6438;   --confirmed-bg: #e2f0e4;   /* 確定符合 */
--possible:  #8a6414;   --possible-bg:  #faf0d2;   /* 建議再確認 */
--urgent:    #97441f;   --urgent-bg:    #fbe6d8;   /* 有時限，優先看 */
```

### ⚠️ `--bg: #f9f5e9` 不可隨手更動

這個值是**主圖左上角天空的實際取樣色**。首頁 hero 是滿版圖直接貼著頁面背景，色值只要差幾階就會出現一條肉眼可見的水平接縫。改動前請先重新取樣主圖左上角。

### 已移除的東西

- 全部 `@media (prefers-color-scheme: dark)` 區塊（build 產物中已歸零，可用 `grep -c "prefers-color-scheme" dist/assets/*.css` 驗證）
- `--hero-solid` / `--hero-ink` / `--hero-ink-soft` / `--hero-chip-bg` / `--hero-badge-bg` 這組橘紅 hero 變數
- 舊的 `--shadow`（未使用）、`--accent` 焦糖橘 `#8a4321`

---

## 三、主視覺插畫

### 檔案位置

```
frontend/public/images/hero-park-1200.webp   25.0 KB
frontend/public/images/hero-park-1600.webp   33.2 KB
frontend/public/images/hero-park-2400.webp   52.9 KB
```

原始尺寸 3168×1344（比例 2.357:1）。內容：公園場景，含拄拐杖的長者、推輪椅的照顧者、牽幼兒的家長、背書包的學生、草地上休息的人。左上角有大片米白天空，是刻意留給標題疊字的空間。

### 為什麼只出 WebP、沒有 PNG fallback

不支援 WebP 的瀏覽器（IE11 等）本來就跑不動 Vue 3，兩者的支援門檻幾乎重疊。為了理論上的相容性在 repo 裡放一份 1 MB 的 PNG 不划算（WebP 33 KB vs PNG 1010 KB，差 30 倍）。扁平向量風格色塊大、漸層少，特別吃 WebP 的編碼優勢。

### 浮水印清除紀錄

Gemini 生成的原圖在右下角（原始座標約 x 2872–2978、y 1050–1148）有一個**四角星形浮水印**，位於米白路面上。已用周圍路面同色 `(249,245,234)` 逐欄平填清除，並在每一欄偵測非路面色（灌木、鞋子）的位置後提早停止，避免蓋到既有內容。

**若日後再生成新圖，務必先檢查是否有同樣的浮水印。** 清除腳本邏輯：

```python
from PIL import Image
import numpy as np
im = Image.open('原圖.png').convert('RGB')
a = np.asarray(im).astype(int)
bg = np.array([249,245,234])          # 取樣浮水印周圍的底色
for x in range(x0, x1):                # 浮水印的水平範圍
    col = a[y_scan_start:y_scan_end, x]
    d = np.abs(col-bg).sum(axis=1)
    stop = next((y_scan_start+i for i,v in enumerate(d) if v > 120), y_scan_end)
    a[y_top:min(stop-3, y_bottom), x] = bg
Image.fromarray(a.astype(np.uint8)).save('clean.png')
```

### 產生同風格新圖的 prompt（問卷頁／結果頁若需要插畫可沿用）

```
Flat vector illustration in Korean editorial style. No outlines, no strokes —
pure flat color shapes with soft layered depth.

Scene: <描述情境>

Simple rounded body shapes, soft shoulders, minimal facial features (small dots
for eyes, no detailed expressions). Subtle soft shadows beneath figures.

Color palette strictly: cream #f9f5e9, pale sage #dfe9d4, mid sage #c8dbb8,
deep sage #7d9b6a, dark green #4f6a41, warm peach #fbe6d8, soft butter #faf0d2,
dusty sky blue #dfeaf2. Muted and desaturated throughout.

Mood: warm, reassuring, dignified, quietly hopeful.
```

負面提示詞：

```
outlines, black strokes, harsh contrast, saturated colors, neon, gradients,
3D render, photorealistic, detailed faces, text, letters, watermark,
cluttered composition, cute cartoon mascot style
```

**人物光譜原則**：本站涵蓋長者、身心障礙者、退伍軍人、原住民、農漁民、學生等族群。插畫若只出現年輕人或小孩，會讓其他族群覺得「這網站不是為我做的」。新增插畫時請維持多元人物。

---

## 四、已修改的檔案

Commit：`395fcd3`（在 `dev` 分支，**尚未 push**）

| 檔案 | 改動 |
|------|------|
| `frontend/public/images/hero-park-*.webp` | 新增，3 種尺寸主圖 |
| `frontend/src/style.css` | 全面改寫色票、移除深色模式、重寫首頁樣式區塊 |
| `frontend/src/components/LandingPage.vue` | 改為滿版主圖 ＋ 左上疊字；新增自己的頁尾與 LegalNotice |
| `frontend/src/components/BadgeIcon.vue` | 改為無描邊實心色塊，圖示換成 4 個分類（housing/care/family/study） |
| `frontend/src/App.vue` | `<main>` 新增 `app--landing` class，讓首頁跳脫 720px 閱讀寬度 |
| `frontend/src/reportDownload.ts` | 下載版 HTML 報告的內嵌樣式同步套用新色票 |

### 幾個實作上的考量（避免之後被誤改）

**`.app--landing`**：`.app` 原本是 `max-width: 720px`，適合表單但綁死首頁。先前版本用 `width: 100vw` ＋ `margin-left: calc(50% - 50vw)` 破格，但 `100vw` 含捲軸寬度，桌機有可見捲軸時會造成水平溢出。改為在 `App.vue` 依狀態加 class、把 `.app--landing` 設成 `max-width: none; padding: 0`，內層各區塊自己控制 `max-width: 1040px`，完全避開 `100vw` 的坑。

**hero 疊字的定位**：`.landing-hero-copy` 用 `padding: 11% 28px 0`。百分比 padding 是相對**容器寬度**計算的，而主圖高度也與寬度成正比（固定比例），所以文字的相對位置在任何視窗寬度下都保持一致，不需要為不同斷點各寫一組數值。

**780px 以下切換為堆疊版**：疊字方案只在文字寬度小於插畫空白區時安全。窄螢幕若繼續疊字會壓到人物，所以改為 `.landing-hero-stacked`（文字在上、圖在下），而非讓文字持續縮小。

**`.landing-hero { margin-top: -68px }`**：讓主圖往上鑽到導覽列底下，導覽列浮在圖上。若之後調整導覽列高度（目前 padding 18px ＋ logo 36px ≒ 72px），這個負值要跟著調。

**顯示襯線字刻意不接 Google Fonts**：`LegalNotice.vue` 已承諾不使用第三方追蹤，載 webfont 會把訪客 IP 送給 Google，與該承諾牴觸。目前 `--serif` 走各作業系統內建的中文襯線 fallback。

---

## 五、未完成 / 待辦

### 1. 推送與部署（需要在使用者的 Mac 上執行）

沙箱環境沒有 GitHub 認證、也沒有 Railway CLI 與登入狀態，因此以下步驟未執行：

```bash
cd ~/AIAgent/welfare-check
git push origin dev
railway up --ci -s welfare-check-frontend --environment staging
```

目前狀態：`local dev = 395fcd3`、`origin/dev = b795327`。

### 2. 視覺驗證（未做）

沙箱下載 Chromium 卡在 50% 無法完成，因此**只做到型別檢查與 build 通過，沒有實際截圖**。

已驗證：

- `npx vue-tsc -b` 通過，無型別錯誤
- 在隔離副本中 `npm run build` 通過（`dist/assets/index-*.css` 13.28 KB）
- dist 產物含 `dist/images/` 三張 WebP
- build 產物中 `prefers-color-scheme: dark` 計數為 0

**待驗證項目**（部署 staging 後請實測）：

- [ ] 桌機 hero 疊字位置是否落在米白天空區、沒有壓到人物
- [ ] 主圖與頁面背景的接縫是否真的看不出來
- [ ] 780px 斷點切換到堆疊版是否順暢
- [ ] 手機各尺寸（iPhone SE / 13 / Pixel 5 / iPad Mini）無水平溢出
- [ ] 無 console error
- [ ] 問卷頁與結果頁在新色票下是否仍可讀（**這兩頁尚未重新設計，只是被動套用新變數**）

### 3. 尚未合併到 main

首頁已是新的鼠尾草綠風格，但**問卷頁與結果頁仍是舊版面**，此時上正式站會是半新半舊的狀態。建議先在 staging 檢視，等問卷頁與結果頁也改完再一起合併進 `main` 並部署 production。

### 4. 待使用者決定的開放問題

**顯示襯線字要不要 self-host**：目前跨平台不一致（macOS 顯示宋體、Windows 顯示新細明體，觀感差異明顯）。要統一就得自己 self-host 一份子集化中文襯線字型，代價是多幾百 KB。或改為全站用無襯線、靠字重與字級拉出層次。

**問卷頁與結果頁的設計方向**：尚未討論。這是下一步的主要工作。

---

## 六、下一步建議

1. push ＋ 部署 staging ＋ 實測驗證（見上方待驗證清單）
2. 討論並重新設計**問卷頁**（`Questionnaire.vue`，18 題逐題引導）
3. 討論並重新設計**結果頁**（`ResultsView.vue` ＋ `BenefitCard.vue`，含補助總覽表與優先順序標記）
4. 全部完成後一次合併 `dev` → `main` 並部署 production

---

## 七、與 CLAUDE.md 既有規則的關係

本次改動屬於**規則 11（前後端程式碼調整）** 的範圍，不涉及 `SKILL.md`／`README.md`／`網站化規劃.md` 的門檻數字或福利項目異動，因此**不需要**走規則 7 的「開分支 ＋ 更新紀錄留檔 ＋ 人工 review」流程。

規則 11 原本要求「調整完直接 commit + push + 部署，不用每次都問」，本次因沙箱環境缺少認證而卡在 push 之後的步驟，需人工接手完成。

本文件不含任何使用者個資，符合規則 6。
