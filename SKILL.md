---
name: ppt-to-md
description: |
  學術／藥廠簡報（.pptx）忠實轉 Markdown 的機械式抽取管線，目標是「盡量真實還原簡報內容」。
  當使用者要把投影片轉成 markdown、且在意「保留原始內容、不失真」時，立即啟動此 skill。
  網頁轉檔工具吃不下的大檔（動輒 25~50MB，內嵌圖片撐大），本 skill 在本機處理、無大小限制。

  主要啟動：丟 .pptx ＋自然語言，或用 /ppt 明確召喚。
  觸發情境：
  - `/ppt`（明確召喚；雲端 Chat 適用，Claude Code 因斜線撞 CLI 建議改用自然語言）
  - 「把這份簡報/投影片/deck 轉成 markdown」「pptx 轉 markdown」「用 PPT_to_MD 轉」
  - 「盡量真實還原這份學術簡報的內容」
  - 「這份 pptx 太大網頁工具吃不下，幫我在本機轉」
  - 「投影片裡的表格/圖表數據也要保留」「講者備註也要一起抽」
  - 提供 .pptx（尤其含講者備註/圖表的學術簡報）並要求轉檔或整理成可讀的 markdown
---

# ppt-to-md — 學術簡報忠實還原 Skill v2

## 用途與定位

把一份學術／藥廠 `.pptx`，**盡量真實地**還原成 Markdown。只做「簡報本身有的內容」，
**不做論點考證、不查外部文獻**（那是之後另一個步驟，見 `later-verification-step/`）。

**核心心法：機械可驗證的才做；一切原文逐字；不猜、不填補、不查外部。**

## 啟動方式

- **`/ppt`**（軟指令，明確召喚）：可單獨輸入，或 `/ppt` 後接說明；通常直接連同 .pptx 一起丟。
  雲端 Chat 直接可用；Claude Code 因斜線會撞 CLI 內建指令，該環境改用自然語言。
- **自然語言**：直接丟 .pptx 並說「忠實轉 markdown / 盡量還原這份簡報」即可觸發。
- 兩種方式都需要**能執行程式碼的環境**（雲端對話、Claude Code、桌面版）以跑 `scripts/extract.py`。

常用參數：`--frontmatter`（加 YAML 骨架，進 Obsidian 用）、`--no-mermaid`（關閉 Mermaid 附圖）。

---

## 第一階段：機械抽取（`scripts/extract.py`）

不靠提示詞、不查外部、可重現。在有 code execution 的環境直接跑：

```bash
python scripts/extract.py <輸入.pptx> [輸出.md] [--no-mermaid] [--frontmatter]
```

自動完成：

| 項目 | 處理方式 |
|------|----------|
| 投影片本文 | 依 shape tree 順序走，保留閱讀順序、逐字不改寫 |
| 表格 | 還原成 Markdown 表格，保留行列結構 |
| 合併儲存格 | **一律留白，不填補、不推論** |
| **原生圖表** | 從 `ppt/charts` 抽底層數據還原成數據表（**無損**）；另附 Mermaid `xychart-beta` 長條圖（Obsidian 1.4+ 原生渲染、無需圖檔；表格為準，圖為附加，可用 `--no-mermaid` 關閉）|
| 視覺強調還原 | 字級明顯大於內文者標為**粗體**（保留原檔重點層次；依 `sz` 字級機械判定，非語意判斷）|
| 講者備註 | 透過 rels 正確對應投影片（notesSlide 編號 ≠ 投影片編號）|
| 備註分級 | 跨頁重複＝「制式引註」；唯一＝「本頁專屬口述論點」|
| 圖片出處字樣 | 抽出 deck 自標的出處（如「Adapted from…」）逐字保留，**僅標示不查證** |
| YAML frontmatter（選用）| `--frontmatter` 於檔頭產出 vault schema 骨架（type/domain/stage/aliases 留白供下游流程補填；date/source 機械預填）|
| 雜訊清理 | 清掉純頁碼與「Present Slide」殘留；本文孤立頁碼剝除；圖表座標軸刻度（連續 ≥4 純數字）折疊為一行；跨頁重複的制式引註全文只顯示一次、後續頁指回首次出現處（保守設定，單一數字 callout 與非頁碼數字不受影響）|

