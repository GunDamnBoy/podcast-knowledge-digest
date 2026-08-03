# AGENT BRIEF — 節目知識庫・每日發布標準說明

這份文件是「節目知識庫（Podcast Knowledge Digest）」的完整規格。任何一個新的 Cowork 對話讀了這份，就能完整重現整套系統。全程使用繁體中文（台灣用語），讀者為專業財經工作者。

網站：<https://gundamnboy.github.io/podcast-knowledge-digest/>

> **本檔只寫「現在的規格與判斷規則」。** 事故經過、當初為什麼這樣決定、被否決的選項，一律寫在 `MAINTENANCE.md` 第 7 節「事故與決策檔案」。本檔會以「見 `MAINTENANCE.md` 第 7 節」指過去。這樣分是因為排程每天要完整讀本檔一次，而執行者不需要知道歷史。

---

## 0. 這個系統在做什麼

每天早上（含週末）自動偵測 20 檔 Podcast 的新集數，取得**全文**，為每一集撰寫約 2,000–3,000 字的繁體中文完整摘譯＋3–5 個核心重點，同時交付兩種形式：

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

## 1. 節目清單與全文來源（20 檔）

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

**B. 音檔轉錄（podfetch ＋ Gemini API，見第 2 節）** — 沒有官方逐字稿的節目一律走這條。iTunes Lookup 回傳的 `episodeUrl` 就是直接的 MP3 網址，**不需要 YouTube**。

All-In／BG2／Pivot／Hard Fork／20VC／No Priors／Lenny's／Invest Like the Best／Capital Allocators／Odd Lots／Bloomberg Surveillance／The Market Huddle

**偵測新集數**用 iTunes Lookup API（不需 Chrome，回傳結構化 JSON）：

```
https://itunes.apple.com/lookup?id=<AppleID>&media=podcast&entity=podcastEpisode&limit=8
```

用 `web_fetch` 取得。每集看 `releaseDate`（**UTC**）、`trackName`、`trackTimeMillis`（毫秒）、`description`、`trackViewUrl`、`episodeUrl`。Bloomberg Surveillance 一天發多集，該檔用 `limit=20`。

**三個已知陷阱**：

- 回傳第一筆是節目本身（`"wrapperType":"track"`），其 `releaseDate` 是舊資料，**不要誤判為新集數**；真正的集數是 `"wrapperType":"podcastEpisode"`。
- **US 商店快取嚴重過期**（尤其 All-In），且 **limit 越小快取越舊**。交叉驗證改用 GB／AU 商店，實測是即時的。
- **`web_fetch` 對 RSS／XML 一律回 `[binary data]`**，不要指望直接讀 feedUrl。

各節目 AppleID：

All-In 1502871393｜BG2 1727278168｜Pivot 1073226719｜Hard Fork 1528594034｜Unhedged 1691284824｜Acquired 1050462261｜20VC 958230465｜Invest Like the Best 1154105909｜Capital Allocators 1223764016｜Masters in Business 730188152｜No Priors 1668002688｜Lenny's 1627920305｜Lex Fridman 1434243584｜Dwarkesh 1516093381｜Latent Space 1674008350｜Odd Lots 1056200096｜Macro Voices 1079172742｜Market Huddle 1444520320｜Bloomberg Surveillance 296237493｜GS Exchanges 948913991

### 時間窗口與去重

**每天**（含週末）抓過去 **26 小時**發布的集數。26 小時對 24 小時的執行間隔留有 2 小時重疊，用意是吸收執行延遲，**代價是相鄰兩天會重複命中同一集**。

**所以產檔前必須去重**：讀 `data/` 裡**日期最大的那一份** `YYYY-MM-DD.json`（注意不一定是昨天——0 集日不產檔），比對 `url` 與 `title`，已收錄過的一律略過。**podfetch 主路徑與 iTunes 退援路徑都要做這件事。**

**允許「當日 0 集」**（週末常見）。此時**不要產生空檔案、不要動 `index.json`、不要產 Word 報告**，直接回報後結束。

**時區換算**：台北 ＝ UTC+8，「台北 7/31 全天」＝ `releaseDate` 落在 `2026-07-30T16:00:00Z` 至 `2026-07-31T15:59:59Z`。務必先換算再篩選，美東晚間發布的集數在台北會落到隔天，很容易算錯一天。

