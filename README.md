# 📑 PPT-to-MD

## 🎯 專案簡介 (About The Project)

這是一個把 PowerPoint 簡報（.pptx）**原封不動**轉成 Markdown 純文字的小工具，專為學術與醫藥簡報設計。它的原則很簡單：簡報裡寫什麼就抄什麼——不猜測、不腦補、不改寫，連圖表裡藏的數據都幫你完整挖出來。

This is a small tool that converts PowerPoint files (.pptx) into plain Markdown **exactly as they are**, built for academic and medical decks. Its rule is simple: copy only what the deck actually says — no guessing, no making things up, no rewriting — and it even digs out the data hidden inside charts for you.

## ✨ 最新更新 (What's New)

- 🆕 **v2 正式發布**：原生圖表的底層數據現在可以「無損」抽出，變成清楚的數據表格，再也不會轉完檔就消失。
- 📊 **附贈 Mermaid 圖**：抽出的圖表數據會順便畫成長條圖，在 Obsidian 裡直接顯示，不需要另外存圖片檔。
- 🏷️ **新增 `--frontmatter` 選項**：可以在檔頭自動加上 YAML 欄位，方便丟進 Obsidian 等筆記軟體管理。
- 🧹 **更聰明的雜訊清理**：自動去掉頁碼、重複的制式引註、圖表座標軸刻度等干擾閱讀的殘留文字。

- 🆕 **v2 released**: the raw data behind native charts is now extracted **losslessly** into clean data tables — it no longer vanishes during conversion.
- 📊 **Bonus Mermaid charts**: extracted chart data is also rendered as bar charts that display directly in Obsidian, no image files needed.
- 🏷️ **New `--frontmatter` option**: automatically adds YAML fields at the top of the file, handy for note apps like Obsidian.
- 🧹 **Smarter noise cleanup**: automatically removes page numbers, repeated boilerplate citations, chart axis ticks, and other leftovers that clutter reading.

## 💡 為什麼要用這個專案？ (Why Choose This?)

1. **忠實不失真** 🔒：一般轉檔工具常把表格壓平（數字跑錯格）、把圖表數據弄丟、把講者備註配錯頁。本工具針對這三大坑逐一防堵，還原不了的就誠實留白，絕不用「看起來很順」的假內容補滿。
2. **零安裝負擔** 🪶：只需要 Python，而且只用內建標準庫——不用 pip 安裝任何套件，下載即用。
3. **大檔也吃得下** 💪：學術簡報常因內嵌圖片肥到 25–50MB，網頁轉檔工具直接拒收；本工具在你自己的電腦上跑，沒有大小限制。

1. **Faithful, no distortion** 🔒: generic converters often flatten tables (numbers land in the wrong cells), lose chart data, and attach speaker notes to the wrong slides. This tool blocks all three failure modes, and where recovery is impossible it leaves an honest blank instead of plausible-looking filler.
2. **Zero installation burden** 🪶: all you need is Python, and it uses only the built-in standard library — no pip packages, download and run.
3. **Handles huge files** 💪: academic decks easily hit 25–50 MB because of embedded images, which web converters reject; this tool runs on your own machine with no size limit.

## 🚀 快速開始 (Getting Started)

只要三步就能開始用：

You are three steps away:

1. **確認 Python**：需要 Python 3.10 以上（大多數電腦裝好 Python 就符合）。
   **Check Python**: you need Python 3.10 or newer (any recent Python install is fine).

   ```bash
   python --version
   ```

2. **下載專案**：
   **Download the project**:

   ```bash
   git clone https://github.com/kau10082/PPT-to-MD.git
   cd PPT-to-MD
   ```

3. **直接執行**（不用安裝任何套件！）：
   **Run it directly** (nothing to install!):

   ```bash
   python scripts/extract.py 你的簡報.pptx
   ```

> ⚠️ 只支援 `.pptx`。舊格式 `.ppt` 請先用 LibreOffice 轉檔：`soffice --headless --convert-to pptx 你的檔案.ppt`
>
> ⚠️ Only `.pptx` is supported. For the legacy `.ppt` format, convert first with LibreOffice: `soffice --headless --convert-to pptx your-file.ppt`

## 📖 基本使用方式 (Usage)

最簡單的用法：一個輸入檔，跑完會在同資料夾產生同名的 `.md` 檔。

The simplest usage: give it one input file, and a `.md` file with the same name appears in the same folder.

```bash
python scripts/extract.py my-deck.pptx
```

執行完會看到摘要報告，告訴你抽出了多少東西：

When it finishes you get a summary report of what was extracted:

