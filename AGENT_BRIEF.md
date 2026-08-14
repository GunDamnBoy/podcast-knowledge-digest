# AGENT BRIEF — 節目知識庫・每日發布標準說明

這份文件是「節目知識庫（Podcast Knowledge Digest）」的完整規格。任何一個新的 Cowork 對話讀了這份，就能完整重現整套系統。全程使用繁體中文（台灣用語），讀者為專業財經工作者。

網站：<https://gundamnboy.github.io/podcast-knowledge-digest/>

> **本檔只寫「現在的規格與判斷規則」。** 事故經過、當初為什麼這樣決定、被否決的選項，一律寫在 `MAINTENANCE.md` 第 7 節「事故與決策檔案」。本檔會以「見 `MAINTENANCE.md` 第 7 節」指過去。這樣分是因為排程每天要完整讀本檔一次，而執行者不需要知道歷史。

---

## 0. 這個系統在做什麼

每天早上（含週末）自動偵測 23 檔 Podcast 的新集數，取得**全文**，為每一集撰寫繁體中文完整摘譯（**字數依節目長度分層，見第 3 節**）＋3–5 個核心重點，同時交付兩種形式：

1. **Word 報告**（.docx）— **由 `~/.podfetch/json2docx.py` 從當日 JSON 機械轉出**（內容以 JSON 為唯一來源，不由 LLM 重寫一遍），交付到對話中供轉發與引用（Cowork 用 `present_files`）。**不要存進 repo 目錄**，該 repo 是 Public。
2. **網站**（本 repo）— 每天新增一個 `data/YYYY-MM-DD.json`，供隨時閱讀與全文搜尋。

**時序（兩者都不會喚醒睡著的 Mac；電源設定見 `MAINTENANCE.md` 第 9 節）**：

| 時刻（台北） | 元件 | 作用 |
|---|---|---|
| 00:55 | `pmset repeat` 排定喚醒 | 把機器叫醒，讓底下兩個排程跑得到 |
| 01:00 | launchd `com.kenny.podfetch` | 抓音檔、Gemini 轉錄、寫出逐字稿 |
| 03:00 | Cowork 排程 `podcast-digest-daily`（cron `0 3 * * *`） | 讀逐字稿、寫摘譯、發布 |

**03:00 這個時段有一個必須知道的結構性取捨**：台北 03:00 ＝ 美東前一天 15:00，而主要節目集中在台北 04:00–06:30 落地（All-In 約 06:23）。所以**前一晚的美東晚間集數在今天這一版必定收不到，會出現在明天凌晨那一版**——All-In 約在發布後 21 小時進日報。**這是設計，不是故障，不要去追，也不必每天在回報中解釋。** 沒有任何集數會遺失：podfetch 視窗以 `last_run_utc` 為起點、日報又會去重，順延的集數下一版必定收得到。動機與完整代價見 `MAINTENANCE.md` 第 7 節。

**排程機制備忘**：Cowork 的 cron 以**本機時區**計算，直接寫 03:00，不要換算 UTC。每次執行都是全新工作階段、讀不到任何過往對話，因此任務 prompt 必須自包含（現行做法：要求執行者先完整讀過本檔）。**排程只在 Claude 桌面 App 開著時執行**，App 關閉時錯過的會在下次啟動補跑。

---

## 1. 節目清單與全文來源（23 檔）

**A. 官方逐字稿——永遠優於機器轉錄，這類節目每天都要去抓**（**唯一例外：片長超過 120 分鐘的集數直接用 podfetch 稿，見第 2 節退援順序第 1 層**）

| 節目 | 取得方式 |
|---|---|
| Acquired | RSS `https://feeds.transistor.fm/acquired` 內 `<podcast:transcript>` → `share.transistor.fm/s/<id>/transcript.txt` |
| Lex Fridman | 索引 `lexfridman.com/podcast/` → `lexfridman.com/<slug>-transcript` |
| Dwarkesh Podcast | `https://www.dwarkesh.com/api/v1/archive?sort=new&limit=10` → `dwarkesh.com/p/<slug>` |
| Latent Space | `https://www.latent.space/api/v1/archive?sort=new&limit=10` → `latent.space/p/<slug>` |
| Macro Voices | `https://www.macrovoices.com/guest-content/list-guest-transcripts`（PDF 可直接 WebFetch）。**官方稿通常落後一週以上**，當集多半還沒上架（08-07 實例：當天最新只到 MV543／7-30）。**這時退回 podfetch 是正常的，不是失效**，照常在 `source` 標明來源即可 |
| Exchanges at Goldman Sachs | `goldmansachs.com/insights/goldman-sachs-exchanges/<slug>`（逐字稿內嵌全文）。**slug 不是節目標題的直譯**——用標題硬拼會回空頁而不是 404，看起來像「沒有官方稿」。從 GS 的 Exchanges 節目列表頁取實際連結，或用 WebSearch 找。08-07 實例：標題是 AI 債務與信用市場，slug 卻是 `how-ai-debt-is-reshaping-the-credit-market` |
| Unhedged (FT) | **入口是 `https://www.ft.com/the-economics-show`**（2026-08-08 更正）。**不要用 `ft.com/unhedged`**——那頁是 Unhedged 電子報存檔，**完全不含 podcast 集數**，過去寫錯了。只能走 Chrome：`find` 取得目標日期文章的 `href` → `navigate` → `get_page_text`。<br>**Unhedged 的 feed 會放姊妹節目 The Economics Show 的重播**（08-08 實例：8/6 的 feed 放的是原 6/19 那集）。遇到重播要在 `published` 與 `source` 標明原始播出日，不要當成新集數 |
| Masters in Business | `ritholtz.com/<YYYY>/<MM>/transcript-<guest-slug>/`（晚 1–2 週；新集數改走 B） |

**取官方逐字稿的兩個陷阱（2026-08-05 實測，都會安靜失敗）**

- **Substack 的 `/api/v1/archive` 會回過期快取。** Dwarkesh 與 Latent Space 首次取回的最新一筆分別停在 6/08 與 7/08，**加了 cache-buster 參數才拿到當天集數**。失效的樣子是「這檔今天沒有新集數」，於是安靜退回機器轉錄，官方稿白白不用。**這兩檔的 archive API 一律要帶 `&cb=<時間戳>`。** 與 iTunes 的 US 商店快取是同一類問題。
- **`web_fetch` 有約 104,700 字元的上限。** 長逐字稿會被截斷且不報錯——Latent Space 那集只取到 01:13:58／01:41:28（約 73%）。**取完要比對逐字稿末尾的時間戳與 `trackTimeMillis`**；不足就用 podfetch 的版本補齊末段，並在 `source` 據實標註兩個來源各涵蓋哪一段。

**B. 音檔轉錄（podfetch ＋ Gemini API，見第 2 節）** — 沒有官方逐字稿的節目一律走這條。iTunes Lookup 回傳的 `episodeUrl` 就是直接的 MP3 網址，**不需要 YouTube**。

All-In／BG2／Pivot／Hard Fork／20VC／No Priors／Lenny's／Invest Like the Best／**Business Breakdowns**／**In Good Company**／**The Compound and Friends**／Odd Lots／Bloomberg Surveillance／The Market Huddle／**Masters in Business（新集數）**／**We Study Billionaires（TIP）**

