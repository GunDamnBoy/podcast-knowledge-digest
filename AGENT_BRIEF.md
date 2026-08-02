# AGENT BRIEF — 節目知識庫・每日發布標準說明

這份文件是「節目知識庫（Podcast Knowledge Digest）」的完整規格。任何一個新的 Cowork 對話讀了這份，就能完整重現整套系統。全程使用繁體中文（台灣用語），讀者為專業財經工作者。

網站：<https://gundamnboy.github.io/podcast-knowledge-digest/>

---

## 0. 這個系統在做什麼

每個平日早上自動偵測 20 檔 Podcast／YouTube 節目的新集數，取得**全文**（官方逐字稿或 YouTube 字幕），為每一集撰寫約 2,000–3,000 字的繁體中文完整摘譯＋3–5 個核心重點，同時交付兩種形式：

1. **Word 報告**（.docx）— 交付到對話中供轉發與引用（Cowork 用 `present_files`；若環境有 `SendUserFile` 亦可）。**不要存進 repo 目錄**，該 repo 是 Public。
2. **網站**（本 repo）— 每天新增一個 `data/YYYY-MM-DD.json`，供手機／平板／桌機隨時閱讀與全文搜尋。

排程任務：應為台北平日 08:30 執行。

> ⚠️ **2026-08-02 狀態**：舊的 trigger `trig_015cf7Kr4zHWmtHtPMh1NYuR` 在目前這台 Mac 的 Cowork 排程清單中**並不存在**（`list_scheduled_tasks` 回傳空）。也就是說目前沒有任何東西會自動執行，每日產出都得手動觸發。要恢復自動化，需以 `create_scheduled_task` 重建（cron `30 8 * * 1-5`，Cowork 的 cron 以**本機時區**計算，所以直接寫 08:30 即可，不要再換算成 UTC），且 prompt 必須自包含——排程每次執行都是全新工作階段，讀不到任何過往對話。

---

## 1. 節目清單與全文來源（20 檔）

**A. 官方逐字稿（雲端 WebFetch 可直接讀，優先使用）**

| 節目 | 取得方式 |
|---|---|
| Acquired | RSS `https://feeds.transistor.fm/acquired` 內 `<podcast:transcript>` → `share.transistor.fm/s/<id>/transcript.txt` |
| Lex Fridman | 索引 `lexfridman.com/podcast/` → `lexfridman.com/<slug>-transcript` |
| Dwarkesh Podcast | `https://www.dwarkesh.com/api/v1/archive?sort=new&limit=10` → `dwarkesh.com/p/<slug>` |
| Latent Space | `https://www.latent.space/api/v1/archive?sort=new&limit=10` → `latent.space/p/<slug>` |
| Macro Voices | `https://www.macrovoices.com/guest-content/list-guest-transcripts`（每週更新，PDF 可直接 WebFetch） |
| Exchanges at Goldman Sachs | `goldmansachs.com/insights/goldman-sachs-exchanges/<標題 kebab-case>`（逐字稿內嵌頁面） |
| Unhedged (FT) | **直接讀 `https://www.ft.com/unhedged`**——這是逐日清單（日期＋標題＋作者＋PREMIUM 標記），比站內搜尋 `ft.com/search` 可靠得多。用 `find` 取得目標日期文章的 `href` 後 `navigate` 進去，再 `get_page_text` 取全文。Podcast 逐字稿版（標題為「Transcript: ⋯」）若有則優先，沒有就用當日 newsletter 正文 |
| Masters in Business | `ritholtz.com/<YYYY>/<MM>/transcript-<guest-slug>/`（晚 1–2 週；新集數改走 B） |

**B. YouTube 字幕（需使用者桌機 Chrome）**

