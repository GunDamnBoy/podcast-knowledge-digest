# MAINTENANCE — 節目知識庫・維護說明

**這份文件是給「要修改這套系統」的人（或 Claude）看的，不是給執行每日產出的人看的。**
每日產出請看 `AGENT_BRIEF.md`。

想改動任何東西時，最快的方式是開一個新對話輸入 `/podcast-maintain`，或直接說「讀 MAINTENANCE.md」。

**分工原則（2026-08-03 確立）**：`AGENT_BRIEF.md` 只寫**現在的規格與判斷規則**，本檔負責**為什麼會變成這樣**——事故經過、誤判過程、被否決的選項。brief 是每日排程每天完整讀一次的東西，塞事故史會讓它越長越慢，而且執行者根本不需要知道當初誰誤判了什麼。歷史寫在這裡，brief 用一行指過來。

---

## 1. 這套系統由哪些東西定義

| # | 檔案／位置 | 角色 | 誰會讀它 |
|---|---|---|---|
| 1 | `~/podcast-knowledge-digest/AGENT_BRIEF.md` | **完整規格**：20 檔節目清單、全文來源、podfetch 管線、內容規格、資料格式、發布流程 | 每日排程在第 0 步完整讀過 |
| 2 | 排程任務 `podcast-digest-daily` 的 SKILL.md | **執行骨架**：流程順序與分支判斷。事實細節指向 brief 章節，不重抄 | 排程觸發時直接執行 |
| 3 | `~/podcast-knowledge-digest/index.html` | 前端外殼：CSS、渲染邏輯、節目徽章 | 瀏覽器 |
| 4 | `~/podcast-knowledge-digest/data/*.json` | 每日內容 | `index.html` |
| 5 | `~/.podfetch/`（腳本、`config.json`、`shows.json`、`state.json`、`logs/`） | 01:00 的轉錄管線，由 launchd `com.kenny.podfetch` 觸發 | 排程排錯時會讀 |
| 6 | `~/podcast-transcripts/<date>/` | podfetch 產出的逐字稿與 `manifest.json` | 排程第 1 步 |
| 7 | `~/.podfetch/healthcheck.py` | 唯讀健康檢查，把機械式檢查集中成一支 | 維護時第一步就跑 |
| 8 | `~/.podfetch/fix-schedule.sh` | 把 launchd 時刻寫回 01:00 的驗證／還原工具 | 只在確認 plist 被改動時 |
| 9 | 本檔 `MAINTENANCE.md` | 維護說明＋事故與決策檔案 | 維護者 |

**最重要的一條規則：第 1 項與第 2 項是一組兩份，改任一邊都必須同步另一邊。**
兩者不同步時，排程會拿到互相矛盾的指示，而且不會報錯。

排程 SKILL.md 沒有版本控制，只有 `AGENT_BRIEF.md` 在 git 裡。**brief 才是真正的來源。**

---

## 2. 修改的標準流程

1. **先跑 `python3 ~/.podfetch/healthcheck.py`**，把機械式檢查一次做完。
2. 讀 `AGENT_BRIEF.md`（全部）與排程 SKILL.md（`list_scheduled_tasks` 取得 `path` 後 Read）。
3. **先比對兩者是否已經不同步**，有的話先修好再談新需求。
4. 改 `AGENT_BRIEF.md`。
5. 用 `mcp__scheduled-tasks__update_scheduled_task` 同步排程 prompt。
6. 在 brief 第 8 節加變更紀錄；**事故經過與被否決的選項寫進本檔第 7 節**，不要寫進 brief。
7. 若動到節目清單，`~/.podfetch/shows.json` 與 `index.html` 的 `.ep.s-<key>::before`／`.b-<key>`／深色模式那一組都要補。
8. 收工前再跑一次 `healthcheck.py`，並用子代理獨立比對 brief 與 SKILL.md。
9. **不要跑任何 git 指令**（含 `git status`）——`com.kenny.dashpush` 每 180 秒自動推送，跑 git 會留下 `.git/index.lock` 擋住推送。要看推送鏈用 `cat .git/refs/heads/main`、`tail .git/logs/refs/remotes/origin/main`，這些是唯讀指令，安全。

---

## 3. 健康檢查

```
python3 ~/.podfetch/healthcheck.py
```

唯讀，不寫檔、不碰 git。在 Cowork 的 Linux 沙箱裡也能跑（會自動偵測掛載點）。檢查項目：