> **Business Breakdowns**（Colossus 出品，與 ILTB 同門）每集拆解一家公司的商業模式、單位經濟、護城河、估值框架與風險，來賓多是實際持有該檔股票的 buy-side。**Colossus 在 `joincolossus.com` 的集數頁有官方逐字稿**，若哪天要把它升到 A 類可從那裡取，目前先走 podfetch。
>
> **In Good Company** 是挪威主權基金 CEO Nicolai Tangen 訪談各大企業 CEO，約 25 分鐘，節奏比其他節目快很多。
>
> **The Compound and Friends** 是美股市場週評，與 Bloomberg／Market Huddle／Unhedged 題材有重疊，摘譯時注意不要在交叉觀察裡重複同一件事。

> **We Study Billionaires（TIP，2026-08-10 加入）** 是 The Investor's Podcast Network 的旗艦，**一週兩檔、其中一檔固定在週日**，這正是加它的原因——週一那一版涵蓋美東週六中午到週日中午，現有節目在這個窗口幾乎沒有供給（08-10 只有 2 集，而且是同一支預告）。
> **兩檔的性質不同**：週日是 William Green 的 **RWH（Richer, Wiser, Happier）**系列，訪談知名投資人與經理人，約 2 小時，偏投資哲學與決策品質；週四是 TIP 本編的個股內在價值拆解（Exor、Intuit、DLocal 這類），約 80 分鐘，與 Business Breakdowns 題材接近，**交叉觀察時注意不要重複同一件事**。
> **語速尚未校準**：新加入時沿用全域 200 字/分，累積幾集後量測實際語速再決定要不要在 `shows.json` 補 `wpm`（同類的 ILTB 實測是 122，所以完整度一開始可能偏低，那是基準問題不是缺字）。
>
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

All-In 1502871393｜BG2 1727278168｜Pivot 1073226719｜Hard Fork 1528594034｜Unhedged 1691284824｜Acquired 1050462261｜20VC 958230465｜Invest Like the Best 1154105909｜**Business Breakdowns 1559120677**｜**In Good Company 1614211565**｜**The Compound and Friends 1456467014**｜Masters in Business 730188152｜No Priors 1668002688｜Lenny's 1627920305｜Lex Fridman 1434243584｜Dwarkesh 1516093381｜Latent Space 1674008350｜Odd Lots 1056200096｜Macro Voices 1079172742｜Market Huddle 1444520320｜Bloomberg Surveillance 296237493｜GS Exchanges 948913991｜**We Study Billionaires（TIP）928933489**

**權威來源是 `~/.podfetch/shows.json`**（含 AppleID、節目名、主持人名單，Bloomberg 的 `limit: 20` 也在那裡）。上面這份清單是給人看的，兩邊不一致時以 `shows.json` 為準。

### 時間窗口與去重

**每天**（含週末）抓新發布的集數。**視窗以 `last_run_utc` 為準**（見第 2 節「四個不要改的設計」第 1 項），往前重疊 30 分鐘、上限 72 小時；**正常情況下大約是 24–26 小時，但那是結果不是設定**。重疊的代價是**相鄰兩天會重複命中同一集**。

**所以產檔前必須去重，而且是兩種去重：**

**① 跨日去重**：讀 `data/` 裡**日期最大的那一份** `YYYY-MM-DD.json`（注意不一定是昨天——0 集日不產檔），比對 `url` 與 `title`，已收錄過的一律略過。**podfetch 主路徑與 iTunes 退援路徑都要做這件事。**

**② 同日同源去重（2026-08-10 新增）**：同一支音檔會被**同一天內的不同節目**推送。比對**當天 manifest 的原文 `title` 與 `durationMs`**——兩者都相同就是同一支，**只留一集**：

- 保留 `config.json` 的 `show_priority` 排比較前面的那一個節目，完整摘譯。
- 被略過的那一集**不另外寫一集**，改在保留那集的 `meta` 加一欄 `{"k":"同源推送","v":"同日亦推送於 {另一個節目名}"}`。
- `episodeCount`、`index.json` 的 `shows`、**以及交叉觀察的「當日 ≥3 集」門檻（第 3 節）**，一律按**去重後**的集數計算。
- 在回報中列出被合併的集數。

> **為什麼要比 manifest 的原文欄位，而不是日檔的 `title`**：日檔標題是各集子代理各自擬的中譯，同一支音檔會生出兩個不同標題；`url` 也因為 feed 不同而不同。**08-10 那次，唯一能認出同源的兩個欄位（原文 `title` 都是 `"Introducing: Our Town"`、`durationMs` 都是 `113000`）剛好都不在比對範圍內**，於是同一支 113 秒預告佔滿了當天兩集。
>
> **這條規則的失敗方向要選對**：漏判（兩集都留）只是重複，誤判（把不同集數當成同源刪掉）會弄丟內容。所以**必須兩個欄位同時相同**才算，不要只比標題、也不要做模糊比對。

> **但「⚠︎ 待補」的佔位不算已收錄（2026-08-04 事故）。** 前一份裡某集的 `source` 若以 `⚠︎` 開頭（代表當時沒拿到全文，只寫了 500 字精簡摘要或空殼），而**這次拿得到完整逐字稿**，就要**重寫那一集**，不要當成重複而略過。
>
> 這個情境一定會發生，因為它是設計的一部分：podfetch 某集失敗時不會推進 `last_run_utc`，下次執行必定重抓同一集。若去重時一視同仁，補回來的完整逐字稿會被自己的去重規則擋掉，那集就永遠停在佔位狀態——**而且完全沒有徵兆**。
>
> 重寫時把該集**從舊檔移除、寫進今天的檔案**（連同 `episodeCount` 與 `shows` 一併更新），並在回報中說明「某集補上了前一版缺的全文」。

**允許「當日 0 集」**（週末常見）。此時**不要產生空檔案、不要動 `index.json`、不要產 Word 報告**，直接回報後結束。

**時區換算**：台北 ＝ UTC+8，「台北 7/31 全天」＝ `releaseDate` 落在 `2026-07-30T16:00:00Z` 至 `2026-07-31T15:59:59Z`。務必先換算再篩選，美東晚間發布的集數在台北會落到隔天，很容易算錯一天。

**檔名慣例**：`data/YYYY-MM-DD.json` 的日期是**執行當天**（台北），內容是該時點往前、`last_run_utc` 之後發布的集數（正常約 26 小時，實際值看 manifest 的 `windowStartUtc`／`windowEndUtc`）。以 03:00 執行為例，`2026-08-04.json` 涵蓋的是**台北 8/3 01:00 至 8/4 03:00** 發布的集數——注意它**不含** 8/4 凌晨 03:00 之後的內容（那批是隔天那一版的）。補跑歷史某天時沿用同一慣例。

