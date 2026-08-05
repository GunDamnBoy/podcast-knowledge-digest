# AGENT BRIEF — 節目知識庫・每日發布標準說明

這份文件是「節目知識庫（Podcast Knowledge Digest）」的完整規格。任何一個新的 Cowork 對話讀了這份，就能完整重現整套系統。全程使用繁體中文（台灣用語），讀者為專業財經工作者。

網站：<https://gundamnboy.github.io/podcast-knowledge-digest/>

> **本檔只寫「現在的規格與判斷規則」。** 事故經過、當初為什麼這樣決定、被否決的選項，一律寫在 `MAINTENANCE.md` 第 7 節「事故與決策檔案」。本檔會以「見 `MAINTENANCE.md` 第 7 節」指過去。這樣分是因為排程每天要完整讀本檔一次，而執行者不需要知道歷史。

---

## 0. 這個系統在做什麼

每天早上（含週末）自動偵測 22 檔 Podcast 的新集數，取得**全文**，為每一集撰寫約 2,000–3,000 字的繁體中文完整摘譯＋3–5 個核心重點，同時交付兩種形式：

1. **Word 報告**（.docx）— 交付到對話中供轉發與引用（Cowork 用 `present_files`）。**不要存進 repo 目錄**，該 repo 是 Public。
2. **網站**（本 repo）— 每天新增一個 `data/YYYY-MM-DD.json`，供隨時閱讀與全文搜尋。

**時序（兩者都不會喚醒睡著的 Mac，見第 6 節）**：

| 時刻（台北） | 元件 | 作用 |
|---|---|---|
| 00:55 | `pmset repeat` 排定喚醒 | 把機器叫醒，讓底下兩個排程跑得到 |
| 01:00 | launchd `com.kenny.podfetch` | 抓音檔、Gemini 轉錄、寫出逐字稿 |
| 03:00 | Cowork 排程 `podcast-digest-daily`（cron `0 3 * * *`） | 讀逐字稿、寫摘譯、發布 |

**03:00 這個時段有一個必須知道的結構性取捨**：台北 03:00 ＝ 美東前一天 15:00，而主要節目集中在台北 04:00–06:30 落地（All-In 約 06:23）。所以**前一晚的美東晚間集數在今天這一版必定收不到，會出現在明天凌晨那一版**——All-In 約在發布後 21 小時進日報。**這是設計，不是故障，不要去追，也不必每天在回報中解釋。** 沒有任何集數會遺失：podfetch 視窗以 `last_run_utc` 為起點、日報又會去重，順延的集數下一版必定收得到。動機與完整代價見 `MAINTENANCE.md` 第 7 節。

**排程機制備忘**：Cowork 的 cron 以**本機時區**計算，直接寫 03:00，不要換算 UTC。每次執行都是全新工作階段、讀不到任何過往對話，因此任務 prompt 必須自包含（現行做法：要求執行者先完整讀過本檔）。**排程只在 Claude 桌面 App 開著時執行**，App 關閉時錯過的會在下次啟動補跑。

---

## 1. 節目清單與全文來源（22 檔）

**A. 官方逐字稿——永遠優於機器轉錄，這類節目每天都要去抓**

| 節目 | 取得方式 |
|---|---|
| Acquired | RSS `https://feeds.transistor.fm/acquired` 內 `<podcast:transcript>` → `share.transistor.fm/s/<id>/transcript.txt` |
| Lex Fridman | 索引 `lexfridman.com/podcast/` → `lexfridman.com/<slug>-transcript` |
| Dwarkesh Podcast | `https://www.dwarkesh.com/api/v1/archive?sort=new&limit=10` → `dwarkesh.com/p/<slug>` |
| Latent Space | `https://www.latent.space/api/v1/archive?sort=new&limit=10` → `latent.space/p/<slug>` |
| Macro Voices | `https://www.macrovoices.com/guest-content/list-guest-transcripts`（每週更新，PDF 可直接 WebFetch） |
| Exchanges at Goldman Sachs | `goldmansachs.com/insights/goldman-sachs-exchanges/<標題 kebab-case>`（逐字稿內嵌頁面） |
| Unhedged (FT) | **直接讀 `https://www.ft.com/unhedged`**——逐日清單（日期＋標題＋作者＋PREMIUM 標記），比站內搜尋可靠得多。`find` 取得目標日期文章的 `href` → `navigate` → `get_page_text`。逐字稿版（標題「Transcript: ⋯」）優先，沒有就用當日 newsletter 正文 |
| Masters in Business | `ritholtz.com/<YYYY>/<MM>/transcript-<guest-slug>/`（晚 1–2 週；新集數改走 B） |

**取官方逐字稿的兩個陷阱（2026-08-05 實測，都會安靜失敗）**

- **Substack 的 `/api/v1/archive` 會回過期快取。** Dwarkesh 與 Latent Space 首次取回的最新一筆分別停在 6/08 與 7/08，**加了 cache-buster 參數才拿到當天集數**。失效的樣子是「這檔今天沒有新集數」，於是安靜退回機器轉錄，官方稿白白不用。**這兩檔的 archive API 一律要帶 `&cb=<時間戳>`。** 與 iTunes 的 US 商店快取是同一類問題。
- **`web_fetch` 有約 104,700 字元的上限。** 長逐字稿會被截斷且不報錯——Latent Space 那集只取到 01:13:58／01:41:28（約 73%）。**取完要比對逐字稿末尾的時間戳與 `trackTimeMillis`**；不足就用 podfetch 的版本補齊末段，並在 `source` 據實標註兩個來源各涵蓋哪一段。

**B. 音檔轉錄（podfetch ＋ Gemini API，見第 2 節）** — 沒有官方逐字稿的節目一律走這條。iTunes Lookup 回傳的 `episodeUrl` 就是直接的 MP3 網址，**不需要 YouTube**。

All-In／BG2／Pivot／Hard Fork／20VC／No Priors／Lenny's／Invest Like the Best／**Business Breakdowns**／**In Good Company**／**The Compound and Friends**／Odd Lots／Bloomberg Surveillance／The Market Huddle／**Masters in Business（新集數）**

> **Business Breakdowns**（Colossus 出品，與 ILTB 同門）每集拆解一家公司的商業模式、單位經濟、護城河、估值框架與風險，來賓多是實際持有該檔股票的 buy-side。**Colossus 在 `joincolossus.com` 的集數頁有官方逐字稿**，若哪天要把它升到 A 類可從那裡取，目前先走 podfetch。
>
> **In Good Company** 是挪威主權基金 CEO Nicolai Tangen 訪談各大企業 CEO，約 25 分鐘，節奏比其他節目快很多。
>
> **The Compound and Friends** 是美股市場週評，與 Bloomberg／Market Huddle／Unhedged 題材有重疊，摘譯時注意不要在交叉觀察裡重複同一件事。

> Masters in Business 兩邊都在：`ritholtz.com` 的官方逐字稿晚 1–2 週，所以**當天一定是走 B**，等官方稿補上是之後補跑才用得到的東西。日常執行把它當 B 類處理即可。

**偵測新集數**用 iTunes Lookup API（不需 Chrome，回傳結構化 JSON）：

```
https://itunes.apple.com/lookup?id=<AppleID>&media=podcast&entity=podcastEpisode&limit=8
```