```
[ppt-to-md] 完成：my-deck.md
  投影片 33 頁 ｜ 表格 5 張 ｜ 原生圖表 3 張 ｜ 本頁專屬口述 12 則 ｜ 制式引註 8 則 ｜ 圖片出處字樣 6 頁
  雜訊清理：折疊座標軸刻度 2 處 ｜ 剝除頁碼 15 處
```

常用選項：

Common options:

| 選項 / Option | 作用 / What it does |
|---|---|
| `--no-mermaid` | 不附 Mermaid 長條圖，只留數據表格 / Skip the Mermaid bar charts, keep only data tables |
| `--frontmatter` | 檔頭加 YAML 欄位（進 Obsidian 用）/ Add YAML fields at the top (for Obsidian) |

## 📁 目錄結構 (Repository Structure)

```
PPT-to-MD/
├── README.md                      # 本說明檔 / this file
├── LICENSE                        # MIT 授權條款 / MIT license
├── SKILL.md                       # 給 AI 助手看的完整操作說明 / full instructions for AI assistants
├── scripts/
│   └── extract.py                 # ⭐ 核心轉檔程式，一個檔案搞定 / the core converter, one single file
├── prompts/
│   └── stage2-argue.md            # 選用：給 LLM 的「忠實整理」提示詞 / optional: LLM prompt for faithful restructuring
└── later-verification-step/       # 選用：之後做「文獻查證」的資料 / optional: materials for later citation verification
    ├── README.md                  # 這個資料夾的說明 / what this folder is about
    ├── stage2-verify.md           # 用 PubMed 查證圖表出處的流程 / workflow for verifying figures via PubMed
    └── worked-example.md          # 虛構教學範例 / a fictional worked example
```

- **`scripts/`**：主角在這裡。`extract.py` 就是整個轉檔工具，不依賴其他檔案，複製走也能單獨用。
  **`scripts/`**: the star of the show. `extract.py` is the whole converter — it has no dependencies on other files, so you can even copy it out and use it alone.
- **`prompts/`**：轉完檔之後，如果想請 AI 幫忙把內容整理成論點清單，用這裡的提示詞（會嚴格要求 AI 不得腦補）。
  **`prompts/`**: after conversion, if you want an AI to organize the content into a list of claims, use the prompt here (it strictly forbids the AI from making things up).
- **`later-verification-step/`**：進階玩法。教你怎麼用 PubMed 查證簡報裡的圖表數據是不是真的有文獻依據。非必要，不用也完全沒關係。
  **`later-verification-step/`**: advanced usage. Shows how to verify whether the numbers in a deck's figures are actually backed by published literature, using PubMed. Entirely optional — skipping it is perfectly fine.

## 🤝 貢獻指南 (Contributing)

非常歡迎任何形式的幫忙！不管你是發現了 bug、有新點子，還是想改進程式碼，都很感謝你願意花時間。

Help of any kind is very welcome! Whether you found a bug, have an idea, or want to improve the code — thank you for taking the time.

- 🐛 **回報問題**：到 [Issues](https://github.com/kau10082/PPT-to-MD/issues) 開一個新 issue，描述你遇到的狀況（如果能附上出問題的簡報特徵，例如「含合併儲存格的表格」，會超有幫助）。
  **Report a problem**: open a new issue on the [Issues](https://github.com/kau10082/PPT-to-MD/issues) page describing what happened (describing the deck feature that triggered it — e.g. "a table with merged cells" — helps a lot).
- 🔧 **修改程式碼**：
  **Change the code**:
  1. Fork 這個專案到你的帳號 / Fork this repo to your account
  2. 開一個新分支：`git checkout -b my-fix` / Create a new branch: `git checkout -b my-fix`
  3. 修改並提交 / Make your changes and commit
  4. 發 Pull Request 回來，簡單說明改了什麼、為什麼 / Open a Pull Request explaining what you changed and why

> 💬 提醒：本專案的核心精神是「忠實還原、不腦補」。新功能若會讓輸出偏離原始簡報內容（例如自動填補空白儲存格），原則上不會被接受喔。
>
> 💬 Note: the soul of this project is "faithful extraction, no fabrication." Features that make the output drift from the original deck (e.g. auto-filling merged cells) will generally not be accepted.

## 📜 授權條款 (License)

本專案採用 **MIT 授權**——你可以自由使用、修改、散布，甚至用於商業用途，唯一的要求是保留原始的授權與著作權聲明（標示出處）。完整條文請見 [LICENSE](LICENSE)。

This project is released under the **MIT License** — you are free to use, modify, and distribute it, even commercially. The only requirement is to keep the original license and copyright notice (credit the source). See [LICENSE](LICENSE) for the full text.