**注意窗口接縫**：**iTunes 退援路徑**的 26 小時窗口以每天固定同一時刻執行為前提，某天沒跑或延後跑就會在兩次窗口之間留下空隙（主路徑沒有這個問題，它以 `last_run_utc` 為準）。**但這個空隙通常不會真的掉集數**，因為真正決定「有哪幾集」的是 podfetch，而 podfetch 的視窗以 `last_run_utc` 為起點（上限 72 小時）、下次執行會自動往回補（見第 2 節）。

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
| 健康檢查 | `~/.podfetch/healthcheck.py`（對受檢系統唯讀；唯一會寫的是自己的 `metrics.csv`。見 `MAINTENANCE.md` 第 3 節） |
| 排程 | launchd `com.kenny.podfetch`，每天 **01:00** |

**流程**：iTunes 偵測 → 下載 MP3 → 切成 20 分鐘段 → 每段經 Files API 上傳後送 Gemini `generateContent` → 合併 → 字數檢查 → 寫出 `.md` 與 `manifest.json`。循序處理，六集約 30–45 分鐘。

**逐字稿格式**：YAML front matter（`show`／`showKey`／`title`／`released_utc`／`duration_ms`／`apple_url`／`source`／`segments`／`words`／`expected_words`／`words_per_minute`／`completeness`／`status`／`warnings`／`speaker_notes`／`timestamp_notes`），正文為 `[MM:SS] 講者姓名：內容`（超過一小時的部分是 `[H:MM:SS]`）。

> **`warnings`、`speaker_notes`、`timestamp_notes` 是三個不同維度，不要混為一談。**
>
> - `warnings` 決定 `status`：完整度、語速異常這類「內容可能缺漏」的問題。
> - **`speaker_notes` 不影響 `status`**：講者標記的可疑訊號。該集內容可能完全完整，只是發言歸屬不可靠。
> - **`timestamp_notes` 也不影響 `status`（2026-08-14 新增）**：時間軸的可疑訊號。內容可能完整、講者也對，只是**時間戳不可信**。
>
> 摘譯時**三個都要讀**。`speaker_notes` 有東西＝金句歸屬與「誰主張什麼」要靠上下文覆核；**`timestamp_notes` 有東西＝不要依時間戳切章節，改用主題轉換判定**。
>
> **前兩者曾經共用同一個欄位，導致完整度正常的集數被誤標為 `DEGRADED`（2026-08-07），已拆開；`timestamp_notes` 從一開始就獨立，理由相同。**

**講者姓名是這條管線最大的增值**。`shows.json` 預先寫入每檔節目的主持人名單，轉錄 prompt 要求 Gemini 用真名而非 `Speaker A`。跨節目交叉觀察因此能具體到人（「Chamath 主張 X，而 Kevin Muir 在同一議題上主張 Y」）。

### 四個不要改的設計

1. **視窗以 `last_run_utc` 為準，不是固定 26 小時。** 從上次成功執行時間往前推 30 分鐘重疊開始抓，上限 72 小時。**不要改回固定窗口**——舊版在漏跑一天時會產生無法察覺的缺口。
2. **字數檢查是防「安靜失效」的唯一機制。** Gemini 是 LLM 不是機械式辨識器，長音檔上可能改寫、壓縮或跳過整段而不報錯。腳本以該節目的語速基準估算期望值，低於 55% 就重試該段；仍不足則標 `DEGRADED` 並寫進 front matter 與 manifest。**不要拿掉。**

> **語速基準是 per-show 的**（2026-08-09 校準）：全域預設 `WORDS_PER_MIN = 200`，個別節目可在 `shows.json` 用 `"wpm"` 覆寫（目前 7 檔有覆寫，如 In Good Company 160、ILTB 140、Odd Lots 185）。
>
> **原本全域 165 太低，後果是幾乎每一集的完整度都顯示 1.2–1.3**——「超標」變成常態，這個數字因此不再有可讀性。**指標要讓「正常 ≈ 1.0」，偏離才有意義。** 校準後 15 檔節目全部落在 0.87–1.09。
>
> **但要分清楚它影響什麼（2026-08-09 訂正一個曾寫錯的因果）：** `wpm` 只決定 ① 完整度分母（使用者看到的那個倍數）、② 段級重試門檻（**上修 wpm 會讓門檻變嚴、更容易重試**）、③ `median_rate` 的後備值。**它不決定 `DEGRADED`。** status 只看 `warnings`，而 warnings 只有三個來源：字數低於 `MIN_RATIO`、段級語速偏離**本集中位數**（`REL_RATIO`／`HIGH_RATIO`，不看 wpm）、跳針剔除。**完整度 1.4 這種「超標」不會產生任何 warning。** 08-09 那兩集的 `DEGRADED` 來自段級相對檢查，與 wpm 無關。
>
> 新增節目時若語速明顯偏離 200，累積幾集後在 `shows.json` 補 `wpm`。

> **計字前會先剔除跳針**（`collapse_loops()`：連續重複 20 次以上的同一 token 壓成一次），剔除量單獨記在 `warnings` 裡並標明集中在第幾段。**沒有這一步，完整度指標在「跳針」這個失效態下會完全反向**——2026-08-08 實例：一行 28,122 個重複的「I」讓完整度顯示成 3.36，實際只有 1.10。看到這則警告時，**跳針處的內容是缺的，不要當成有內容**。

> 這個常數在程式碼裡、不在 `config.json`，所以 `healthcheck.py` 的「brief vs config」檢查**涵蓋不到它**——改動時要自己回頭改本節。沿革：130（初版）→ 165（08-06）→ 200（08-09）。
3. **Lite 是主力，Flash 是備援（2026-08-05 反轉）。** 池子仍是 3 Lite ＋ 3 Flash，但**順序改成 Lite 在前**（`config.json` 的 `prefer_lite: true`）。

   | 模型 | RPD |
   |---|---|
   | Flash 3.5／3.6 | **10–20，會浮動** |
   | Flash 2.5 | 20 |
   | Flash-Lite 2.5 | 20 |
   | **Flash-Lite 3.1／3.5** | **500** |

   > **Flash 的 RPD 上限不是常數**：08-05 從 20 掉到 10，08-07 又顯示回 20。**不要把它當固定值來做設計判斷**——Lite 優先的理由是「500 遠大於 10–20」這個量級差，不是某個特定數字。

   新版 Flash 只剩 10 RPD，而重試會讓實際請求放大約 2.5 倍（08-05 實測：預估 17 個請求，實際打出 42 次，Flash 兩個模型雙雙超限而 Lite 只用 8 次）。**把最稀缺的資源排在最前面，等於每天開場就燒光它。** 實測 Lite 的完整度 1.14–1.16，與 Flash 沒有可辨識的品質差距。要改回品質優先就把 `prefer_lite` 設為 `false`。
