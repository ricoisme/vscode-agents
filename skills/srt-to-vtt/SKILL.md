---
title: srt-to-vtt
description : 提供一個可重用的 skill，用於指導使用者將 SRT 格式字幕轉換為 VTT（WebVTT）格式。此 skill 支援多語言（英文、繁體中文、簡體中文），並示範如何使用現成的 `srt-to-vtt` Python 套件與備選工具進行完整轉換與格式/編碼自動偵測。
---

# `srt-to-vtt` Skill

**目的**：提供一個可重用的 skill，用於指導使用者將 SRT 格式字幕轉換為 VTT（WebVTT）格式。此 skill 支援多語言（英文、繁體中文、簡體中文），並示範如何使用現成的 `srt-to-vtt` Python 套件與備選工具進行完整轉換與格式/編碼自動偵測。

## 適用情境
- 使用者想要將 SRT 檔案轉換為 VTT 以供網頁播放器或前端使用。
- 需要自動偵測字幕編碼與語言（英文、繁體中文、簡體中文）。
- 想要 CLI 或 Python 程式化轉換流程。

## 安裝建議

建議使用 Python 套件 `srt-to-vtt`（若已存在），並使用輔助套件進行編碼與語言偵測：

```bash
pip install srt-to-vtt chardet langdetect
```

備註：若 `srt-to-vtt` 套件不存在或需求更細緻的處理，可改用 `pysrt` + `webvtt-py` 或自行實作解析/重建時間軸。

```bash
pip install pysrt webvtt-py chardet langdetect
```

## 功能說明（Skill 回應要點）
- 簡短說明：此 skill 會引導使用者如何安裝套件並執行轉換。
- 自動偵測：說明如何用 `chardet` 偵測檔案編碼，並用 `langdetect` 檢測語言，以便在必要時顯示語言標記或採取語言特定處理（例如特殊標點轉換）。
- CLI 與 Python 範例：提供一組簡單可執行的指令與程式碼片段。

## CLI 範例

假設系統有 `srt-to-vtt` CLI：

```bash
# 基本單檔轉換
srt-to-vtt input.srt -o output.vtt

# 指定編碼與覆寫（當自動偵測失敗時）
srt-to-vtt --encoding=utf-8 input.srt -o output.vtt
```

## Python 範例（含自動偵測編碼與語言）

以下示例以 `pysrt` + `webvtt` 為備援示範；若使用 `srt-to-vtt` 套件，其 API 可替換相應部分：

```python
import chardet
from langdetect import detect
import pysrt
from webvtt import WebVTT, Caption

def detect_encoding(path):
    with open(path, 'rb') as f:
        raw = f.read()
    return chardet.detect(raw)['encoding'] or 'utf-8'

def srt_to_vtt(input_path, output_path):
    enc = detect_encoding(input_path)
    subs = pysrt.open(input_path, encoding=enc)

    # 簡單語言偵測（使用前 5 條字幕文字）
    sample = ' '.join([s.text for s in subs[:5]])
    try:
        lang = detect(sample)
    except Exception:
        lang = 'und'

    vtt = WebVTT()
    for s in subs:
        start = s.start.to_time()
        end = s.end.to_time()
        caption = Caption(str(start), str(end), s.text)
        vtt.captions.append(caption)

    # 可在檔頭加入語言資訊（選用）
    with open(output_path, 'w', encoding='utf-8') as out:
        out.write('WEBVTT')
        out.write('\n')
        out.write(f'LANG: {lang}\n')
    vtt.save(output_path)

if __name__ == '__main__':
    import sys
    if len(sys.argv) < 3:
        print('Usage: python srt_to_vtt.py input.srt output.vtt')
    else:
        srt_to_vtt(sys.argv[1], sys.argv[2])
```

## 使用者互動指引（skill 範本回答）
- 若使用者只上傳 SRT 檔並要求轉換：建議回覆一段簡短步驟包括安裝、單行 CLI、或提供上方 Python 範例以供下載與執行。
- 若 SRT 為非 UTF-8：請先嘗試自動偵測編碼（`chardet`），若偵測不確定，提示使用者提供編碼或嘗試常用編碼（`utf-8`, `big5`, `gb18030`）。
- 若使用者要求語言標註或多語處理：建議用 `langdetect` 檢測並回傳結果；若偵測失敗，詢問使用者指定語言。

## 範例回應模板

```
我可以幫你將 SRT 轉為 VTT。建議先安裝：
`pip install srt-to-vtt chardet langdetect`

如果你想快速轉換（CLI）：
`srt-to-vtt input.srt -o output.vtt`

或要用 Python 自動偵測編碼與語言，請參考我提供的 `srt_to_vtt.py` 範例。
如果你上傳檔案，我也可以幫你檢查編碼並示範轉換步驟。
```

## 注意事項與建議
- 自動語言偵測非 100% 準確，對短字幕片段可能失敗，必要時請讓使用者手動指定語言。
- 若字幕含 HTML 或特殊標記，建議先清理或使用安全的 HTML 轉碼工具（避免 XSS 與不必要的標記）。
- 若需支援大量批次轉換，可建議將該流程包成 CLI 或簡單的 Flask/FastAPI 服務以便上傳與回傳。

## 腳本檔案位置
- 輔助腳本放在：`.github/skills/srt-to-vtt/scripts/srt_to_vtt.py`。

---

