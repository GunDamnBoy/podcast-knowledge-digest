# AGENT BRIEF — 節目知識庫・每日發布標準說明

這份文件是「節目知識庫（Podcast Knowledge Digest）」的完整規格。任何一個新的 Cowork 對話讀了這份，就能完整重現整套系統。全程使用繁體中文（台灣用語），讀者為專業財經工作者。

網站：<https://gundamnboy.github.io/podcast-knowledge-digest/>

---

## 0. 這個系統在做什麼

每個平日早上自動偵測 20 檔 Podcast／YouTube 節目的新集數，取得**全文**（官方逐字稿或 YouTube 字幕），為每一集撰寫約 2,000–3,000 字的繁體中文完整摘譯＋3–5 個核心重點，同時交付兩種形式：

1. **Word 報告**（.docx）— 交付到對話中供轉發與引用（Cowork 用 `present_files`；若環境有 `SendUserFile` 亦可）。**不要存進 repo 目錄**，該 repo 是 Public。
2. **網站**（本 repo）— 每天新增一個 `data/YYYY-MM-DD.json`，供手機／平板／桌機隨時閱讀與全文搜尋。

排程任務：`podcast-digest-daily`，**每天 03:00（台北，含週末）**，cron `0 3 * * *`。搭配的 launchd `com.kenny.podfetch` 在 **01:00** 先跑完轉錄。

> **2026-08-03 從 09:00 改到 03:00，動機與代價都要記住。** 動機有二：一是希望起床就看得到成果；二是與 07:30 的 `advisory-dashboard-daily` 拉開 token 用量。
>
> **代價是結構性的，不是 bug。** 台北 03:00 ＝ 美東前一天 15:00（EDT），而主要節目全部集中在台北 04:00–06:30 落地：Bloomberg TV 04:01、Bloomberg Money 04:25、Masters in Business 05:00、**All-In 06:23**。這些在 03:00 那一刻根本還沒發布，所以**每天的日報固定收不到前一晚的美東晚間集數，它們會出現在隔天凌晨那一版**。All-In 因此大約在發布後 21 小時才進日報，而不是原本的 3 小時。
>
> podfetch 在 01:00 跑，看到的更早（美東 13:00 為止），13:00–15:00 EDT 之間發布的同樣順延一版。
>
> **但沒有任何集數會遺失。** podfetch 的視窗以 `last_run_utc` 為起點，日報又會比對 `url`／`title` 去重，順延的集數下一版必定收得到。看到 All-In 永遠「晚一天」是預期行為，**不要當成故障去追**。

> Cowork 的 cron 以**本機時區**計算，直接寫 03:00 即可，不要換算成 UTC。排程每次執行都是全新工作階段，讀不到任何過往對話，因此任務 prompt 必須自包含（現行版本的做法是：要求執行者先完整讀過本檔案再開工）。
>
> 舊的 trigger `trig_015cf7Kr4zHWmtHtPMh1NYuR`（平日 08:30）已不存在，2026-08-02 以本任務取代。
>
> **排程只在 Claude 桌面 App 開著時執行**；App 關閉時錯過的排程會在下次啟動時補跑。

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

**B. 音檔轉錄（podfetch ＋ Gemini API，見第 2 節）** — 以下節目沒有官方逐字稿，一律走音檔轉錄。iTunes Lookup 回傳的 `episodeUrl` 就是直接的 MP3 網址，不需要 YouTube。

All-In `@allin`／BG2 `@Bg2Pod`／Pivot `@pivot`／Hard Fork `@hardfork`／20VC `@20VC`／No Priors `@NoPriorsPodcast`／Lenny's `@LennysPodcast`／Invest Like the Best `@ILTB_Podcast`／Capital Allocators `UCbzQ_YWf9RsBP9ATbmv5kxQ`／Odd Lots 與 Bloomberg Surveillance `@BloombergPodcasts`／Macro Voices `UCICRehoZjq3ZtAWgRJX118A`／The Market Huddle `UCTNgTBKATr18Z7kR32rKOBw`

**偵測新集數**用 iTunes Lookup API（2026-08-02 實測：比爬 Apple 網頁快且穩，回傳結構化 JSON，不需 Chrome）：

```
https://itunes.apple.com/lookup?id=<AppleID>&media=podcast&entity=podcastEpisode&limit=8
```