用 `web_fetch` 取得。每集看 `releaseDate`（**UTC**）、`trackName`、`trackTimeMillis`（毫秒）、`description`、`trackViewUrl`、`episodeUrl`。Bloomberg Surveillance 一天發多集，該檔用 `limit=20`。

**五個已知陷阱**：

- 回傳第一筆是節目本身（`"wrapperType":"track"`），其 `releaseDate` 是舊資料，**不要誤判為新集數**；真正的集數是 `"wrapperType":"podcastEpisode"`。
- **US 商店快取嚴重過期**（尤其 All-In），且 **limit 越小快取越舊**。上面的 `limit=8` 只是起手式；**只要某一檔回傳的最新集數看起來太舊（例如距今超過該節目正常更新間隔），就換 GB 或 AU 商店重查一次**——把網址的 `itunes.apple.com/lookup` 前面加上國別即可（`https://itunes.apple.com/gb/lookup?...`）。實測 GB／AU 是即時的。2026-08-03 實例：US 商店回報 All-In 最新只到 7/18，GB 商店拿到的是 7/31。**這一條若漏掉，退援路徑會安靜漏抓主秀。**
- **`web_fetch` 對 RSS／XML 一律回 `[binary data]`**，不要指望直接讀 feedUrl。
- **`lookup` 端點正常，但 `search` 端點透過 `web_fetch` 回空字串**（沙箱 bash 也連不到 iTunes）。要找新節目的 AppleID 時不能靠 `search`，改用 WebSearch，或直接從 Apple Podcasts 網址的 `id<數字>` 取。
- **節目層那筆的 `releaseDate` 可能落後好幾個月**，用它判斷節目是否停更會出錯。**一律看 `entity=podcastEpisode` 回傳的集數層日期。**

各節目 AppleID：

All-In 1502871393｜BG2 1727278168｜Pivot 1073226719｜Hard Fork 1528594034｜Unhedged 1691284824｜Acquired 1050462261｜20VC 958230465｜Invest Like the Best 1154105909｜**Business Breakdowns 1559120677**｜**In Good Company 1614211565**｜**The Compound and Friends 1456467014**｜Masters in Business 730188152｜No Priors 1668002688｜Lenny's 1627920305｜Lex Fridman 1434243584｜Dwarkesh 1516093381｜Latent Space 1674008350｜Odd Lots 1056200096｜Macro Voices 1079172742｜Market Huddle 1444520320｜Bloomberg Surveillance 296237493｜GS Exchanges 948913991

**權威來源是 `~/.podfetch/shows.json`**（含 AppleID、節目名、主持人名單，Bloomberg 的 `limit: 20` 也在那裡）。上面這份清單是給人看的，兩邊不一致時以 `shows.json` 為準。

### 時間窗口與去重

**每天**（含週末）抓過去 **26 小時**發布的集數。26 小時對 24 小時的執行間隔留有 2 小時重疊，用意是吸收執行延遲，**代價是相鄰兩天會重複命中同一集**。

**所以產檔前必須去重**：讀 `data/` 裡**日期最大的那一份** `YYYY-MM-DD.json`（注意不一定是昨天——0 集日不產檔），比對 `url` 與 `title`，已收錄過的一律略過。**podfetch 主路徑與 iTunes 退援路徑都要做這件事。**

> **但「⚠︎ 待補」的佔位不算已收錄（2026-08-04 事故）。** 前一份裡某集的 `source` 若以 `⚠︎` 開頭（代表當時沒拿到全文，只寫了 500 字精簡摘要或空殼），而**這次拿得到完整逐字稿**，就要**重寫那一集**，不要當成重複而略過。
>
> 這個情境一定會發生，因為它是設計的一部分：podfetch 某集失敗時不會推進 `last_run_utc`，下次執行必定重抓同一集。若去重時一視同仁，補回來的完整逐字稿會被自己的去重規則擋掉，那集就永遠停在佔位狀態——**而且完全沒有徵兆**。
>
> 重寫時把該集**從舊檔移除、寫進今天的檔案**（連同 `episodeCount` 與 `shows` 一併更新），並在回報中說明「某集補上了前一版缺的全文」。

**允許「當日 0 集」**（週末常見）。此時**不要產生空檔案、不要動 `index.json`、不要產 Word 報告**，直接回報後結束。

**時區換算**：台北 ＝ UTC+8，「台北 7/31 全天」＝ `releaseDate` 落在 `2026-07-30T16:00:00Z` 至 `2026-07-31T15:59:59Z`。務必先換算再篩選，美東晚間發布的集數在台北會落到隔天，很容易算錯一天。

**檔名慣例**：`data/YYYY-MM-DD.json` 的日期是**執行當天**（台北），內容是該時點往前推 26 小時窗口內發布的集數。以 03:00 執行為例，`2026-08-04.json` 涵蓋的是**台北 8/3 01:00 至 8/4 03:00** 發布的集數——注意它**不含** 8/4 凌晨 03:00 之後的內容（那批是隔天那一版的）。補跑歷史某天時沿用同一慣例。

**注意窗口接縫**：26 小時窗口以每天固定同一時刻執行為前提，某天沒跑或延後跑就會在兩次窗口之間留下空隙。**但這個空隙通常不會真的掉集數**，因為真正決定「有哪幾集」的是 podfetch，而 podfetch 的視窗以 `last_run_utc` 為起點（上限 72 小時）、下次執行會自動往回補（見第 2 節）。

**真正會掉集數的只有一種情況：podfetch 也一起漏跑，而且中斷超過 72 小時。** 此外走 iTunes 退援路徑時沒有 `last_run_utc` 兜底，26 小時窗口就是硬邊界——**這種時候才需要手動把窗口往前延伸到接上前一份檔案為止**。補跑時一律回頭確認前一份檔案的實際涵蓋範圍，別假設它蓋滿整個日曆日。

---

## 2. 全文取得：本機 podfetch 管線（主要方式）

**元件**

| 項目 | 位置 |
|---|---|
| 主程式 | `~/.podfetch/podfetch.py`（**零外部相依**，只用 Python 標準函式庫） |
| 設定 | `~/.podfetch/config.json`、`~/.podfetch/shows.json` |
| API key | `~/.podfetch/gemini.key`（權限 600，**絕不進 repo**） |
| 執行狀態 | `~/.podfetch/state.json`（`last_run_utc` ＋ 30 天內已處理的 trackId） |
| 段落快取 | `~/.podfetch/cache/`——額度用完中斷時，**已完成的段落留在這裡，下次執行直接沿用不重跑**。未完成的集數不寫進 `seen`、`last_run_utc` 也不推進，所以下次視窗仍涵蓋得到 |
| 紀錄 | `~/.podfetch/logs/YYYY-MM-DD.log` |
| 逐字稿輸出 | `~/podcast-transcripts/YYYY-MM-DD/`（**repo 外部**，須另外加為 Cowork 連線資料夾） |
| 健康檢查 | `~/.podfetch/healthcheck.py`（唯讀，見 `MAINTENANCE.md` 第 3 節） |
| 排程 | launchd `com.kenny.podfetch`，每天 **01:00** |

