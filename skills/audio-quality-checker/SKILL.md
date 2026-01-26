---
name: audio-quality-checker
description: '專業音訊品質檢測員：分析本地音訊檔案的編碼、取樣、聲道與音量特徵，並依規則給出品質評等與報告。使用情境：當使用者提供本地 .mp3/.wav/.m4a 路徑，需快速生成技術檢測報告與品質建議。'
---

# 專業音訊品質檢測員 (Audio Quality Checker)

此 skill 由具 20 年經驗的音訊工程師視角撰寫，專注於數位音訊處理 (DSP) 的客觀品質檢測。當使用者提供本地音訊檔案路徑時，依序執行下列步驟，並輸出一致格式的檢測報告。

## 何時使用此 Skill

- 想要自動化檢查音訊檔案（.mp3, .wav, .flac, .m4a）之技術規格與潛在爆音/剪裁問題。
- 批次處理音訊庫、上架內容審核、或作為發行前品質把關的一環。

## 前置需求

- 已安裝 `ffmpeg` 與 `ffprobe` 並可於 PATH 使用。
- 可在 Windows / macOS / Linux 環境執行命令列工具。

## 核心指令 (Core Command)

當使用者提供本地音訊檔案路徑（例如 `C:\audio\track.mp3` 或 `/home/user/track.flac`），請依序執行：

### 步驟 A：以 Python 腳本提取格式與編碼資訊
使用本專案提供的 `scripts/audio_analyze.py`（純 Python）直接解析音訊檔案並輸出 JSON，該 JSON 會包含：`channels`、`sample_rate`、`sample_width_bytes`、`nframes`、`duration_seconds` 等技術欄位。

範例命令：

```bash
python scripts/audio_analyze.py "[FILE_PATH]"
```

### 步驟 B：檢測數位動態與爆音 (Clipping)
同一支 `scripts/audio_analyze.py` 也會計算每個區塊的 RMS、最大樣本值與相對 dBFS（`max_dbfs`、`mean_dbfs`），並回報 `clipped_chunks`/`clipped_chunk_ratio` 以判定是否有削波（clipping）。

解析腳本輸出中的 `max_dbfs` 與 `clipped_chunks`：若 `max_dbfs` 非常接近 0 dBFS（例如 ≥ -1.0 dB）或 `clipped_chunks` > 0，則視為有剪裁/爆音風險。

## 品質評等邏輯

依下列規則給出最終評論：

- 🏆 高品質 (High Quality):
  - Bitrate > 256kbps 或為無損格式 (WAV/FLAC)。
  - Sample Rate ≥ 44,100 Hz。
  - max_volume < 0.0 dB（無數位剪裁）。

- ⚖️ 品質中等 (Medium Quality):
  - Bitrate 介於 128kbps ~ 256kbps。
  - 有輕微的動態壓縮，但無嚴重失真。

- ⚠️ 低品質 (Low Quality):
  - Bitrate < 128kbps。
  - max_volume 長時間處於 0.0 dB（嚴重爆音）。
  - 取樣率低於 32,000 Hz 或為單聲道（當原始音源預期為立體聲時）。

在評等時，請同時考量多項指標（取樣率、編碼、位元率、聲道與爆音風險），並以最接近真實感受的等級做判定。

## 輸出模板（務必嚴格遵守）

請以下列格式輸出最終報告（繁體中文）：

```
🎙️ 音訊檢測報告
檔案名稱: [檔名]

編碼格式: [Codec] / [Channels]

技術規格: [Bitrate] / [Sample Rate]

📊 數據分析
爆音風險: [無 / 輕微 / 嚴重 (Max Volume: X dB)]

平均音量: [Mean Volume: X dB]

🏁 最終評論：【高品質 / 品質中等 / 低品質】
```

替換方括號內容為實際數值（例如 `Bitrate: 320kbps`、`Sample Rate: 44100Hz`、`Channels: stereo` 等）。當檔案為無損格式，請在 `技術規格` 中標註為 `無損` 或直接顯示 bit depth/format。

## 範例工作流程（使用 Python）

1. 取得使用者輸入的本地路徑。
2. 執行 `scripts/audio_analyze.py`，該腳本會讀取 WAV/PCM 檔案並輸出 JSON（含 `sample_rate`、`channels`、`max_dbfs`、`mean_dbfs`、`clipped_chunks` 等）。
3. 解析 JSON，萃取所需欄位。
4. 根據位元率（若可得）、取樣率、聲道與音量指標（`max_dbfs`、`clipped_chunk_ratio`）套用品質評等邏輯。
5. 輸出符合「輸出模板」的報告文字，供使用者閱讀或收藏。可將此流程整合至 CI 或自動化檢查。

## 常見問題與診斷

- bit_rate 為 null：有些無損格式或特定封裝會不回傳 `bit_rate`，此時以 `format_name` 與 `codec_name` 判定是否無損（如 WAV/FLAC）並標註 `無損`。
- 請確認 python 版本3.11以上，並安裝相關套件。

## 使用自帶分析腳本範例

此儀表板範例使用專案內的 `audio_analyze.py` 腳本快速產生技術性分析（RMS、峰值、取樣、聲道、時長、削波等）。`audio_analyze.py` 可直接執行於安裝有 Python 的環境。

範例（Windows PowerShell）：

```powershell
cd "d:\OnLineCourse\Github Copilot\course\demo\.github\skills\audio-quality-checker"
python .\scripts\audio_analyze.py "d:/TechMovie/cleantestaudio_48k24.wav"
```

範例（輸出 JSON 範例）：

```json
{
  "channels": 1,
  "sample_width_bytes": 3,
  "sample_rate": 48000,
  "nframes": 85639167,
  "duration_seconds": 1784.149,
  "max_sample_value": 7094644,
  "max_dbfs": -1.46,
  "mean_rms": 1099147.66,
  "mean_dbfs": -17.65,
  "total_chunks": 1307,
  "clipped_chunks": 0,
  "clipped_chunk_ratio": 0.0
}
```

說明：
- `max_dbfs` 與 `mean_dbfs` 表示相對於數位滿量程 (dBFS) 的峰值與平均能量，數值越接近 0 表示越接近飽和。若 `clipped_chunks` > 0 表示有檔案範圍發生削波（需注意）。

---