用 `web_fetch` 取得即可。每集看 `releaseDate`（**UTC**）、`trackName`、`trackTimeMillis`（毫秒）、`description`、`trackViewUrl`。Bloomberg Surveillance 一天發多集，該檔要用 `limit=20`。

注意：回傳的第一筆是節目本身（`wrapperType":"track"`），其 `releaseDate` 是舊資料，不要誤判為新集數；真正的集數是 `wrapperType":"podcastEpisode"` 那些。

各節目 AppleID：

All-In 1502871393｜BG2 1727278168｜Pivot 1073226719｜Hard Fork 1528594034｜Unhedged 1691284824｜Acquired 1050462261｜20VC 958230465｜Invest Like the Best 1154105909｜Capital Allocators 1223764016｜Masters in Business 730188152｜No Priors 1668002688｜Lenny's 1627920305｜Lex Fridman 1434243584｜Dwarkesh 1516093381｜Latent Space 1674008350｜Odd Lots 1056200096｜Macro Voices 1079172742｜Market Huddle 1444520320｜Bloomberg Surveillance 296237493｜GS Exchanges 948913991

**時間窗口**（台北時間）：**每天**（含週末）抓過去 **26 小時**發布的集數。

> 2026-08-02 起改為每日執行、七天不間斷（08-02 訂在 09:00，08-03 改為 03:00），因此不再需要舊版「週一抓 74 小時涵蓋週末」的規則。每日 26 小時窗口對 24 小時的執行間隔留有 2 小時重疊，用意是吸收執行延遲，**代價是相鄰兩天會重複命中同一集**。所以產檔前**必須去重**：讀取前一天的 `data/YYYY-MM-DD.json`，比對 `url` 與 `title`，已收錄過的集數一律略過。
>
> 週末新集數通常很少，允許出現「當日 0 集」。此時**不要產生空檔案、也不要動 `index.json`**，直接向使用者回報今天沒有新集數即可。

換算方式：台北 ＝ UTC+8，所以「台北 7/31 全天」＝ `releaseDate` 落在 `2026-07-30T16:00:00Z` 至 `2026-07-31T15:59:59Z`。務必先換算再篩選，美東晚間發布的集數在台北會落到隔天，很容易算錯一天。

**檔名慣例**：`data/YYYY-MM-DD.json` 的日期是**執行當天**（台北），內容是該執行時點往前推 26／74 小時窗口內發布的集數——所以 `2026-07-30.json` 裝的是 7/29 晚間至 7/30 上午發布的集數。補跑歷史某天時要沿用同一慣例，否則日期會對不上。

**注意窗口接縫**：26 小時窗口是以每天固定同一時刻執行為前提（現為 03:00）；若某天沒跑或延後跑，前一次窗口結束到這次窗口開始之間的集數會整個掉出去。補跑時務必回頭檢查前一份檔案的實際涵蓋範圍，別假設它蓋滿了整個日曆日。

---

## 2. 全文取得：本機 podfetch 管線（2026-08-02 起為主要方式）

**背景**：2026-08-02 當天 YouTube 轉錄稿在本機 Chrome 上全面失效——面板可開啟但內容永遠停在載入中，`timedtext` 回傳空字串，InnerTube `get_transcript` 回 `FAILED_PRECONDITION`。在兩支不相干影片上重現，確認為環境層級故障。當日六集全部沒有逐字稿。

該次事故暴露的真正問題是架構：全文取得被綁死在「Chrome 開著 ＋ YouTube 已登入 ＋ YouTube 沒改版」三個條件上，任一失效就整天報廢，而且是**安靜失效**。

**修法**：改用 podcast 原始 MP3 ＋ Gemini API 語音轉錄。iTunes Lookup API 的每個 `podcastEpisode` 都帶有 `episodeUrl`（直接 MP3 網址），20 檔節目全部確認可取得——這套系統從一開始就不需要 YouTube。

**元件**

| 項目 | 位置 |
|---|---|
| 主程式 | `~/.podfetch/podfetch.py`（**零外部相依**，只用 Python 標準函式庫） |
| 設定 | `~/.podfetch/config.json`、`~/.podfetch/shows.json` |
| API key | `~/.podfetch/gemini.key`（權限 600，**絕不進 repo**） |
| 執行狀態 | `~/.podfetch/state.json`（`last_run_utc` ＋ 30 天內已處理的 trackId） |
| 紀錄 | `~/.podfetch/logs/YYYY-MM-DD.log` |
| 逐字稿輸出 | `~/podcast-transcripts/YYYY-MM-DD/`（**repo 外部**，須另外加為 Cowork 連線資料夾） |
| 排程 | launchd `com.kenny.podfetch`，每天 **01:00**（比 Cowork 任務早兩小時） |