4. **500／503 換模型，但只冷卻、不除名。** 過載是「這個模型現在忙」，不是額度問題。同一模型重試兩次仍 503 就丟 `ModelOverloaded`，該模型進 `OVERLOADED` 冷卻 `overload_cooldown_seconds` 秒（現為 300）後**自動回池**；`EXHAUSTED` 只放日額度用盡與 404 這類**永久性**失效。

   **這兩件事必須用不同的資料結構，共用一個集合就等於把語意也合併了。** 2026-08-04 把 503 也丟進 `EXHAUSTED`，結果 08-06 一次過載尖峰在 77 秒內把三個 500 RPD 的 Lite 全部永久除名，剩 10 RPD 的 Flash 扛完整場、燒到 22/10。**暫時性錯誤不可以產生永久性後果。**

   **輪換同時受次數與時間約束**：過載輪換上限 `max(4, len(pool) * 3)`，單集牆鐘上限 `episode_budget_seconds`（現為 3600 秒；**2026-08-10 修正語意**——舊版名為單集上限、實為每段每次重試各領一份 1200 秒且只在過載分支檢查，等於無上界；現在整集只設一次、每段開始前檢查）。另有**整場執行上限 `run_budget_seconds`（現為 6000 秒＝100 分鐘）**：01:00 起跑、02:40 後不再開始新的集數，未處理的標 FAILED——03:00 日報要讀 manifest，寧可缺集也不能讓日報讀到不完整的檔案。**光有次數上限不夠**——每次輪換都可能等一輪 300 秒冷卻，18 次就超過一小時。

   撞到任一上限就丟 `RuntimeError`，該例外會穿出分段迴圈，**使該集標為 `FAILED`**（不只是那一段）。這是可接受的：已完成的段落留在 `~/.podfetch/cache/`，該集不寫進 `seen`、`last_run_utc` 不推進，下次執行接續。日額度輪換不計入過載上限，兩者語意不同、用不同的計數器。經過見 `MAINTENANCE.md` 第 7 節。

**`config.json` 現行值**：`segment_seconds: 1200`、`max_chunk_mb: 48`、`min_request_interval_seconds: 10`、`avoid_preview_models: true`、`flash_slots: 3`／`lite_slots: 3`、`max_output_tokens: 32768`、`default_window_hours: 48`、`max_lookback_hours: 72`。

另有 `overload_cooldown_seconds: 300`（500／503 的冷卻秒數，見上）、`episode_budget_seconds: 3600`（單集牆鐘上限）、`run_budget_seconds: 6000`（整場執行上限）與 `prefer_lite: true`（模型池是否 Lite 優先）。**後者是布林值，`healthcheck.py` 的數值比對抓不到它**，改動時要自己確認 `config.json` 與本節一致。

另有兩個**清單型**設定，內容不列在這裡（會過期），直接看檔案：

- `show_priority` — **有序陣列，有兩個用途**：①額度不足時的處理順序，All-In 最前，犧牲的是排在後面的邊際節目；②**同日同源去重時決定保留哪一集**（第 1 節）。**新增節目時要記得插進去。**
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
3. **今天的日誌根本不存在** → **先不要判定失效，這一格有陷阱**。日報跑在 03:00，若 podfetch 的執行時刻漂到 03:00 之後（例如 plist 被改成別的小時、或機器睡到天亮才補跑），當下「今天還沒有日誌」是必然的，看起來和真失效一模一樣。**此時去讀 `logs/` 裡最新那一份，看「視窗：」那些行的時間戳**（每次執行都會印一行「視窗：」，log 是按日期附加的，**不要只看第一行**——手動跑過一次就會把排程執行擠出檔案開頭，2026-08-10 修正）：若沒有任何一次落在 `01:0x`，就是時刻漂移而非失效，按下面的守衛處理並在回報中明講；若最新日誌是昨天且有正常的 `01:0x` 執行，那才比較像今天真的沒跑起來。兩種情況都要走 iTunes 退援把當天內容補齊，但**回報時要講對是哪一種**——講錯會讓使用者往錯的方向修。

### 時刻漂移守衛

**podfetch 日誌裡當天「視窗：」行的時間戳正常應為 `[01:00:0x]`（看全部執行、不要只看檔案第一行）。都不是的話，代表 podfetch 的實際執行時刻已經漂掉，日報有可能搶在它前面執行**——這種失效是安靜的：podfetch 本身完全正常，只有日報品質悄悄掉一級。

**成因有兩類，症狀完全相同**：(a) plist 的時刻值不對；(b) 機器睡著、launchd 醒來後才補跑。要在當日回報中明講，並依這個順序提示使用者排查（**三項都要看完**）：

1. `/usr/libexec/PlistBuddy -c "Print :StartCalendarInterval" ~/Library/LaunchAgents/com.kenny.podfetch.plist` — 應為 `Hour = 1, Minute = 0`。**先查這一項**：它最便宜、最確定，而且時間戳若剛好落在某個整點又只差一兩秒（例如 `[07:00:01]`），那正是 `StartCalendarInterval` 準時觸發的特徵，指向設定值而非喚醒失敗
2. `pmset -g custom` — AC Power 段的 `sleep` 應為 `0`（**這是主要保障**，插電時永不睡眠）
3. `pmset -g sched` — 應有 `wakepoweron at 0:55AM every day`（後備）

**三項都要看，不要查到一項就收手。** 兩類成因（設定值錯、機器睡著）會產生一模一樣的症狀，而且**先查到的那一項若已經被人改過，很容易把「修改後的狀態」誤讀成「修改前的證據」**。若 plist 正確而時間戳仍偏晚，才往喚醒方向查；環境設定全貌見 `MAINTENANCE.md` 第 9 節。

漏跑一天不會造成缺口：podfetch 視窗以 `last_run_utc` 為起點（上限 72 小時），下次執行會自動補回。

### 退援順序

**只有四層。**（2026-08-10 訂正：FT 曾被列成獨立的第 3 層，但那與同一段的說明自相矛盾，也與排程 SKILL.md 的層號對不上——**FT 流程取得的就是 Unhedged 的官方逐字稿，屬第 1 層**。）

1. **官方逐字稿**（第 1 節 A 類）— 永遠優先。**manifest 決定「有哪幾集」，不決定「用哪份全文」**：A 類節目即使 podfetch 已轉錄，仍要去抓官方稿，抓不到才退回 podfetch 版本，並據實填 `source`。

   > **超長節目的例外：片長超過 120 分鐘的 A 類節目直接用 podfetch 稿，不要抓官方稿（2026-08-11 新增）。** `web_fetch` 有約 104,700 字元的單次上限且**會靜默截斷**，兩小時以上的官方稿必然超出數倍，拼接要反覆抓取與比對接縫——**成本高、失敗模式安靜、而 podfetch 稿本來就已經在手上**。08-11 的 Acquired（273 分鐘、45,237 字、完整度 0.83）就是子代理自主做了這個判斷，判斷是對的，只是規格裡當時沒有這條路。**在 `source` 據實標明「因片長超過 120 分鐘未取官方稿」即可，不必在回報中另外解釋。**

   > **第 1 層的特例：FT 專用流程（Unhedged）。** 它不是另一層，只是取得方式特殊、且有專屬的失效檢查。
   >
   > **只能走 Chrome**（`find` → `navigate` → `get_page_text`）。**`ft.com` 已於 2026-08-06 進入本環境 `web_fetch` 的封鎖清單（回 HTTP 403 `URL is on blocklist`），那條路已死，不要再試。** **2026-08-08 這條 Chrome 路徑已在無人值守的排程中跑完並成功**（45,181 字元、無付費牆標記），不再是未驗證狀態。仍要注意底下的 syndication cookie 是會安靜過期的依賴（見第 6 節）；**若卡在工具權限就直接退回下一層並在回報中明講，不要空等**。

   > **取到後必須檢查正文長度**，通常 5,000 字元以上；明顯偏短或出現 `Subscribe to unlock`／`Complete digital access` 即視為 FT 存取失效。**此時退回第 2 層（podfetch 逐字稿），不是跳到 YouTube**——Unhedged 是 B 類以外的節目但 podfetch 一樣有轉錄它。podfetch 也沒有才繼續往下，並明確告知使用者 FT 存取已失效。