**流程**：iTunes 偵測 → 下載 MP3 → 切成 20 分鐘段 → 每段經 Files API 上傳後送 Gemini `generateContent` → 合併 → 字數檢查 → 寫出 `.md` 與 `manifest.json`。循序處理，六集約 30–45 分鐘。

**逐字稿格式**：YAML front matter（`show`／`title`／`released_utc`／`duration_ms`／`apple_url`／`source`／`words`／`expected_words`／`completeness`／`status`／`warnings`），正文為 `[MM:SS] 講者姓名：內容`。

**講者姓名是這條管線最大的增值**。`shows.json` 預先寫入每檔節目的主持人名單，轉錄 prompt 要求 Gemini 用真名而非 `Speaker A`。跨節目交叉觀察因此能具體到人（「Chamath 主張 X，而 Kevin Muir 在同一議題上主張 Y」）。

### 四個不要改的設計

1. **視窗以 `last_run_utc` 為準，不是固定 26 小時。** 從上次成功執行時間往前推 30 分鐘重疊開始抓，上限 72 小時。**不要改回固定窗口**——舊版在漏跑一天時會產生無法察覺的缺口。
2. **字數檢查是防「安靜失效」的唯一機制。** Gemini 是 LLM 不是機械式辨識器，長音檔上可能改寫、壓縮或跳過整段而不報錯。腳本以英語口說每分鐘 130 字估算期望值，低於 55% 就重試該段；仍不足則標 `DEGRADED` 並寫進 front matter 與 manifest。**不要拿掉。**
3. **Lite 是主力，Flash 是備援（2026-08-05 反轉）。** 池子仍是 3 Lite ＋ 3 Flash，但**順序改成 Lite 在前**（`config.json` 的 `prefer_lite: true`）。

   | 模型 | RPD |
   |---|---|
   | Flash 3.5／3.6 | **10**（08-05 從 20 砍半） |
   | Flash 2.5 | 20 |
   | Flash-Lite 2.5 | 20 |
   | **Flash-Lite 3.1／3.5** | **500** |

   新版 Flash 只剩 10 RPD，而重試會讓實際請求放大約 2.5 倍（08-05 實測：預估 17 個請求，實際打出 42 次，Flash 兩個模型雙雙超限而 Lite 只用 8 次）。**把最稀缺的資源排在最前面，等於每天開場就燒光它。** 實測 Lite 的完整度 1.14–1.16，與 Flash 沒有可辨識的品質差距。要改回品質優先就把 `prefer_lite` 設為 `false`。
4. **500／503 要換模型，不是死守重試。** 過載是「這個模型現在忙」，不是額度問題；同一模型重試兩次仍 503 就丟 `ModelOverloaded`，走與 404／日額度相同的輪換路徑。**重試同樣計入 RPD**，死守單一模型是雙重浪費——2026-08-04 就因此讓兩個 Flash 的 RPD 爆掉（21/20）而還有 491 次額度的 Lite 完全沒用到，三集白白失敗。經過見 `MAINTENANCE.md` 第 7 節。

**`config.json` 現行值**：`segment_seconds: 1200`、`max_chunk_mb: 48`、`min_request_interval_seconds: 10`、`avoid_preview_models: true`、`flash_slots: 3`／`lite_slots: 3`、`max_output_tokens: 32768`、`default_window_hours: 48`、`max_lookback_hours: 72`。

另有 `prefer_lite: true`（模型池是否 Lite 優先，見上）。**這是布林值，`healthcheck.py` 的數值比對抓不到它**，改動時要自己確認 `config.json` 與本節一致。

另有兩個**清單型**設定，內容不列在這裡（會過期），直接看檔案：

- `show_priority` — 額度不足時的處理順序，All-In 最前，犧牲的是排在後面的邊際節目。**新增節目時要記得插進去。**
- `model_preference` — 模型輪替池的優先序。

> `healthcheck.py` 會比對上面**數值型**設定與 `config.json` 是否一致，專門抓「改了設定卻漏改 brief」；**清單型的那兩個它檢查不到**，改動時要自己確認。額度實測數據、模型選擇的來龍去脈見 `MAINTENANCE.md` 第 7 節。

**手動執行與排錯**

```
python3 ~/.podfetch/podfetch.py              # 立即跑一次
tail -f ~/.podfetch/logs/$(date +%F).log     # 看進度
launchctl list | grep com.kenny.podfetch     # 確認排程存在
python3 ~/.podfetch/healthcheck.py           # 一次跑完所有機械式檢查
```

`status` 三種值：`OK` 正常；`DEGRADED` 完整度不足，摘譯照做但要在 `source` 註明；`FAILED` 沒有逐字稿，走退援。

### 讀不到當天目錄時的三段排查

**「當天沒有目錄」≠「podfetch 掛了」。** 0 集時 podfetch 正常結束但不建立當天目錄。依序排查，不要跳步：

1. **資料夾根本沒連線** → 先 `request_cowork_directory` 連上再重讀（見第 6 節）。
2. **連上了但沒有今天的目錄** → 讀 `~/.podfetch/logs/<今天>.log`。有 `沒有新集數。` 就是真的 0 集，一切正常；停在異常處才是 podfetch 失效。也可看 `state.json` 的 `last_run_utc` 是否已推進到今天。
3. **今天的日誌根本不存在** → **先不要判定失效，這一格有陷阱**。日報跑在 03:00，若 podfetch 的執行時刻漂到 03:00 之後（例如 plist 被改成別的小時、或機器睡到天亮才補跑），當下「今天還沒有日誌」是必然的，看起來和真失效一模一樣。**此時去讀 `logs/` 裡最新那一份的開頭時間戳**：若不是 `[01:`，就是時刻漂移而非失效，按下面的守衛處理並在回報中明講；若最新日誌是昨天且開頭正常為 `[01:`，那才比較像今天真的沒跑起來。兩種情況都要走 iTunes 退援把當天內容補齊，但**回報時要講對是哪一種**——講錯會讓使用者往錯的方向修。

### 時刻漂移守衛

**podfetch 日誌開頭的時間戳正常應為 `[01:00:0x]`。不是的話，代表 podfetch 的實際執行時刻已經漂掉，日報有可能搶在它前面執行**——這種失效是安靜的：podfetch 本身完全正常，只有日報品質悄悄掉一級。

**成因有兩類，症狀完全相同**：(a) plist 的時刻值不對；(b) 機器睡著、launchd 醒來後才補跑。要在當日回報中明講，並依這個順序提示使用者排查（**三項都要看完**）：

1. `/usr/libexec/PlistBuddy -c "Print :StartCalendarInterval" ~/Library/LaunchAgents/com.kenny.podfetch.plist` — 應為 `Hour = 1, Minute = 0`。**先查這一項**：它最便宜、最確定，而且時間戳若剛好落在某個整點又只差一兩秒（例如 `[07:00:01]`），那正是 `StartCalendarInterval` 準時觸發的特徵，指向設定值而非喚醒失敗
2. `pmset -g custom` — AC Power 段的 `sleep` 應為 `0`（**這是主要保障**，插電時永不睡眠）
3. `pmset -g sched` — 應有 `wakepoweron at 0:55AM every day`（後備）