All-In `@allin`／BG2 `@Bg2Pod`／Pivot `@pivot`／Hard Fork `@hardfork`／20VC `@20VC`／No Priors `@NoPriorsPodcast`／Lenny's `@LennysPodcast`／Invest Like the Best `@ILTB_Podcast`／Capital Allocators `UCbzQ_YWf9RsBP9ATbmv5kxQ`／Odd Lots 與 Bloomberg Surveillance `@BloombergPodcasts`／Macro Voices `UCICRehoZjq3ZtAWgRJX118A`／The Market Huddle `UCTNgTBKATr18Z7kR32rKOBw`

**偵測新集數**用 iTunes Lookup API（2026-08-02 實測：比爬 Apple 網頁快且穩，回傳結構化 JSON，不需 Chrome）：

```
https://itunes.apple.com/lookup?id=<AppleID>&media=podcast&entity=podcastEpisode&limit=8
```

用 `web_fetch` 取得即可。每集看 `releaseDate`（**UTC**）、`trackName`、`trackTimeMillis`（毫秒）、`description`、`trackViewUrl`。Bloomberg Surveillance 一天發多集，該檔要用 `limit=20`。

注意：回傳的第一筆是節目本身（`wrapperType":"track"`），其 `releaseDate` 是舊資料，不要誤判為新集數；真正的集數是 `wrapperType":"podcastEpisode"` 那些。

各節目 AppleID：

All-In 1502871393｜BG2 1727278168｜Pivot 1073226719｜Hard Fork 1528594034｜Unhedged 1691284824｜Acquired 1050462261｜20VC 958230465｜Invest Like the Best 1154105909｜Capital Allocators 1223764016｜Masters in Business 730188152｜No Priors 1668002688｜Lenny's 1627920305｜Lex Fridman 1434243584｜Dwarkesh 1516093381｜Latent Space 1674008350｜Odd Lots 1056200096｜Macro Voices 1079172742｜Market Huddle 1444520320｜Bloomberg Surveillance 296237493｜GS Exchanges 948913991

**時間窗口**（台北時間）：週二至週五抓過去 26 小時發布的集數；週一抓過去 74 小時（涵蓋週末）。

換算方式：台北 ＝ UTC+8，所以「台北 7/31 全天」＝ `releaseDate` 落在 `2026-07-30T16:00:00Z` 至 `2026-07-31T15:59:59Z`。務必先換算再篩選，美東晚間發布的集數在台北會落到隔天，很容易算錯一天。

**檔名慣例**：`data/YYYY-MM-DD.json` 的日期是**執行當天**（台北），內容是該執行時點往前推 26／74 小時窗口內發布的集數——所以 `2026-07-30.json` 裝的是 7/29 晚間至 7/30 上午發布的集數。補跑歷史某天時要沿用同一慣例，否則日期會對不上。

**注意窗口接縫**：26 小時窗口是以每天 08:30 執行為前提；若某天沒跑或延後跑，前一次窗口結束到這次窗口開始之間的集數會整個掉出去。補跑時務必回頭檢查前一份檔案的實際涵蓋範圍，別假設它蓋滿了整個日曆日。

---

## 2. YouTube 字幕操作要領（已實測）

**先找到影片**：用 `https://www.youtube.com/results?search_query=%22<完整標題>%22`（加引號精確比對）比逐頁捲頻道 `/videos` 快得多。用 `read_page` 帶 `ref_id` 取得結果的 `href` 拿到 `watch?v=` 連結，並核對片長與 Apple 的 `trackTimeMillis` 是否吻合。

**取字幕（2026-08-02 重新實測，以下為實際可行的順序）**：

1. `navigate` 到 `watch` 頁，等 4 秒
2. `find`「`...更多內容`」按鈕並點擊，展開影片說明，等 3 秒
3. 用 `computer` 的 `scroll` 往下捲約 10–12 格，直到畫面出現標題「**字幕記錄**」與藍色按鈕「**顯示轉錄稿**」。先 `screenshot` 確認位置
4. **用座標點擊**那顆「顯示轉錄稿」按鈕，等 6 秒
5. 按 `Home` 回頁面頂端，等 3 秒，再 `get_page_text`
6. 頁面文字中「字幕記錄／搜尋轉錄稿」之後、到片尾台詞之前的整段（含時間戳）即為逐字稿；移除時間戳行後合併