- `data/*.json` 可解析、`index.json` 由新到舊、`days` 與實際檔案雙向對應、`episodeCount` 與實際集數相符
- 資料用到的 `showKey` 是否都有色條／徽章／深色模式 CSS，且都沿用 `shows.json` 的鍵值
- podfetch 最新日誌的**開頭時間戳是否為 `01:`**、是 0 集還是異常收束、`state.json` 的 `last_run_utc` 新鮮度
- 最新逐字稿目錄的 `OK`／`DEGRADED`／`FAILED` 統計
- 推送鏈 local vs origin（唯讀 `cat`）
- **brief 引用的 `config.json` 數值是否與實際設定相符**——這一項專門抓 2026-08-03 那類「下文改了、上文漏改」的內部矛盾

結束碼 0 = 通過或僅有 WARN，1 = 有 FAIL。

---

## 4. 已知的坑（踩過才寫進來的，不要再踩一次）

- **「當天沒有目錄」≠「podfetch 掛了」。** 0 集時 podfetch 正常結束但不建立目錄。要照三段排查：資料夾連線 → 讀當天日誌看是否 `沒有新集數。` → 日誌異常才算真的失效。
- **「日誌時間戳對不上」有兩種成因，別跳過第一種驗證。** (a) plist 被改動 → `/usr/libexec/PlistBuddy -c "Print :StartCalendarInterval" ~/Library/LaunchAgents/com.kenny.podfetch.plist`；(b) **機器睡著、launchd 延後補跑** → `pmset -g sched` 看有沒有排定喚醒。2026-08-03 的真相是 (b)，經過見第 7 節。
- **`pmset` 排定喚醒是唯一不存在於設定檔裡的依賴。** 重灌或換機不會遷移，且在「只靠電池」與「完全關機」兩種情況下會失效。使用習慣一改（晚上關機、不插電），01:00→03:00 的時序保證就沒了。
- **驗證上線一定要帶 cache-buster。** 裸網址與 `raw.githubusercontent.com` 都會回舊快取（實測回到三天前），且要同時確認 `updatedLabel` 是本次執行時間，只看日期會被騙。
- **`showKey` 一律沿用 `~/.podfetch/shows.json` 的鍵值**，不要在網站端另取名字，否則徽章永遠對不上。20 檔節目中目前只有 9 組定義了 CSS，其餘 11 個第一次出現時會走預設藍（功能正常，視覺不一致）。
- **iTunes lookup 的 US 商店快取嚴重過期**，尤其 All-In，而且 limit 越小快取越舊。交叉驗證改用 GB／AU 商店。
- **`web_fetch` 對 RSS／XML 一律回 `[binary data]`**，不要指望直接讀 feedUrl。
- **FT 存取失效時不會報錯**，只會安靜退回付費牆。每次都要檢查正文長度（Unhedged 通常 5,000 字元以上）。
- **YouTube 字幕自 2026-08-02 起全面失效**，只當最後手段，每集最多試 5 分鐘。操作要領見第 8 節。
- **Word 報告絕對不能存進 repo**（那是 public repo），要寫到暫存輸出資料夾再用 `present_files` 交付。
- **前一晚的美東晚間集數必定順延到隔天那一版**，這是 03:00 時段的設計取捨，不是故障，不要去追。
- **brief 內部會自打架。** 邊做邊改時習慣在下文補新值卻漏改上文，2026-08-03 一次抓到四處。`healthcheck.py` 的「brief vs config」就是為此而寫，但它只涵蓋數值型設定，敘述性矛盾仍要靠子代理比對。

---

## 5. 新增一檔節目的完整步驟

1. `AGENT_BRIEF.md` 第 1 節：加進節目清單，含 AppleID、官方逐字稿來源（若有）、排序位置。
2. `~/.podfetch/shows.json`：加上 `appleId`／`name`／`hosts`（主持人名單會餵給轉錄 prompt，讓 Gemini 寫真名而不是 `Speaker A`）。
3. `~/.podfetch/config.json` 的 `show_priority`：插到適當位置（額度不足時先犧牲排在後面的）。
4. `index.html`：補 `.ep.s-<key>::before`、`.b-<key>`、`html[data-theme="dark"] .b-<key>` 三處。
5. 排程 SKILL.md 同步（若影響步驟或排序規則）。
6. brief 第 8 節加變更紀錄。
7. 跑 `healthcheck.py` 確認 showKey 三項檢查都 PASS。

---