**三項都要看，不要查到一項就收手。** 兩類成因（設定值錯、機器睡著）會產生一模一樣的症狀，而且**先查到的那一項若已經被人改過，很容易把「修改後的狀態」誤讀成「修改前的證據」**。若 plist 正確而時間戳仍偏晚，才往喚醒方向查；環境設定全貌見 `MAINTENANCE.md` 第 9 節。

漏跑一天不會造成缺口：podfetch 視窗以 `last_run_utc` 為起點（上限 72 小時），下次執行會自動補回。

### 退援順序

1. **官方逐字稿**（第 1 節 A 類）— 永遠優先。**manifest 決定「有哪幾集」，不決定「用哪份全文」**：A 類節目即使 podfetch 已轉錄，仍要去抓官方稿，抓不到才退回 podfetch 版本，並據實填 `source`。
2. **podfetch 逐字稿** — B 類節目的主要來源。
3. **FT 專用流程**（Unhedged）— Unhedged 屬於第 1 節 A 類，**它的「官方逐字稿」就是走這條 FT 流程取得**，不是獨立於第 1 層之外的另一層；列在這裡只是因為它有專屬的失效檢查。

   > **只能走 Chrome**（`find` → `navigate` → `get_page_text`）。**`ft.com` 已於 2026-08-06 進入本環境 `web_fetch` 的封鎖清單（回 HTTP 403 `URL is on blocklist`），那條路已死，不要再試。** 這一層目前掛在一個**沒被無人值守驗證過**的路徑上——Chrome 從未在排程執行中實際跑完 FT 流程（08-06 那集是休刊日轉播姊妹節目，本來就沒有官方稿）。下次真有 Unhedged 自製集數時是第一次實測，**若卡在工具權限就直接退回下一層並在回報中明講，不要空等**。

   **取到後必須檢查正文長度**，通常 5,000 字元以上；明顯偏短或出現 `Subscribe to unlock`／`Complete digital access` 即視為 FT 存取失效。**此時退回第 2 層（podfetch 逐字稿），不是跳到第 4 層**——Unhedged 是 B 類以外的節目但 podfetch 一樣有轉錄它。podfetch 也沒有才繼續往下，並明確告知使用者 FT 存取已失效。
4. **YouTube 字幕** — 2026-08-02 起已知全面失效，只當最後手段，每集最多試 5 分鐘。須為 Chrome 已登入 YouTube 的狀態，未登入就直接走下一層並告知，不要嘗試代為登入。操作要領見 `MAINTENANCE.md` 第 8 節。
5. **都拿不到** — 依節目說明＋WebSearch 公開報導寫約 500 字精簡摘要，`source` 標註「⚠︎ 全文摘譯待補」及原因，**該集 `quotes` 留空陣列**。若某集本來就在窗口邊緣且拿不到全文，寧可不收錄，並在交付訊息中明講這一集沒被涵蓋。

**絕對不要憑印象編造節目內容，也不要編造引述。沒有逐字稿就不寫金句。**

---

## 3. 內容規格

每一集包含：

- **一句話總結** — 一段，抓住全集最重要的張力，不要流水帳
- **核心重點 3–5 條** — 每條「重點N｜粗體標題」＋2–4 句說明，**必須含對投資人的含義**
- **完整摘譯——依節目長度分層（2026-08-06 改）** — 依章節時間軸分節，忠於原文論點與數字，正反方意見都要呈現。

  | 節目長度 | 目標字數 |
  |---|---|
  | ≤15 分鐘 | 1,200–1,800 |
  | 15–30 分鐘 | 2,000–3,000 |
  | 30–55 分鐘 | 2,500–4,000 |
  | ≥55 分鐘，或 10 個以上獨立主題 | 4,000–6,500 |

  **原本一律 2,000–3,000 是不切實際的**：57–65 分鐘、10 個以上獨立主題的節目（Compound、Unhedged、ILTB 這類）壓到 3,000 字必然砍掉整段內容，實務上執行者都會選擇保留完整性然後在回報裡說明超規格——**規格天天被違反就不是規格**。

  **上限仍然存在，`不要灌水` 的紀律不變。** 超出所屬層級上限時要在回報中說明理由；短節目硬拉長比長節目超規格更嚴重。
- **本集金句 2–5 句** — 須為逐字稿中實際出現的發言，中譯＋標明講者姓名

**跨節目交叉觀察**：當日集數 ≥3 時必寫。呈現「他們一致同意什麼」與「他們在哪裡正面對撞」——同一議題不同節目的收斂與分歧，是這個工具最大的價值來源。有講者姓名時要具體到人。

**觀察後記**：2–3 條可在接下來幾天實際對照驗證的觀察點。

**排序**：All-In 永遠在最前，其後依對總經／AI／資本市場的重要性排序。

**寫作紀律**：機器轉錄存在語音辨識誤差（人名、專有名詞），須依上下文校正，不確定處採保守表述並標註。數字一律不四捨五入、不概括。引述為中譯非逐字引文。

> **講者標記會誤植，而且字數檢查抓不到（2026-08-06）。** 該集完整度 1.01、狀態 OK，但 Gemini 從中段起把主持人標成片頭廣告旁白者的名字。**`shows.json` 的主持人名單只是提示，不保證正確歸屬。**
>
> 因此金句與立場歸屬**不能只信逐字稿的講者標籤**，要用開場自我介紹、代稱人稱、話題連續性交叉驗證——尤其是「開場說明某人今天請假」這類資訊，它會讓整集的預設歸屬失效。**判定不了就寫節目名而不是猜人名。** 跨節目交叉觀察寫「誰主張什麼」時風險最高，因為錯誤歸屬會直接變成對某個人的錯誤指涉。

---

## 4. 網站資料格式

```
podcast-knowledge-digest/
├── index.html                # 閱讀器（樣式與邏輯，內容不寫死在這裡）
├── data/
│   ├── index.json            # 日期清單（manifest）
│   └── YYYY-MM-DD.json       # 每天一個檔
├── robots.txt                # 全站 noindex，不進搜尋引擎
├── README.md                 # GitHub 門面（Public，改動系統時記得同步）
├── AGENT_BRIEF.md            # 本檔：規格
├── MAINTENANCE.md            # 維護說明＋事故與決策檔案
└── .github/workflows/deploy.yml
```