**已知的坑（別再踩）**：

- 用 `find` 拿到的「顯示轉錄稿」ref 直接點**經常沒有反應**（頁面上有兩個同名節點，且影片播放會讓描述自動收合）。要捲到該區塊、用座標點才穩。
- 影片右上角的「⋯」選單**沒有**轉錄稿選項，只有下載與檢舉，別浪費時間。
- 想抄捷徑用 `javascript_tool` 讀 `ytInitialPlayerResponse.captions` 再 fetch 字幕檔：**行不通**。YouTube 有 Trusted Types，`DOMParser` 會被擋；改用 `&fmt=json3` 則回傳空字串（baseUrl 需要 POT token）。乖乖走 UI。
- 純音訊型 Podcast 影片（如 Bloomberg Surveillance）一樣有自動字幕，流程相同。

每集在 Chrome 上最多嘗試 8 分鐘，失敗就走退援。

**退援規則（兩種情況）**：

1. *Chrome／桌面裝置不可用* — B 類節目改以 Apple 節目說明＋WebSearch 相關報導撰寫約 500 字精簡摘要，`source` 欄標註「⚠︎ 全文摘譯待補（執行當下無法連線使用者電腦）」。
2. *該集根本不在 YouTube 上* — 這確實會發生。2026-07-31 補跑時，Bloomberg 的 *Reacting to PCE, GDP, and Kevin Warsh*（42:23）全站搜尋無結果，官方播放清單當日只有四則且顯示「已隱藏無法播放的影片」。此時**不要硬湊內容**：若該集落在窗口內，就寫 500 字精簡摘要並在 `source` 標註「⚠︎ 該集未上架 YouTube，僅依節目說明整理」；若它本來就在窗口邊緣，寧可不收錄，並在交付訊息中明確告知使用者這一集沒被涵蓋。

---

## 3. 內容規格

每一集包含：

- **一句話總結** — 一段，抓住全集最重要的張力，不要流水帳
- **核心重點 3–5 條** — 每條「重點N｜粗體標題」＋2–4 句說明，**必須含對投資人的含義**
- **完整摘譯 2,000–3,000 字** — 依章節時間軸分節，忠於原文論點與數字，正反方意見都要呈現；短節目（15 分鐘以內）約 1,200–1,800 字即可，**不要灌水**
- **本集金句 2–5 句** — 中譯＋出處人名

**跨節目交叉觀察**：當日集數 ≥3 時必寫。呈現「他們一致同意什麼」與「他們在哪裡正面對撞」——同一議題不同節目的收斂與分歧，是這個工具最大的價值來源。

**觀察後記**：2–3 條可在接下來幾天實際對照驗證的觀察點。

排序：All-In 永遠在最前，其後依對總經／AI／資本市場的重要性排序。

**寫作紀律**：自動字幕存在語音辨識誤差（人名、專有名詞），須依上下文校正，不確定處採保守表述並標註。數字一律不四捨五入、不概括。引述為中譯非逐字引文。

---

## 4. 網站資料格式

```
podcast-knowledge-digest/
├── index.html                # 閱讀器（樣式與邏輯，內容不寫死在這裡）
├── data/
│   ├── index.json            # 日期清單（manifest）
│   └── YYYY-MM-DD.json       # 每天一個檔
├── robots.txt                # 全站 noindex，不進搜尋引擎
├── AGENT_BRIEF.md
└── .github/workflows/deploy.yml
```

**每天只需要動兩個檔**：新增 `data/YYYY-MM-DD.json`，並把該日加到 `data/index.json` 的 `days` 陣列**最前面**。`index.html` 不要動（除非要改版面）。

