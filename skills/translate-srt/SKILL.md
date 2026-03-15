---
name: translate-srt
description: Extracts subtitles from video files or transcribes audio via Whisper and translates them into bilingual dual-language SRT files. Use when asked to translate subtitles, create bilingual SRT captions, extract and translate video captions from MKV or MP4 files, or download and translate YouTube video subtitles. Supports 19 languages including English, Japanese, Traditional Chinese, Korean, Russian, French, German, and Spanish. Works with local video files and YouTube URLs.
license: Complete terms in LICENSE.txt
---

# 影片字幕翻譯技能

從影片提取字幕（或用 Whisper 語音轉錄），翻譯後分別輸出目標語言與來源語言兩個 SRT 字幕檔（如 `a.zh.srt`、`a.en.srt`），輸出檔名與影片主檔名一致，方便播放器自動載入。

## 使用時機

在以下情境啟用本技能：

- 使用者要求翻譯影片字幕或字幕檔
- 需要建立雙語（原文 + 譯文）SRT 字幕
- 從 MKV、MP4 等影片提取並翻譯字幕軌
- 需要下載 YouTube 影片並翻譯其字幕
- 影片無字幕軌，需要語音轉錄後翻譯

## 先決條件

確認以下工具已安裝：

| 工具 | 用途 | 安裝指令 |
|------|------|---------|
| `ffmpeg` + `ffprobe` | 影片解析、字幕提取與音軌轉換 | `winget install ffmpeg` / `brew install ffmpeg` |
| `yt-dlp` | YouTube 影片下載 | `pip install yt-dlp` |
| `openai-whisper` | 語音轉錄（無字幕軌時使用） | `pip install openai-whisper` |
| `Python 3.10+` | 執行 SRT 解析與組裝腳本 | [python.org](https://www.python.org) |

> **注意**：Whisper large 模型需要約 5GB VRAM，建議使用 CUDA GPU。

## 語法與範例

**語法**：`<影片路徑或YouTube網址> [來源語言>目標語言]`

預設翻譯方向：英文 (`en`) → 繁體中文 (`zh`)

```
/translate-srt video.mkv                       → 自動偵測，翻譯成繁體中文
/translate-srt video.mkv en>zh                 → 英文翻譯成繁體中文
/translate-srt video.mkv ja>en                 → 日文翻譯成英文
/translate-srt video.mkv en>ru                 → 英文翻譯成俄文
/translate-srt video.mkv fr>de                 → 法文翻譯成德文
/translate-srt https://youtu.be/xxxxx          → 下載 YouTube 影片，翻譯成繁體中文
/translate-srt https://youtu.be/xxxxx ja>zh    → 下載日文 YouTube 影片，翻譯成繁體中文
```

## 支援語言

| 代碼 | 語言 | ffprobe 標籤 | 代碼 | 語言 | ffprobe 標籤 |
|------|------|-------------|------|------|-------------|
| `zh` | 繁體中文 | chi, zho, cmn, zh | `ko` | 韓文 | kor, ko |
| `en` | 英文 | eng, en | `ru` | 俄文 | rus, ru |
| `ja` | 日文 | jpn, ja | `fr` | 法文 | fra, fre, fr |
| `de` | 德文 | deu, ger, de | `es` | 西班牙文 | spa, es |
| `pt` | 葡萄牙文 | por, pt | `it` | 義大利文 | ita, it |
| `ar` | 阿拉伯文 | ara, ar | `th` | 泰文 | tha, th |
| `vi` | 越南文 | vie, vi | `pl` | 波蘭文 | pol, pl |
| `nl` | 荷蘭文 | nld, dut, nl | `sv` | 瑞典文 | swe, sv |
| `tr` | 土耳其文 | tur, tr | `uk` | 烏克蘭文 | ukr, uk |
| `hi` | 印地文 | hin, hi | | | |

## 工作流程

在執行前，顯示解析結果請用戶確認：

```
來源：<INPUT_FILE>（YouTube 影片 / 本機檔案）
翻譯方向：<SRC_LANG 全名> → <TGT_LANG 全名>
```

完整的逐步工作流程請參考 [workflow-detailed.md](./references/workflow-detailed.md)。

高層次流程摘要：

1. **解析參數** — 從 `$ARGUMENTS` 提取影片路徑和語言對
2. **下載 YouTube 影片**（若為 YouTube 網址）— 使用 yt-dlp，同時下載可用字幕
3. **驗證輸入** — 確認影片檔案存在
4. **偵測字幕軌** — 使用 ffprobe；若無字幕軌，使用 Whisper 語音轉錄
5. **提取字幕** — 使用 ffmpeg 提取 SRT 到 `/tmp/_translate_temp_src.srt`
6. **解析並分批** — 執行 [parse_srt.py](./scripts/parse_srt.py)（每批 40 條）
7. **分批翻譯** — 遵循翻譯規範，每批完成後立即寫入結果
8. **驗證翻譯品質** — 執行 [verify_translation.py](./scripts/verify_translation.py)
9. **組裝單語言 SRT（兩個檔案）** — 執行 [assemble_srt.py](./scripts/assemble_srt.py)，分別輸出 `<檔名>.<tgt>.srt` 和 `<檔名>.<src>.srt`
10. **清理並報告** — 移除臨時檔案，告知用戶輸出路徑

## 翻譯規範

- 影視翻譯風格：口語自然、語意準確
- 保留專有名詞（品牌名、技術術語）原文
- 時間碼必須完全保留，不可修改
- 雙語格式：**目標語言在上**、來源語言在下
- 同一人名全片必須保持一致譯法

**繁體中文特別規範**：
- 使用台灣慣用繁體中文及人名譯法
- 音譯人名中**嚴禁使用「乘」（U+4E58）字**（如 D 音應用「德/戴/丹」，T 音應用「特/泰/塔」）

詳細各語言翻譯規範請參考 [workflow-detailed.md](./references/workflow-detailed.md#翻譯規範)。

## 可用腳本

| 腳本 | 功能 |
|------|------|
| [parse_srt.py](./scripts/parse_srt.py) | 解析 SRT 並分批成 JSON chunks（每批 40 條） |
| [assemble_srt.py](./scripts/assemble_srt.py) | 將翻譯後 JSON 組裝成兩個單語言 SRT 檔案（`<檔名>.<tgt>.srt` + `<檔名>.<src>.srt`） |
| [verify_translation.py](./scripts/verify_translation.py) | 驗證翻譯品質，偵測禁用字元（如 U+4E58）|

## 疑難排解

| 問題 | 解決方案 |
|------|---------|
| yt-dlp 下載失敗（地區限制） | 使用 VPN，或以 `--cookies-from-browser chrome` 提供 cookies |
| Whisper 顯示 CUDA 記憶體不足 | 改用 `--model medium` 或加上 `--device cpu` |
| ffprobe 回傳空字幕軌列表 | 確認影片含有嵌入字幕軌；外掛字幕請直接提供 `.srt` 檔 |
| Windows 上 Python 顯示編碼錯誤 | 確認所有 Python 指令前綴 `PYTHONIOENCODING=utf-8` |
| 字幕格式為 ASS/SSA | ffmpeg 在提取時會自動轉換為 SRT，無需手動處理 |
| 翻譯結果含禁用字元 | `verify_translation.py` 偵測後，逐一修正對應 JSON 並重新驗證 |
| 影片超過 500 條字幕 | 翻譯需較長時間，分批進行；每批完成後立即寫入 |