**每天只需要動兩個檔**：新增 `data/YYYY-MM-DD.json`，並把該日加到 `data/index.json` 的 `days` 陣列**最前面**（`days` 一律由新到舊）。**`index.html` 不要動。**

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
      "source": "podfetch 逐字稿（Gemini 轉錄）", "url": "https://…", "chars": 2992,
      "summary": "一句話總結…",
      "takeaways": [{ "label": "重點一", "title": "…", "body": "…" }],
      "sections": [{ "heading": "一、…", "paragraphs": ["…", "…"] }],
      "quotes": [{ "text": "…", "by": "David Sacks" }]
    }
  ]
}
```

### showKey

`showKey` 決定卡片色條與徽章顏色，**一律採用 `~/.podfetch/shows.json` 的鍵值**，不要在網站端另取名字，否則徽章永遠對不上。22 檔完整鍵值：

`allin`／`bg2`／`pivot`／`hardfork`／`unhedged`／`acquired`／`twentyvc`／`iltb`／`breakdowns`／`ingoodcompany`／`compound`／`mib`／`nopriors`／`lennys`／`lex`／`dwarkesh`／`latentspace`／`oddlots`／`macrovoices`／`markethuddle`／`bloomberg`／`gsx`

**`index.html` 目前定義了 17 組**：`allin`／`macrovoices`／`markethuddle`／`unhedged`／`bloomberg`／`latentspace`／`lex`／`mib`／`twentyvc`／`breakdowns`／`ingoodcompany`／`compound`／`oddlots`／`dwarkesh`／`iltb`／`pivot`，另含已下架的 `capitalallocators`（供歷史資料顯示）。其餘鍵值第一次出現在資料裡時，該集會走預設藍——功能正常但視覺不一致，此時在回報中提一句即可。補的時候三處都要補：`.ep.s-<key>::before`、`.b-<key>`、`html[data-theme="dark"] .b-<key>`。

> `capitalallocators` 於 2026-08-03 移除。舊資料檔裡若還有這個鍵值，該集會走預設藍——**不要為此回頭改歷史檔案**，歷史資料保持原樣。

`index.html` 的交叉觀察展開按鈕標籤依 `crossCut.points` 實際條數產生（`cnZh` 函式），不寫死條數。

---

## 5. 發布流程

1. 產生當日 `data/YYYY-MM-DD.json` 與更新後的 `data/index.json`。
2. **寫入 `~/podcast-knowledge-digest/data/`**：連線資料夾用一般檔案工具（Write／Edit）即可。若本次工作階段剛好掛載了 `mcp__remote-devices__device_commit_files`（`force: true`）也可以，但**不要假設它存在**。
3. 交付當日 Word 報告。**Word 檔不要放進 repo 目錄**——這個 repo 是 Public，放進去會被背景程式推上 GitHub。寫到暫存輸出資料夾再交付。
4. **不需手動 push**：launchd `com.kenny.dashpush`（每 180 秒）自動 `git add`＋`commit`＋`push`，GitHub Actions 再部署到 Pages。從寫檔到生效約 2–4 分鐘。
5. **驗證上線，一定要帶 cache-buster**：

   ```
   https://gundamnboy.github.io/podcast-knowledge-digest/data/index.json?cb=<YYYYMMDDHHMMSS>
   ```

   確認 `days[0].date` 是當天、**且 `updatedLabel` 是本次執行時間**。裸網址與 `raw.githubusercontent.com` 都會回舊快取（實測回到三天前），**只看日期會被騙**——2026-08-03 的 `auto-push.sh` 事故當天 `days[0].date` 早就是當天日期。

   若帶了 cache-buster 仍是舊內容，才是真的沒推上去。此時用唯讀方式確認推送鏈：`cat .git/refs/heads/main` 與 `cat .git/refs/remotes/origin/main` 是否同一雜湊、`tail .git/logs/refs/remotes/origin/main` 最後一筆 `update by push` 的時間戳。**這些是 `cat`／`tail`，不是 git 指令，安全。**

**寫不進 repo 時的退援（不要因此放棄當天產出）**：照常交付 Word 報告，並把 `data/YYYY-MM-DD.json` 與更新後的 `data/index.json` 一併交付，說明需要手動放進 repo 的 `data/` 目錄，其餘由背景程式完成。

**重要操作禁忌**：不要跑任何 `git` 指令（含 `git status`），不論透過何種方式。跑 git 可能留下 `.git/index.lock` 擋住背景推送。只用 `cat`／`ls`／`grep` 等唯讀指令。

---

## 6. 基礎設施備忘

- **Repo（本機）**：`~/podcast-knowledge-digest`（放家目錄下，不要放進 `~/Documents`，macOS TCC 會擋背景程式存取受保護資料夾）。
- **GitHub**：`GunDamnBoy/podcast-knowledge-digest`，Public，Pages（Source ＝ GitHub Actions）。
- **推送認證**：remote URL 內嵌 fine-grained PAT（只授權此 repo、Contents 讀寫），存於本機 `.git/config`。換 token：產新 PAT → `git -C ~/podcast-knowledge-digest remote set-url origin https://<新PAT>@github.com/GunDamnBoy/podcast-knowledge-digest.git` → 撤舊。
- **背景推送腳本**：`~/.dashpush/auto-push.sh`，**多 repo 版**，依序處理 `advisory-knowledge-hub` 與 `podcast-knowledge-digest`，由 launchd `com.kenny.dashpush` 每 180 秒觸發。**這支腳本曾經靜默失效整整一天**（見 `MAINTENANCE.md` 第 7 節），所以第 5 節的驗證不能省。

- **電源與睡眠設定（整套系統的隱藏前提，完整說明見 `MAINTENANCE.md` 第 9 節）**：01:00 的 podfetch 與 03:00 的日報**都不會把睡著的 Mac 叫醒**，而且需要的不是「時間到醒一下」，是**從 01:00 到中午的連續清醒**（03:00 日報、07:30 投顧那條線都在這個窗口內）。這台機器定位為常時開機的伺服器：放在家裡、全天開機、插著電、蓋子打開。

  ```bash
  sudo pmset -c sleep 0      # 主要保障：插電時永不睡眠
  sudo pmset -c disksleep 0
  sudo pmset -c womp 1
  sudo pmset repeat wakeorpoweron MTWRFSU 00:55:00   # 後備：萬一仍睡著
  ```

  **`sleep 0` 是主要保障，`repeat wakeorpoweron` 是後備，兩者都要留。** 只有後備而沒有主要保障時，機器會在 00:55 醒來、閒置後又睡回去，03:00 就接不到。

  **驗證**：`pmset -g custom`（AC Power 段 `sleep` 應為 0）、`pmset -g sched`、`pmset -g ps`（應顯示 `AC Power`）。

  **這一整組設定都不存在於任何設定檔裡，重灌或換機不會跟著遷移**，還包括幾個沒有指令可查的前提：蓋子要打開、Claude 桌面版要在登入項目、不要裝會讓 Mac 插電時改用電池的充電管理軟體（會使 `-c sleep 0` 整個失效，且失效方式是安靜的）。清單見 `MAINTENANCE.md` 第 9 節。

- **podfetch 排程時刻**：必須在 01:00，比日報早兩小時。`~/.podfetch/fix-schedule.sh` 可把 plist 的 `StartCalendarInterval` 寫回 01:00 並重新 `launchctl load`。**動它之前先照第 2 節「時刻漂移守衛」底下那三項（plist →`pmset -g custom` → `pmset -g sched`）確認成因**——設定值錯與機器睡著會產生相同症狀，盲目套用這支腳本在後者情境下會造成「看起來修好了但問題沒動」的假性修復。腳本刻意放在 repo 外部。
- **逐字稿輸出刻意放在 repo 外部**：本 repo 是 Public，Bloomberg／FT 等付費來源的完整逐字稿一旦被背景推送帶上 GitHub 會是實質的著作權問題。**不要為了方便把輸出目錄改到 repo 裡面，就算加了 `.gitignore` 也不要。**