**流程**：iTunes 偵測 → 下載 MP3 → 切成 25 分鐘段（見下）→ 每段以 base64 內嵌送 Gemini `generateContent`（不需 File API）→ 合併 → 字數檢查 → 寫出 `.md` 與 `manifest.json`。

**切段方式（2026-08-02 改版）**：原本用 ffmpeg，但使用者的 Mac 沒有 Homebrew，為了一個切檔動作要求安裝套件管理器不合理。改為**用純 Python 解析 MPEG Layer III 的 frame 標頭、在 frame 邊界切檔**，不重新編碼，因此零外部相依。單段同時受「秒數」與「9 MiB」兩個上限約束（base64 膨脹約 1.34 倍，須低於 Gemini 的 20MB 請求上限），高位元速率的檔案會自動切得更短。第一個 frame 若是 Xing／Info／VBRI 標頭會跳過——它記的是整個原檔的長度，複製到第一段會讓解碼器誤判時長。若系統剛好有 ffmpeg 則優先使用（會順便降到 16kHz 單聲道 32kbps，上傳量小很多），失敗時自動退回內建切檔器。

**兩個設計重點，改動前請先理解**

1. **視窗以 `last_run_utc` 為準，不是固定 26 小時。** 舊版固定窗口在漏跑一天時會產生無法察覺的缺口（2026-08-02 就發生了，7/31 22:53 到 8/1 15:24 之間整段掉出去）。新版從上次成功執行時間往前推 30 分鐘重疊開始抓，上限 72 小時。**不要改回固定窗口。**
2. **字數檢查是防「安靜失效」的唯一機制。** Gemini 是 LLM 不是機械式辨識器，長音檔上可能改寫、壓縮或跳過整段而不報錯。腳本以英語口說每分鐘 130 字估算期望值，低於 55% 就重試該段；重試後仍不足則標為 `DEGRADED` 並把原因寫進檔案的 YAML front matter 與 manifest。**這個檢查不要拿掉**——沒有它，某天產出一份薄摘譯會沒有任何人察覺。

**逐字稿格式**：檔頭是 YAML front matter（`show`／`title`／`released_utc`／`duration_ms`／`apple_url`／`source`／`words`／`expected_words`／`completeness`／`status`／`warnings`），正文為 `[MM:SS] 講者姓名：內容`。

**講者姓名是新流程最大的增值**。`shows.json` 為每檔節目預先寫入主持人名單，轉錄 prompt 會要求 Gemini 用真名而非 `Speaker A`。跨節目交叉觀察因此可以具體到人（「Chamath 主張 X，而 Kevin Muir 在同一議題上主張 Y」），這是 YouTube 自動字幕從來給不了的維度。

**免費層的額度長這樣（2026-08-02 從 AI Studio Console 實測，同一專案內）**：

| 模型 | RPM | TPM | RPD |
|---|---|---|---|
| Flash（2.5／3／3.5／3.6） | 5 | 250K | **20** |
| Flash-Lite 2.5 | 10 | 250K | 20 |
| **Flash-Lite 3.1／3.5** | 15 | 250K | **500** |

新版 Flash-Lite 的日額度是一般 Flash 的 **25 倍**，這是整個設計裡最重要的一個數字。模型池因此固定為「3 個 Flash（品質優先）＋ 3 個 Flash-Lite（溢流）」，合計逾 1,000 RPD，而一天只需約 15 個請求。**不要把 Lite 名額拿掉**，那等於自願放棄 25 倍額度。另註：`gemini-flash-latest` 目前對應 Gemini 3.6 Flash，屬 20 RPD 那一組；`gemini-2.5-flash` 已對新專案關閉（呼叫回 404），`gemini-2 flash`／`gemini-3.1 pro`／`gemini-2.5 pro` 在免費層是 0/0 不開放。

**免費層真正的瓶頸是 RPD，不是 TPM（2026-08-02 從 Console 實測數據確認）。** 一般 Flash 每個模型每天只有 **20 個請求**，而 TPM 上限 250K 實際只用到 12%（約 30K）。這推翻了直覺——正確策略是「少而大」的請求，不是「多而小」。因此：MP3 一律走 **Files API**（上傳免費且不計入 RPD，也繞開 inline base64 的 20MB 上限）；每個模型各有獨立的日額度，因此組成**多模型輪替池**，撞到日額度就換下一個。處理順序依 `show_priority`（All-In 最前），額度不足時犧牲的是邊際節目而不是主秀。

