---
name: sql-cheatsheet-generator
description: |
  產生針對指定資料庫方言的 SQL 速查手冊與高頻實戰案例。當使用者想建立 PostgreSQL、MySQL、MariaDB、SQL Server、Oracle、SQLite 等資料庫的 SQL cheatsheet、quick reference、語法手冊、學習手冊、100 個常用案例或資料庫方言對照內容時使用。Use when asked to: create SQL cheatsheet, SQL quick reference, database-specific SQL handbook, SQL 語法手冊, SQL 速查手冊, PostgreSQL cheat sheet, MySQL cheat sheet, MariaDB cheat sheet, SQL Server cheat sheet, Oracle cheat sheet, SQLite cheat sheet.
---

# SQL 速查手冊生成技能

建立一份面向指定資料庫方言的 SQL 速查手冊，預設整理 100 個高頻實戰使用案例，並輸出為結構化 Markdown，適合日常查閱、教學與內部知識整理。

## 使用時機

在以下情境啟用本技能：

- 使用者想建立某個資料庫的 SQL 速查手冊或 quick reference
- 需要整理 100 個常見 SQL 使用案例與範例
- 需要產出 PostgreSQL、MySQL、MariaDB、SQL Server、Oracle、SQLite 的方言化 SQL 教材
- 需要把既有 schema、查詢或專案資料庫慣例整理成資料庫手冊
- 需要比較不同資料庫方言時，先生成其中一種資料庫的基準版本手冊

## 必要輸入資訊

使用者至少必須提供以下資訊。若缺少必要欄位，主動詢問，不得自行假設：

| 欄位 | 必填 | 說明 | 範例 |
|------|------|------|------|
| **資料庫種類** | 是 | 本次手冊採用的目標資料庫方言 | `PostgreSQL`、`MySQL`、`MariaDB`、`SQL Server`、`Oracle`、`SQLite` |
| **案例數量** | 否 | 預設為 100；若使用者明確指定其他數量，依使用者要求處理 | `100` |
| **資料庫版本** | 否 | 有版本差異時用來收斂語法與注意事項 | `PostgreSQL 16`、`SQL Server 2022` |
| **目標讀者** | 否 | 用來調整講解深度與術語密度 | `初階開發者`、`中階工程師`、`DBA` |
| **輸出檔名** | 否 | 若需要直接建立檔案，優先使用使用者指定檔名 | `postgresql-sql-cheatsheet-100-use-cases.md` |

若使用者只說「幫我做 SQL 速查手冊」但沒有指定資料庫，先詢問資料庫種類，不要直接產出泛用版內容。

## 上下文來源

可優先使用以下上下文：

- 使用者選取的 SQL、schema、DDL、DML、查詢片段
- 目前檔案中的手冊草稿、SQL 腳本或規格文件
- 工作區中的資料表定義、README、資料庫 migration、範例查詢

若沒有足夠上下文，請建立一致且合理的示範模型，例如 `users`、`orders`、`products`、`order_items`、`categories`，並在全篇保持命名一致。

## 工作流程

詳細步驟請參考 [sql-cheatsheet-workflow.md](./references/sql-cheatsheet-workflow.md)。

## TODO

- [ ] 步驟 1：確認資料庫種類與案例數量 — 見 [sql-cheatsheet-workflow.md](./references/sql-cheatsheet-workflow.md#步驟-1確認輸入)
- [ ] 步驟 2：蒐集工作區與使用者上下文 — 見 [sql-cheatsheet-workflow.md](./references/sql-cheatsheet-workflow.md#步驟-2蒐集上下文)
- [ ] 步驟 3：規劃章節與案例分布 — 見 [sql-cheatsheet-workflow.md](./references/sql-cheatsheet-workflow.md#步驟-3規劃章節)
- [ ] 步驟 4：撰寫每個案例的固定欄位 — 見 [sql-cheatsheet-workflow.md](./references/sql-cheatsheet-workflow.md#步驟-4撰寫案例)
- [ ] 步驟 5：處理方言差異與不支援功能 — 見 [sql-cheatsheet-workflow.md](./references/sql-cheatsheet-workflow.md#步驟-5處理方言差異)
- [ ] 步驟 6：完成品質驗證與輸出 — 見 [sql-cheatsheet-workflow.md](./references/sql-cheatsheet-workflow.md#步驟-6品質驗證與輸出)

## 輸出規範

- **語言**：繁體中文
- **格式**：單一份結構化 Markdown 文件
- **內容**：預設為 100 個案例，每個案例都要有情境、SQL、說明、資料庫注意事項、常見陷阱或實務建議
- **方言要求**：主要 SQL 範例必須嚴格符合目標資料庫，不得混入其他資料庫的專屬語法
- **安全要求**：遇到高風險操作時，必須加入風險提示與較安全的執行建議

## 品質標準

- 案例數量必須精確符合要求
- 不得產出泛用 SQL 清單而忽略目標資料庫脈絡
- 不得捏造目標資料庫不存在的功能、函式、保留字或管理能力
- 章節分布必須合理，至少覆蓋 CRUD、JOIN、聚合、交易、索引、效能與管理主題
- 命名、語氣與格式需在全文保持一致