- **連線資料夾**：本系統需要三個——`~/podcast-knowledge-digest`（寫網站資料）、`~/podcast-transcripts`（讀逐字稿）、`~/.podfetch`（排錯讀 log 與 state）。

  **連線不保證跨工作階段留存，每次執行都要當作可能沒有。** 失敗的樣子和「podfetch 沒跑」一模一樣（都是讀不到當天 `manifest.json`），極容易誤判。**讀不到就先自己連，連不上才算失效**：呼叫 `mcp__cowork__request_cowork_directory`（`path` 直接給 `~/podcast-transcripts`）。實測**在無人值守的排程執行中這個呼叫不會跳核准對話框，直接成功**，是可靠的自我修復手段。在桌面 App 以「Add folder」加進來仍值得做（少一次往返），但不要當成唯一保障。

- **FT 存取現況**：這台機器的 Chrome **並未登入 FT 帳號**，但有一張有效的 **syndication 授權 cookie**：FT 會自動在站內連結後補上 `?syn-25a6b1a6=1`，premium 文章因此可完整讀取。

  **這是脆弱的依賴**：cookie 會過期，清快取、換 Chrome profile 都會失效，而且**失效時不會報錯**，只安靜退回付費牆。所以每次處理 FT 內容都要驗證正文長度（見第 2 節退援順序第 3 項）。長期解法是登入真正的 FT 帳號。
- **YouTube 登入狀態**：走到該退援層時必須是 Chrome 已登入狀態。Claude 不會也不應代為輸入帳密——發現未登入就走下一層並在交付時告知。

---

## 7. 合規與語氣

- 全站 `robots.txt` 與 `<meta name="robots" content="noindex, nofollow">`，定位為個人知識管理站，不做公開發行。
- **每集保留來源標註與原文連結**，鼓勵前往原始節目收聽。
- 摘譯為濃縮中譯、非逐字轉載；付費來源（FT、Bloomberg 等）尤其只做重點濃縮並附連結。
- 語氣：繁體中文（台灣慣用語）、專業財經研究腔、全形標點；有觀點但中立，明確標示非投資建議。

---

## 8. 變更紀錄（CHANGELOG）

**維護規則**：本檔與排程任務 `podcast-digest-daily` 的 SKILL.md 是**一組兩份**，改任一邊都必須同步另一邊，並在本節加一筆。**事故經過寫進 `MAINTENANCE.md` 第 7 節，不要寫進這裡**——本節只記「改了什麼、為什麼改」。日期由新到舊。

### 2026-08-06

- **修掉 08-05 我自己引進的 bug：503 不再讓模型永久除名。** 新增 `OVERLOADED` 冷卻表（`config.json` 的 `overload_cooldown_seconds: 300`），500／503 改為冷卻 5 分鐘後自動回池；`EXHAUSTED` 回歸原設計，只放日額度用盡與 404。**08-06 的實況是：三個 500 RPD 的 Lite 在 77 秒內被一次過載尖峰全數永久除名，剩下 10 RPD 的 Flash 扛完 13 段裡的 10 段，把 3.6 Flash 燒到 22/10。** `prefer_lite` 本身生效了，是冷卻語意錯誤把它的效果整個抵銷掉。經過見 `MAINTENANCE.md` 第 7 節。
- **摘譯字數改為依節目長度分層**（第 3 節）：≤15 分 1,200–1,800／15–30 分 2,000–3,000／30–55 分 2,500–4,000／≥55 分或 10 個以上獨立主題 4,000–6,500。**原本一律 2,000–3,000 每天都被違反**——57–65 分鐘的節目壓到 3,000 字必然砍掉整段內容，執行者只能超規格後在回報裡解釋。**天天被違反的規格不是規格。** 上限與「不要灌水」的紀律仍在，超出所屬層級才需要說明。
- **`ft.com` 已進入本環境 `web_fetch` 的封鎖清單**（HTTP 403 `URL is on blocklist`）。第 2 節退援第 3 層改為明寫「只能走 Chrome」，並標註**這條路徑從未在無人值守的排程中實測過**，卡住就退回 podfetch 那層並在回報中明講，不要空等。
- **新增「講者標記誤植」的寫作紀律**（第 3 節）。08-06 實例：完整度 1.01、狀態 OK，但 Gemini 從中段起把主持人標成片頭廣告旁白者，而開場已說明該主持人請假。**這是字數檢查抓不到的失敗態**——`shows.json` 的主持人名單只是提示、不保證歸屬正確。金句與立場歸屬要交叉驗證，判定不了就寫節目名。SKILL.md 的主動回報清單也補上這一項（現為十項）。

### 2026-08-05

- **Google 把新版 Flash 的免費層 RPD 從 20 砍到 10**（3.5／3.6；2.5 Flash 仍是 20，Flash-Lite 3.1／3.5 仍是 500）。第 2 節額度表已更新。
- **模型池順序反轉為 Lite 優先**（`config.json` 新增 `prefer_lite: true`，`podfetch.py` 的 `build_model_pool` 依此決定 `take()` 順序）。**注意：光改 `model_preference` 沒有用**——舊版一律先 `take(heavy)` 再 `take(lite)`，池子順序與偏好清單無關，必須改程式。08-05 實測預估 17 個請求實際打出 42 次（重試放大約 2.5 倍），Flash 兩個模型雙雙超限而 Lite 只用 8 次；Lite 完整度 1.14–1.16 與 Flash 無可辨識差距。
- **補兩個會安靜失敗的官方稿陷阱**（第 1 節）：Substack `/api/v1/archive` 回過期快取（Dwarkesh、Latent Space 分別停在 6/08 與 7/08，要帶 cache-buster）；`web_fetch` 約 104,700 字元上限會截斷長逐字稿且不報錯（Latent Space 只取到 73%，末段以 podfetch 補齊）。**兩者失效的樣子都是「今天沒有官方稿」，於是安靜退回機器轉錄。**
- 補 `dwarkesh`／`iltb`／`pivot` 三組 CSS，`index.html` 現為 17 組。
- **還原被覆寫的排程 SKILL.md 四項改動**（08-03 第五次巡檢加的：iTunes 子代理的 US 商店快取規則、第 7 節合規入口、回報清單的「寫不進 repo」、三段排查第 3 格）。**08-04 我用 `update_scheduled_task` 送出完整 prompt 時把它們蓋掉了**——`prompt` 是整份取代不是局部編輯，而我以為自己就是上一個改它的人。經過與教訓見 `MAINTENANCE.md` 第 7 節，維護 skill 已加入對應的檢查步驟。
- **修掉子代理比對抓到的其餘不一致**：`config.json` 的 `_comment_quota` 仍寫舊的 20 RPD（與同檔 `_comment_pool` 打架）；`MAINTENANCE.md` 第 7 節 08-02 那篇的額度表沒標明是當時值、讀起來像現行規格；MAINTENANCE 多處仍寫 20 檔／9 組 CSS；「三個不要改的設計」下面有四項、「三個已知陷阱」下面有五條；本節變更紀錄未由新到舊排序；Masters in Business 被誤接在 Compound 的說明結尾而不在 B 類清單裡。

### 2026-08-04（首次實跑後的修正）