`data/index.json`：

```json
{
  "updated": "2026-07-29T10:30:00+08:00",
  "updatedLabel": "7/29 10:30",
  "days": [
    { "date": "2026-07-29", "label": "2026年7月29日（週三）", "short": "7/29 週三",
      "episodeCount": 5, "shows": ["All-In Podcast", "..."] }
  ]
}
```

`data/YYYY-MM-DD.json`：

```json
{
  "date": "2026-07-29",
  "label": "2026年7月29日（週三）",
  "generatedAt": "2026-07-29T10:30:00+08:00",
  "crossCut": { "title": "跨節目交叉觀察", "intro": "…",
                "points": [{ "title": "一、…", "body": "…" }] },
  "postscript": { "title": "本期觀察後記", "paragraphs": ["…"] },
  "episodes": [
    {
      "id": "allin-1", "showKey": "allin", "show": "All-In Podcast",
      "title": "All-In Podcast 第282集",
      "meta": [{ "k": "節目標題", "v": "…" }, { "k": "原始連結", "v": "https://…" }],
      "published": "2026年7月25日｜片長…", "hosts": "…", "guest": "…",
      "source": "YouTube 官方頻道自動字幕全文", "url": "https://…", "chars": 2992,
      "summary": "一句話總結…",
      "takeaways": [{ "label": "重點一", "title": "…", "body": "…" }],
      "sections": [{ "heading": "一、…", "paragraphs": ["…", "…"] }],
      "quotes": [{ "text": "…", "by": "David Sacks" }]
    }
  ]
}
```

`showKey` 決定卡片色條與徽章顏色，現有值：`allin`／`macrovoices`／`markethuddle`／`unhedged`／`bloomberg`。新增節目時在 `index.html` 的 CSS 加一組 `.ep.s-<key>::before` 與 `.b-<key>`，沒加也能正常顯示（走預設藍）。

---

## 5. 發布流程

1. 產生當日 `data/YYYY-MM-DD.json` 與更新後的 `data/index.json`。
2. **寫入本機 repo 的 `data/` 目錄**：
   - `~/podcast-knowledge-digest/data/YYYY-MM-DD.json`
   - `~/podcast-knowledge-digest/data/index.json`

   **寫入方式依當次可用工具擇一**（2026-08-02 實測：`mcp__remote-devices__*` 整組可能根本沒掛載，不要假設它存在）：
   - **優先**：若 `~/podcast-knowledge-digest` 是本次工作階段的連線資料夾，直接用一般檔案工具（Write／Edit）寫入即可，效果與 `device_commit_files` 完全相同。
   - **次選**：`mcp__remote-devices__device_commit_files`（`force: true`），僅在該工具確實存在時使用。
3. 交付當日 Word 報告給使用者。**Word 檔不要放進 repo 目錄**——這個 repo 是 Public，放進去會被背景程式一起推上 GitHub。寫到暫存輸出資料夾再交付給使用者。
4. 之後**不需手動 push**：Mac 上的 launchd 背景程式 `com.kenny.dashpush`（每 180 秒）會自動 `git add`＋`commit`＋`push`；GitHub Actions 再自動部署到 GitHub Pages。實測從寫檔到 Pages 生效約 2–4 分鐘。
5. 驗證上線：抓 `https://gundamnboy.github.io/podcast-knowledge-digest/data/index.json`，確認 `days[0].date` 是當天。

**重要操作禁忌**：不要跑任何 `git` 指令（含 `git status`），不論是透過 `device_bash` 或沙箱 bash。跑 git 可能留下 `.git/index.lock` 鎖檔擋住背景推送。只用 `cat`／`ls`／`grep` 等唯讀指令檢查狀態即可。

---

## 6. 基礎設施備忘

