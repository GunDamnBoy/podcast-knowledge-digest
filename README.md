# 節目知識庫 · Podcast Knowledge Digest

把每天沒時間聽完的頂級 Podcast 與 YouTube 節目，變成可以在手機上讀完的完整中文摘譯。

**網站**：<https://gundamnboy.github.io/podcast-knowledge-digest/>

每個平日早上 08:30（台北）自動執行：偵測 20 檔節目的新集數 → 取得全文逐字稿 → 每集產出約 2,000–3,000 字繁體中文完整摘譯與 3–5 個核心重點 → 發布到本站，同時產出一份 Word 報告。

## 追蹤的節目

**科技／創投／AI**：All-In、Acquired、20VC、Pivot、No Priors、Lenny's Podcast、Lex Fridman、BG2 Pod、Hard Fork、Dwarkesh Podcast、Latent Space

**總經／市場／資本配置**：Invest Like the Best、Odd Lots、Macro Voices、The Market Huddle、Unhedged (FT)、Bloomberg Surveillance、Capital Allocators、Masters in Business、Exchanges at Goldman Sachs

## 內容結構

每一集包含一句話總結、3–5 個核心重點（含投資含義）、依章節分節的完整摘譯，以及中譯金句。當日集數三集以上時，額外產出**跨節目交叉觀察**——同一議題在不同節目之間的共識與正面對撞，通常是最有價值的一段。

## 全文來源

優先使用官方逐字稿（Acquired、Lex Fridman、Dwarkesh、Latent Space、Macro Voices、Goldman Sachs Exchanges、FT Unhedged、Masters in Business）；其餘節目讀 YouTube 官方頻道字幕。自動字幕存在語音辨識誤差，摘譯時已依上下文校正，不確定處採保守表述。

## 網站特色

單頁閱讀器，手機優先。支援全文搜尋（跨所有日期）、依節目篩選、深淺色切換、字級調整。每天只新增一個 `data/YYYY-MM-DD.json`，歷史完整累積不刪除。

## 檔案結構

```
.
├── index.html                 # 閱讀器單頁（樣式與邏輯）
├── data/index.json            # 日期清單
├── data/YYYY-MM-DD.json       # 每日內容
├── robots.txt                 # 全站 noindex
├── AGENT_BRIEF.md             # 每日產出的標準作業說明
└── .github/workflows/deploy.yml
```

## 免責

本站為個人知識管理與研究輔助用途，**非投資建議**。摘譯為濃縮中譯而非逐字轉載，可能遺漏原文細節；節目中提及的個股、ETF、價格水準與交易結構均為原節目來賓或主持人之個人意見。引用數字前請回查原始節目與官方資料。