**但切段長度最後不是由 RPD 決定，而是由「輸出上限」決定。** Lite 有 500 RPD 之後 RPD 就不再是瓶頸，真正會咬人的是 `maxOutputTokens`：30 分鐘音檔的逐字稿約 6,000 字≒8,000＋ token，很容易撞到輸出天花板。所以段長收斂到 **20 分鐘**（約 4,000 字），425 分鐘的一天約 22 個請求。

**成本：目前跑在免費層，月費 0 元。** 2026-08-02 初次測試時撞到 rate limit，原因有二：(1) 自動挑到 `gemini-3-flash-preview`，**preview 模型的免費額度比穩定版嚴格得多**；(2) 三個請求並行，每段 25 分鐘約 4.8 萬 audio token，瞬間 14 萬 token 直接撞 TPM 上限。

**`config.json` 現行實際值（2026-08-03 核對）**：`segment_seconds: 1200`（20 分鐘）、`max_chunk_mb: 48`、`min_request_interval_seconds: 10`、`avoid_preview_models: true`、`flash_slots: 3`／`lite_slots: 3`、`max_output_tokens: 32768`、`default_window_hours: 48`、`max_lookback_hours: 72`。`model_preference` 依序為 `gemini-3-flash`／`gemini-flash-latest`／`gemini-3.5-flash`／`gemini-2.5-flash`／`gemini-3.5-flash-lite`／`gemini-3.1-flash-lite`／`flash-lite`／`flash`。循序處理，六集約需 30–45 分鐘，01:00 起跑到 03:00 的日報仍有兩小時餘裕。

> 上一版 brief 寫的 `gemini-2.5-flash`／`parallel: 1`／`min_request_interval_seconds: 7`／`segment_seconds: 900` 都已過期，勿再引用。

**`max_output_tokens` 必須明確指定，這是最容易重蹈的坑。** 預設約 8,192，而 Gemini 3.x 的 thinking token 也算進輸出預算，2026-08-02 實測導致多段被腰斬（一致卡在 5,600–6,200 字，最慘一段只吐出 6 個字）。同時以 `thinkingConfig.thinkingBudget = 0` 關掉 thinking——逐字轉錄不需要推理。

**模型池會在執行中「瘦身」，這是正常的。** `state.json` 的 `model_pool` 記的是當次跑完後仍可用的模型，不是設定值。2026-08-02 當天的實際軌跡是：`gemini-3-flash-preview`（自動挑到 preview，429）→ `gemini-2.5-flash`（回 404「no longer available to new users」）→ `gemini-2.5-flash-image`（額度滿）→ `gemini-flash-latest`（跑了一段後日額度用盡）→ 最後落到三個 Flash-Lite 完成全部六集。**看到 `model_pool` 只剩 Lite 不代表設定壞了**，代表當天 Flash 額度已耗盡而溢流機制正常運作。

**額度用完時的行為**：429 會讀取 Google 回傳的 `retryDelay` 照建議等待；若判定為日額度耗盡則丟出 `QuotaExhausted`，停止本次執行，**已完成的段落留在 `~/.podfetch/cache/`，下次執行直接沿用不重跑**，且未完成的集數不寫進 `seen`、`last_run_utc` 也不推進，因此下次視窗仍涵蓋得到。若哪天真的要加量再考慮付費，換算約 US$0.12／小時音檔。

**手動執行與排錯**

```
python3 ~/.podfetch/podfetch.py              # 立即跑一次
tail -f ~/.podfetch/logs/$(date +%F).log     # 看進度
launchctl list | grep com.kenny.podfetch     # 確認排程存在
```

`status` 的三種值：`OK` 正常；`DEGRADED` 完整度不足，摘譯照做但要在 `source` 註明；`FAILED` 沒有逐字稿，走退援。

**「當天沒有目錄」≠「podfetch 掛了」（2026-08-03 教訓）。** 0 集時 podfetch 正常結束但不建立當天目錄，所以 `~/podcast-transcripts/<今天>/manifest.json` 讀不到有三種可能，判斷順序如下：