## 6. 目前已知待辦與觀察中的事項

- **`pmset` 排定喚醒待觀察（2026-08-03 設定）**：接下來幾天早上看 `healthcheck.py` 的「podfetch 時刻」是否穩定 PASS。若仍偶爾 FAIL，多半是那晚沒接電源或關機了。連續失效就別再靠時序，改成讓日報容忍 podfetch 尚未跑完（例如短暫等待後重讀，或改用前一天的 manifest 並在回報中標明）。
- **YouTube 字幕退援路徑實質上已死**，目前只剩 podfetch、官方逐字稿、FT 三條路。若 podfetch 出問題，退援能力比看起來薄。
- **FT 的 syndication cookie 是脆弱依賴**，會過期且失效時安靜。長期解法是登入真正的 FT 帳號。
- **資料夾連線不保證跨工作階段留存**，排程要能自我修復（已寫進 SKILL.md）。
- **`healthcheck.py` 的 brief 一致性檢查只涵蓋數值**。敘述性的自相矛盾（例如退援順序寫兩套）目前只能靠子代理比對抓，值得再想有沒有機械化的辦法。

---

## 7. 事故與決策檔案

brief 裡看到「見 `MAINTENANCE.md` 第 7 節」時就是指這裡。寫這些不是為了留存記憶，是因為**每一條都對應一個會重蹈的判斷失誤**。

### 2026-08-03　podfetch 延後補跑：第一個假設是錯的

**現象**：08-03 日誌開頭是 `[07:00:01]` 而非 `[01:00:0x]`，比日報的 03:00 還晚四小時。

**錯誤的第一個假設**：從時間戳推論「plist 被設成 07:00」，還為此寫了修正腳本。實際執行 `PlistBuddy -c "Print :StartCalendarInterval"` 印出來是 `Hour = 1, Minute = 0`——**設定一直都對**。

**真正的根因**：`pmset -g sched` 完全空白，沒有任何排定的喚醒事件。`StartCalendarInterval` 不會喚醒睡著的 Mac，01:00 機器在睡就是不跑，等醒來才補跑一次。`07:00:01` 那個「整點又剛好 01 秒」正是喚醒瞬間補跑的特徵。旁證：當時 `logs/` 只有 08-02（手動 19:29 跑的）與 08-03 兩份，**08-03 07:00 是 launchd 有史以來第一次自動觸發，第一次就沒準時**。

**修法**：`sudo pmset repeat wakeorpoweron MTWRFSU 00:55:00`，不是改 plist。`fix-schedule.sh` 因此降級為驗證／還原工具。

**教訓**：症狀（時間戳晚了）到成因之間有兩條路，先驗設定、再驗喚醒。看到症狀就跳結論會做出一個修不到問題的修法，而且因為 plist 本來就對，執行後「看起來成功了」——這種假性修復比沒修更危險。

**後果為何嚴重**：日報 cron 改成 03:00 後，只要 podfetch 當天延後，日報就會搶在它前面執行，讀不到當天目錄與日誌，被三段排查的第 3 點誤判成「podfetch 失效」而掉進已死的 YouTube 退援路徑。08-03 沒有爆掉純粹是因為日報那次仍跑在改制前的 09:00。

### 2026-08-03　`auto-push.sh` 靜默失效

8/2 18:20 腳本被改成只含 `REPO="$HOME/advisory-knowledge-hub"` 的單一 repo 版，本 repo 從此完全脫離自動推送。**整個失效過程沒有任何外顯徵兆**——launchd 回報 exit 0、`push.log` 沒有新行（原版在「無變更」時直接 `exit 0` 且不留紀錄）、`data/` 檔案照常寫入、排程任務照常回報成功，只有網站悄悄停在舊版。發現方式是比對 `.git/logs/HEAD` 最後一次 commit 的時間戳與檔案 mtime。

修復後的腳本改為多 repo 迴圈、以 `continue` 而非 `exit` 跳過個別 repo、**無變更時也寫入 log**，並在推送成功後記錄 HEAD 短雜湊。

**教訓：「靜默」必須是可辨識的狀態，不能與正常運作無法區分。** 這條原則後來也用在別處——日報的 `notifyOnCompletion`、podfetch 的字數檢查、FT 的正文長度檢查，全都是同一件事的不同版本。也因為這次，第 5 節的上線驗證必須比對 `updatedLabel` 而不能只看 `days[0].date`（事故當天 `days[0].date` 早就是當天日期，光看它會被騙過去）。