- **Repo（本機）**：`~/podcast-knowledge-digest`（放在家目錄下，不要放進 `~/Documents`，macOS TCC 會擋背景程式存取受保護資料夾）。
- **GitHub**：`GunDamnBoy/podcast-knowledge-digest`，Public，GitHub Pages（Source ＝ GitHub Actions）。
- **推送認證**：remote URL 內嵌 fine-grained PAT（只授權此 repo、Contents 讀寫），存於本機 `.git/config`。換 token：產新 PAT →
  `git -C ~/podcast-knowledge-digest remote set-url origin https://<新PAT>@github.com/GunDamnBoy/podcast-knowledge-digest.git` → 撤舊。
- **背景推送腳本**：`~/.dashpush/auto-push.sh`，**多 repo 版**，會依序處理 `advisory-knowledge-hub` 與 `podcast-knowledge-digest`；由 launchd agent `com.kenny.dashpush` 每 180 秒觸發。
- **模式限制備忘**：互動／排程階段能讀 Chrome，但雲端不能直接推 GitHub；因此一律由本機背景程式負責推送。
- **連線資料夾（重要）**：不論用哪種寫入方式，都只能寫進「已連線的資料夾」。排程是無人值守執行，當下沒有人能按核准對話框，因此 `~/podcast-knowledge-digest` 必須事先在 Claude 桌面 App 以「Add folder」加為連線資料夾。若某次執行寫不進去，退援作法：照常交付 Word 報告，並把當日的 `data/YYYY-MM-DD.json` 與更新後的 `data/index.json` 一併交付，於結尾說明需要手動放進 repo 的 `data/` 目錄，其餘由背景程式自動完成。
- **登入狀態（每次執行先確認）**：YouTube 必須是 Chrome 已登入狀態。Claude 不會、也不應代為輸入帳密——發現未登入就走退援並在交付時告知使用者。
- **FT 存取現況（2026-08-02 實測，重要）**：這台機器的 Chrome **並未登入 FT 帳號**（首頁右上角仍是 Subscribe／Sign In），但擁有一張有效的 **syndication 授權 cookie**：FT 會自動在站內所有連結後面補上 `?syn-25a6b1a6=1`，premium 文章因此可完整讀取。已用一篇標示 PREMIUM CONTENT、未曾以 token 開啟過的文章驗證：輸入裸網址 → FT 自動改寫補參數 → 取得 7,799 字完整內文、無付費牆訊號。

  **這是脆弱的依賴**：syndication cookie 會過期，清快取、換 Chrome profile 都會失效，而且**失效時不會報錯**，只會安靜退回付費牆，讓排程產出一篇薄摘要而沒人察覺。因此每次處理 FT 內容時，**務必先驗證取到的正文長度是否合理**（Unhedged newsletter 正文通常 5,000 字元以上）；若明顯偏短或出現 `Subscribe to unlock`／`Complete digital access` 等字樣，即視為存取失效，走退援並在交付訊息中明確告知使用者「FT 存取已失效，需重新登入或更新授權」。長期解法仍是登入真正的 FT 帳號。
- **`index.html` 的動態欄位**：交叉觀察的展開按鈕標籤已改為依 `crossCut.points` 實際條數產生（`cnZh` 函式），不再寫死「四條主線」。新增節目時仍需在 CSS 補一組 `.ep.s-<key>::before` 與 `.b-<key>`，沒補會走預設藍色，不影響功能。

---

## 7. 合規與語氣

- 全站 `robots.txt` 與 `<meta name="robots" content="noindex, nofollow">`，定位為個人知識管理站，不做公開發行。
- 每集保留來源標註與原文連結，鼓勵前往原始節目收聽。
- 摘譯為濃縮中譯、非逐字轉載；付費來源（FT、Bloomberg 等）尤其只做重點濃縮並附連結。
- 語氣：繁體中文（台灣慣用語）、專業財經研究腔、全形標點；有觀點但中立，明確標示非投資建議。