- **`pmset` 那套設定驗證成功**：08-04 的 podfetch 日誌開頭是 `[01:00:00]`，準時執行。08-03 的延後補跑問題確認解決。
- **修掉一個會靜默吃掉集數的去重缺陷（本次最重要）。** 08-04 有 3 集因 Gemini HTTP 503 轉錄失敗，日報照規則寫成 `⚠︎ 全文摘譯待補` 的佔位。但 podfetch 失敗時不推進 `last_run_utc`，下次執行必定重抓同一集——**而去重規則會比對 `url`／`title` 把它當成「已收錄」而略過，補回來的完整逐字稿因此永遠進不了網站，且毫無徵兆**。這是設計本身保證會發生的組合，不是偶發。已在第 1 節加入例外：`source` 以 `⚠︎` 開頭的集數不算已收錄，拿到全文要重寫並跨檔搬移。同時明訂 **`⚠︎` 是機器讀的標記，不可改寫成別的格式**。
- **`healthcheck.py` 兩處誤報，都是這次實跑才暴露的**：(1) 缺 CSS 原本判 FAIL，但 brief 明訂那只是視覺不一致、功能正常，改為 WARN；(2) showKey 命名檢查原本拿全部歷史資料比對 `shows.json`，於是移除節目後會產生**永久性假警報**（歷史檔案裡的 `capitalallocators` 永遠都在），改為只檢查最新一份，並把僅存在於歷史的鍵值單獨列為預期狀態。
- **新增「待補全文」檢查**：列出最新一份裡 `⚠︎` 開頭的集數，提醒下次要重寫。
- 補上 `oddlots` 與 `capitalallocators` 的 CSS（前者是現役節目卻一直沒定義，08-04 第一次出現；後者為了讓歷史資料正常顯示），`index.html` 現為 14 組。
- **`podfetch.py` 新增 `ModelOverloaded`：500／503 重試兩次就換模型。** 從 AI Studio Console 的當日數據反推才看清根因——兩個 Flash 的 RPD 都爆到 21/20，而 Flash-Lite 只用了 9/500 與 1/500，503 才是主要錯誤（約 22 次）。**舊版只有 429 日額度會觸發輪換，503 則在同一模型上把 5 次重試燒完再判定整集失敗**；由於重試也計入 RPD，等於一邊燒掉 Flash 額度、一邊放著 491 次 Lite 額度不用。順帶確認 TPM 只用到 12–15%，brief 原本「瓶頸是 RPD 不是 TPM」的判斷成立。
- 08-04 那兩集 Capital Allocators 佔位已從 `data/2026-08-04.json` 移除（空殼內容，且節目本次下架不會再補），該日 6 集改為 4 集，`index.json` 同步。

### 2026-08-03（第五次，同步巡檢）

- **撤銷「podfetch 延後補跑」這個根因判定，`MAINTENANCE.md` 該篇事故紀錄已刪除。** 該篇宣稱 08-03 日誌是 `[07:00:01]` 的原因是機器睡眠、且「plist 一直都是 `Hour = 1`」。實情相反：**當天 plist 就是 `Hour = 7`**（那也是重整前本檔第 6 節記載的設計值），是當日稍晚才由使用者改成 1；調查者讀到的 `Hour = 1` 是修改後的狀態，卻被當成修改前的證據。`[07:00:01]` 這種「整點加一秒」正是 `StartCalendarInterval` 準時觸發的特徵，不是喚醒補跑。**`pmset` 那組電源設定獨立保留**——01:00 的工作在會睡眠的 Mac 上確實需要它，那部分的決策沒有問題（第 6 節、`MAINTENANCE.md` 第 9 節）。
- **時間戳排查順序改為 plist 優先**（原為 `pmset -g custom` → `pmset -g sched` → plist）。plist 最便宜也最確定，且「整點加一秒」的特徵直接指向設定值。同時加上一條通則：**先查到的那一項若已經被人改過，很容易把「修改後的狀態」誤讀成「修改前的證據」**，所以三項都要看完。
- **補上排程 SKILL.md 給 iTunes 子代理的指示裡缺的「US 商店快取」規則。** 子代理讀不到本檔，而該規則只寫在本檔第 1 節，實測會導致退援路徑漏抓 All-In（US 商店回報最新只到 7/18，GB 商店為 7/31）。同時把「怎麼換國別商店」寫成具體網址格式，不再只說「改用 GB／AU」。
- **SKILL.md 補上指向第 7 節「合規與語氣」的入口**。第三次重整時漏了，導致來源標註、付費來源只做重點濃縮、非投資建議這些會影響交付內容的規則沒有任何入口。
- **修掉四處內部矛盾**：窗口接縫敘述與 `last_run_utc` 自癒機制對撞（已釐清為「只有走 iTunes 退援路徑時 26 小時才是硬邊界」）、檔名慣例的舉例仍停留在 09:00 時代、Unhedged 同時被放在退援第 1 層與第 3 層（已說明 FT 流程就是它取得官方稿的方式）、Masters in Business 在 A 類表格說「新集數改走 B」但 B 類清單裡沒有它。
- **釐清 `limit=8` 與「limit 越小快取越舊」的拉扯**：`limit=8` 是起手式，發現回傳過舊就換國別商店重查。
- **SKILL.md 的主動回報清單由七項增為八項**，補上「寫不進 repo `data/`」——該情境的處置本來就寫在本檔第 5 節，但沒進封閉列舉的回報清單，等於會安靜地不被講出來。
- **補上時刻漂移守衛的死角**：守衛原本掛在「今天的日誌」上，但若 podfetch 的時刻漂到 03:00 之後，日報執行當下今天的日誌必然不存在，會直接落進「podfetch 失效」分支，守衛永遠不會觸發。已在三段排查加入第 3 格：今天的日誌不存在時，**先讀 `logs/` 裡最新那一份的開頭時間戳**來區分「時刻漂移」與「真失效」，兩者的修法完全不同。

### 2026-08-03（第四次，節目異動）

- **移除 Capital Allocators，加入 Business Breakdowns（1559120677）、In Good Company（1614211565）、The Compound and Friends（1456467014）。節目數 20 → 22。** Capital Allocators 本身完全正常（812 集，當天還發了新集），移除是取捨不是汰換：它談的是機構配置者與 LP-GP 關係，在這份清單裡最不直接可用。
- **補上的是一個真正的缺口：個股／公司基本面拆解。** 原本 20 檔裡沒有任何一檔在做這件事——ILTB 是投資人訪談，不是公司拆解。Business Breakdowns 每集拆一家公司的商業模式、單位經濟、護城河、估值與風險，來賓多是實際持有部位的 buy-side。
- 三檔都已加進 `shows.json`、`config.json` 的 `show_priority`，`index.html` 也補了三組 CSS（現為 12 組）。
- **驗證候選時踩到 brief 早就警告過的坑，值得記一筆**：Business Breakdowns 的節目層 `releaseDate` 顯示 2026-05-29，看起來停更兩個月；拉集數層才發現最新是 07-27。**節目層那個日期就是第 1 節說的「舊資料，不要誤判」**，差點因此把一檔活著的節目判死。挑選節目時一律要看 `entity=podcastEpisode` 的結果。
- **另外發現 iTunes 的 `search` 端點透過 `web_fetch` 回空字串，`lookup` 正常。** 找新節目的 AppleID 不能靠 `search`，要用 WebSearch 或直接從 Apple Podcasts 網址取 id。已補進第 1 節的已知陷阱。

### 2026-08-03（第三次，結構重整）