2. **podfetch 逐字稿** — B 類節目的主要來源。
3. **YouTube 字幕** — 2026-08-02 起已知全面失效，只當最後手段，每集最多試 5 分鐘。須為 Chrome 已登入 YouTube 的狀態，未登入就直接走下一層並告知，不要嘗試代為登入。操作要領見 `MAINTENANCE.md` 第 8 節。
4. **都拿不到** — 依節目說明＋WebSearch 公開報導寫約 500 字精簡摘要，`source` 標註「⚠︎ 全文摘譯待補」及原因，**該集 `quotes` 留空陣列**。若某集本來就在窗口邊緣且拿不到全文，寧可不收錄，並在交付訊息中明講這一集沒被涵蓋。

**絕對不要憑印象編造節目內容，也不要編造引述。沒有逐字稿就不寫金句。**

---

## 3. 內容規格

每一集包含：

- **一句話總結** — 一段，抓住全集最重要的張力，不要流水帳
- **核心重點 3–5 條** — 每條「重點N｜粗體標題」＋2–4 句說明，**必須含對投資人的含義**
- **完整摘譯——依節目長度分層（2026-08-06 改）** — 依章節時間軸分節，忠於原文論點與數字，正反方意見都要呈現。

  | 節目長度 | 目標字數 | ≈ 段數 |
  |---|---|---|
  | 未滿 15 分鐘 | 1,200–1,800 | 6–9 |
  | 15 分鐘以上、未滿 30 分鐘 | 2,000–3,000 | 10–15 |
  | 30 分鐘以上、未滿 55 分鐘 | 2,500–4,000 | 13–20 |
  | 55 分鐘以上，或 10 個以上獨立主題 | 4,000–6,500 | 20–33 |

  > **「字數」的唯一定義（2026-08-12 定死）：`sections[].paragraphs[]` 全部串接後的字元數，含標點、含空白，不含 `summary`／`takeaways`／`quotes`／JSON 結構。** 一個英文單字算它自己的字元數，不是算一個單位。
  >
  > **為什麼要寫死**：08-12 實測 13 個日檔 74 集，子代理自報的 `chars` 與實際字元數**偏差中位數 0%，但範圍是 −38% 到 +81%，42% 的集數偏差 20% 以上**——不是系統性偏差，是**雜訊**。一把無偏但誤差 ±40% 的尺，比一把有偏但穩定的尺更沒用：08-12 的 Dwarkesh 與 Pivot 自以為在區間內、實際超上界 23.8% 與 34.0%，而 In Good Company 自以為超標壓縮了兩輪、實際一直低於下界。**08-11 那條「先估篇幅再落筆」失效的根因就在這裡——尺是浮動的，估不了。**
  >
  > **`chars` 欄位現在由組檔時的 python 機械計算並覆寫**（見第 4 節），子代理不必也不應該自己數。但**寫作當下沒有 python 可用**，所以請用**段數**當代理指標：實測 1,546 個段落的中位數是 **198 字元**（四分位 150–251），上表的「≈ 段數」就是這樣換算的。**下筆前數骨架有幾段，比事後數字元可靠得多。**

  （邊界一律「含下界、不含上界」，例如 30 分鐘整算在第三層。）

  > **先估篇幅再落筆，不要寫完再壓縮（08-11 新增，08-12 改為以段數規劃）。這是成本規則，不只是文風規則。** 動筆前先做兩件事：①依片長查出目標**段數**（上表右欄）；②**在心裡**列出章節骨架並**把段數分配到各節**（**不要寫成檔案**——那會多一次工具呼叫，等於用成本換整齊），總段數落在區間內才開始寫。
  > **08-12 為什麼把規劃單位從字數換成段數**：08-11 只寫「先估篇幅」而沒換單位，隔天重寫比例一模一樣（3/5）——**因為子代理在寫作當下量不準字元數**（誤差 −38% 到 +81%，見上方定義段）。段數它數得準。**加強一條建立在壞量測上的規則，只會讓執行者更用力地做錯事。**
  > **為什麼寫進規格**：08-11 五集有三集初稿超出上界後重寫（Odd Lots 8,257→6,434、Acquired 14,255→6,583、Bloomberg 3,642→2,983），08-12 又有三集（ILTB 11,611→6,485、Compound 5,546→3,987、In Good Company 2,769→1,789），而**每重寫一輪，整份逐字稿就被重新計費一次**。**寫作規格與成本預算在長節目上會互相打架，解法是先規劃、不是事後刪。**
  > 骨架階段就發現內容量遠超上界時，**是砍章節深度或合併次要主題，不是寫完再刪**——刪掉的字已經付過錢了。

  **官方逐字稿的資訊密度高於機器轉錄**（沒有廣告、沒有口頭贅語），同樣片長可能多出三到五成的實質內容。這種情況下超出所屬層級上限一成左右是合理的，在回報中說明即可——**不要為了壓進區間而砍掉整段論點**。

  **原本一律 2,000–3,000 是不切實際的**：57–65 分鐘、10 個以上獨立主題的節目（Compound、Unhedged、ILTB 這類）壓到 3,000 字必然砍掉整段內容，實務上執行者都會選擇保留完整性然後在回報裡說明超規格——**規格天天被違反就不是規格**。

  **上限仍然存在，`不要灌水` 的紀律不變。** 超出所屬層級上限時要在回報中說明理由；短節目硬拉長比長節目超規格更嚴重。

  **下界也有例外，而且優先於下界（2026-08-10 新增）**：**素材本身的字數就撐不起下界時，以素材為準，不要拉長。** 判準是逐字稿的實際字數——**摘譯不應該超過逐字稿本身**。08-10 那兩集的逐字稿只有 301／303 字（113 秒的預告片），下界卻是 1,200 字，硬寫就只能灌水。
  **但這種情況必須在回報中講出來**（哪一集、逐字稿幾字、寫了幾段），否則「寫得太短」與「偷懶」在事後完全分不出來。**原本規格只規定超上限要說明、低於下界完全沒有條款**，08-10 是靠子代理自己寫進 `source` 欄位才留下痕跡——**依賴自覺的紀律不是紀律。**
- **本集金句 2–5 句** — 須為逐字稿中實際出現的發言，中譯＋標明講者姓名

**跨節目交叉觀察**：當日集數 ≥3 時必寫（**集數以第 1 節的兩種去重之後為準**）。呈現「他們一致同意什麼」與「他們在哪裡正面對撞」——同一議題不同節目的收斂與分歧，是這個工具最大的價值來源。有講者姓名時要具體到人。