**檔名慣例**：`data/YYYY-MM-DD.json` 的日期是**執行當天**（台北），內容是該時點往前推 26 小時窗口內發布的集數——所以 `2026-07-30.json` 裝的是 7/29 晚間至 7/30 上午發布的集數。補跑歷史某天時沿用同一慣例。

**注意窗口接縫**：26 小時窗口以每天固定同一時刻執行為前提；某天沒跑或延後跑，前一次窗口結束到這次窗口開始之間的集數會整個掉出去。補跑時要回頭檢查前一份檔案的實際涵蓋範圍，別假設它蓋滿整個日曆日。

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

### 三個不要改的設計

1. **視窗以 `last_run_utc` 為準，不是固定 26 小時。** 從上次成功執行時間往前推 30 分鐘重疊開始抓，上限 72 小時。**不要改回固定窗口**——舊版在漏跑一天時會產生無法察覺的缺口。
2. **字數檢查是防「安靜失效」的唯一機制。** Gemini 是 LLM 不是機械式辨識器，長音檔上可能改寫、壓縮或跳過整段而不報錯。腳本以英語口說每分鐘 130 字估算期望值，低於 55% 就重試該段；仍不足則標 `DEGRADED` 並寫進 front matter 與 manifest。**不要拿掉。**
3. **模型池保留 Flash-Lite 名額。** 3 個 Flash（品質優先）＋ 3 個 Flash-Lite（溢流），撞到日額度自動換下一個。Lite 的日額度是一般 Flash 的 25 倍，拿掉等於自願放棄。

**`config.json` 現行值**：`segment_seconds: 1200`、`max_chunk_mb: 48`、`min_request_interval_seconds: 10`、`avoid_preview_models: true`、`flash_slots: 3`／`lite_slots: 3`、`max_output_tokens: 32768`、`default_window_hours: 48`、`max_lookback_hours: 72`。

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
2. **連上了但沒有今天的目錄** → 讀 `~/.podfetch/logs/<今天>.log`。有 `沒有新集數。` 就是真的 0 集，一切正常；日誌不存在或停在異常處，才是 podfetch 失效。也可看 `state.json` 的 `last_run_utc` 是否已推進到今天。
3. **確認失效** → 才走 iTunes 退援偵測，並在交付訊息中明講。

**排查第 2 點時，順手看日誌開頭的時間戳。** 正常應為 `[01:00:0x]`。**若不是，代表當天 podfetch 延後補跑了，日報有可能搶在它前面執行**——這種失效是安靜的：podfetch 本身完全正常，只有日報品質悄悄掉一級。要在當日回報中明講，並依這個順序提示使用者排查（**兩種成因都要驗，不要跳過任何一步**）：

1. `pmset -g custom` — AC Power 段的 `sleep` 應為 `0`（**這是主要保障**，插電時永不睡眠）
2. `pmset -g sched` — 應有 `wakepoweron at 0:55AM every day`（後備）
3. `/usr/libexec/PlistBuddy -c "Print :StartCalendarInterval" ~/Library/LaunchAgents/com.kenny.podfetch.plist` — 應為 `Hour = 1, Minute = 0`

2026-08-03 那次的真相是機器睡眠（第 1、2 項），plist 本來就正確——**但那是一次性的查證結果，不是可以永久假設的前提**，排查時三項都要看。經過與教訓見 `MAINTENANCE.md` 第 7 節，環境設定全貌見第 9 節。

漏跑一天不會造成缺口：podfetch 視窗以 `last_run_utc` 為起點（上限 72 小時），下次執行會自動補回。

### 退援順序

1. **官方逐字稿**（第 1 節 A 類）— 永遠優先。**manifest 決定「有哪幾集」，不決定「用哪份全文」**：A 類節目即使 podfetch 已轉錄，仍要去抓官方稿，抓不到才退回 podfetch 版本，並據實填 `source`。
2. **podfetch 逐字稿** — B 類節目的主要來源。
3. **FT 專用流程**（Unhedged）— **取到後必須檢查正文長度**，通常 5,000 字元以上；明顯偏短或出現 `Subscribe to unlock`／`Complete digital access` 即視為 FT 存取失效，走下一層並明確告知使用者。
4. **YouTube 字幕** — 2026-08-02 起已知全面失效，只當最後手段，每集最多試 5 分鐘。須為 Chrome 已登入 YouTube 的狀態，未登入就直接走下一層並告知，不要嘗試代為登入。操作要領見 `MAINTENANCE.md` 第 8 節。
5. **都拿不到** — 依節目說明＋WebSearch 公開報導寫約 500 字精簡摘要，`source` 標註「⚠︎ 全文摘譯待補」及原因，**該集 `quotes` 留空陣列**。若某集本來就在窗口邊緣且拿不到全文，寧可不收錄，並在交付訊息中明講這一集沒被涵蓋。