**舊版 `.ppt` 不支援**，先轉檔：`soffice --headless --convert-to pptx 你的檔案.ppt`

**若無 code execution**：請使用者上傳 .pptx，Claude 在本機容器代跑此腳本。

---

## 圖的處理原則（本 skill 只做前兩者，第三者屬之後步驟）

分析圖有三種來源，處理方式不同：

1. **原生圖表**（PowerPoint 內建圖表）→ 底層數據還在 XML，`extract.py` **無損抽出成數據表**。
   這是最理想情況：圖裡的數字精確還原，不必讀像素、不會失真。
2. **貼上的點陣圖**（森林圖、KM 曲線截圖等）→ 像素無法讀數。
   本 skill 保留其**周邊文字、圖說、以及 deck 自標的出處字樣**（逐字），並標明該處為圖片。
   如需人工複核，可將該頁 rasterize 成 PNG 另存（見下「圖片降級保留」）。
3. **查證圖的出處與重點**（PubMed／Consensus）→ **這是之後的步驟，不在本 skill 核心**。
   相關 SOP 與「坐實帳」schema 暫存於 `later-verification-step/`。

### 圖片降級保留（選用，供人工複核）

對點陣圖頁，可用 LibreOffice 把整頁轉圖，連結於 markdown 供人工對照（不自動執行）：

```bash
soffice --headless --convert-to pdf 輸入.pptx
pdftoppm -jpeg -r 150 輸入.pdf slide
```

---

## 第二階段（選用）：忠實整理（`prompts/stage2-argue.md`）

把第一階段的 markdown 當輸入，套用 `prompts/stage2-argue.md`，做**有界的忠實整理**——
三層分離（原文層／結構層／延伸層 🔸）、hedge 全保留、數字照抄、備註分級採信。
**同樣不查外部文獻**。是否要跑由使用者決定；只需要乾淨 markdown 時，第一階段產出即可直接用。

---

## 人工核對（human holdout，不可省）

- 合併儲存格留白處各屬哪一組（表格最左欄尤其常見）。
- 並列/對照視覺區塊被攤平後，順序是否被誤讀成論證先後。
- 點陣圖頁：數據只能回看原圖，markdown 不會有其數值（原生圖表則已還原）。

---

## 設計理由（為什麼是這個架構）

從真實藥廠學術簡報實測校準。內容失真的幾個坑，本 skill 逐一擋掉：

1. **講者備註編號不對應投影片編號**（`notesSlide14`→第 18 頁）→ 讀 rels 對回去，程式保證，不靠猜。
2. **表格壓平＝掉結構**（16×7 比較表線性化後數字錯置）→ 程式還原網格。
3. **原生圖表數據藏在 `ppt/charts`、不在投影片 XML** → 若不特別抽取會整批遺失；本版補上無損抽取。
4. **備註混著跨頁複製的制式引註** → 用「是否跨頁重複」自動分級，機械可判。

機械能保證的交給程式；需要判斷立場、查證文獻的（論點考證）**留到之後的步驟**，不混進忠實還原。

---

## 檔案結構

```
ppt-to-md/
├── SKILL.md                       # 本檔
├── scripts/
│   └── extract.py                 # 第一階段：機械抽取（含原生圖表；可獨立執行，僅標準庫）
├── prompts/
│   └── stage2-argue.md            # 第二階段（選用）：忠實整理提示詞
└── later-verification-step/       # 【之後的步驟】論點考證，非核心，暫存待用
    ├── README.md
    ├── stage2-verify.md           # PubMed/Consensus 核實 SOP + 鎖定坐實帳 schema
    └── worked-example.md          # 坐實帳範例（虛構教學案例）
```

## 相依

- Python 3.10+（僅標準庫：zipfile / xml.etree，無需安裝）
- 舊版 .ppt 轉檔、點陣圖 rasterize 需 LibreOffice（`soffice`）與 Poppler（`pdftoppm`）
