---
name: gitlab-ci-cd-expert
description: 'Generate, review, modularize, and harden gitlab-ci.yml pipelines for different software architectures and frameworks. Use when asked to create GitLab CI/CD, produce restore/build/test/deploy stages, show test reports correctly in GitLab UI, validate artifact and report paths, improve pipeline readability, avoid leaking secrets in logs, or troubleshoot GitLab CI failures for .NET, Node.js, Python, Java, and mixed-stack projects.'
compatibility: 'Requires a repository with GitLab CI/CD enabled. Especially useful for .NET projects that need split restore/build/test/deploy jobs, test report publishing, and safe variable handling.'
---

# GitLab CI/CD Expert

建立、審查與修正 `gitlab-ci.yml`，重點放在正確性、可讀性、模組化、測試報告整合與敏感資訊保護。

## When to Use This Skill

- 使用者要求「建立 GitLab CI/CD」、「產生 gitlab-ci.yml」、「修正 pipeline」
- 需要至少四個階段：`restore`、`build`、`test`、`deploy`
- 需要讓 test report 正確顯示在 GitLab UI
- 需要確認 artifacts、reports、工作目錄與相對路徑是否正確
- 需要把 pipeline 寫得更模組化、更可讀，或依框架切換策略
- 需要避免 secrets、tokens、connection strings 出現在 CI logs 或 YAML 中

## Prerequisites

- 知道專案主要技術堆疊，例如 .NET、Node.js、Python、Java 或混合架構
- 知道建置入口，例如 solution、project、package.json、pytest、maven/gradle 專案
- 知道部署目標是否已存在，例如 SSH、VM、Kubernetes、App Service、artifact-only
- 若需要正式部署，應先由 GitLab CI/CD Variables 提供敏感資訊，禁止硬編碼於 YAML

## Workflow

1. 先辨識架構與 build/test 入口。
   - .NET: 找 `.sln`、`*.csproj`、測試專案與 test logger 套件。
   - Node.js: 找 `package.json`、lock file、test script、coverage script。
   - Python: 找 `pyproject.toml`、`requirements*.txt`、pytest 設定。
   - Java: 找 `pom.xml` 或 `build.gradle`。

2. 先設計 stages，再決定 artifacts 串接方式。
   - 預設至少 `restore`、`build`、`test`、`deploy`。
   - 若後續 job 使用 `--no-restore` 或 `--no-build`，必須傳遞前一階段產生的必要檔案。
   - 快取只用於加速，不可假設 cache 等同於可重現的 build 輸入。

3. 為 test report 建立 GitLab 可辨識輸出。
   - 優先輸出 `junit` XML。
   - `artifacts:reports:junit` 路徑必須對應實際生成位置。
   - 若工具對相對路徑有特殊解譯規則，改用明確絕對或 CI 專案根目錄拼接路徑。

4. 讓 deploy 預設安全。
   - 若無足夠環境資訊，先產出 publish artifact，而不是假裝完成真實部署。
   - 正式 deploy job 必須以 variables 注入認證資訊，避免 `echo` 或 `set -x` 類型的洩漏。
   - 重要環境建議搭配 `rules`、protected branches、manual deploy。

5. 完成後驗證每個階段。
   - 檢查 restore 輸出是否足以支持 build。
   - 檢查 build artifacts 是否足以支持 test 與 deploy。
   - 檢查 junit XML 檔案在 job 結束後是否落在 `artifacts:reports:junit` 指向的實際位置。
   - 檢查 deploy 是否僅在合理條件下執行。

## Output Requirements

- 高可讀性：使用集中變數、清楚的 stage 名稱與簡短註解
- 模組化：用 `default`、`variables`、`needs`、`rules` 降低重複
- 安全性：禁止把 secrets 寫死在 YAML，避免在 log 中輸出敏感資訊
- 正確性：artifact 與 test report 路徑必須可追溯、可驗證
- 可維護性：部署命令與框架相依命令分離，方便之後替換

## Recommended Structure

- 先看 [references/pipeline-design-checklist.md](references/pipeline-design-checklist.md)
- .NET Web API 可直接參考 [templates/dotnet-webapi.gitlab-ci.yml](templates/dotnet-webapi.gitlab-ci.yml)

## Troubleshooting

### Test report 沒出現在 GitLab UI

- 檢查 `artifacts:reports:junit` 指向的路徑是否真的存在
- 檢查 test logger 是否有安裝，例如 .NET 常見的 `JunitXml.TestLogger`
- 檢查 logger 對相對路徑的解析規則，必要時改用 `${CI_PROJECT_DIR}` 組合完整路徑

### 後續 job 使用 `--no-restore` 或 `--no-build` 失敗

- 把 restore/build 產生的必要 `obj/`、`bin/` 透過 artifacts 傳到後續 job
- 不要只依賴快取的套件資料夾

### Deploy job 風險太高

- 先改成 `manual`
- 只在 default branch 或 tag 觸發
- 把真正的部署指令保留為待替換占位，直到 CI variables 與目標環境準備完成

## References

- [Pipeline design checklist](references/pipeline-design-checklist.md)
- [Reusable .NET Web API template](templates/dotnet-webapi.gitlab-ci.yml)
