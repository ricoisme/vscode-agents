# 詳細工作流程

字幕翻譯技能的完整逐步執行流程。

---

## 步驟 0：解析參數

從 `$ARGUMENTS` 中解析影片路徑（或 YouTube 網址）和語言對：

1. 檢查 `$ARGUMENTS` 最後一個空格分隔的 token 是否符合 `XX>YY` 格式（兩個小寫字母 + `>` + 兩個小寫字母）
2. 若符合：
   - 語言對 = 該 token（例如 `ja>en`）
   - 影片路徑/網址 = 去掉最後一個 token 後的剩餘字串（trim 前後空白）
3. 若不符合：
   - 語言對 = `en>zh`（預設：英文 → 繁體中文）
   - 影片路徑/網址 = 整個 `$ARGUMENTS`

解析結果：
- `SRC_LANG`：來源語言代碼（`>` 左側）
- `TGT_LANG`：目標語言代碼（`>` 右側）
- `INPUT_FILE`：影片路徑或 YouTube 網址
- `IS_YOUTUBE`：若包含 `youtube.com/watch`、`youtu.be/`、`youtube.com/shorts/` 等模式，設為 `true`

顯示解析結果請用戶確認：

```
來源：<INPUT_FILE>（YouTube 影片 / 本機檔案）
翻譯方向：<SRC_LANG 全名> → <TGT_LANG 全名>
```

---

## 步驟 0.5：下載 YouTube 影片（僅 `IS_YOUTUBE=true` 時執行）

若為本機檔案，跳過此步驟直接到步驟 1。

### 0.5.1 下載影片

```bash
yt-dlp -f "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best" \
  --merge-output-format mp4 \
  -o "%(title)s.%(ext)s" \
  --no-playlist \
  --write-subs \
  --sub-langs all \
  --convert-subs srt \
  "<YOUTUBE_URL>"
```

| 參數 | 說明 |
|------|------|
| `-f "bestvideo..."` | 優先選擇 mp4 格式 |
| `--merge-output-format mp4` | 合併後輸出 mp4 |
| `-o "%(title)s.%(ext)s"` | 以影片標題作為檔名 |
| `--no-playlist` | 僅下載單一影片 |
| `--write-subs --sub-langs all` | 同時下載所有可用字幕（轉換為 SRT）|

### 0.5.2 取得實際檔名

```bash
yt-dlp --no-playlist --print filename \
  -f "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best" \
  --merge-output-format mp4 \
  -o "%(title)s.%(ext)s" \
  "<YOUTUBE_URL>"
```

將輸出的檔名設為新的 `INPUT_FILE`。若下載失敗，告知用戶具體錯誤並停止。

### 0.5.3 檢查 yt-dlp 下載的外部字幕

```bash
ls -la "$(dirname "<INPUT_FILE>")"/*.srt 2>/dev/null
```

若找到對應來源語言的 `.srt` 字幕檔：
- 複製到 `/tmp/_translate_temp_src.srt`
- 跳過步驟 2 和步驟 3，直接到步驟 3.5

---

## 步驟 1：驗證輸入

確認影片檔案存在：

```bash
ls -la "<INPUT_FILE>"
```

若不存在，嘗試用 Glob 搜尋包含關鍵字的檔案。仍找不到時告知用戶並停止。

---

## 步驟 2：偵測字幕軌

```bash
ffprobe -v quiet -print_format json -show_streams -select_streams s "<INPUT_FILE>"
```

- 依語言代碼對照表找到對應 ffprobe 標籤，查找 `tags.language` 匹配的字幕軌
- 多個匹配軌道時，優先選擇非 forced、非 SDH 的軌道
- 找不到匹配但有其他字幕軌時，列出所有可用字幕軌讓用戶選擇
- **完全沒有字幕軌**（streams 陣列為空）→ 跳到步驟 2.5
- 記下選定軌道在字幕流中的索引（0-based）

---

## 步驟 2.5：Whisper 語音轉錄（無字幕軌時觸發）

僅在步驟 2 確認**完全沒有字幕軌**時執行。

### 2.5.1 確認音軌存在

```bash
ffprobe -v quiet -print_format json -show_streams -select_streams a "<INPUT_FILE>"
```

若 streams 陣列為空，告知用戶「影片既無字幕軌也無音軌，無法處理」並停止。