### 2026-08-03　執行時段從 09:00 改到 03:00

**動機**：一是希望起床就看得到成果；二是與 07:30 的 `advisory-dashboard-daily` 拉開 token 用量。

**代價是結構性的**：台北 03:00 ＝ 美東前一天 15:00（EDT），而主要節目全部集中在台北 04:00–06:30 落地（Bloomberg TV 04:01、Bloomberg Money 04:25、MiB 05:00、All-In 06:23）。這些在 03:00 那一刻還沒發布，所以每天的日報固定收不到前一晚的美東晚間集數。All-In 因此大約在發布後 21 小時才進日報，而不是原本的 3 小時。podfetch 在 01:00 跑，看到的更早（美東 13:00 為止），13:00–15:00 EDT 之間發布的同樣順延一版。

**但沒有任何集數會遺失**：podfetch 視窗以 `last_run_utc` 為起點，日報又會去重，順延的集數下一版必定收得到。

### 2026-08-02　YouTube 字幕全面失效，改建 podfetch 管線

當天 YouTube 轉錄稿在本機 Chrome 上全面失效——面板可開啟但內容永遠停在載入中，`timedtext` 回傳空字串，InnerTube `get_transcript` 回 `FAILED_PRECONDITION`。在兩支不相干影片上重現，確認為環境層級故障，當日六集全部沒有逐字稿。

**事故暴露的真正問題是架構**：全文取得被綁死在「Chrome 開著 ＋ YouTube 已登入 ＋ YouTube 沒改版」三個條件上，任一失效就整天報廢，而且是安靜失效。

**修法**：改用 podcast 原始 MP3 ＋ Gemini API 轉錄。iTunes Lookup 的每個 `podcastEpisode` 都帶 `episodeUrl`（直接 MP3 網址），20 檔全部確認可取得——**這套系統從一開始就不需要 YouTube**。副作用是拿到了 YouTube 自動字幕從來給不了的維度：`shows.json` 預先寫入主持人名單，轉錄 prompt 要求 Gemini 用真名，跨節目交叉觀察因此能具體到人。

### 2026-08-02　Gemini 免費層：瓶頸是 RPD 不是 TPM

從 AI Studio Console 實測（同一專案內）：

| 模型 | RPM | TPM | RPD |
|---|---|---|---|
| Flash（2.5／3／3.5／3.6） | 5 | 250K | **20** |
| Flash-Lite 2.5 | 10 | 250K | 20 |
| **Flash-Lite 3.1／3.5** | 15 | 250K | **500** |

一般 Flash 每個模型每天只有 20 個請求，而 TPM 上限 250K 實際只用到 12%（約 30K）。**這推翻了直覺——正確策略是「少而大」的請求，不是「多而小」。** 因此 MP3 一律走 Files API（上傳免費、不計入 RPD，也繞開 inline base64 的 20MB 上限），並組成多模型輪替池。

新版 Flash-Lite 的日額度是一般 Flash 的 **25 倍**，是整個設計裡最重要的一個數字。**不要把 Lite 名額拿掉**，那等於自願放棄 25 倍額度。

**但段長最後不是由 RPD 決定，而是由輸出上限決定。** Lite 有 500 RPD 之後 RPD 就不再是瓶頸，真正咬人的是 `maxOutputTokens`：30 分鐘音檔的逐字稿約 6,000 字≒8,000+ token，很容易撞天花板。所以段長收斂到 20 分鐘（約 4,000 字），425 分鐘的一天約 22 個請求。

其他實測結論：`gemini-flash-latest` 目前對應 Gemini 3.6 Flash，屬 20 RPD 那一組；`gemini-2.5-flash` 已對新專案關閉（回 404）；`gemini-2 flash`／`gemini-3.1 pro`／`gemini-2.5 pro` 在免費層是 0/0。初次測試撞 rate limit 的兩個原因：自動挑到 preview 模型（免費額度比穩定版嚴格得多），以及三個請求並行瞬間撞 TPM。

**`max_output_tokens` 必須明確指定，這是最容易重蹈的坑。** 預設約 8,192，而 Gemini 3.x 的 thinking token 也算進輸出預算，實測導致多段被腰斬（一致卡在 5,600–6,200 字，最慘一段只吐出 6 個字）。同時以 `thinkingConfig.thinkingBudget = 0` 關掉 thinking——逐字轉錄不需要推理。