1. **資料夾根本沒連線** → 先 `request_cowork_directory` 連上再重讀（見第 6 節）。
2. **連上了但沒有今天的目錄** → 讀 `~/.podfetch/logs/<今天>.log`。有 `[01:00:0x] 沒有新集數。` 就是真的 0 集，一切正常；日誌根本不存在或停在異常處，才是 podfetch 失效。也可比對 `~/.podfetch/state.json` 的 `last_run_utc` 是否已推進到今天。
3. **確認 podfetch 失效** → 才走第 2 步的 iTunes 退援偵測，並在交付訊息中明講。

漏跑一天不會造成缺口：podfetch 的視窗以 `last_run_utc` 為起點（上限 72 小時），下次執行會自動補回。

**退援順序**：官方逐字稿（A 類節目，永遠優於機器轉錄）→ podfetch → FT 專用流程 → YouTube 字幕（已知不穩，最後手段）→ 節目說明＋WebSearch 寫 500 字精簡摘要並標 ⚠︎。

---

## 2B. YouTube 字幕操作要領（2026-08-02 起已知失效，僅存查）

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
5. 驗證上線：抓 `https://gundamnboy.github.io/podcast-knowledge-digest/data/index.json`，確認 `days[0].date` 是當天、且 `updatedLabel` 是本次執行時間。

   **一定要帶 cache-buster，否則會誤判成推送失效（2026-08-03 實測）。** 裸網址抓回來的是舊快取：當天實測拿到 7/30 的內容，而加上 `?cb=<時間戳>` 重抓立刻是正確的 8/3 版本。`raw.githubusercontent.com` 同樣有快取（當天回的是 7/29）。所以驗證一律用：

   ```
   https://gundamnboy.github.io/podcast-knowledge-digest/data/index.json?cb=<YYYYMMDDHHMMSS>
   ```

   若帶了 cache-buster 仍是舊內容，才是真的沒推上去。此時可用唯讀方式確認推送鏈：`cat .git/refs/heads/main` 與 `cat .git/refs/remotes/origin/main` 是否同一個雜湊、`tail .git/logs/refs/remotes/origin/main` 最後一筆 `update by push` 的時間戳是否為本次執行後。**這些都是 `cat`／`tail`，不是 git 指令，安全。**

**重要操作禁忌**：不要跑任何 `git` 指令（含 `git status`），不論是透過 `device_bash` 或沙箱 bash。跑 git 可能留下 `.git/index.lock` 鎖檔擋住背景推送。只用 `cat`／`ls`／`grep` 等唯讀指令檢查狀態即可。

---

## 6. 基礎設施備忘

- **Repo（本機）**：`~/podcast-knowledge-digest`（放在家目錄下，不要放進 `~/Documents`，macOS TCC 會擋背景程式存取受保護資料夾）。
- **GitHub**：`GunDamnBoy/podcast-knowledge-digest`，Public，GitHub Pages（Source ＝ GitHub Actions）。
- **推送認證**：remote URL 內嵌 fine-grained PAT（只授權此 repo、Contents 讀寫），存於本機 `.git/config`。換 token：產新 PAT →
  `git -C ~/podcast-knowledge-digest remote set-url origin https://<新PAT>@github.com/GunDamnBoy/podcast-knowledge-digest.git` → 撤舊。
- **逐字稿管線**：`~/.podfetch/`（見第 2 節），launchd agent `com.kenny.podfetch` 每天 01:00 執行。輸出到 `~/podcast-transcripts/`，**刻意放在 repo 外部**——本 repo 是 Public，Bloomberg／FT 等付費來源的完整逐字稿一旦被背景推送程式帶上 GitHub 會是實質的著作權問題。不要為了方便把輸出目錄改到 repo 裡面，就算加了 `.gitignore` 也不要。
- **背景推送會無聲失敗，每次都要驗證（2026-08-03 事故）**：8/2 18:20 `auto-push.sh` 被改成只含 `REPO="$HOME/advisory-knowledge-hub"` 的單一 repo 版，本 repo 從此完全脫離自動推送。整個失效過程**沒有任何外顯徵兆**——launchd 回報 exit 0、`push.log` 沒有新行（因為原版在「無變更」時直接 `exit 0` 且不留紀錄）、`data/` 檔案照常寫入、排程任務照常回報成功，只有網站悄悄停在舊版。發現方式是比對 `.git/logs/HEAD` 最後一次 commit 的時間戳與檔案 mtime。
  - **因此第 5 節的驗證步驟必須比對 `updatedLabel` 是否為本次執行時間，不能只看 `days[0].date`**——事故當天 `days[0].date` 早就已經是當天日期，光看它會被騙過去。
  - 修復後的腳本改為多 repo 迴圈、以 `continue` 而非 `exit` 跳過個別 repo、無變更時也寫入 log，並在推送成功後記錄 HEAD 短雜湊。**「靜默」必須是可辨識的狀態，不能與正常運作無法區分。**
