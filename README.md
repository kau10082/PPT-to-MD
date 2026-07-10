# PPT-to-MD

## 1. 專案簡介 (About The Project)

這是一個把 PowerPoint 簡報（.pptx）**原封不動**轉成 Markdown 純文字的小工具，專為學術與醫藥簡報設計。它的原則很簡單：簡報裡寫什麼就抄什麼——不猜測、不腦補、不改寫，連圖表裡藏的數據都幫你完整挖出來。

This is a small tool that converts PowerPoint files (.pptx) into plain Markdown **exactly as they are**, built for academic and medical decks. Its rule is simple: copy only what the deck actually says — no guessing, no making things up, no rewriting — and it even digs out the data hidden inside charts for you.

## 2. 為什麼要用這個專案？ (Why Choose This?)

GitHub 上已經有不少 pptx 轉 Markdown 的工具（例如 [pptx2md](https://github.com/ssine/pptx2md)、微軟的 [MarkItDown](https://github.com/microsoft/markitdown)），為什麼還需要這一個？因為它們的目標是「轉得出來」，而本專案的目標是「**轉得忠實**」。比較如下：

There are already several pptx-to-Markdown tools on GitHub (e.g. [pptx2md](https://github.com/ssine/pptx2md) and Microsoft's [MarkItDown](https://github.com/microsoft/markitdown)), so why this one? Because their goal is "gets converted", while this project's goal is "**converted faithfully**". Here is the comparison:

| 比較項目 / Feature | 本專案 / This project | pptx2md | MarkItDown | 網頁轉檔工具 / Web converters |
|---|---|---|---|---|
| 原生圖表的底層數據 / Native chart data | **無損抽出成數據表 / Lossless data tables** | 不支援 / No | 不支援 / No | 不支援 / No |
| 講者備註 / Speaker notes | **預設抽取，且頁碼保證對應正確 / Extracted by default, slide mapping guaranteed** | 預設不抽 / Not by default | 有抽但不分類 / Extracted, no triage | 多半不抽 / Usually no |
| 備註自動分類 / Notes triage | **區分「制式引註」與「本頁專屬口述」/ Boilerplate vs. slide-specific** | 無 / No | 無 / No | 無 / No |
| 合併儲存格 / Merged table cells | **誠實留白，不填假值 / Honest blanks, no filler** | 依區塊順序攤平 / Flattened by block order | 攤平 / Flattened | 常錯置 / Often scrambled |
| 安裝需求 / Installation | **零安裝，僅 Python 標準庫 / Zero install, stdlib only** | 需 pip 安裝 / pip required | 需 pip 安裝 / pip required | 免裝但有大小限制 / No install but size-limited |
| 大檔（25–50MB）/ Huge files (25–50 MB) | **本機執行，無上限 / Runs locally, no limit** | 可 / OK | 可 / OK | 常直接拒收 / Often rejected |
| 當 Claude skill 用 / Works as a Claude skill | **是，用講的就能轉 / Yes, just ask in plain words** | 否 / No | 否 / No | 否 / No |

一句話總結三大賣點：

The three selling points in one sentence each:

1. **忠實不失真**：一般轉檔工具常把表格壓平（數字跑錯格）、把圖表數據弄丟、把講者備註配錯頁。本工具針對這三大坑逐一防堵，還原不了的就誠實留白，絕不用「看起來很順」的假內容補滿。
   **Faithful, no distortion**: generic converters often flatten tables (numbers land in the wrong cells), lose chart data, and attach speaker notes to the wrong slides. This tool blocks all three failure modes, and where recovery is impossible it leaves an honest blank instead of plausible-looking filler.
2. **零安裝負擔**：只需要 Python，而且只用內建標準庫——不用 pip 安裝任何套件，下載即用。
   **Zero installation burden**: all you need is Python, and it uses only the built-in standard library — no pip packages, download and run.
3. **大檔也吃得下**：學術簡報常因內嵌圖片肥到 25–50MB，網頁轉檔工具直接拒收；本工具在你自己的電腦上跑，沒有大小限制。
   **Handles huge files**: academic decks easily hit 25–50 MB because of embedded images, which web converters reject; this tool runs on your own machine with no size limit.

## 3. 最新更新 (What's New)

- **v2 正式發布**：原生圖表的底層數據現在可以「無損」抽出，變成清楚的數據表格，再也不會轉完檔就消失。
- **附贈 Mermaid 圖**：抽出的圖表數據會順便畫成長條圖，在 Obsidian 裡直接顯示，不需要另外存圖片檔。
- **新增 `--frontmatter` 選項**：可以在檔頭自動加上 YAML 欄位，方便丟進 Obsidian 等筆記軟體管理。
- **更聰明的雜訊清理**：自動去掉頁碼、重複的制式引註、圖表座標軸刻度等干擾閱讀的殘留文字。

- **v2 released**: the raw data behind native charts is now extracted **losslessly** into clean data tables — it no longer vanishes during conversion.
- **Bonus Mermaid charts**: extracted chart data is also rendered as bar charts that display directly in Obsidian, no image files needed.
- **New `--frontmatter` option**: automatically adds YAML fields at the top of the file, handy for note apps like Obsidian.
- **Smarter noise cleanup**: automatically removes page numbers, repeated boilerplate citations, chart axis ticks, and other leftovers that clutter reading.

## 4. 快速開始 (Getting Started)

本專案的設計定位就是 **Claude 的 skill（技能）**：安裝一次，之後在對話裡丟簡報、用講的就能轉檔。安裝只要三步：

This project is designed to be a **Claude skill**: install it once, then just drop a deck into a chat and ask. Installation takes three steps:

1. **下載專案**：點本頁綠色的 **Code → Download ZIP**（或 `git clone`），解壓縮後把資料夾**改名為 `ppt-to-md`**。
   **Download the project**: click the green **Code → Download ZIP** button on this page (or `git clone`), unzip it, and **rename the folder to `ppt-to-md`**.

2. **壓縮成 ZIP**：把整個 `ppt-to-md` 資料夾壓縮成一個 ZIP 檔（ZIP 打開後第一層就是 `ppt-to-md/`，裡面直接看得到 `SKILL.md`）。
   **Zip it up**: compress the whole `ppt-to-md` folder into a ZIP (opening the ZIP should show `ppt-to-md/` at the top level, with `SKILL.md` right inside).

3. **上傳到 Claude**：到 claude.ai 的 **Settings → Capabilities**，上傳這個 ZIP 並啟用。完成！
   **Upload to Claude**: go to **Settings → Capabilities** on claude.ai, upload the ZIP, and enable it. Done!

> **Claude Code 使用者**更簡單：不用壓 ZIP，直接把資料夾放到 `~/.claude/skills/ppt-to-md` 就裝好了。
>
> **Claude Code users** have it even easier: no ZIP needed — just place the folder at `~/.claude/skills/ppt-to-md` and you're set.

> 注意：使用時需要「能執行程式碼」的環境（claude.ai 對話、Claude Code 或桌面版），因為 skill 背後會替你執行轉檔程式。
>
> Note: usage requires a code-execution environment (a claude.ai chat, Claude Code, or the desktop app), because the skill runs the converter script for you behind the scenes.

## 5. 基本使用方式 (Usage)

安裝好之後，在對話裡**丟上一個 .pptx 檔**，然後用講的就行。兩種觸發方式：

Once installed, **drop a .pptx file** into a chat and just ask. Two ways to trigger it:

- 輸入 **`/ppt`** 指令（可以只打這三個字，也可以後面接補充說明），或
  Type the **`/ppt`** command (on its own, or followed by extra instructions), or
- 直接用自然語言說，例如：
  Just say it in plain words, for example:
  > 「把這份簡報忠實轉成 markdown」
  > 「盡量真實還原這份簡報的內容」
  > 「這份 pptx 太大網頁工具吃不下，幫我在本機轉」
  >
  > "Faithfully convert this deck to markdown."
  > "Reproduce this deck's content as accurately as possible."

Claude 會照 [SKILL.md](SKILL.md) 的規則替你執行轉檔程式，產出一份 `.md` 檔，並回報抽出了多少東西：

Claude will run the converter for you following the rules in [SKILL.md](SKILL.md), produce a `.md` file, and report what was extracted:

```
[ppt-to-md] 完成：my-deck.md
  投影片 33 頁 ｜ 表格 5 張 ｜ 原生圖表 3 張 ｜ 本頁專屬口述 12 則 ｜ 制式引註 8 則 ｜ 圖片出處字樣 6 頁
  雜訊清理：折疊座標軸刻度 2 處 ｜ 剝除頁碼 15 處
```

需求也可以直接用講的，skill 會自己換成對應的程式選項：

Preferences can be stated in plain words too — the skill maps them to the right script options:

| 你說 / You say | 效果 / Effect |
|---|---|
| 「加上 frontmatter，我要進 Obsidian」/ "Add frontmatter, this goes into Obsidian" | 檔頭產出 YAML 欄位（`--frontmatter`）/ YAML fields at the top (`--frontmatter`) |
| 「不要附 Mermaid 圖」/ "Skip the Mermaid charts" | 只留數據表格（`--no-mermaid`）/ Data tables only (`--no-mermaid`) |
| 「講者備註也要一起抽」/ "Extract the speaker notes too" | 本來就會做，還會自動分類 / Already done by default, with automatic triage |

> 兩個小提醒 / Two small notes:
> - 在 **Claude Code** 裡請用自然語言觸發，`/ppt` 斜線指令會和它的內建指令衝突。
>   Inside **Claude Code**, trigger with natural language — the `/ppt` slash command collides with its built-ins.
> - 只支援 `.pptx`；舊格式 `.ppt` 請先轉檔：`soffice --headless --convert-to pptx 你的檔案.ppt`
>   Only `.pptx` is supported; convert legacy `.ppt` first: `soffice --headless --convert-to pptx your-file.ppt`

<details>
<summary>進階：不透過 Claude，直接當命令列工具跑 / Advanced: run it directly as a CLI tool, no Claude needed</summary>

轉檔核心就是一支獨立的 Python 程式（3.10+，僅標準庫），可以完全脫離 Claude 使用：

The converter core is a standalone Python script (3.10+, standard library only) that works entirely without Claude:

```bash
python scripts/extract.py <輸入.pptx> [輸出.md] [--no-mermaid] [--frontmatter]
```

```bash
python scripts/extract.py my-deck.pptx                  # 最簡用法：同資料夾產生 my-deck.md / simplest: creates my-deck.md next to the input
python scripts/extract.py my-deck.pptx notes/out.md     # 自訂輸出位置與檔名 / custom output path and name
python scripts/extract.py my-deck.pptx --no-mermaid     # 不附 Mermaid 長條圖 / skip Mermaid bar charts
python scripts/extract.py my-deck.pptx --frontmatter    # 檔頭加 YAML 欄位 / add YAML fields at the top
```

</details>

## 6. 目錄結構 (Repository Structure)

```
PPT-to-MD/
├── README.md                      # 本說明檔 / this file
├── LICENSE                        # MIT 授權條款 / MIT license
├── SKILL.md                       # 給 AI 助手看的完整操作說明 / full instructions for AI assistants
├── scripts/
│   └── extract.py                 # 核心轉檔程式，一個檔案搞定 / the core converter, one single file
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

## 7. 貢獻指南 (Contributing)

非常歡迎任何形式的幫忙！不管你是發現了 bug、有新點子，還是想改進程式碼，都很感謝你願意花時間。

Help of any kind is very welcome! Whether you found a bug, have an idea, or want to improve the code — thank you for taking the time.

- **回報問題**：到 [Issues](https://github.com/kau10082/PPT-to-MD/issues) 開一個新 issue，描述你遇到的狀況（如果能附上出問題的簡報特徵，例如「含合併儲存格的表格」，會超有幫助）。
  **Report a problem**: open a new issue on the [Issues](https://github.com/kau10082/PPT-to-MD/issues) page describing what happened (describing the deck feature that triggered it — e.g. "a table with merged cells" — helps a lot).
- **修改程式碼**:
  **Change the code**:
  1. Fork 這個專案到你的帳號 / Fork this repo to your account
  2. 開一個新分支：`git checkout -b my-fix` / Create a new branch: `git checkout -b my-fix`
  3. 修改並提交 / Make your changes and commit
  4. 發 Pull Request 回來，簡單說明改了什麼、為什麼 / Open a Pull Request explaining what you changed and why

> 提醒：本專案的核心精神是「忠實還原、不腦補」。新功能若會讓輸出偏離原始簡報內容（例如自動填補空白儲存格），原則上不會被接受。
>
> Note: the soul of this project is "faithful extraction, no fabrication." Features that make the output drift from the original deck (e.g. auto-filling merged cells) will generally not be accepted.

## 8. 授權條款 (License)

本專案採用 **MIT 授權**——你可以自由使用、修改、散布，甚至用於商業用途，唯一的要求是保留原始的授權與著作權聲明（標示出處）。完整條文請見 [LICENSE](LICENSE)。

This project is released under the **MIT License** — you are free to use, modify, and distribute it, even commercially. The only requirement is to keep the original license and copyright notice (credit the source). See [LICENSE](LICENSE) for the full text.