**模型池會在執行中「瘦身」，這是正常的。** `state.json` 的 `model_pool` 記的是當次跑完後仍可用的模型，不是設定值。08-02 的實際軌跡：`gemini-3-flash-preview`（429）→ `gemini-2.5-flash`（404）→ `gemini-2.5-flash-image`（額度滿）→ `gemini-flash-latest`（跑一段後用盡）→ 最後三個 Flash-Lite 完成全部六集。**看到 `model_pool` 只剩 Lite 不代表設定壞了**，代表溢流機制正常運作。

**額度用完時的行為**：429 會照 Google 回傳的 `retryDelay` 等待；判定為日額度耗盡則丟 `QuotaExhausted` 停止本次執行，**已完成的段落留在 `~/.podfetch/cache/`，下次直接沿用不重跑**，未完成的集數不寫進 `seen`、`last_run_utc` 也不推進，下次視窗仍涵蓋得到。若要加量再考慮付費，約 US$0.12／小時音檔。

### 2026-08-02　切段改用純 Python

原本用 ffmpeg，但這台 Mac 沒有 Homebrew——為了一個切檔動作要求安裝套件管理器不合理。改為解析 MPEG Layer III 的 frame 標頭、在 frame 邊界切檔，不重新編碼，因此零外部相依。第一個 frame 若是 Xing／Info／VBRI 標頭會跳過：它記的是整個原檔的長度，複製到第一段會讓解碼器誤判時長。若系統剛好有 ffmpeg 則優先使用（順便降到 16kHz 單聲道 32kbps，上傳量小很多），失敗時自動退回內建切檔器。

早期的 9 MiB 單段上限是 inline base64 時代的產物（膨脹約 1.34 倍須低於 20MB 請求上限），改走 Files API 後已放寬到 `max_chunk_mb: 48`。

### 2026-08-02　固定窗口造成無法察覺的缺口

podfetch 舊版用固定 26 小時窗口，漏跑一天就會產生缺口——7/31 22:53 到 8/1 15:24 之間整段掉出去，而且完全沒有徵兆。新版改為**以 `last_run_utc` 為起點**往前推 30 分鐘重疊，上限 72 小時。**不要改回固定窗口。**

（日報那一側仍是 26 小時窗口，因為它有去重機制兜底；兩者的窗口邏輯不同是刻意的。）

---

## 8. YouTube 字幕操作要領（2026-08-02 起已知失效，僅存查）

真的掉進這條退援路徑時才需要看。每集最多試 5 分鐘。

**先找到影片**：用 `https://www.youtube.com/results?search_query=%22<完整標題>%22`（加引號精確比對）比逐頁捲頻道 `/videos` 快得多。用 `read_page` 帶 `ref_id` 取得結果的 `href` 拿到 `watch?v=` 連結，並核對片長與 Apple 的 `trackTimeMillis` 是否吻合。

**取字幕的實際可行順序**：

1. `navigate` 到 `watch` 頁，等 4 秒
2. `find`「`...更多內容`」按鈕並點擊，展開影片說明，等 3 秒
3. 用 `computer` 的 `scroll` 往下捲約 10–12 格，直到出現標題「**字幕記錄**」與藍色按鈕「**顯示轉錄稿**」。先 `screenshot` 確認位置
4. **用座標點擊**那顆「顯示轉錄稿」按鈕，等 6 秒
5. 按 `Home` 回頁面頂端，等 3 秒，再 `get_page_text`
6. 「字幕記錄／搜尋轉錄稿」之後、到片尾台詞之前的整段（含時間戳）即為逐字稿；移除時間戳行後合併

**已知的坑**：

- 用 `find` 拿到的「顯示轉錄稿」ref 直接點**經常沒有反應**（頁面上有兩個同名節點，且影片播放會讓描述自動收合）。要捲到該區塊、用座標點才穩。
- 影片右上角的「⋯」選單**沒有**轉錄稿選項，只有下載與檢舉，別浪費時間。
- 想用 `javascript_tool` 讀 `ytInitialPlayerResponse.captions` 再 fetch 字幕檔：**行不通**。YouTube 有 Trusted Types，`DOMParser` 會被擋；改用 `&fmt=json3` 回傳空字串（baseUrl 需要 POT token）。乖乖走 UI。
- 純音訊型 Podcast 影片（如 Bloomberg Surveillance）一樣有自動字幕，流程相同。