**觀察後記**：2–3 條可在接下來幾天實際對照驗證的觀察點。

**排序**：All-In 永遠在最前，其後依對總經／AI／資本市場的重要性排序。

**寫作紀律**：機器轉錄存在語音辨識誤差（人名、專有名詞），須依上下文校正，不確定處採保守表述並標註。數字一律不四捨五入、不概括。引述為中譯非逐字引文。

> **講者標記誤植是這套系統目前最主要的品質問題（2026-08-07：九集有五集需要人工校正）。**
>
> 轉錄 prompt 已改為保守標記——有明確依據（自我介紹、被直呼、主持人點名）才寫真名，否則一律 `Speaker N`，廣告與台呼標 `Announcer`。**因此看到 `Speaker N` 是誠實而非失敗**，不要硬去補人名。`podfetch.py` 的 `check_speaker_labels()` 會把**五種**可疑訊號寫進**獨立的 `speaker_notes`／`speakerNotes` 欄位（不是 `warnings`、不影響 `status`）**：裸時間戳（整行沒有講者標記）、標籤格式異常（把台詞或廣告當人名）、全集只有一個講者、泛稱佔比 ≥40% 卻混著真名、單一講者連續獨佔 15 分鐘以上。
>
> **但它抓不到「合理人名張冠李戴」**——08-07 的 All-In 把開頭 13 分鐘的 Jason Calacanis 整段標成 Chamath Palihapitiya，標籤本身完全合理，只是錯的。**這一類只能靠讀內容時的上下文校正**（誰被直呼名字、誰在問問題、開場說了誰不在）。

> **時間軸也會壞，而且壞得比講者更安靜（2026-08-14 新增 `check_timestamps()`）。** 兩種訊號寫進獨立的 `timestamp_notes`／`timestampNotes`：
>
> 1. **時間戳溢出**——最大時間戳超過片長 25% 以上。08-11 的 20VC 最大值跑到 1,192 分鐘（片長 59 分，溢出 1888%）、08-14 的 TIP837 跑到 253 分（片長 78 分，溢出 224%）。**兩集的完整度分別是 0.91 與 0.98、status 都是 OK，三天來沒有任何機制看見它**——講者檢查只抓到副作用（「整段錯置」），時間軸崩壞本身隱形。
> 2. **大間隙＋完整度雙重成立**——無時間戳的時間佔片長 30% 以上**且**完整度低於 0.85。（「無時間戳的時間」＝每個超過 90 秒的間隙**超出 90 秒的那部分**加總，不是整段間隙。）08-14 的 MIB 就是這樣被抓到的（22 分鐘無戳、完整度 0.73，子代理獨立確認確有兩處跳段）。
>
> **第 2 條刻意設成「兩個訊號同時成立」**：長篇獨白（時間戳只在換人時出現）與真的跳段長得一模一樣，只看間隙會對 72 集報 15 集，那就是講者檢查初版「九集報八集」的同一種失敗。收緊後全庫 72 集只報 7 集。
>
> **看到 `timestamp_notes` 就不要依時間戳切章節，改用主題轉換判定。** 08-14 的 TIP837 是子代理自己發現異常才改的——那是規格缺條款，不是它機靈。
>
> 以下是 2026-08-06／07 實際出現過的失敗型態，看到就要提高警覺：**某集完整度 1.01、狀態 OK，但 Gemini 從中段起把主持人標成片頭廣告旁白者的名字。****`shows.json` 的主持人名單只是提示，不保證正確歸屬。**
>
> 因此金句與立場歸屬**不能只信逐字稿的講者標籤**，要用開場自我介紹、代稱人稱、話題連續性交叉驗證——尤其是「開場說明某人今天請假」這類資訊，它會讓整集的預設歸屬失效。**判定不了就寫節目名而不是猜人名。** 跨節目交叉觀察寫「誰主張什麼」時風險最高，因為錯誤歸屬會直接變成對某個人的錯誤指涉。

---

## 4. 網站資料格式

```
podcast-knowledge-digest/
├── index.html                # 閱讀器（樣式與邏輯，內容不寫死在這裡）
├── data/
│   ├── index.json            # 日期清單（manifest）
│   ├── YYYY-MM-DD.json       # 每天一個檔
│   └── observations.json     # 觀察點記分板（2026-08-10 起，每天回訪寫回）
├── robots.txt                # 全站 noindex，不進搜尋引擎
├── README.md                 # GitHub 門面（Public，改動系統時記得同步）
├── AGENT_BRIEF.md            # 本檔：規格
├── MAINTENANCE.md            # 維護說明＋事故與決策檔案
└── .github/workflows/deploy.yml
```

**每天要動三個檔**（2026-08-10 起）：新增 `data/YYYY-MM-DD.json`、把該日加到 `data/index.json` 的 `days` 陣列**最前面**（`days` 一律由新到舊）、**回訪並寫回 `data/observations.json`**（見下方「觀察點記分板」）。**`index.html` 不要動。**

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
      "title": "All-In Podcast｜中文標題（格式＝節目名｜標題）",
      "meta": [{ "k": "節目標題", "v": "…" }, { "k": "原始連結", "v": "https://…" }],
      "published": "2026年7月25日｜片長…", "hosts": "…", "guest": "…",
      "source": "podfetch 逐字稿（Gemini 轉錄）", "url": "https://…", "chars": 2992,
      "summary": "一句話總結…",
      "guests": [{ "name": "Lacy Hunt", "org": "Hoisington" }],
      "topics": ["聯準會與利率", "通膨"],
      "quality": { "completeness": 1.02, "status": "OK", "speakerNote": "", "timestampNote": "" },
      "takeaways": [{ "label": "重點一", "title": "…", "body": "…" }],
      "sections": [{ "heading": "一、…", "paragraphs": ["…", "…"] }],
      "quotes": [{ "text": "…", "by": "David Sacks" }]
    }
  ]
}
```

**2026-08-10 新增的三個欄位**（舊集數沒有，前端會相容）：

- **`guests`**：結構化來賓清單，取代自由文字 `guest` 欄位的解析（`guest` 仍保留給人讀）。**姓名照節目說法、不要自己正規化**；判斷不了單位就留空字串。這是網站「來賓索引」頁的資料來源——自由文字時代前端用「頓號切、括號切」硬拆，同名異寫會讓索引分裂。
- **`topics`**：主題標籤，**只能從下面的受控詞表選，1–3 個**——自由發揮的標籤跨日對不上，等於沒有標籤。詞表（15 個）：`總經與利率`／`聯準會與利率`／`通膨`／`美股大盤`／`信用與債市`／`AI資本支出`／`AI技術與應用`／`半導體`／`個股拆解`／`科技產業`／`創投與私募`／`加密資產`／`地緣政治`／`能源與大宗商品`／`投資哲學`。詞表要擴充時改這裡並同步任務卡。
- **`quality`**：轉錄品質的結構化欄位，從 manifest 直接抄（`completeness`／`status`；`speakerNote` 填 speakerNotes 的一句話總結，`timestampNote` 填 timestampNotes 的一句話總結，無警示一律留空字串）。過去這些資訊只以散文埋在 `source` 字串裡，前端無法顯示品質提示。

**`chars` 由組檔時機械計算（2026-08-12 改）**：第 4 步組檔的 python 一律用

```python
ep["chars"] = len("".join(p for s in ep.get("sections") or [] for p in s.get("paragraphs") or []))
```

覆寫子代理填的值。**這不是為了精確，是為了讓所有集數用同一把尺**——自報值的誤差範圍是 −38% 到 +81%（見第 3 節），而字數分層是拿來判斷「有沒有超規格」的，用一把每集不同的尺去判斷等於沒判斷。**歷史 13 個日檔已於 08-12 一併重算（74 集中 42 集的值有變）。**

### 觀察點記分板（`data/observations.json`，2026-08-10 新增）

每天「觀察後記」提出的可驗證觀察點，寫完不能就丟——這個檔案追蹤它們後來應驗了沒，網站 `#/obs` 頁顯示。格式：

