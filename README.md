# 節目知識庫 · Podcast Knowledge Digest

把每天沒時間聽完的頂級財經 Podcast，變成可以在手機上讀完的完整中文摘譯。

**網站**：<https://gundamnboy.github.io/podcast-knowledge-digest/>

每天早上（含週末）自動執行：偵測 23 檔節目的新集數 → 取得全文逐字稿 → 每集產出繁體中文完整摘譯與 3–5 個核心重點 → 發布到本站，同時產出一份 Word 報告。摘譯長度依節目長度而定，短節目約 1,200–1,800 字，一小時以上、主題密集的長節目可達 6,500 字。

轉錄在台北時間 01:00 跑，摘譯在 03:00 跑。因為台北 03:00 等於美東前一天下午，**前一晚的美東晚間集數會出現在隔天那一版**——這是排程時段的取捨，不是遺漏，沒有任何集數會掉。

## 追蹤的節目

**科技／創投／AI**：All-In、Acquired、20VC、Pivot、No Priors、Lenny's Podcast、Lex Fridman、BG2 Pod、Hard Fork、Dwarkesh Podcast、Latent Space

**總經／市場**：Odd Lots、Macro Voices、The Market Huddle、Unhedged (FT)、Bloomberg Surveillance、The Compound and Friends、Exchanges at Goldman Sachs

**投資與公司基本面**：Invest Like the Best、Business Breakdowns、In Good Company、Masters in Business、We Study Billionaires (TIP)

## 內容結構

每一集包含一句話總結、3–5 個核心重點（含投資含義）、依章節分節的完整摘譯、中譯金句、主題標籤與轉錄品質資訊。當日集數三集以上時，額外產出**跨節目交叉觀察**——同一議題在不同節目之間的共識與正面對撞，通常是最有價值的一段。

另有兩個跨日累積的區塊：**觀察點記分板**（每天觀察後記提出的可驗證觀察點，由日報逐日回訪判定應驗或落空）與**來賓索引**（同一位來賓歷次出現的集數彙整）。

## 全文來源

**優先使用官方逐字稿**（Acquired、Lex Fridman、Dwarkesh、Latent Space、Macro Voices、Goldman Sachs Exchanges、FT Unhedged、Masters in Business）。兩種情況會改用語音轉錄：部分節目的官方稿會落後一到兩週；**片長超過兩小時的集數也一律走語音轉錄**——取稿工具有單次長度上限，超長稿會被靜默截斷，拼接反而不可靠。Acquired 的深度特輯經常四個半小時，實務上多半屬於後者。

其餘節目走**本機語音轉錄管線**：抓取節目原始音檔，經 Gemini API 轉為逐字稿。轉錄時會帶入各節目的主持人名單作為參考，但**只有在音訊裡有明確依據時才標真名**（自我介紹、被直呼、主持人點名），否則一律標為「講者 1／2」——錯的名字會變成對真實人物的不實陳述，比沒有名字糟得多。轉錄結果會做三種機械檢查——字數完整度、講者標記合理性、時間軸可信度（時間戳偶爾會整個崩壞，而內容其實是完整的）——異常的集數會在該集標記出來。

機器轉錄存在語音辨識誤差（人名、專有名詞尤其明顯），摘譯時已依上下文校正，不確定處採保守表述。

## 網站特色

單頁閱讀器，手機優先。支援全文搜尋（跨所有日期）、依節目篩選、深淺色切換、字級調整、觀察點記分板與來賓索引。每天新增一個 `data/YYYY-MM-DD.json` 並更新 `data/observations.json`，歷史完整累積不刪除。

## 檔案結構

```
.
├── index.html                 # 閱讀器單頁（樣式與邏輯）
├── data/index.json            # 日期清單
├── data/YYYY-MM-DD.json       # 每日內容
├── data/observations.json     # 觀察點記分板（逐日回訪更新）
├── robots.txt                 # 全站 noindex
├── AGENT_BRIEF.md             # 每日產出的完整規格
├── MAINTENANCE.md             # 維護說明與事故／決策檔案
└── .github/workflows/deploy.yml
```

逐字稿本身**不放在這個 repo**——這是 Public repo，付費來源的完整逐字稿不適合公開存放。

## 免責

本站為個人知識管理與研究輔助用途，**非投資建議**。摘譯為濃縮中譯而非逐字轉載，可能遺漏原文細節；節目中提及的個股、ETF、價格水準與交易結構均為原節目來賓或主持人之個人意見。引用數字前請回查原始節目與官方資料。
