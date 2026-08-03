# MAINTENANCE — 節目知識庫・維護說明

**這份文件是給「要修改這套系統」的人（或 Claude）看的，不是給執行每日產出的人看的。**
每日產出請看 `AGENT_BRIEF.md`。

想改動任何東西時，最快的方式是開一個新對話輸入 `/podcast-maintain`，或直接說「讀 MAINTENANCE.md」。

---

## 1. 這套系統由哪些東西定義

| # | 檔案／位置 | 角色 | 誰會讀它 |
|---|---|---|---|
| 1 | `~/podcast-knowledge-digest/AGENT_BRIEF.md` | **完整規格**：20 檔節目清單、全文來源、podfetch 管線、內容規格、資料格式、發布流程 | 每日排程在第 0 步完整讀過 |
| 2 | 排程任務 `podcast-digest-daily` 的 SKILL.md | **執行手冊**：當天的步驟與退援順序。內容是 brief 的濃縮版 | 排程觸發時直接執行 |
| 3 | `~/podcast-knowledge-digest/index.html` | 前端外殼：CSS、渲染邏輯、節目徽章 | 瀏覽器 |
| 4 | `~/podcast-knowledge-digest/data/*.json` | 每日內容 | `index.html` |
| 5 | `~/.podfetch/`（腳本、`state.json`、`logs/`） | 01:00 的轉錄管線，由 launchd `com.kenny.podfetch` 觸發 | 排程排錯時會讀 |
| 6 | `~/podcast-transcripts/<date>/` | podfetch 產出的逐字稿與 `manifest.json` | 排程第 1 步 |

**最重要的一條規則：第 1 項與第 2 項是一組兩份，改任一邊都必須同步另一邊。**
兩者不同步時，排程會拿到互相矛盾的指示，而且不會報錯。

改完務必在 `AGENT_BRIEF.md` 第 8 節「變更紀錄」加一筆，寫清楚**為什麼改**。

排程 SKILL.md 沒有版本控制，只有 `AGENT_BRIEF.md` 在 git 裡。**brief 才是真正的來源。**

---

## 2. 修改的標準流程

1. 讀 `AGENT_BRIEF.md`（全部）與排程 SKILL.md（`list_scheduled_tasks` 取得 `path` 後 Read）。
2. **先比對兩者是否已經不同步**，有的話先修好再談新需求。
3. 改 `AGENT_BRIEF.md`。
4. 用 `mcp__scheduled-tasks__update_scheduled_task` 同步排程 prompt。
5. 在第 8 節加變更紀錄。
6. 若動到節目清單，`index.html` 的 `.ep.s-<key>::before` 與 `.b-<key>` 也要補一組（沒補會走預設藍色，不影響功能但會不一致）。
7. **不要跑任何 git 指令**（含 `git status`）——`com.kenny.dashpush` 每 180 秒自動推送，跑 git 會留下 `.git/index.lock` 擋住推送。要看推送鏈狀態用 `cat .git/refs/heads/main`、`tail .git/logs/refs/remotes/origin/main`，這些是唯讀指令，安全。

---

## 3. 已知的坑（踩過才寫進來的，不要再踩一次）

- **「當天沒有目錄」≠「podfetch 掛了」。** 0 集時 podfetch 正常結束但不建立目錄。要照三段排查：資料夾連線 → 讀當天日誌看是否 `沒有新集數。` → 日誌異常才算真的失效。
- **驗證上線一定要帶 cache-buster。** 裸網址與 `raw.githubusercontent.com` 都會回舊快取（實測回到三天前），且要同時確認 `updatedLabel` 是本次執行時間，只看日期會被騙。
- **iTunes lookup 的 US 商店快取嚴重過期**，尤其 All-In，而且 limit 越小快取越舊。交叉驗證改用 GB／AU 商店。
- **`web_fetch` 對 RSS／XML 一律回 `[binary data]`**，不要指望直接讀 feedUrl。
- **FT 存取失效時不會報錯**，只會安靜退回付費牆。每次都要檢查正文長度（Unhedged 通常 5,000 字元以上）。
- **YouTube 字幕自 2026-08-02 起全面失效**，只當最後手段，每集最多試 5 分鐘。
- **Word 報告絕對不能存進 repo**（那是 public repo），要寫到暫存輸出資料夾再用 `present_files` 交付。
- **前一晚的美東晚間集數必定順延到隔天那一版**，這是 03:00 時段的設計取捨，不是故障，不要去追。

---

## 4. 新增一檔節目的完整步驟

1. `AGENT_BRIEF.md` 第 1 節：加進節目清單，含 AppleID、官方逐字稿來源（若有）、排序位置。
2. `~/.podfetch/` 的設定：把節目加進抓取清單。
3. `index.html`：補一組 `.ep.s-<key>::before` 與 `.b-<key>`。
4. 排程 SKILL.md 同步（若影響步驟或排序規則）。
5. 第 8 節加變更紀錄。

---

## 5. 目前已知待辦與觀察中的事項

- **YouTube 字幕退援路徑實質上已死**，目前只剩 podfetch、官方逐字稿、FT 三條路。若 podfetch 出問題，退援能力比看起來薄。
- **FT 的 syndication cookie 是脆弱依賴**，會過期且失效時安靜。長期解法是登入真正的 FT 帳號。
- **資料夾連線不保證跨工作階段留存**，排程要能自我修復（已寫進 SKILL.md）。

---

## 6. 不要做的事

- 不要憑印象編造節目內容，也不要編造引述。沒有逐字稿就不寫金句。
- 0 集時不要產生空檔案、不要動 `index.json`、不要產 Word 報告。
- 不要把 Word 報告寫進 repo。
- 不要跑 git 指令。