### 2.5.2 提取音軌為 WAV

```bash
ffmpeg -y -i "<INPUT_FILE>" -vn -acodec pcm_s16le -ar 16000 -ac 1 "/tmp/_translate_temp_audio.wav"
```

### 2.5.3 Whisper 轉錄

**模型路徑解析順序**（依序檢查，取第一個存在的）：

1. 使用者透過環境變數 `WHISPER_MODEL_DIR` 指定的目錄
2. 預設快取目錄 `~/.cache/whisper`（Linux/macOS）或 `%USERPROFILE%\.cache\whisper`（Windows）
3. 若以上皆無對應模型檔案，才連線下載

**步驟一：確認模型是否已存在**

```bash
# 取得模型快取目錄
MODEL_DIR="${WHISPER_MODEL_DIR:-$HOME/.cache/whisper}"
MODEL_NAME="large"
MODEL_FILE="$MODEL_DIR/${MODEL_NAME}.pt"

if [ -f "$MODEL_FILE" ]; then
  echo "✅ 已找到本機模型：$MODEL_FILE，略過下載。"
else
  echo "⚠️  本機模型不存在，將自動下載至 $MODEL_DIR ..."
fi
```

> 在 Windows (PowerShell) 環境下，等效檢查：
> ```powershell
> $modelDir  = if ($env:WHISPER_MODEL_DIR) { $env:WHISPER_MODEL_DIR } else { "$env:USERPROFILE\.cache\whisper" }
> $modelFile = Join-Path $modelDir "large.pt"
> if (Test-Path $modelFile) { Write-Host "✅ 已找到本機模型：$modelFile" }
> else                       { Write-Host "⚠️  本機模型不存在，將自動下載 ..." }
> ```

**步驟二：執行轉錄**

```bash
PYTHONIOENCODING=utf-8 whisper "/tmp/_translate_temp_audio.wav" \
  --model large \
  --model_dir "$MODEL_DIR" \
  --language <SRC_LANG> \
  --output_format srt \
  --output_dir "/tmp" \
  --device cuda
```

| 參數 | 說明 |
|------|------|
| `--model large` | 指定模型大小（`tiny` / `base` / `small` / `medium` / `large`） |
| `--model_dir "$MODEL_DIR"` | 優先從此目錄載入模型；若不存在才下載至此目錄 |
| `--device cuda` | 使用 GPU；若無 GPU 請改為 `--device cpu` |

> **注意**：
> - Whisper `large` 模型需要約 5 GB VRAM；若記憶體不足，改用 `--model medium`（~1.5 GB）或 `--device cpu`。
> - 設定 `WHISPER_MODEL_DIR` 可共用同一份模型，避免多次下載：
>   ```bash
>   export WHISPER_MODEL_DIR="/data/models/whisper"   # Linux/macOS
>   # 或
>   $env:WHISPER_MODEL_DIR = "D:\models\whisper"      # Windows PowerShell
>   ```

### 2.5.4 重命名 SRT

```bash
mv /tmp/_translate_temp_audio.srt /tmp/_translate_temp_src.srt
```

完成後跳到步驟 3.5，跳過步驟 3。

---

## 步驟 3：提取字幕

若步驟 2.5 已產生 SRT，跳過此步驟。

```bash
ffmpeg -y -i "<INPUT_FILE>" -map 0:s:N -c:s srt "/tmp/_translate_temp_src.srt"
```

`N` 為字幕流在字幕軌中的 0-based 索引。若字幕格式為 ASS/SSA，ffmpeg 會自動轉換。

---

## 步驟 3.5：取得臨時目錄路徑

在 Windows (Git Bash / MSYS2) 環境下，Python 無法直接存取 `/tmp`：

```bash
TMPDIR=$(cygpath -w /tmp 2>/dev/null || echo /tmp)
echo "臨時目錄: $TMPDIR"
```

後續所有 Python 腳本均使用 `$TMPDIR`。

---

## 步驟 4：解析 SRT 並分批

執行 [parse_srt.py](../scripts/parse_srt.py)：

```bash
PYTHONIOENCODING=utf-8 python3 .github/skills/translate-srt/scripts/parse_srt.py "$TMPDIR"
```

腳本將 SRT 解析後每批 40 條輸出為 `$TMPDIR/_translate_chunk_N.json`，格式：