**該集根本不在 YouTube 上**也確實會發生。2026-07-31 補跑時，Bloomberg 的 *Reacting to PCE, GDP, and Kevin Warsh*（42:23）全站搜尋無結果，官方播放清單當日只有四則且顯示「已隱藏無法播放的影片」。此時不要硬湊內容，照 brief 第 2 節退援順序最後一層處理。

---

## 9. 執行環境：機器與電源（2026-08-03 確立）

第 4 節寫過「`pmset` 排定喚醒是唯一不存在於設定檔裡的依賴」。本節把整個環境依賴一次寫清楚，因為它同樣不存在於任何設定檔中，換機或重灌不會遷移。

**決策**：把這台舊 MacBook Pro 當常時開機的伺服器——放在家裡、全天開機、插著電、**不裝任何第三方電源管理軟體**。

### 每天需要醒著的時間窗口

| 時間（台北） | 事件 | 需要什麼 |
|---|---|---|
| **01:00** | **`com.kenny.podfetch`** | Mac 醒著，約 30–45 分鐘（六集） |
| **03:00** | **`podcast-digest-daily`** | Mac 醒著、Claude 桌面版開著 |
| 07:35 | `advisory-dashboard-daily`（另一條線） | Mac 醒著、Chrome 開著 |
| 至 11:30 | 該線跑完 | 同上，持續 |

**是連續七小時，不是「時間到醒一下」。** 排定喚醒只解決 01:00 那個起點；喚醒後若閒置，macOS 會再睡回去，03:00 就接不到——這正是第 7 節那起「延後補跑」事故的結構性風險，只是當時日報還在 09:00 才沒爆掉。

### 已套用的設定

```bash
sudo pmset -c sleep 0          # 插電時永不睡眠（螢幕仍可關）
sudo pmset -c disksleep 0
sudo pmset -c womp 1           # 允許網路喚醒
sudo pmset -c autorestart 1    # 斷電復電後自動開機
sudo pmset repeat wakeorpoweron MTWRFSU 00:55:00   # 保險：萬一仍睡著
```

`sleep 0` 是主要保障，`repeat wakeorpoweron` 是後備。**兩者都要留**——第 7 節的教訓就是只有後備、沒有主要保障時，launchd 會安靜地延後補跑。

### 為什麼不用 AlDente（或任何充電管理軟體）

AlDente 有三個功能會讓 Mac **在插著電時改用電池供電**：Discharge、Sailing Mode、Calibration Mode。電源來源一變成電池，macOS 就改套用 `pmset -b` 並積極睡眠，`-c sleep 0` 完全不生效。

否決的真正理由不是「它會出錯」，而是**它的失效方式是安靜的**——與第 7 節 `auto-push.sh` 那起事故同一種模式：失效狀態與正常運作在現場無法區分。代價是電池長期停在 100%；這台是舊機且定位為固定式伺服器，判斷為可接受。macOS 內建的「最佳化電池充電」可保持開啟（只延後充電、不放電，無害）。

### 其他前提

- **蓋子必須打開**，除非接外接螢幕。闔蓋且無外接螢幕時一定會睡。
- **Claude 桌面版加進登入項目**；投顧那條還需要 Chrome 維持開啟與登入。
- **避免半夜自動重開機**，建議自動更新設成「僅下載、手動安裝」。
- **若啟用 FileVault，重開機需人工輸入密碼**，`autorestart` 救不回無人值守情境。已知單點，尚未解決。
- 全天開機要注意散熱，不要塞在密閉空間。

### 驗證

```bash
pmset -g custom     # AC Power 段的 sleep 應為 0
pmset -g sched      # 應有 repeat wakeorpoweron 00:55:00
pmset -g ps         # 應顯示 "AC Power"
```

`healthcheck.py` 的「podfetch 時刻」若持續 PASS（日誌開頭是 `[01:`），代表這套設定有效。

---

## 10. 不要做的事

- 不要憑印象編造節目內容，也不要編造引述。沒有逐字稿就不寫金句。
- 0 集時不要產生空檔案、不要動 `index.json`、不要產 Word 報告。
- 不要把 Word 報告寫進 repo。
- 不要跑 git 指令。
- 不要把 `~/podcast-transcripts` 移進 repo（Public repo ＋ 付費來源逐字稿 ＝ 著作權問題），就算加 `.gitignore` 也不要。
- 不要只改 brief 或只改排程 SKILL.md 其中一邊。
- 不要把事故經過寫進 brief——寫進本檔第 7 節。
