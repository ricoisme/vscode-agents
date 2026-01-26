# vscode-agents

此專案為一組「skills」範例與範本，展示如何在 VS Code Agents / agent-like 工作流程中組織、說明與測試小型技能 (skills)。

## 專案概覽

vscode-agents 包含多個獨立的 skill 資料夾，每個 skill 都有自己的說明與範例程式。此專案主要作為範例庫與文件範本集合，方便快速建立與驗證 agent 類型的能力模組。

## 快速開始

1. 確認已安裝 Python 3.11+（若要執行 Python 範例）。
2. 在專案目錄建立並啟用虛擬環境：

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1   # PowerShell
# 或 .venv\Scripts\activate.bat  # cmd.exe
```

3. 若有 `requirements.txt`，請安裝相依套件：

```powershell
pip install -r requirements.txt
```

4. 範例：執行 `audio-quality-checker` 的分析腳本：

```powershell
python skills/audio-quality-checker/scripts/audio_analyze.py --help
```

（各 skill 的實際執行方式請參考對應資料夾內的 `SKILL.md`）

## 目錄結構（重點）

- `skills/`：每個子資料夾為單一 skill。
  - `audio-quality-checker/`：包含分析腳本於 `scripts/`。
- `LICENSE`：授權檔。


## 使用範例與文件類型

每個 skill 內通常包含下列文件：

- `SKILL.md`：說明該 skill 的目的、使用方式與範例。
- `templates/`：設計或任務模板，作為教學或參考使用。

## 開發與測試

- **啟動環境**: 依上方虛擬環境步驟建立。
- **執行範例**: 參考對應 `SKILL.md` 中的執行指示。
- **測試**: 若有測試套件，請依專案慣例執行（目前專案未包含全域測試設定）。

## 貢獻指南

歡迎透過 Issue 或 Pull Request 提供改進：

- Fork 專案、建立分支、提交 PR。請在 PR 描述中包含變更說明與測試步驟。
- 保持 commit 訊息簡潔並描述目的。

---