- **本檔與 `MAINTENANCE.md` 重新分工**：brief 只留規格與判斷規則，事故經過／誤判過程／被否決的選項全部搬到 `MAINTENANCE.md` 第 7 節「事故與決策檔案」，YouTube 操作要領搬到第 8 節。**動機是本檔已膨脹到 42 KB 而排程每天要完整讀一次**，其中很大一部分是執行者根本不需要知道的歷史；而且同一件事在兩處各寫一份，反而讓「哪個是現行規格」變得不清楚。
- **排程 SKILL.md 改為流程骨架**：只留執行順序與分支判斷，事實細節指向本檔章節，不再重抄。**這是為了根除「漏抄型」同步 bug**——08-03 第二次巡檢抓到的四處缺漏全部屬於這一類，只要兩份文件都在描述同一批事實，這種 bug 就會無限重演。保留了「讀不到 brief 時仍能自我修復連線」的最小集合，不會因為瘦身而失去韌性。
- **新增 `~/.podfetch/healthcheck.py`**：把每次維護都要手動重跑的機械式檢查集中成一支唯讀腳本（JSON 可解析與排序、`days` 與檔案雙向對應、`episodeCount` 相符、showKey 三處 CSS 與 `shows.json` 對齊、podfetch 日誌時間戳與收束狀態、逐字稿降級統計、推送鏈、**brief 引用的 `config.json` 數值是否與實際一致**）。最後一項專門抓 08-03 那類「下文改了、上文漏改」的內部矛盾。
- **開啟排程的 `notifyOnCompletion`**：0 集日不動 `index.json`、不產 Word 報告，網站毫無變化，先前完全無法區分「今天沒東西」與「排程根本沒跑」。這是這套系統反覆中招的靜默失效模式，補上通知作為最低限度的心跳。
- **修正去重的措辭**：原寫「前一天的 json」，但 0 集日不產檔，昨天的檔案可能不存在。改為「`data/` 裡日期最大的那一份」。
- **重構後的回歸檢查抓到九處問題，一併修掉**（子代理獨立比對）：
  - **給 iTunes 子代理的指示缺了完成任務所需的定義。** SKILL.md 把「窗口判定」外包給子代理，但子代理讀不到 brief，而 26 小時窗口、`releaseDate` 是 UTC、台北 ＝ UTC+8、Bloomberg 要用 `limit=20` 全都只寫在 brief 裡。**瘦身的代價就在這裡：指向章節對主代理有效，對子代理無效**，凡是外包出去的步驟，定義必須隨指示一起傳。
  - 「窗口邊緣又拿不到全文的集數不收錄」原本沒進 SKILL.md 的主動回報清單（那是封閉列舉的六項），被排除的集數不會出現在 manifest 狀態裡，等於靜默掉一集。已補為第 4 項。
  - **本檔與 `MAINTENANCE.md` 對「日誌時間戳不對」的第一步互相牴觸**：brief 寫「不要建議去改 plist」，MAINTENANCE 寫「兩種成因都要驗、先驗 plist」。前者把一次性的查證結果固化成永久前提，是錯的——已改為三項依序全查（順序於第四次修訂再調整為 plist 優先）。
  - **`pmset -c sleep 0` 這個主要保障原本完全不在 brief**，只有後備的 `repeat wakeorpoweron`。實際需要的是 01:00 到中午的連續清醒，只靠排定喚醒會在閒置後睡回去、03:00 接不到。同時刪掉「唯一一個不在設定檔裡的依賴」這句——蓋子、登入項目、充電管理軟體等前提同樣不在設定檔裡。
  - `~/.podfetch/cache/` 補進元件表（額度中斷時的續跑機制，排錯時看不到會困惑）。
  - `config.json` 的 `show_priority` 與 `model_preference` 補進說明，並註明 `healthcheck.py` 只檢查數值型、這兩個清單型的檢查不到。
  - `MAINTENANCE.md` 第 7 節一處章節引用指錯（「第 5 節」實指 brief 第 5 節），以及 07:30／07:35 的不一致（cron 設 07:30，帶 jitter 實際約 07:35）。
  - **`README.md` 整份過期且是 Public repo 的門面**：仍寫「每個平日早上 08:30」「其餘節目讀 YouTube 官方頻道字幕」，檔案結構也沒有 `MAINTENANCE.md`。已改寫為現行實況。brief 第 4 節的目錄結構圖原本也沒列 `README.md`，一併補上——**兩份文件的檔案清單互不涵蓋對方，是這次才發現的盲點**。

### 2026-08-03（第二次，維護巡檢）

- **修正 podfetch 與日報的時序倒置**：podfetch 實際跑在 07:00 而非 01:00，日報 cron 改 03:00 後會每天搶先執行、誤判成「podfetch 失效」而掉進已死的 YouTube 退援。修法是把 plist 的 `StartCalendarInterval` 從 `Hour = 7` 改為 `Hour = 1`。
- **第 2 節加入「時刻漂移」守衛**：排查時要順手確認日誌開頭時間戳是 `[01:`，不是就在當日回報中明講。
- **`pmset` 電源設定登記為基礎設施依賴**（第 6 節）。它與 plist 時刻是兩件獨立的事：plist 決定「幾點跑」，`pmset` 決定「那個時刻機器醒不醒著」，兩者都要對。
- **補齊 `index.html` 四組節目徽章**（`latentspace`／`lex`／`mib`／`twentyvc`），這四個 showKey 早已出現在資料裡卻一直走預設藍。同時要求 showKey 一律沿用 `shows.json` 的鍵值。
- **統一 YouTube 嘗試上限為 5 分鐘**（當時的 YouTube 操作章節寫 8 分鐘，與其他三處牴觸；該章節已於第三次重整搬到 `MAINTENANCE.md` 第 8 節）。
- **修掉本檔內部自打架的過期數值**：20 分鐘段／Files API（原寫 25 分鐘／base64）、`max_chunk_mb: 48`（原寫 9 MiB）、每日請求數（該數值已不列在本檔，改由 `config.json` 註解與 `MAINTENANCE.md` 第 7 節記載）、「每天（含週末）」（原寫「每個平日」）、26 小時（原殘留「26／74 小時」）。
- **補上排程 SKILL.md 缺的四條規則**：A 類節目仍須抓官方稿（原本的「不要開 Chrome」會讓官方稿永遠拿不到）、podfetch 主路徑同樣要去重、寫不進 repo 時的退援、YouTube 登入前提。

### 2026-08-03（第一次）

- **執行時段從 09:00 改到 03:00**，確立「前一晚美東晚間集數順延一版」的取捨。
- **資料夾連線不保證跨工作階段留存**：排程執行中讀不到就用 `request_cowork_directory` 自我修復。
- **確立「當天沒有目錄 ≠ podfetch 掛了」的三段排查。**
- **iTunes lookup 已知陷阱**（US 商店快取、RSS 回 `[binary data]`）。
- **驗證上線必須帶 cache-buster**，且要確認 `updatedLabel`。

### 2026-08-02

- **改以本機 podfetch 管線為主要全文來源**（第 2 節）：01:00 抓音檔經 Gemini API 轉錄，產出帶講者姓名的逐字稿。跨節目交叉觀察因此可以具體到人。
- **YouTube 字幕全面失效**，降為最後手段。