```json
{ "updated": "2026-08-11",
  "note": "收錄標準的一句話提醒（給人讀的，程式不依賴它）",
  "items": [{ "id": "obs-20260810-1", "date": "2026-08-10", "text": "…",
              "status": "觀察中", "verdict": "", "verdictDate": "" }] }
```

`status` 只有五種值：`觀察中`／`應驗`／`部分應驗`／`落空`／`無法驗證`。**每日排程在第 4 步回訪**：讀這個檔，對照當天摘要卡，把有明確結果的「觀察中」條目改判（**保守判定，不確定就維持觀察中**；純管線自檢類的條目標「無法驗證」），再把今天後記的新觀察點附加進去。判定要填 `verdict`（一句話理由）與 `verdictDate`。

> **什麼算觀察點，什麼不算（2026-08-11 新增）。** 只收**可驗證的預測或檢驗點**——有具體對象、有可對照的事件或數據、原則上會有真假。
> **不收**：免責聲明與來源標註（「以上內容非投資建議」）、管線自檢（「明天可回頭確認窗口銜接」）、純敘述性總結。
> 這條是踩出來的：08-10 回填種子時把後記段落照單全收，連免責文句都進了記分板，**08-11 六條改判裡有四條是在清這些雜訊**——記分板的價值在於「哪些判斷後來被證明對了」，混進不可能有真假的條目就只是稀釋它。新增前先問一句：**這句話三個月後有可能被證明是錯的嗎？** 不能就不要收。

### showKey

`showKey` 決定卡片色條與徽章顏色，**一律採用 `~/.podfetch/shows.json` 的鍵值**，不要在網站端另取名字，否則徽章永遠對不上。23 檔完整鍵值：

`allin`／`bg2`／`pivot`／`hardfork`／`unhedged`／`acquired`／`twentyvc`／`iltb`／`breakdowns`／`ingoodcompany`／`compound`／`mib`／`nopriors`／`lennys`／`lex`／`dwarkesh`／`latentspace`／`oddlots`／`macrovoices`／`markethuddle`／`bloomberg`／`gsx`／`tip`

**`index.html` 目前定義了 24 組——現役 23 檔全部齊備**（2026-08-11 補完 `acquired`／`bg2`／`lennys`），另含已下架的 `capitalallocators`（供歷史資料顯示）。補新色時要確認**沒有跟既有的撞色**（08-08 就差點讓 `hardfork` 用到 `markethuddle` 的橘紅）；**三處要分別檢查**，08-10 只查了色條就宣稱查過，徽章文字色與現役節目只差 12。門檻：與最近鄰的 RGB 距離至少 25，低於 20 一定要換。其餘鍵值第一次出現在資料裡時，該集會走預設藍——功能正常但視覺不一致，此時在回報中提一句即可。補的時候三處都要補：`.ep.s-<key>::before`、`.b-<key>`、`html[data-theme="dark"] .b-<key>`。

> `capitalallocators` 於 2026-08-03 移除。舊資料檔裡若還有這個鍵值，該集會走預設藍——**不要為此回頭改歷史檔案**，歷史資料保持原樣。

`index.html` 的交叉觀察展開按鈕標籤依 `crossCut.points` 實際條數產生（`cnZh` 函式），不寫死條數。

---

## 5. 發布流程

1. 產生當日 `data/YYYY-MM-DD.json` 與更新後的 `data/index.json`。
2. **寫入 `~/podcast-knowledge-digest/data/`**：連線資料夾用一般檔案工具（Write／Edit）即可。若本次工作階段剛好掛載了 `mcp__remote-devices__device_commit_files`（`force: true`）也可以，但**不要假設它存在**。
3. **Word 報告用腳本轉出，不由 LLM 重寫**（2026-08-08 起）：

   ```
   python3 ~/.podfetch/json2docx.py data/YYYY-MM-DD.json <暫存輸出資料夾>/節目知識庫-YYYY-MM-DD.docx
   ```

   相依 python-docx（沙箱：`pip install python-docx --break-system-packages`）。腳本會印出集數，要等於當日實際集數。**Word 檔不要放進 repo 目錄**——這個 repo 是 Public，放進去會被背景程式推上 GitHub。寫到暫存輸出資料夾再用 `present_files` 交付。
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

## 6. 基礎設施備忘（每日執行需要知道的部分）

> 完整的基礎設施文件（GitHub 設定、PAT 換發、電源設定的完整指令與決策、launchd 排錯）在 `MAINTENANCE.md` 第 4B、7、9 節。**本節只留每日執行會用到的。**

- **背景推送**：launchd `com.kenny.dashpush` 每 180 秒自動 `add`＋`commit`＋`push`，Actions 再部署到 Pages。**它曾靜默失效整整一天**，所以第 5 節的上線驗證不能省。
- **連線資料夾**：需要三個——`~/podcast-knowledge-digest`（寫網站資料）、`~/podcast-transcripts`（讀逐字稿）、`~/.podfetch`（排錯讀 log 與 state）。**連線不保證跨工作階段留存**，失敗的樣子和「podfetch 沒跑」一模一樣。**讀不到就先自己連**：`mcp__cowork__request_cowork_directory`（`path` 給 `~/podcast-transcripts` 這樣的路徑），無人值守下實測不會跳核准對話框。
- **逐字稿輸出（`~/podcast-transcripts/`）刻意放在 repo 外部**：Public repo ＋ 付費來源全文 ＝ 著作權問題。**不要移進 repo，加 `.gitignore` 也不行。**
- **FT 存取靠一張會安靜過期的 syndication cookie**（Chrome 未登入 FT）。每次處理 FT 內容都要驗證正文長度（見第 2 節退援第 1 層底下的 FT 特例）；失效就退回第 2 層 podfetch 並在回報中明講。
- **YouTube 退援層需要 Chrome 已登入**。發現未登入就走下一層並告知，不要代為輸入帳密。
- **時刻漂移時不要盲目跑 `fix-schedule.sh`**——先照第 2 節「時刻漂移守衛」三項確認成因（設定值錯與機器睡著症狀相同），修錯邊會變成假性修復。

---

## 7. 合規與語氣