```json
[
  {"index": 1, "timecode": "00:00:09,490 --> 00:00:11,992", "text": "原文字幕"},
  ...
]
```

---

## 步驟 5：分批翻譯

對每一批依序執行：

1. 讀取 `$TMPDIR/_translate_chunk_N.json`
2. 將每條 `text` 從 `SRC_LANG` 翻譯成 `TGT_LANG`
3. 寫入翻譯結果至 `$TMPDIR/_translate_result_N.json`：

```json
[
  {"index": 1, "timecode": "00:00:09,490 --> 00:00:11,992", "tgt": "譯文", "src": "原文"},
  ...
]
```

**重要**：每批完成後立即寫入，不可等全部翻譯完再寫入。

---

## 翻譯規範

### 通用規範（所有語言對）

- 影視翻譯風格：口語自然流暢，保持語意準確
- 口語縮寫或俚語（gonna, wanna 等）翻譯也要口語化
- 專有名詞（品牌名、技術術語）保留原文
- 同一人名全片保持一致譯法；不確定時保留原文
- 時間碼完全保留，不可修改

### 繁體中文（zh）

- 使用台灣慣用繁體中文及人名譯法
- **絕對禁止在音譯中使用「乘」（U+4E58）字**
  - D 音：德 / 戴 / 丹 / 迪 / 杜 / 道 / 達
  - T 音：特 / 泰 / 塔 / 提 / 湯 / 陶
  - W 音：懷 / 威 / 沃 / 韋 / 溫
  - B 音：布 / 巴 / 比 / 貝 / 鮑 / 博
  - M 音：曼 / 馬 / 米 / 莫 / 墨 / 麥
  - R 音：瑞 / 里 / 羅 / 雷 / 魯
  - Ch 音：奇 / 查 / 柴 / 切
  - 其他：克 / 斯 / 森 / 爾 / 恩 / 艾 / 歐 / 亞 / 伊 / 薩 / 拉 / 納 / 尼

### 日文（ja）

- 外來人名使用片假名音譯
- 語氣要符合角色性別和年齡

### 韓文（ko）

- 外來人名使用韓文音譯慣例

### 俄文（ru）

- 外來人名使用俄語音譯慣例（транслитерация）

### 其他語言

- 使用標準書面語，人名按該語言音譯慣例處理

---

## 步驟 5.5：驗證翻譯品質

執行 [verify_translation.py](../scripts/verify_translation.py)：

```bash
PYTHONIOENCODING=utf-8 python3 .github/skills/translate-srt/scripts/verify_translation.py "$TMPDIR" "<TGT_LANG>"
```

若發現錯誤，逐一修正對應 JSON 後重新執行驗證，直到通過為止。

---

## 步驟 6：組裝單語言 SRT（兩個檔案）

執行 [assemble_srt.py](../scripts/assemble_srt.py)：

```bash
PYTHONIOENCODING=utf-8 python3 .github/skills/translate-srt/scripts/assemble_srt.py "$TMPDIR" "<INPUT_FILE>" "<SRC_LANG>" "<TGT_LANG>"
```

輸出規則：
- 依主檔名加上語言代碼副檔名，分別輸出兩個獨立字幕檔：
  - `<basename>.<TGT_LANG>.srt` — 目標語言字幕（例：`Tulsa.King.S01E04.zh.srt`）
  - `<basename>.<SRC_LANG>.srt` — 來源語言字幕（例：`Tulsa.King.S01E04.en.srt`）
- 若 `SRC_LANG == TGT_LANG`，僅輸出一個 `<basename>.<lang>.srt` 檔（目標語言內容）
- 範例：`movie.mkv` + `en>zh` → `movie.zh.srt` + `movie.en.srt`

---

## 步驟 7：清理臨時檔案

```bash
rm -f "$TMPDIR/_translate_temp_src.srt" \
      "$TMPDIR/_translate_temp_audio.wav" \
      "$TMPDIR"/_translate_chunk_*.json \
      "$TMPDIR"/_translate_result_*.json
```

---

## 步驟 8：報告結果

告知用戶：

- 輸出檔案路徑
- 總字幕條數
- 翻譯方向（來源語言 → 目標語言）
- 提醒播放器可自動載入同名字幕檔
