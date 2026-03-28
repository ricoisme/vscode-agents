# GitLab CI/CD Pipeline Design Checklist

這份清單用來快速檢查 `gitlab-ci.yml` 是否同時滿足正確性、可讀性、安全性與 GitLab UI 整合。

## 1. Stage 設計

- 至少拆成 `restore`、`build`、`test`、`deploy`
- 各階段只做單一責任，避免把所有命令塞進同一個 job
- 用 `needs` 明確描述 job 依賴，縮短 pipeline 時間並保持資料流清楚

## 2. Artifact 與 Cache 邊界

- Cache 用於加速，例如 NuGet、npm、pip 套件快取
- Artifact 用於跨 job 傳遞本次 pipeline 必要輸出
- 如果 build/test 使用 `--no-restore` 或 `--no-build`，就不能只靠 cache

## 3. Test Report 顯示

- 優先選擇 GitLab 支援的 `junit` 報告
- XML 報告必須在 job 結束前產生完成
- `artifacts:reports:junit` 必須對到實際檔案
- 同時保留 `artifacts:paths` 方便下載原始結果

## 4. 路徑策略

- 盡量集中於 variables 管理，例如 solution、test project、publish dir、results dir
- 避免散落多個硬編碼路徑
- 若工具對相對路徑有特殊行為，改用 `${CI_PROJECT_DIR}` 明確定位

## 5. 安全策略

- 所有 secrets 只能來自 GitLab CI/CD Variables 或外部 secret provider
- 不要在 YAML 寫入 access token、connection string、password
- 不要在 script 中 `echo` secrets 或開啟詳細 trace
- deploy job 預設改成 `manual`，並限制在受保護分支或 tag 上執行

## 6. 驗證策略

- restore: 確認 dependency 解析成功
- build: 確認編譯產物與必要 obj/bin 存在
- test: 確認測試結果與 junit XML 已產出
- deploy: 確認 publish artifact 存在，或正式部署條件正確受控

## 7. .NET 專案特別注意

- 使用 `--no-restore` 時，必須保留 restore 產生的 `obj/project.assets.json`
- 使用 `--no-build` 測試時，必須保留 Release `bin/` 與 `obj/`
- `JunitXml.TestLogger` 在某些情況下會以專案目錄解析相對 `LogFilePath`，建議輸出到 `${CI_PROJECT_DIR}/...`

## 8. 交付標準

- YAML 結構清楚，易於後續新增 lint、security scan、review app
- 所有 job 命名與變數名稱具可讀性
- 沒有敏感資訊外洩風險
- GitLab UI 可直接看到 test report
