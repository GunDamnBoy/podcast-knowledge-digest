#!/usr/bin/env python3
"""全庫實測：時間戳回跳與重複，在正常逐字稿裡到底有多常見？

**這支腳本只讀不寫，跑完可以直接刪。** 它存在的唯一目的，是回答
`MODIFY.md`「新增檢查」那條規矩問的問題——**正常情況會不會也觸發？**

背景：2026-08-18 的 20VC 有兩處時間戳跳躍與一段重複，`check_timestamps()`
完全沒報。根因是 `podfetch.py:676` 的 `sorted({...})` 在任何判斷之前就把
順序與重複同時丟掉，所以「回跳」這個形態結構上看不見。

要不要補一道單調性檢查，取決於它在全庫的誤報率：
  - 報 ≤ 全庫一成  → 低雜訊訊號，**單訊號就夠**，可以直接補進 check_timestamps()
  - 報 > 全庫一成  → 雜訊，要退回「兩個獨立訊號同時成立」的設計

用法（在 Mac 上跑，沙箱看不到 ~/podcast-transcripts）：
    python3 ~/podcast-knowledge-digest/measure-ts-monotonic.py
"""
import glob
import os
import re
from collections import Counter

TS = re.compile(r"^\s*\[(?:(\d+):)?(\d{1,2}):(\d{2})\]", re.M)
ROOT = os.path.expanduser("~/podcast-transcripts")

# 回跳容忍值：相鄰時間戳倒退超過這麼多秒才算數。
# 小幅倒退可能只是同一分鐘內的排版差異，不該當成異常。
TOLERANCE = 5


def scan(path):
    """回傳 (回跳次數, 最大回跳秒數, 重複時間戳個數, 總時間戳數)。

    **關鍵：這裡刻意不排序、不去重**——順序與重複正是要量的東西，
    而 podfetch 的 check_timestamps() 就是在這一步把它們丟掉的。
    """
    text = open(path, encoding="utf-8", errors="replace").read()
    secs = [int(h or 0) * 3600 + int(m) * 60 + int(s)
            for h, m, s in TS.findall(text)]
    if len(secs) < 5:
        return None
    backs = [a - b for a, b in zip(secs, secs[1:]) if a - b > TOLERANCE]
    dup = sum(c - 1 for c in Counter(secs).values() if c > 1)
    return len(backs), (max(backs) if backs else 0), dup, len(secs)


rows = []
for f in sorted(glob.glob(os.path.join(ROOT, "*", "*.md"))):
    r = scan(f)
    if r is None:
        continue
    n_back, max_back, dup, total = r
    rows.append((os.path.basename(os.path.dirname(f)),
                 os.path.basename(f)[:44], n_back, max_back, dup, total))

if not rows:
    print("找不到逐字稿。確認路徑：%s" % ROOT)
    raise SystemExit(1)

flagged = [r for r in rows if r[2] > 0]
dup_only = [r for r in rows if r[2] == 0 and r[4] > 0]

print("全庫 %d 集（相異時間戳 ≥5 的才計入）" % len(rows))
print("──────────────────────────────────────────────")
print("有回跳的集數：%d 集（%.0f%%）" % (len(flagged), 100 * len(flagged) / len(rows)))
print("只有重複、無回跳：%d 集（%.0f%%）" % (len(dup_only), 100 * len(dup_only) / len(rows)))
print()

if flagged:
    print("=== 回跳明細（依最大回跳秒數排序）===")
    print("%-12s %-46s %5s %9s %6s %6s" % ("日期", "檔名", "回跳次", "最大回跳", "重複", "總戳數"))
    for d, n, nb, mb, dp, tt in sorted(flagged, key=lambda r: -r[3]):
        print("%-12s %-46s %5d %7d秒 %6d %6d" % (d, n, nb, mb, dp, tt))
    print()

print("=== 判讀 ===")
pct = 100 * len(flagged) / len(rows)
if pct <= 10:
    print("回跳率 %.0f%% ≤ 10%%：**低雜訊訊號，單訊號就夠**。" % pct)
    print("可以補進 check_timestamps()，門檻建議取上面明細裡「最大回跳秒數」的")
    print("自然斷點（正常集數應該完全是 0 次，任何非零都值得出聲）。")
else:
    print("回跳率 %.0f%% > 10%%：**雜訊太高，不要當獨立判準**。" % pct)
    print("要嘛提高 TOLERANCE、要嘛改成雙訊號（例如「回跳」＋「該段內容重複」）。")
    print("這正是 2026-08-07 講者檢查初版『九集報八集』與時間軸初版")
    print("『72 集報 15 集』踩過的同一種失敗。")