- **背景推送腳本**：`~/.dashpush/auto-push.sh`，**多 repo 版**，會依序處理 `advisory-knowledge-hub` 與 `podcast-knowledge-digest`；由 launchd agent `com.kenny.dashpush` 每 180 秒觸發。
- **模式限制備忘**：互動／排程階段能讀 Chrome，但雲端不能直接推 GitHub；因此一律由本機背景程式負責推送。
- **連線資料夾（重要，2026-08-03 更新）**：不論用哪種寫入方式，都只能讀寫「已連線的資料夾」。本系統需要三個：`~/podcast-knowledge-digest`（寫網站資料）、`~/podcast-transcripts`（讀逐字稿）、`~/.podfetch`（排錯時讀 log 與 state）。

  **連線不保證跨工作階段留存，每次執行都要當作可能沒有。** 2026-08-02 的執行讀得到 `~/podcast-transcripts`，但 8/3 09:00 的排程起跑時工作階段裡只剩 `~/podcast-knowledge-digest`——連線沒有帶過來，而且失敗的樣子和「podfetch 沒跑」一模一樣（都是讀不到當天的 `manifest.json`），極容易誤判。

  **正確作法：讀不到就先自己連，連不上才算失效。** 呼叫 `mcp__cowork__request_cowork_directory`（`path` 直接給 `~/podcast-transcripts`）。2026-08-03 實測，**在無人值守的排程執行中這個呼叫不會跳核准對話框，直接成功**，所以這是可靠的自我修復手段，不需要人在場。`~/.podfetch` 同理。

  在桌面 App 以「Add folder」加進來仍然值得做（少一次往返），但**不要把它當成唯一保障**。若某次執行寫不進去，退援作法：照常交付 Word 報告，並把當日的 `data/YYYY-MM-DD.json` 與更新後的 `data/index.json` 一併交付，於結尾說明需要手動放進 repo 的 `data/` 目錄，其餘由背景程式自動完成。
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

---

## 8. 變更紀錄（CHANGELOG）

**維護規則**：這份 brief 與排程任務 `podcast-digest-daily` 的 SKILL.md 是**一組兩份**，改任一邊都必須同步另一邊，並在本節加一筆。詳見 `MAINTENANCE.md`。日期由新到舊。

### 2026-08-03

- **確立 03:00 執行時段的取捨**：台北 03:00 ＝ 美東前一天 15:00，主要節目集中在台北 04:00–06:30 落地，因此**前一晚的美東晚間集數必定順延到隔天那一版**（All-In 約發布後 21 小時進日報）。這是刻意設計，不是故障，也不需要每天在回報中重複解釋。
- **資料夾連線不保證跨工作階段留存**：排程執行中若讀不到，直接用 `request_cowork_directory` 自我修復。實測無人值守時該呼叫不會跳核准對話框。
- **確立「當天沒有目錄 ≠ podfetch 掛了」的三段排查**：先確認資料夾連線 → 再讀 `~/.podfetch/logs/<今天>.log` 看是否為 0 集 → 日誌異常才算真的失效。
- **iTunes lookup 已知陷阱**：US 商店對某些節目（尤其 All-In）快取嚴重過期且 limit 越小越舊，交叉驗證改用 GB／AU 商店；`web_fetch` 對 RSS／XML 一律回 `[binary data]`。
- **驗證上線必須帶 cache-buster**：裸網址與 `raw.githubusercontent.com` 都會回舊快取，只看日期會被騙，要同時確認 `updatedLabel` 是本次執行時間。

### 2026-08-02

- **改以本機 podfetch 管線為主要全文來源**（第 2 節）：launchd `com.kenny.podfetch` 於 01:00 抓音檔並經 Gemini API 轉錄，產出帶講者姓名的逐字稿。跨節目交叉觀察因此可以具體到人。
- **YouTube 字幕全面失效**，降為最後手段（第 2B 節僅存查）。