- 全站 `robots.txt` 與 `<meta name="robots" content="noindex, nofollow">`，定位為個人知識管理站，不做公開發行。
- **每集保留來源標註與原文連結**，鼓勵前往原始節目收聽。
- 摘譯為濃縮中譯、非逐字轉載；付費來源（FT、Bloomberg 等）尤其只做重點濃縮並附連結。
- 語氣：繁體中文（台灣慣用語）、專業財經研究腔、全形標點；有觀點但中立，明確標示非投資建議。

---

## 8. 變更紀錄（CHANGELOG）

### 2026-08-14

- **「用段數規劃」成立，而且效果比預期大。** 連續三天測同一條規則：08-11 寫進措辭（3/5 重寫）、08-12 加強措辭（3/5 重寫）、08-12 晚間把規劃單位從字數換成段數 → **08-14 十二集零重寫**，段數達標 11/12（唯一超標的 GS Exchanges 是官方逐字稿密度高的允許情形）。**每集成本 54.9 萬 → 28.3 萬，減半**；子代理平均 2.6 次工具呼叫、無一集超過 5 次。**這條規則現在有效，沒有新證據就不要再動它**——連續三次修改同一條規則已經證明，前兩次都因為改錯了層次而白費。
- **順帶驗證「新架構是線性成長、集數多才顯優勢」**（08-08 寫下、一直沒機會測）：12 集這天，固定開銷（指令與工具清單）佔比從 08-12 的 20.1% 降到 **10.4%**，攤薄效果清楚。
- **新增時間軸檢查 `check_timestamps()`，這是一個存在很久卻從沒人看見的盲區。** 08-11 的 20VC 最大時間戳跑到 1,192 分鐘（片長 59 分，**溢出 1888%**）、08-14 的 TIP837 跑到 253 分（片長 78 分，**溢出 224%**）——兩集完整度分別是 0.91 與 0.98、status 都是 OK，**三天來沒有任何機制看見它**。訊號寫進**獨立的 `timestamp_notes`／`timestampNotes`，不影響 `status`**（時間軸壞掉不等於內容缺漏，併進 `warnings` 會用錯的理由標降級——08-07 講者檢查踩過這個坑）。詳見第 2 節（維度定義）與第 3 節（兩條門檻）。
  **第二條規則刻意設成「兩個訊號同時成立」**：只看大間隙會對 72 集報 15 集，因為長篇獨白與真跳段長得一樣；加上「完整度 <0.85」之後全庫只報 7 集，而唯一被抓到的間隙案例（08-14 MIB，22 分鐘無戳、完整度 0.73）正是子代理獨立確認確有兩處跳段的那一集。**「與完整度一起看」這件事應該由程式做，不是寫進訊息叫人自己判斷。**
- **回歸複驗（子代理）抓到 9 處，全修。** 最嚴重的兩處都是**已經記過的同型錯誤又犯一次**：①08-12 的變更紀錄以 changelog 體例留在 `MAINTENANCE.md` 第 7 節、沒進第 11 節——**這正是 08-09 抓過的 08-08 同型錯，防它的規則就寫在本節末尾**；②第 12 節那段列舉又對不上（08-12 那列已翻 ✅ 卻沒進第三類 bullet），**連續五輪、四種排列**，所以把「改字與改表必須同一次做完」改寫成三步檢查清單。其餘七處：`podfetch.py` 新註解裡的例子數字（1,114／56 應為 1,192／59）與三份文件不符、`_ANY_TS` 不吃縮排時間戳（同檔其他正則都吃，帶縮排的稿會靜默回空）、`TOKEN_NOTE` 被回填日覆寫（今天的量測失敗原因指向 08-13）、檔頭設計清單沒有時間軸那條、README 只寫兩種檢查、brief 第 3 節有句子被新區塊擠斷、`TS_DARK_GAP=90` 的定義沒寫進 brief。
- **token 量測的路徑終於用 `find` 定位出來，不再猜。** 真實位置是 `~/Library/Application Support/Claude/local-agent-mode-sessions/<帳號>/<工作區>/local_<階段>/.claude/projects/<專案>/<uuid>.jsonl`，子代理在同層的 `<uuid>/subagents/agent-*.jsonl`——**掃描邏輯本來就對得上，錯的只有根目錄那一行 glob**。前兩次分別猜成 `~/.claude/projects` 與 `$TMPDIR/claude-hostloop-plugins/`，`eff_tokens_k` 因此連續五天空白。**猜兩次不中就該停下來去量，而不是猜第三次。**（此欄仍只在 Mac 上跑 healthcheck 時才有值，沙箱看不到 `~/Library`。）
  **路徑修好之後又露出第二層問題，而且是同一種毛病**：原本用「mtime 落在 02:30–06:00」判斷哪一個 transcript 是排程執行，實測 70 個檔案**沒有一個**落在窗口內——**mtime 是「最後一次寫入」，桌面 App 之後重開或續讀同一個 session 都會把它往後推**。已改用**內容指紋**（排程 prompt 開頭那句只會出現在排程執行的 transcript 裡）＋**檔內 `timestamp`** 判日期，mtime 窗口留作退援並在訊息中標明走了哪一條。**時間是外部條件，內容才是「這個檔案是什麼」的證據。**
- **`skill_kb` 這一欄從來沒有被填過任何一天**（15 列全空）——它讀 `~/Documents/`，而沙箱看不到那裡，維護幾乎都在沙箱跑。**刻意不改成從別處猜**：空值至少誠實，填一個猜來的大小會讓這一欄看起來有在追蹤。要它有值就得在 Mac 的終端機直接跑 healthcheck。
- **`healthcheck.py` 會回填 `metrics.csv` 缺漏的日子。** 指標原本只在「跑 healthcheck 的當天」寫入，**沒跑維護的日子就沒有那一列**——08-13 就這樣缺了，而那天其實有 3 集、其中一集 DEGRADED，完全沒進基線。現在掃 `data/` 與逐字稿目錄的聯集回填（本次補了 07-29／07-30／07-31／08-13）。**回填列的 `brief_kb`／`skill_kb` 一律留空**，那兩個是「當下的檔案大小」，回填舊日期時填今天的值會是假的。

> **維護規則（不要刪這段）**：本檔與排程任務 `podcast-digest-daily` 的 SKILL.md 是**一組兩份**，改任一邊都必須同步另一邊，並在本節加一筆。**事故經過寫進 `MAINTENANCE.md` 第 7 節，不要寫進這裡**——本節只記「改了什麼、為什麼改」。日期由新到舊。
> 2026-08-09 發現這條規則在 08-08 隨紀錄被搬進 MAINTENANCE 第 7 節後，**brief 本體整整一天沒有任何一句要求雙邊同步**——而 08-04 的 SKILL.md 整份覆寫事故正是這類漏抄造成的。**歸檔時要分辨哪些是紀錄、哪些是規則；規則不跟著走。**
>
> **更早的變更紀錄（2026-08-02 至 08-11）已歸檔至 `MAINTENANCE.md` 第 11 節。**
> 本節只保留**最近一次維護當天**的條目——完整讀本檔的是每日排程，它不需要歷史。
> 歸檔規則：每次維護開工時，先把非當日的條目整段移到 `MAINTENANCE.md` 第 11 節（由新到舊插在最前）。