**絕對不要憑印象編造節目內容，也不要編造引述。沒有逐字稿就不寫金句。**

---

## 3. 內容規格

每一集包含：

- **一句話總結** — 一段，抓住全集最重要的張力，不要流水帳
- **核心重點 3–5 條** — 每條「重點N｜粗體標題」＋2–4 句說明，**必須含對投資人的含義**
- **完整摘譯 2,000–3,000 字** — 依章節時間軸分節，忠於原文論點與數字，正反方意見都要呈現；短節目（15 分鐘以內）約 1,200–1,800 字即可，**不要灌水**
- **本集金句 2–5 句** — 須為逐字稿中實際出現的發言，中譯＋標明講者姓名

**跨節目交叉觀察**：當日集數 ≥3 時必寫。呈現「他們一致同意什麼」與「他們在哪裡正面對撞」——同一議題不同節目的收斂與分歧，是這個工具最大的價值來源。有講者姓名時要具體到人。

**觀察後記**：2–3 條可在接下來幾天實際對照驗證的觀察點。

**排序**：All-In 永遠在最前，其後依對總經／AI／資本市場的重要性排序。

**寫作紀律**：機器轉錄存在語音辨識誤差（人名、專有名詞），須依上下文校正，不確定處採保守表述並標註。數字一律不四捨五入、不概括。引述為中譯非逐字引文。

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

`showKey` 決定卡片色條與徽章顏色，**一律採用 `~/.podfetch/shows.json` 的鍵值**，不要在網站端另取名字，否則徽章永遠對不上。20 檔完整鍵值：

`allin`／`bg2`／`pivot`／`hardfork`／`unhedged`／`acquired`／`twentyvc`／`iltb`／`capitalallocators`／`mib`／`nopriors`／`lennys`／`lex`／`dwarkesh`／`latentspace`／`oddlots`／`macrovoices`／`markethuddle`／`bloomberg`／`gsx`

**`index.html` 目前定義了 9 組**：`allin`／`macrovoices`／`markethuddle`／`unhedged`／`bloomberg`／`latentspace`／`lex`／`mib`／`twentyvc`。其餘 11 個第一次出現在資料裡時，該集會走預設藍——功能正常但視覺不一致，此時在回報中提一句即可。補的時候三處都要補：`.ep.s-<key>::before`、`.b-<key>`、`html[data-theme="dark"] .b-<key>`。

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

  **`sleep 0` 是主要保障，`repeat wakeorpoweron` 是後備，兩者都要留。** 只有後備而沒有主要保障時，機器會在 00:55 醒來、閒置後又睡回去，03:00 就接不到——2026-08-03 那起延後補跑事故就是這個結構。

  **驗證**：`pmset -g custom`（AC Power 段 `sleep` 應為 0）、`pmset -g sched`、`pmset -g ps`（應顯示 `AC Power`）。

  **這一整組設定都不存在於任何設定檔裡，重灌或換機不會跟著遷移**，還包括幾個沒有指令可查的前提：蓋子要打開、Claude 桌面版要在登入項目、不要裝會讓 Mac 插電時改用電池的充電管理軟體（會使 `-c sleep 0` 整個失效，且失效方式是安靜的）。清單見 `MAINTENANCE.md` 第 9 節。

- **podfetch 排程時刻**：必須在 01:00，比日報早兩小時。`~/.podfetch/fix-schedule.sh` 可把 plist 的 `StartCalendarInterval` 寫回 01:00 並重新 `launchctl load`，但這是**驗證／還原工具，不是例行修復**——時間戳不對時多半是喚醒問題而非設定問題。腳本刻意放在 repo 外部。
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

### 2026-08-03（第三次，結構重整）

