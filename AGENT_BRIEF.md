# AGENT BRIEF — 節目知識庫・每日發布標準說明

這份文件是「節目知識庫（Podcast Knowledge Digest）」的完整規格。任何一個新的 Cowork 對話讀了這份，就能完整重現整套系統。全程使用繁體中文（台灣用語），讀者為專業財經工作者。

網站：<https://gundamnboy.github.io/podcast-knowledge-digest/>

---

## 0. 這個系統在做什麼

每個平日早上自動偵測 20 檔 Podcast／YouTube 節目的新集數，取得**全文**（官方逐字稿或 YouTube 字幕），為每一集撰寫約 2,000–3,000 字的繁體中文完整摘譯＋3–5 個核心重點，同時交付兩種形式：

1. **Word 報告**（.docx）— 透過 `SendUserFile` 送到對話中，供轉發與引用。
2. **網站**（本 repo）— 每天新增一個 `data/YYYY-MM-DD.json`，供手機／平板／桌機隨時閱讀與全文搜尋。

排程任務：`trig_015cf7Kr4zHWmtHtPMh1NYuR`（cron `30 0 * * 1-5` UTC ＝ 台北平日 08:30）。

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
| Unhedged (FT) | FT 站內搜尋 `ft.com/search?q=<關鍵字>` → 標題為「Transcript: ⋯」的那篇（**需在使用者已登入的 Chrome 中讀**） |
| Masters in Business | `ritholtz.com/<YYYY>/<MM>/transcript-<guest-slug>/`（晚 1–2 週；新集數改走 B） |

**B. YouTube 字幕（需使用者桌機 Chrome）**

All-In `@allin`／BG2 `@Bg2Pod`／Pivot `@pivot`／Hard Fork `@hardfork`／20VC `@20VC`／No Priors `@NoPriorsPodcast`／Lenny's `@LennysPodcast`／Invest Like the Best `@ILTB_Podcast`／Capital Allocators `UCbzQ_YWf9RsBP9ATbmv5kxQ`／Odd Lots 與 Bloomberg Surveillance `@BloombergPodcasts`／Macro Voices `UCICRehoZjq3ZtAWgRJX118A`／The Market Huddle `UCTNgTBKATr18Z7kR32rKOBw`

**偵測新集數**一律讀 Apple Podcasts 頁面 `https://podcasts.apple.com/us/podcast/id<AppleID>`：

All-In 1502871393｜BG2 1727278168｜Pivot 1073226719｜Hard Fork 1528594034｜Unhedged 1691284824｜Acquired 1050462261｜20VC 958230465｜Invest Like the Best 1154105909｜Capital Allocators 1223764016｜Masters in Business 730188152｜No Priors 1668002688｜Lenny's 1627920305｜Lex Fridman 1434243584｜Dwarkesh 1516093381｜Latent Space 1674008350｜Odd Lots 1056200096｜Macro Voices 1079172742｜Market Huddle 1444520320｜Bloomberg Surveillance 296237493｜GS Exchanges 948913991

**時間窗口**（台北時間）：週二至週五抓過去 26 小時發布的集數；週一抓過去 74 小時（涵蓋週末）。

---

## 2. YouTube 字幕操作要領（已實測）

1. `tabs_context_mcp{createIfEmpty:true}` → `navigate` 到頻道 `/videos`
2. 點開目標影片 → 按 `k` 暫停
3. 點描述區「⋯更多內容」展開
4. `find`「顯示轉錄稿」按鈕（在**展開後描述的最底部**，不是側欄）
5. 點擊後右側開啟「字幕記錄」面板，等 5 秒讓它載入
6. `browser_batch` 呼叫 `get_page_text` 並帶 `max_chars: 250000`
7. 擷取「影片相關資訊」／「字幕記錄」與「英文 (自動產生)」之間的段落即為逐字稿；移除時間戳行後合併

每集在 Chrome 上最多嘗試 8 分鐘，失敗就走退援。

**退援規則**：若 Chrome／桌面裝置不可用，B 類節目改以 Apple 頁面節目說明＋WebSearch 相關報導撰寫約 500 字精簡摘要，並在該集 `source` 欄標註「⚠︎ 全文摘譯待補（執行當下無法連線使用者電腦）」。

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

1. 產生當日 `data/YYYY-MM-DD.json` 與更新後的 `data/index.json`（在雲端沙箱寫好）。
2. `SendUserFile` 送出當日 Word 報告。
3. **寫入使用者 Mac 的 repo**：`mcp__remote-devices__device_commit_files`，寫到
   - `~/podcast-knowledge-digest/data/YYYY-MM-DD.json`
   - `~/podcast-knowledge-digest/data/index.json`
   （`force: true`）
4. 之後**不需手動 push**：Mac 上的 launchd 背景程式 `com.kenny.dashpush`（每 180 秒）會自動 `git add`＋`commit`＋`push`；GitHub Actions 再自動部署到 GitHub Pages。

**重要操作禁忌**：不要用 `device_bash` 跑任何 `git` 指令（含 `git status`）。device_bash 是無網路的沙箱、且不能刪檔，跑 git 會留下 `.git/index.lock` 鎖檔擋住背景推送。只用 `cat`／`ls`／`grep` 等唯讀指令檢查狀態即可。

---

## 6. 基礎設施備忘

- **Repo（本機）**：`~/podcast-knowledge-digest`（放在家目錄下，不要放進 `~/Documents`，macOS TCC 會擋背景程式存取受保護資料夾）。
- **GitHub**：`GunDamnBoy/podcast-knowledge-digest`，Public，GitHub Pages（Source ＝ GitHub Actions）。
- **推送認證**：remote URL 內嵌 fine-grained PAT（只授權此 repo、Contents 讀寫），存於本機 `.git/config`。換 token：產新 PAT →
  `git -C ~/podcast-knowledge-digest remote set-url origin https://<新PAT>@github.com/GunDamnBoy/podcast-knowledge-digest.git` → 撤舊。
- **背景推送腳本**：`~/.dashpush/auto-push.sh`，**多 repo 版**，會依序處理 `advisory-knowledge-hub` 與 `podcast-knowledge-digest`；由 launchd agent `com.kenny.dashpush` 每 180 秒觸發。
- **模式限制備忘**：互動／排程階段能讀 Chrome，但雲端不能直接推 GitHub；因此一律由本機背景程式負責推送。
- **連線資料夾（重要）**：`device_commit_files` 只能寫入「已連線的資料夾」。排程是無人值守執行，當下沒有人能按核准對話框，因此 `~/podcast-knowledge-digest` 必須事先在 Claude 桌面 App 以「Add folder」加為連線資料夾。若某次執行寫不進去（工具回報未連線），退援作法：照常交付 Word 報告，並把當日的 `data/YYYY-MM-DD.json` 與更新後的 `data/index.json` 用 `SendUserFile` 送到對話中，於結尾說明需要手動放進 repo 的 `data/` 目錄，其餘由背景程式自動完成。

---

## 7. 合規與語氣

- 全站 `robots.txt` 與 `<meta name="robots" content="noindex, nofollow">`，定位為個人知識管理站，不做公開發行。
- 每集保留來源標註與原文連結，鼓勵前往原始節目收聽。
- 摘譯為濃縮中譯、非逐字轉載；付費來源（FT、Bloomberg 等）尤其只做重點濃縮並附連結。
- 語氣：繁體中文（台灣慣用語）、專業財經研究腔、全形標點；有觀點但中立，明確標示非投資建議。
