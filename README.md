# PPT-to-MD

把學術／藥廠簡報（.pptx）**忠實**轉成 Markdown 的機械式抽取管線。目標只有一個：盡量真實還原簡報本身的內容——不猜、不填補、不改寫、不查外部資料。

A mechanical extraction pipeline that **faithfully** converts academic / pharma slide decks (.pptx) into Markdown. One goal only: reproduce what the deck actually says — no guessing, no gap-filling, no rewriting, no external lookups.

## 為什麼需要它 / Why

一般轉檔工具處理學術簡報時常見三種失真：表格被壓平導致數字錯位、圖表底層數據整批遺失、講者備註對應到錯誤的頁碼。對醫學內容來說，這些失真是不可接受的。本工具用「機械可驗證」的方式逐一擋掉這些坑，還原不了的就誠實留白，絕不用看起來通順的內容補滿。

Generic converters tend to distort academic decks in three ways: tables get flattened and numbers land in the wrong cells, the data behind native charts is silently dropped, and speaker notes get attached to the wrong slides. For medical content these distortions are unacceptable. This tool blocks each failure mode with mechanically verifiable logic, and where faithful recovery is impossible it leaves an honest blank instead of plausible-sounding filler.

另一個現實理由：內嵌大量圖片的簡報動輒 25–50MB，網頁轉檔工具經常吃不下。本工具在本機執行，沒有檔案大小限制。

A practical reason too: image-heavy decks easily reach 25–50 MB, beyond what web converters accept. This tool runs locally with no size limit.

## 它做什麼 / What it does

| 項目 / Item | 處理方式 / Behavior |
|---|---|
| 投影片本文 / Slide text | 依 shape tree 順序逐字抽取，不改寫 / Extracted verbatim in shape-tree order, never rewritten |
| 表格 / Tables | 還原行列結構；合併儲存格一律留白不填補 / Grid structure restored; merged cells left blank, never inferred |
| 原生圖表 / Native charts | 從 `ppt/charts` XML 無損抽出底層數據成數據表，另附 Mermaid 長條圖 / Underlying data extracted losslessly from `ppt/charts` XML into a data table, plus an optional Mermaid bar chart |
| 講者備註 / Speaker notes | 透過 rels 對應正確頁碼（備註檔編號 ≠ 投影片編號）/ Mapped to the correct slide via rels (notes-file numbering ≠ slide numbering) |
| 備註分級 / Note triage | 跨頁重複＝制式引註；唯一＝本頁專屬口述論點 / Repeated across slides = boilerplate citation; unique = slide-specific spoken point |
| 圖片出處 / Figure provenance | deck 自標的出處字樣（如 "Adapted from…"）逐字保留，僅標示不查證 / Deck-stated attributions (e.g. "Adapted from…") kept verbatim — flagged, not verified |
| 雜訊清理 / Noise cleanup | 頁碼、介面殘留、座標軸刻度串折疊，皆採保守規則 / Page numbers, PowerPoint UI leftovers and axis-tick runs collapsed, all under conservative rules |

## 快速開始 / Quick start

只需要 Python 3.10+，僅用標準庫、無需安裝任何套件。

Requires only Python 3.10+. Standard library only — nothing to install.

```bash
python scripts/extract.py 你的簡報.pptx                # 基本用法 / basic usage
python scripts/extract.py deck.pptx out.md            # 指定輸出 / custom output path
python scripts/extract.py deck.pptx --no-mermaid      # 不附 Mermaid 圖 / skip Mermaid charts
python scripts/extract.py deck.pptx --frontmatter     # 加 YAML frontmatter（進 Obsidian 用）/ add YAML frontmatter (for Obsidian)
```

舊版 `.ppt` 不支援，請先用 LibreOffice 轉檔 / Legacy `.ppt` is not supported — convert it first with LibreOffice:

```bash
soffice --headless --convert-to pptx your-file.ppt
```

## 管線分段 / Pipeline stages

1. **機械抽取（[scripts/extract.py](scripts/extract.py)）**：純程式、可重現、不靠提示詞。上表的一切都在這步完成。
   **Mechanical extraction ([scripts/extract.py](scripts/extract.py))**: pure code, reproducible, no prompts involved. Everything in the table above happens here.
2. **忠實整理（選用，[prompts/stage2-argue.md](prompts/stage2-argue.md)）**：給 LLM 的提示詞，把第一階段的 markdown 整理成講者論點清單——不確定語氣全保留、數字照抄、制式引註不得當論點。同樣不查外部資料。
   **Faithful restructuring (optional, [prompts/stage2-argue.md](prompts/stage2-argue.md))**: an LLM prompt that turns the stage-1 markdown into a list of the speaker's claims — hedging preserved, numbers copied exactly, boilerplate citations never treated as arguments. Still no external lookups.
3. **論點考證（暫存，[later-verification-step/](later-verification-step/)）**：之後才做的獨立步驟——用 PubMed／Consensus 核實圖表出處與數據的 SOP 與虛構教學範例。不屬於核心流程。
   **Claim verification (parked, [later-verification-step/](later-verification-step/))**: a separate, later step — an SOP plus a fictional worked example for verifying figure provenance and data against PubMed / Consensus. Not part of the core pipeline.

## 已知限制與人工核對 / Known limits & human checks

- 貼上的點陣圖（截圖式分析圖）無法讀出數值；本工具只保留其周邊文字與出處字樣。原生圖表則可無損還原。
  Pasted bitmap figures (screenshot-style plots) cannot yield numbers; only their surrounding text and attributions are kept. Native charts, by contrast, are recovered losslessly.
- 版面上並列／對照的視覺區塊會被攤平成線性順序，閱讀時需回看原檔，確認順序不被誤讀成論證先後。
  Side-by-side visual blocks get flattened into linear order — check the original deck before reading that order as argument structure.
- 表格空白格代表原檔的合併儲存格，各屬哪一組需人工判讀。
  Blank table cells mean merged cells in the source; which group each belongs to requires human judgment.

## 授權 / License

MIT — 見 [LICENSE](LICENSE) / see [LICENSE](LICENSE).
