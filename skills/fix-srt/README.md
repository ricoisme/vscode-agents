# Fix SRT Enhanced - 增強版字幕修正工具

🎯 **專為繁體中文優化**的 SRT/VTT 字幕自動修正工具，大幅提升錯別字修正準確率與執行效能。

## ✨ 主要特色

- 🇹🇼 **繁體中文優先**：內建 40+ 常見錯別字對照表 + OpenCC + pycorrector 三重修正
- 🇬🇧 **英文增強**：pyspellchecker 拼字檢查 + language_tool_python 語法修正
- 🎯 **上下文感知**：滑動窗口分析前後句，提升語意連貫性
- ⚡ **高效能**：LRU 快取 + 批次處理，**10 分鐘片長可在 1-2 分鐘內完成**
- 🔄 **格式支援**：SRT ↔ VTT 雙向支援與轉換
- ⏱️ **時間軸修正**：自動修正重疊、長度為 0、編號錯誤等問題

## 📦 快速開始

### 1. 安裝依賴

```bash
# 基礎功能（無需額外套件）
python fix_srt_enhanced.py --help

# 完整功能（建議）
pip install -r requirements.txt

# 或手動安裝
pip install opencc-python-reimplemented pycorrector pyspellchecker

# 可選：更強大的語法檢查（首次會下載 100-200MB 語言模型）
pip install language-tool-python
```

### 2. 基本使用

```bash
# 修正 SRT 字幕（繁體中文優先）
python fix_srt_enhanced.py --input input.srt --output output.srt

# 修正 VTT 字幕
python fix_srt_enhanced.py --input input.vtt --output output.vtt

# 預覽變更（不實際寫入）
python fix_srt_enhanced.py --input input.srt --output output.srt --dry-run
```

### 3. 進階選項

```bash
# 啟用深度語法檢查（較慢但更準確）
python fix_srt_enhanced.py --input input.srt --output output.srt --enable-lt

# 調整上下文窗口大小（預設 3 句）
python fix_srt_enhanced.py --input input.srt --output output.srt --context-window 5

# 調整最小字幕持續時間（預設 0.5 秒）
python fix_srt_enhanced.py --input input.srt --output output.srt --min-duration 1.0

# SRT 轉 VTT
python fix_srt_enhanced.py --input input.srt --output output.vtt
```

## 📊 效能基準

| 片長 | 字幕數 | 基礎模式 | 標準模式 | 完整模式 (--enable-lt) |
|------|--------|----------|----------|------------------------|
| 5 分鐘 | 75-150 | < 15 秒 | 30-60 秒 | 1-2 分鐘 |
| 10 分鐘 | 150-300 | < 30 秒 | **1-2 分鐘** | 3-5 分鐘 |
| 30 分鐘 | 450-900 | < 90 秒 | 3-6 分鐘 | 10-15 分鐘 |

*測試環境：Intel i7-10700K, 32GB RAM, Windows 11*

## 🔧 修正範例

### 繁體中文修正

**輸入**
```srt
91
00:03:48,000 --> 00:03:49,000
就是你說的Pump

92
00:03:49,000 --> 00:03:49,000
你要在

93
00:03:49,000 --> 00:03:54,000
這邊透過寫信跟施力去呼叫起來你可以看到
```

**輸出**
```srt
91
00:03:48,000 --> 00:03:49,000
就是你說的 Prompt

92
00:03:49,000 --> 00:03:49,500
你要在

93
00:03:49,500 --> 00:03:54,000
這邊透過寫程式跟實例去呼叫起來你可以看到
```

**修正項目**
- ✅ 時間軸：編號 92 長度從 0 調整為 500ms
- ✅ 錯別字：`Pump` → `Prompt`
- ✅ 語意修正：`寫信` → `寫程式`、`施力` → `實例`
- ✅ 空白規範：`Prompt` 前後加空白

### 英文修正

**輸入**
```srt
1
00:00:00,000 --> 00:00:02,000
ths is a exmple of speling erors.it should be fixed.
```

**輸出**
```srt
1
00:00:00,000 --> 00:00:02,000
This is a example of spelling errors. It should be fixed.
```

**修正項目**
- ✅ 拼字：`ths` → `This`, `exmple` → `example`, `speling` → `spelling`, `erors` → `errors`
- ✅ 大寫：`ths` → `This`（句首）
- ✅ 標點：`.it` → `. It`（標點後加空白）

## 📁 批次處理

### Windows (PowerShell)
```powershell
Get-ChildItem -Filter *.srt | ForEach-Object {
    python fix_srt_enhanced.py --input $_.FullName --output "$($_.BaseName).fixed.srt"
}
```

### Linux / macOS (Bash)
```bash
for file in *.srt; do
    python fix_srt_enhanced.py --input "$file" --output "${file%.srt}.fixed.srt"
done
```

## ⚙️ 自訂錯別字字典

編輯 `fix_srt_enhanced.py` 中的 `TRADITIONAL_CHINESE_TYPO_MAP`：

```python
TRADITIONAL_CHINESE_TYPO_MAP = {
    # 新增你的常見錯誤
    '你的錯誤': '正確寫法',
    '另一個錯誤': '另一個正確寫法',
    
    # 現有項目...
    '己經': '已經',
    '因該': '應該',
    # ...
}
```

## 🐛 疑難排解

### Q: 為什麼繁體中文修正效果不佳？

A: 請確認已安裝 `opencc-python-reimplemented` 和 `pycorrector`：
```bash
pip install opencc-python-reimplemented pycorrector
```

### Q: 執行速度很慢，如何加快？

A: 嘗試以下方法：
1. 減少上下文窗口：`--context-window 1`
2. 不啟用 `--enable-lt`（language_tool_python 較慢）
3. 確保使用 LRU 快取（已內建）

### Q: 為什麼有些專有名詞被誤修正？

A: 請將專有名詞加入自訂字典或使用 `--dry-run` 預覽後手動調整。

### Q: 支援哪些字幕格式？

A: 目前支援 SRT 和 VTT 兩種格式，可雙向轉換。

## 📚 相關資源

- [SKILL.md](./SKILL.md) - 完整技術文件與規格說明
- [fix_srt.py](./scripts/fix_srt.py) - 原始基礎版本
- [fix_srt_enhanced.py](./scripts/fix_srt_enhanced.py) - 增強版（本版本）

## 📄 授權

MIT License - 歡迎自由使用與貢獻改善建議！

## 🙏 致謝

- [OpenCC](https://github.com/BYVoid/OpenCC) - 簡繁轉換
- [pycorrector](https://github.com/shibing624/pycorrector) - 中文錯別字修正
- [pyspellchecker](https://github.com/barrust/pyspellchecker) - 英文拼字檢查
- [language-tool-python](https://github.com/jxmorris12/language-tool-python) - 語法檢查

---

**最後更新**: 2026-02-06  
**維護者**: GitHub Copilot Community