- **本檔與 `MAINTENANCE.md` 重新分工**：brief 只留規格與判斷規則，事故經過／誤判過程／被否決的選項全部搬到 `MAINTENANCE.md` 第 7 節「事故與決策檔案」，YouTube 操作要領搬到第 8 節。**動機是本檔已膨脹到 42 KB 而排程每天要完整讀一次**，其中很大一部分是執行者根本不需要知道的歷史；而且同一件事在兩處各寫一份，反而讓「哪個是現行規格」變得不清楚。
- **排程 SKILL.md 改為流程骨架**：只留執行順序與分支判斷，事實細節指向本檔章節，不再重抄。**這是為了根除「漏抄型」同步 bug**——08-03 第二次巡檢抓到的四處缺漏全部屬於這一類，只要兩份文件都在描述同一批事實，這種 bug 就會無限重演。保留了「讀不到 brief 時仍能自我修復連線」的最小集合，不會因為瘦身而失去韌性。
- **新增 `~/.podfetch/healthcheck.py`**：把每次維護都要手動重跑的機械式檢查集中成一支唯讀腳本（JSON 可解析與排序、`days` 與檔案雙向對應、`episodeCount` 相符、showKey 三處 CSS 與 `shows.json` 對齊、podfetch 日誌時間戳與收束狀態、逐字稿降級統計、推送鏈、**brief 引用的 `config.json` 數值是否與實際一致**）。最後一項專門抓 08-03 那類「下文改了、上文漏改」的內部矛盾。
- **開啟排程的 `notifyOnCompletion`**：0 集日不動 `index.json`、不產 Word 報告，網站毫無變化，先前完全無法區分「今天沒東西」與「排程根本沒跑」。這是這套系統反覆中招的靜默失效模式，補上通知作為最低限度的心跳。
- **修正去重的措辭**：原寫「前一天的 json」，但 0 集日不產檔，昨天的檔案可能不存在。改為「`data/` 裡日期最大的那一份」。

### 2026-08-03（第二次，維護巡檢）

- **修正 podfetch 與日報的時序倒置**：podfetch 實際跑在 07:00 而非 01:00，日報 cron 改 03:00 後會每天搶先執行、誤判成「podfetch 失效」而掉進已死的 YouTube 退援。根因是機器睡眠導致延後補跑（**不是** plist 設定錯誤），修法為 `pmset repeat wakeorpoweron`。經過見 `MAINTENANCE.md` 第 7 節。
- **第 2 節加入「時刻漂移」守衛**：排查時要順手確認日誌開頭時間戳是 `[01:`，不是就在當日回報中明講。
- **`pmset` 排定喚醒登記為基礎設施依賴**（第 6 節），它是唯一不存在於任何設定檔的依賴。
- **補齊 `index.html` 四組節目徽章**（`latentspace`／`lex`／`mib`／`twentyvc`），這四個 showKey 早已出現在資料裡卻一直走預設藍。同時要求 showKey 一律沿用 `shows.json` 的鍵值。
- **統一 YouTube 嘗試上限為 5 分鐘**（原第 2B 節寫 8 分鐘，與其他三處牴觸）。
- **修掉本檔內部四處自打架的過期數值**：20 分鐘段／Files API（原寫 25 分鐘／base64）、`max_chunk_mb: 48`（原寫 9 MiB）、約 22 個請求（原寫 15）、「每天（含週末）」（原寫「每個平日」）、26 小時（原殘留「26／74 小時」）。
- **補上排程 SKILL.md 缺的四條規則**：A 類節目仍須抓官方稿（原本的「不要開 Chrome」會讓官方稿永遠拿不到）、podfetch 主路徑同樣要去重、寫不進 repo 時的退援、YouTube 登入前提與合規要求。

### 2026-08-03（第一次）

- **執行時段從 09:00 改到 03:00**，確立「前一晚美東晚間集數順延一版」的取捨。
- **資料夾連線不保證跨工作階段留存**：排程執行中讀不到就用 `request_cowork_directory` 自我修復。
- **確立「當天沒有目錄 ≠ podfetch 掛了」的三段排查。**
- **iTunes lookup 已知陷阱**（US 商店快取、RSS 回 `[binary data]`）。
- **驗證上線必須帶 cache-buster**，且要確認 `updatedLabel`。

### 2026-08-02

- **改以本機 podfetch 管線為主要全文來源**（第 2 節）：01:00 抓音檔經 Gemini API 轉錄，產出帶講者姓名的逐字稿。跨節目交叉觀察因此可以具體到人。
- **YouTube 字幕全面失效**，降為最後手段。
