# SQL 速查手冊 for MariaDB：100 個高頻使用案例

## 適用對象與使用方式

本手冊以 MariaDB 10.6+ 到 11.x 常見實務為基準，面向初階到中階開發者、資料工程師與日常需要維護資料庫的工程團隊。

全文使用同一套 `shop_demo` 電商示範 schema，主要資料表包含：

- `customers`：客戶主檔
- `categories`：商品分類，支援階層
- `products`：商品資料
- `orders`：訂單主檔
- `order_items`：訂單明細
- `inventory_movements`：庫存異動紀錄
- `admin_audit_logs`：管理操作稽核紀錄

## 目錄

- 第 1 章：資料庫與資料表管理（案例 01-08）
- 第 2 章：基本查詢與條件篩選（案例 09-17）
- 第 3 章：新增、更新、刪除（案例 18-26）
- 第 4 章：排序、分頁與限制（案例 27-33）
- 第 5 章：JOIN 與多表查詢（案例 34-42）
- 第 6 章：聚合、分組與 HAVING（案例 43-50）
- 第 7 章：子查詢、CTE 與集合操作（案例 51-58）
- 第 8 章：字串、日期、數值與分析函式（案例 59-68）
- 第 9 章：交易控制、鎖定與一致性（案例 69-76）
- 第 10 章：索引、執行效能與查詢優化（案例 77-85）
- 第 11 章：View、Procedure、Function、Trigger、Event（案例 86-93）
- 第 12 章：使用者、角色、權限與安全（案例 94-97）
- 第 13 章：匯入匯出、備份與管理操作（案例 98-100）

## 第 1 章：資料庫與資料表管理

## 案例 01：建立新的業務資料庫

**使用情境**
當你要為新系統建立獨立資料庫，並先定好字元集與排序規則時使用。

**SQL 範例**
```sql
CREATE DATABASE IF NOT EXISTS shop_demo
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;
```

**說明**
`utf8mb4` 是 MariaDB 實務上的安全預設值，能正確存放多語系文字與表情符號。先在資料庫層決定字元集，可降低後續資料表設定不一致的風險。

**資料庫注意事項**
- 若伺服器層已有不同預設字元集，資料表仍可能繼承各自設定，建立後最好再檢查實際 DDL。

**常見陷阱／實務建議**
- 不要沿用舊系統常見的 `utf8`，那在 MariaDB/MySQL 生態裡通常不是完整的 UTF-8。

## 案例 02：調整既有資料庫的預設字元集與排序規則

**使用情境**
資料庫已經存在，但你希望未來新建立的資料表與欄位一律採用新的字元集與排序規則。

**SQL 範例**
```sql
ALTER DATABASE shop_demo
  CHARACTER SET = utf8mb4
  COLLATE = utf8mb4_unicode_ci;
```

**說明**
這會調整資料庫層級的預設值，之後新建立的物件若未明確指定字元集，會沿用這裡的設定。

**資料庫注意事項**
- 這不會自動改寫既有資料表與欄位的字元集；舊資料要另用 `ALTER TABLE ... CONVERT TO CHARACTER SET ...` 處理。

**常見陷阱／實務建議**
- 不要誤以為改完資料庫預設值，舊表就跟著同步；上線前應抽查幾張核心表的 `SHOW CREATE TABLE`。

## 案例 03：建立核心業務資料表

**使用情境**
你要先建立一套可支援會員、商品、訂單與庫存管理的基礎 schema。

**SQL 範例**
```sql
CREATE TABLE IF NOT EXISTS customers (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  customer_code VARCHAR(20) NOT NULL,
  full_name VARCHAR(100) NOT NULL,
  email VARCHAR(255) NOT NULL,
  phone VARCHAR(30) NULL,
  tier ENUM('BRONZE', 'SILVER', 'GOLD') NOT NULL DEFAULT 'BRONZE',
  city VARCHAR(100) NULL,
  deleted_at DATETIME NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  UNIQUE KEY uq_customers_code (customer_code),
  UNIQUE KEY uq_customers_email (email)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS categories (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  parent_id BIGINT UNSIGNED NULL,
  name VARCHAR(120) NOT NULL,
  slug VARCHAR(120) NOT NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  UNIQUE KEY uq_categories_slug (slug)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS products (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  category_id BIGINT UNSIGNED NOT NULL,
  sku VARCHAR(40) NOT NULL,
  product_name VARCHAR(150) NOT NULL,
  price DECIMAL(12, 2) NOT NULL,
  cost DECIMAL(12, 2) NOT NULL,
  stock_qty INT NOT NULL DEFAULT 0,
  status ENUM('ACTIVE', 'INACTIVE') NOT NULL DEFAULT 'ACTIVE',
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  UNIQUE KEY uq_products_sku (sku)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS orders (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  customer_id BIGINT UNSIGNED NOT NULL,
  order_no VARCHAR(32) NOT NULL,
  order_status ENUM('PENDING', 'PAID', 'SHIPPED', 'CANCELLED', 'COMPLETED') NOT NULL DEFAULT 'PENDING',
  payment_status ENUM('UNPAID', 'PAID', 'REFUNDED') NOT NULL DEFAULT 'UNPAID',
  order_date DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  shipped_at DATETIME NULL,
  total_amount DECIMAL(12, 2) NOT NULL DEFAULT 0.00,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  UNIQUE KEY uq_orders_order_no (order_no)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS order_items (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  order_id BIGINT UNSIGNED NOT NULL,
  product_id BIGINT UNSIGNED NOT NULL,
  qty INT NOT NULL,
  unit_price DECIMAL(12, 2) NOT NULL,
  line_amount DECIMAL(12, 2) NOT NULL,
  PRIMARY KEY (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS inventory_movements (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  product_id BIGINT UNSIGNED NOT NULL,
  movement_type ENUM('IN', 'OUT', 'ADJUST') NOT NULL,
  qty INT NOT NULL,
  reason VARCHAR(100) NOT NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS admin_audit_logs (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  actor VARCHAR(100) NOT NULL,
  action_name VARCHAR(100) NOT NULL,
  target_table VARCHAR(64) NOT NULL,
  target_id BIGINT UNSIGNED NULL,
  changed_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  detail_text TEXT NULL,
  PRIMARY KEY (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

**說明**
先把交易主體、產品主體、訂單主體與稽核主體分開，後續不論是查詢、權限或索引規劃都更容易維護。

**資料庫注意事項**
- MariaDB 的 `AUTO_INCREMENT` 必須搭配索引鍵使用，通常直接掛在主鍵欄位即可。

**常見陷阱／實務建議**
- 不要一開始就把所有資訊塞進 `orders` 單表；拆出 `order_items` 才能保留明細粒度並避免更新異常。

## 案例 04：補上外鍵與關聯完整性

**使用情境**
資料表先建立完成，接著要明確宣告父子關係，避免寫入孤兒資料。

**SQL 範例**
```sql
ALTER TABLE categories
  ADD CONSTRAINT fk_categories_parent
    FOREIGN KEY (parent_id) REFERENCES categories(id)
    ON DELETE SET NULL
    ON UPDATE CASCADE;

ALTER TABLE products
  ADD CONSTRAINT fk_products_category
    FOREIGN KEY (category_id) REFERENCES categories(id)
    ON DELETE RESTRICT
    ON UPDATE CASCADE;

ALTER TABLE orders
  ADD CONSTRAINT fk_orders_customer
    FOREIGN KEY (customer_id) REFERENCES customers(id)
    ON DELETE RESTRICT
    ON UPDATE CASCADE;

ALTER TABLE order_items
  ADD CONSTRAINT fk_order_items_order
    FOREIGN KEY (order_id) REFERENCES orders(id)
    ON DELETE CASCADE
    ON UPDATE CASCADE,
  ADD CONSTRAINT fk_order_items_product
    FOREIGN KEY (product_id) REFERENCES products(id)
    ON DELETE RESTRICT
    ON UPDATE CASCADE;

ALTER TABLE inventory_movements
  ADD CONSTRAINT fk_inventory_movements_product
    FOREIGN KEY (product_id) REFERENCES products(id)
    ON DELETE RESTRICT
    ON UPDATE CASCADE;
```

**說明**
外鍵把資料完整性下沉到資料庫層，能在應用程式出錯時保住基本一致性。例如刪除訂單時自動連動刪除明細，就能避免殘留孤兒資料。

**資料庫注意事項**
- InnoDB 才支援可靠的外鍵行為；若使用其他儲存引擎，外鍵可能不會真的生效。

**常見陷阱／實務建議**
- `ON DELETE CASCADE` 只該用在真的願意一起刪掉的明細資料，對主檔與歷史資料要保守評估。

## 案例 05：替既有資料表增加新欄位與索引

**使用情境**
業務需求變更後，需要在既有表增加欄位，並同步補上查詢會用到的索引。

**SQL 範例**
```sql
ALTER TABLE products
  ADD COLUMN weight_grams INT NULL AFTER price,
  ADD INDEX idx_products_status_created (status, created_at);
```

**說明**
`ALTER TABLE` 可一次完成欄位與索引變更，減少多次 DDL 帶來的等待與風險。這類需求常見於新功能上線前的 schema 擴充。

**資料庫注意事項**
- 大表執行 DDL 可能造成鎖等待與重建成本，上線前要確認可接受的維護窗口。

**常見陷阱／實務建議**
- 不要先加欄位、之後再補索引卻忘了發版順序；若新查詢立即上線，先準備好索引通常更穩妥。

## 案例 06：建立暫存表處理一次性分析

**使用情境**
你想做一輪中間計算或報表整理，但不想把臨時資料永久寫進正式表。

**SQL 範例**
```sql
CREATE TEMPORARY TABLE tmp_top_customers AS
SELECT
  o.customer_id,
  SUM(o.total_amount) AS total_spent
FROM orders AS o
WHERE o.payment_status = 'PAID'
GROUP BY o.customer_id
HAVING SUM(o.total_amount) >= 50000;
```

**說明**
暫存表只在目前連線存在，適合做 ETL 中繼、人工分析、資料比對或一次性報表拆解。

**資料庫注意事項**
- `TEMPORARY TABLE` 只對當前 session 可見，連線中斷後就會消失。

**常見陷阱／實務建議**
- 臨時表雖然方便，但仍會佔用磁碟或記憶體；大量分析時不要把它當成無成本結構。

## 案例 07：查看資料表實際 DDL

**使用情境**
你要確認資料表的真實結構、索引、預設值或外鍵，而不是只看 ORM 定義。

**SQL 範例**
```sql
SHOW CREATE TABLE orders;
```

**說明**
`SHOW CREATE TABLE` 是最直接的真相來源，尤其在排查字元集、儲存引擎、索引名稱與外鍵細節時非常實用。

**資料庫注意事項**
- ORM migration 與實際 DB 結構偶爾會漂移，正式排查應以資料庫輸出為準。

**常見陷阱／實務建議**
- 不要只靠 `DESCRIBE`；欄位清單不會完整顯示表級選項、完整索引與約束定義。

## 案例 08：快速清空暫存或中繼資料表

**使用情境**
中繼表或 staging table 需要定期清空資料，並重置自動編號時使用。

**SQL 範例**
```sql
TRUNCATE TABLE admin_audit_logs;
```

**說明**
`TRUNCATE TABLE` 比逐筆 `DELETE` 更快，適合一次清空整張表。但它本質上是高風險操作，通常只應用在可重建或可丟棄的資料。

**資料庫注意事項**
- `TRUNCATE` 會重置 `AUTO_INCREMENT`，且通常不能像一般 DML 那樣細緻回滾。

**常見陷阱／實務建議**
- 不要對正式歷史資料直接 `TRUNCATE`；若只是清理舊資料，應先改用條件式刪除與批次策略。

## 第 2 章：基本查詢與條件篩選

## 案例 09：查詢特定欄位而不是使用 `SELECT *`

**使用情境**
你只需要客戶清單的少數欄位，想降低網路傳輸與後續維護成本。

**SQL 範例**
```sql
SELECT
  id,
  customer_code,
  full_name,
  email,
  tier,
  city
FROM customers
WHERE deleted_at IS NULL;
```

**說明**
明確列出欄位可降低 I/O，也能避免未來表結構變動時查詢行為悄悄改變。

**資料庫注意事項**
- MariaDB 優化器會根據實際投影欄位決定讀取成本；欄位越少，越有機會讓索引覆蓋查詢成立。

**常見陷阱／實務建議**
- 正式系統不要養成 `SELECT *` 習慣，尤其是 API、批次與報表查詢。

## 案例 10：用別名與運算欄位做較易讀的輸出

**使用情境**
你要直接輸出更具商業語意的欄位，讓報表或檢查結果更容易閱讀。

**SQL 範例**
```sql
SELECT
  order_no AS 訂單編號,
  total_amount AS 訂單金額,
  total_amount * 0.05 AS 預估手續費,
  DATE(order_date) AS 下單日期
FROM orders;
```

**說明**
欄位別名與簡單運算可讓查詢結果直接對應商務語意，適合用在 ad hoc 檢查與匯出前整理。

**資料庫注意事項**
- 若別名包含空白或特殊字元，建議使用引號以避免解析差異。

**常見陷阱／實務建議**
- 計算欄位如果在多個地方重複出現，應考慮做成 view 或由應用層封裝，不要到處複製貼上。

## 案例 11：使用比較運算與多條件篩選

**使用情境**
你要找出最近仍未付款、且金額超過門檻的訂單做催收或提醒。

**SQL 範例**
```sql
SELECT
  id,
  order_no,
  customer_id,
  total_amount,
  order_date
FROM orders
WHERE payment_status = 'UNPAID'
  AND total_amount >= 3000
  AND order_date >= NOW() - INTERVAL 7 DAY;
```

**說明**
條件式查詢是所有報表與流程的基礎。把狀態、金額、日期一起篩掉，通常比查回來後再在應用層過濾更有效率。

**資料庫注意事項**
- 日期欄位若有索引，與狀態欄位組成複合索引時通常能進一步降低掃描成本。

**常見陷阱／實務建議**
- 條件越常一起出現，越要檢討是否該設計複合索引，而不是每個欄位各自一條索引。

## 案例 12：使用 `IN` 與 `BETWEEN` 做多值與區間查詢

**使用情境**
你要一次找出特定狀態、且價格落在目標區間內的商品。

**SQL 範例**
```sql
SELECT
  id,
  sku,
  product_name,
  price,
  status
FROM products
WHERE status IN ('ACTIVE', 'INACTIVE')
  AND price BETWEEN 100 AND 2000;
```

**說明**
`IN` 適合少量離散值篩選，`BETWEEN` 適合連續區間。兩者搭配可讓商務條件更直觀。

**資料庫注意事項**
- `BETWEEN` 是包含上下界的，處理時間區間時要特別注意秒數與毫秒邊界。

**常見陷阱／實務建議**
- 日期欄位常建議改寫成 `>= 起點 AND < 終點`，會比 `BETWEEN` 更不容易踩到邊界錯誤。

## 案例 13：使用 `LIKE` 進行模糊搜尋

**使用情境**
客服或營運人員只記得客戶姓名片段，需要快速查出可能對象。

**SQL 範例**
```sql
SELECT
  id,
  full_name,
  email,
  phone
FROM customers
WHERE full_name LIKE '%陳%'
  AND deleted_at IS NULL;
```

**說明**
`LIKE` 是最基本的模糊搜尋方式，對小型資料表或後台查詢很常見。

**資料庫注意事項**
- 前綴與後綴都加 `%` 的寫法通常無法有效使用一般 B-Tree 索引。

**常見陷阱／實務建議**
- 若模糊搜尋是高頻功能，應考慮 Full-Text、搜尋引擎或專門的搜尋索引策略。

## 案例 14：找出尚未完成某個流程的資料

**使用情境**
你要找出還沒出貨、尚未填時間戳記的訂單，作為物流處理清單。

**SQL 範例**
```sql
SELECT
  id,
  order_no,
  order_status,
  payment_status,
  shipped_at
FROM orders
WHERE shipped_at IS NULL
  AND payment_status = 'PAID';
```

**說明**
`IS NULL` 常用來表示流程尚未完成、欄位尚未補齊或資料仍在待處理狀態。

**資料庫注意事項**
- `NULL` 不是空字串，也不是 0；判斷時必須用 `IS NULL` 或 `IS NOT NULL`。

**常見陷阱／實務建議**
- 千萬不要寫成 `shipped_at = NULL`，那不會得到你要的結果。

## 案例 15：用 `CASE` 做查詢內分級與轉換

**使用情境**
你要在報表中直接把訂單金額分成不同客戶價值區間。

**SQL 範例**
```sql
SELECT
  order_no,
  total_amount,
  CASE
    WHEN total_amount >= 20000 THEN '大型訂單'
    WHEN total_amount >= 5000 THEN '中型訂單'
    ELSE '一般訂單'
  END AS order_band
FROM orders;
```

**說明**
`CASE` 可以把原始資料轉成更容易理解的業務分類，適合做報表、標記與條件聚合前處理。

**資料庫注意事項**
- `CASE` 若放在 `WHERE` 內做複雜判斷，可能讓查詢可讀性變差，也可能影響索引使用。

**常見陷阱／實務建議**
- 分級邏輯若牽涉商業規則，建議把門檻集中管理，不要散落在多支 SQL 中。

## 案例 16：以日期區間查詢最近資料

**使用情境**
你要抓某一天的所有訂單，但想保留索引可用性並避免跨時區邊界問題。

**SQL 範例**
```sql
SELECT
  id,
  order_no,
  order_date,
  total_amount
FROM orders
WHERE order_date >= '2026-03-01 00:00:00'
  AND order_date < '2026-03-02 00:00:00';
```

**說明**
用半開區間表達日期範圍，通常比包 `DATE(order_date)` 更容易讓索引生效，也更容易避免日終邊界錯誤。

**資料庫注意事項**
- 若應用程式與 DB 時區不同，查詢時間邊界必須先在同一時區下換算。

**常見陷阱／實務建議**
- 不要直接對索引欄位套函式，例如 `DATE(order_date)`，那常會讓 MariaDB 放棄索引。

## 案例 17：用 `EXISTS` 找出符合關聯條件的主檔

**使用情境**
你要找出至少有一筆已付款訂單的客戶名單做行銷活動。

**SQL 範例**
```sql
SELECT
  c.id,
  c.full_name,
  c.email,
  c.tier
FROM customers AS c
WHERE EXISTS (
  SELECT 1
  FROM orders AS o
  WHERE o.customer_id = c.id
    AND o.payment_status = 'PAID'
);
```

**說明**
`EXISTS` 很適合表達「是否存在至少一筆關聯資料」，尤其在不需要把子表欄位帶回來時可保持語意清楚。

**資料庫注意事項**
- MariaDB 優化器可能將 `EXISTS` 轉成 semijoin 之類的執行策略；實務上仍要看 `EXPLAIN` 結果。

**常見陷阱／實務建議**
- 若只為了判斷存在與否，不要先 `JOIN` 再 `DISTINCT`，那通常比直接 `EXISTS` 更笨重。

## 第 3 章：新增、更新、刪除

## 案例 18：插入單筆主檔資料

**使用情境**
新客戶註冊完成後，要把客戶基本資料寫入主檔。

**SQL 範例**
```sql
INSERT INTO customers (
  customer_code,
  full_name,
  email,
  phone,
  tier,
  city
) VALUES (
  'C202603220001',
  '王小明',
  'ming.wang@example.com',
  '0912-345-678',
  'BRONZE',
  'Taipei'
);
```

**說明**
最基本的 `INSERT` 仍是大量交易系統的核心動作。明確列出欄位可讓未來 schema 擴充時更安全。

**資料庫注意事項**
- 若目標欄位有 `NOT NULL` 或唯一約束，缺值或重複值都會直接失敗。

**常見陷阱／實務建議**
- 永遠指定欄位清單，不要依賴表中欄位順序。

## 案例 19：一次插入多筆資料

**使用情境**
你要批次建立多筆商品資料，降低 round-trip 次數與寫入成本。

**SQL 範例**
```sql
INSERT INTO products (
  category_id,
  sku,
  product_name,
  price,
  cost,
  stock_qty,
  status
) VALUES
  (1, 'SKU-1001', '無線滑鼠', 699.00, 420.00, 100, 'ACTIVE'),
  (1, 'SKU-1002', '機械鍵盤', 2490.00, 1680.00, 60, 'ACTIVE'),
  (2, 'SKU-2001', '27 吋顯示器', 6990.00, 5200.00, 35, 'ACTIVE');
```

**說明**
多列插入通常比一筆一筆送更有效率，也比較適合初始化資料與小型批次同步。

**資料庫注意事項**
- 單次批次若過大，可能受封包大小與交易長度限制影響。

**常見陷阱／實務建議**
- 批次大小要實測，不要把數十萬筆塞成一條 SQL；分批通常更穩定。

## 案例 20：使用 `INSERT IGNORE` 略過重複鍵錯誤

**使用情境**
你在做去重導入時，希望重複的唯一鍵略過，不要整批中斷。

**SQL 範例**
```sql
INSERT IGNORE INTO customers (
  customer_code,
  full_name,
  email,
  phone,
  city
) VALUES
  ('C202603220002', '陳美玲', 'mei.chen@example.com', '0988-111-222', 'Taichung'),
  ('C202603220003', '林志成', 'ming.wang@example.com', '0988-333-444', 'Tainan');
```

**說明**
當碰到唯一鍵衝突時，`INSERT IGNORE` 會把錯誤降級為 warning，讓其他合法資料繼續插入。

**資料庫注意事項**
- 被忽略的資料不會更新既有列；若你要同步新值，應改用 upsert。

**常見陷阱／實務建議**
- 不要把 `INSERT IGNORE` 當成萬用解法，否則很容易靜默吞掉資料品質問題。

## 案例 21：使用 `ON DUPLICATE KEY UPDATE` 做 upsert

**使用情境**
商品主檔以 `sku` 為唯一鍵同步資料，若已存在就更新價格與庫存。

**SQL 範例**
```sql
INSERT INTO products (
  category_id,
  sku,
  product_name,
  price,
  cost,
  stock_qty,
  status
) VALUES (
  1,
  'SKU-1001',
  '無線滑鼠',
  749.00,
  430.00,
  120,
  'ACTIVE'
)
ON DUPLICATE KEY UPDATE
  product_name = VALUES(product_name),
  price = VALUES(price),
  cost = VALUES(cost),
  stock_qty = VALUES(stock_qty),
  status = VALUES(status);
```

**說明**
upsert 很適合同步主資料、匯入商品目錄與週期性更新快取表。唯一鍵命中時會直接轉成更新。

**資料庫注意事項**
- `VALUES(col)` 在這裡代表插入語句原本要寫入的值；升版或跨方言時要留意相容性說明。

**常見陷阱／實務建議**
- 更新欄位不要一股腦全覆蓋；對於人工作業欄位或稽核欄位，通常需要保留更精細的策略。

## 案例 22：建立訂單並取得新主鍵

**使用情境**
你要在同一個交易中新增訂單主檔與明細，並取得剛插入的 `order_id`。

**SQL 範例**
```sql
START TRANSACTION;

INSERT INTO orders (
  customer_id,
  order_no,
  order_status,
  payment_status,
  order_date,
  total_amount
) VALUES (
  1,
  'SO-20260322-0001',
  'PENDING',
  'UNPAID',
  NOW(),
  0.00
);

SET @new_order_id := LAST_INSERT_ID();

INSERT INTO order_items (
  order_id,
  product_id,
  qty,
  unit_price,
  line_amount
) VALUES
  (@new_order_id, 1, 2, 699.00, 1398.00),
  (@new_order_id, 2, 1, 2490.00, 2490.00);

COMMIT;
```

**說明**
`LAST_INSERT_ID()` 會回傳目前連線最近一次成功插入的自動編號，適合在交易內串起主檔與明細。

**資料庫注意事項**
- `LAST_INSERT_ID()` 是 session 級別值，不會被其他連線干擾，但必須在同一連線內使用。

**常見陷阱／實務建議**
- 主檔、明細與後續總額計算最好放在同一交易中，避免半套資料落地。

## 案例 23：用彙總結果回寫主表欄位

**使用情境**
訂單明細更新後，你要重新計算訂單總額並回寫 `orders.total_amount`。

**SQL 範例**
```sql
UPDATE orders AS o
JOIN (
  SELECT
    order_id,
    SUM(line_amount) AS new_total_amount
  FROM order_items
  GROUP BY order_id
) AS s
  ON s.order_id = o.id
SET o.total_amount = s.new_total_amount;
```

**說明**
這是典型的匯總回寫模式，常見於訂單金額、庫存快照、統計欄位或 cache 欄位維護。

**資料庫注意事項**
- 批次更新大表時要留意鎖定時間與 undo log 壓力。

**常見陷阱／實務建議**
- 若總額是高頻查詢欄位，可以保存；但一定要有明確的重算策略，避免主表與明細失同步。

## 案例 24：使用 `UPDATE ... JOIN` 批次調整客戶等級

**使用情境**
你要根據最近累積消費金額，重新計算會員等級。

**SQL 範例**
```sql
UPDATE customers AS c
JOIN (
  SELECT
    customer_id,
    SUM(total_amount) AS total_spent
  FROM orders
  WHERE payment_status = 'PAID'
  GROUP BY customer_id
) AS s
  ON s.customer_id = c.id
SET c.tier = CASE
  WHEN s.total_spent >= 50000 THEN 'GOLD'
  WHEN s.total_spent >= 20000 THEN 'SILVER'
  ELSE 'BRONZE'
END;
```

**說明**
MariaDB 的 `UPDATE ... JOIN` 非常適合做主檔同步與批次派生欄位更新。

**資料庫注意事項**
- 若 join 結果不是一對一，更新結果可能超出預期；先用 `SELECT` 驗證目標集合很重要。

**常見陷阱／實務建議**
- 先寫成 `SELECT` 看看會命中哪些列，再改成 `UPDATE`，這是避免大範圍誤更新的基本習慣。

## 案例 25：做軟刪除而不是直接物理刪除

**使用情境**
客戶停用後你希望先保留歷史資料與關聯，而不是立刻永久移除。

**SQL 範例**
```sql
UPDATE customers
SET deleted_at = NOW()
WHERE id = 1001
  AND deleted_at IS NULL;
```

**說明**
軟刪除適合需要稽核、追蹤與復原空間的場景。對交易系統而言，直接刪主檔往往比你想像中更危險。

**資料庫注意事項**
- 軟刪除後所有查詢都必須持續記得排除 `deleted_at IS NOT NULL` 的資料。

**常見陷阱／實務建議**
- 若採軟刪除，建議把「只看有效資料」封裝成 view 或 repository 規則，避免漏寫條件。

## 案例 26：分批刪除舊稽核資料

**使用情境**
稽核紀錄保留期已滿，你要逐批清掉舊資料，避免單次刪除鎖太久。

**SQL 範例**
```sql
DELETE FROM admin_audit_logs
WHERE changed_at < NOW() - INTERVAL 180 DAY
LIMIT 5000;
```

**說明**
對大表做條件刪除時，搭配 `LIMIT` 分批執行通常比一次砍到底更穩定，可降低長交易與鎖衝擊。

**資料庫注意事項**
- `DELETE ... LIMIT` 只是限制刪除數量，不保證順序；若要可預期批次，應加上鍵值條件。

**常見陷阱／實務建議**
- 高風險刪除務必先改成 `SELECT COUNT(*)` 驗證影響筆數，正式執行前最好先備份或在從庫演練。

## 第 4 章：排序、分頁與限制

## 案例 27：依多個欄位排序

**使用情境**
你要讓後台先看到未完成訂單，再看最新與最高金額的項目。

**SQL 範例**
```sql
SELECT
  order_no,
  order_status,
  order_date,
  total_amount
FROM orders
ORDER BY order_status ASC, order_date DESC, total_amount DESC;
```

**說明**
多欄排序能把結果集按商務優先序排好，適合後台列表與人工處理清單。

**資料庫注意事項**
- 排序欄位若沒有合適索引，MariaDB 可能需要額外排序與使用暫存空間。

**常見陷阱／實務建議**
- 如果列表是高頻查詢，排序欄位應納入索引設計，而不是每次都讓 DB 臨時排序。

## 案例 28：使用 `LIMIT` 與 `OFFSET` 做基本分頁

**使用情境**
你要做最傳統的頁碼式列表，前端指定頁數與每頁筆數。

**SQL 範例**
```sql
SELECT
  id,
  order_no,
  customer_id,
  total_amount,
  order_date
FROM orders
ORDER BY order_date DESC, id DESC
LIMIT 20 OFFSET 40;
```

**說明**
這代表跳過前 40 筆、取接下來 20 筆，適合資料量不大或管理後台一般列表。

**資料庫注意事項**
- `OFFSET` 越大，MariaDB 通常要掃過越多資料後才能丟棄前面的列。

**常見陷阱／實務建議**
- 深頁分頁不要只靠 `OFFSET`；大表應改用 seek pagination。

## 案例 29：使用 seek pagination 做深頁分頁

**使用情境**
你要在大量訂單表中做高效滾動分頁，不想讓深頁越翻越慢。

**SQL 範例**
```sql
SELECT
  id,
  order_no,
  order_date,
  total_amount
FROM orders
WHERE (order_date < '2026-03-22 12:00:00')
   OR (order_date = '2026-03-22 12:00:00' AND id < 10500)
ORDER BY order_date DESC, id DESC
LIMIT 20;
```

**說明**
seek pagination 以「上一頁最後一筆」當游標，能避免大量 `OFFSET` 造成的掃描浪費。

**資料庫注意事項**
- 排序鍵必須穩定且可唯一定位；常見組合是時間戳加主鍵。

**常見陷阱／實務建議**
- 若只用 `order_date` 當游標，遇到同秒多筆資料可能重複或漏資料，所以通常要再加主鍵。

## 案例 30：用 `FIELD()` 自訂商務排序順序

**使用情境**
你想讓訂單狀態依商務處理優先級排序，而不是字母順序。

**SQL 範例**
```sql
SELECT
  order_no,
  order_status,
  payment_status,
  order_date
FROM orders
ORDER BY FIELD(order_status, 'PENDING', 'PAID', 'SHIPPED', 'COMPLETED', 'CANCELLED'),
         order_date DESC;
```

**說明**
`FIELD()` 是 MariaDB/MySQL 系常用技巧，可快速定義自訂排序規則。

**資料庫注意事項**
- 這類函式排序通常無法像純索引排序那樣高效，適合筆數有限的後台查詢。

**常見陷阱／實務建議**
- 若排序規則是長期固定業務邏輯，應考慮改成代碼欄位或映射表，避免 SQL 中散落硬編碼。

## 案例 31：讓空值排在最後面

**使用情境**
你想優先查看已出貨訂單，最後才顯示還沒出貨的資料。

**SQL 範例**
```sql
SELECT
  order_no,
  shipped_at,
  order_status
FROM orders
ORDER BY shipped_at IS NULL ASC, shipped_at DESC;
```

**說明**
利用布林運算結果先排序，可控制 `NULL` 的顯示位置，這在 MariaDB 沒有 `NULLS LAST` 語法時很實用。

**資料庫注意事項**
- `shipped_at IS NULL` 會產生 0/1 值；實務上可把這視為排序輔助欄位。

**常見陷阱／實務建議**
- 若清單是大量高頻查詢，應評估是否需要額外狀態欄位來簡化排序邏輯。

## 案例 32：隨機抽樣少量資料做人工檢查

**使用情境**
你想快速抽幾筆商品做資料品質人工驗證。

**SQL 範例**
```sql
SELECT
  id,
  sku,
  product_name,
  price
FROM products
ORDER BY RAND()
LIMIT 5;
```

**說明**
`ORDER BY RAND()` 對小表或臨時抽樣很方便，能快速取得看起來隨機的幾筆資料。

**資料庫注意事項**
- 對大表來說，`RAND()` 通常很昂貴，因為每列都可能需要計算與排序。

**常見陷阱／實務建議**
- 正式環境大表抽樣不要濫用 `ORDER BY RAND()`；可改用 ID 區段抽樣或離線抽樣策略。

## 案例 33：同時查頁面資料與總筆數

**使用情境**
分頁 API 需要同時返回目前頁資料與總筆數給前端顯示。

**SQL 範例**
```sql
SELECT
  id,
  order_no,
  order_status,
  total_amount,
  order_date
FROM orders
WHERE payment_status = 'PAID'
ORDER BY order_date DESC, id DESC
LIMIT 20 OFFSET 0;

SELECT COUNT(*) AS total_rows
FROM orders
WHERE payment_status = 'PAID';
```

**說明**
分頁查詢與總數統計通常拆成兩條 SQL 比較直觀，也較容易分別優化。

**資料庫注意事項**
- 在高併發系統中，頁面資料與總數可能不是完全同一瞬間快照，這是正常現象。

**常見陷阱／實務建議**
- 不要過度依賴精確總筆數；對超大資料集，近似值或延遲更新的統計有時更實際。

## 第 5 章：JOIN 與多表查詢

## 案例 34：查詢訂單與客戶基本資料

**使用情境**
你要在訂單列表中直接看到下單客戶名稱與會員等級。

**SQL 範例**
```sql
SELECT
  o.order_no,
  o.order_date,
  o.total_amount,
  c.full_name,
  c.tier
FROM orders AS o
JOIN customers AS c
  ON c.id = o.customer_id;
```

**說明**
這是最典型的內連接查詢，用來把主交易資料與主檔資訊組合在一起。

**資料庫注意事項**
- 若 `orders.customer_id` 沒有索引，join 成本通常會明顯上升。

**常見陷阱／實務建議**
- 在多表 join 前先明確知道主表是誰，否則 SQL 很容易越寫越難維護。

## 案例 35：使用 `LEFT JOIN` 保留主表資料

**使用情境**
你要列出所有商品，即使它尚未被正確分類，也要顯示在結果中。

**SQL 範例**
```sql
SELECT
  p.sku,
  p.product_name,
  p.price,
  c.name AS category_name
FROM products AS p
LEFT JOIN categories AS c
  ON c.id = p.category_id;
```

**說明**
`LEFT JOIN` 會保留左表全部資料，即使右表沒有對應列，也很適合做資料完整性檢查。

**資料庫注意事項**
- 條件若寫在 `WHERE` 而不是 `ON`，可能會把 `LEFT JOIN` 意外變成內連接效果。

**常見陷阱／實務建議**
- 想保留左表所有資料時，過濾右表條件要特別注意放置位置。

## 案例 36：用自我連接查分類階層

**使用情境**
分類表用 `parent_id` 表示上下層，你想同時顯示子分類與父分類名稱。

**SQL 範例**
```sql
SELECT
  child.id,
  child.name AS child_category,
  parent.name AS parent_category
FROM categories AS child
LEFT JOIN categories AS parent
  ON parent.id = child.parent_id;
```

**說明**
同一張表在不同角色下各用一個別名，是階層資料最常見的基本查法。

**資料庫注意事項**
- 自我連接只適合查固定層級；若要走整棵樹，應考慮遞迴 CTE。

**常見陷阱／實務建議**
- 別名要取得清楚，不然一旦欄位變多就很容易讀不懂自己寫的 SQL。

## 案例 37：查詢訂單中的商品明細

**使用情境**
你要顯示某張訂單包含哪些商品、各買幾件與單價多少。

**SQL 範例**
```sql
SELECT
  o.order_no,
  p.sku,
  p.product_name,
  oi.qty,
  oi.unit_price,
  oi.line_amount
FROM orders AS o
JOIN order_items AS oi
  ON oi.order_id = o.id
JOIN products AS p
  ON p.id = oi.product_id
WHERE o.order_no = 'SO-20260322-0001';
```

**說明**
透過主檔、明細、商品三表 join，就能完整還原訂單內容，這是電商與 ERP 最常見的查詢之一。

**資料庫注意事項**
- 訂單明細通常會成長很快，`order_items.order_id` 與 `order_items.product_id` 都應該有索引。

**常見陷阱／實務建議**
- 若是列表畫面，不一定要一次帶全明細；可先顯示主檔，再視需求載入明細。

## 案例 38：找出尚未下單的客戶

**使用情境**
你要做新會員啟用或沉睡名單分析，找出從未有訂單的客戶。

**SQL 範例**
```sql
SELECT
  c.id,
  c.full_name,
  c.email,
  c.created_at
FROM customers AS c
LEFT JOIN orders AS o
  ON o.customer_id = c.id
WHERE o.id IS NULL
  AND c.deleted_at IS NULL;
```

**說明**
這是 anti-join 的經典寫法，透過 `LEFT JOIN` 搭配 `IS NULL` 找出不存在關聯資料的主檔。

**資料庫注意事項**
- 在某些資料量與索引條件下，`NOT EXISTS` 可能會更好，仍應以 `EXPLAIN` 驗證。

**常見陷阱／實務建議**
- 如果 `orders` 可能存在重複或特殊狀態，條件要明確定義「什麼算有下單」再查。

## 案例 39：計算每位客戶的累積消費

**使用情境**
你要在客戶名單中附上已付款訂單累積金額，作為會員經營依據。

**SQL 範例**
```sql
SELECT
  c.id,
  c.full_name,
  IFNULL(s.total_spent, 0) AS total_spent
FROM customers AS c
LEFT JOIN (
  SELECT
    customer_id,
    SUM(total_amount) AS total_spent
  FROM orders
  WHERE payment_status = 'PAID'
  GROUP BY customer_id
) AS s
  ON s.customer_id = c.id;
```

**說明**
把先聚合再 join 的模式用好，可以大幅提高查詢可讀性，也較容易維護與優化。

**資料庫注意事項**
- 聚合子查詢最好先把條件篩掉，再 group，避免不必要的中間資料量。

**常見陷阱／實務建議**
- 聚合結果若在多個報表都會用到，可考慮做成 view 或定時彙總表。

## 案例 40：查詢每個商品最近一次庫存異動

**使用情境**
你要在商品後台顯示最後一次進出貨資訊，方便營運快速判斷庫存異常。

**SQL 範例**
```sql
SELECT
  p.id,
  p.sku,
  p.product_name,
  m.movement_type,
  m.qty,
  m.reason,
  m.created_at
FROM products AS p
LEFT JOIN (
  SELECT im1.*
  FROM inventory_movements AS im1
  JOIN (
    SELECT product_id, MAX(id) AS max_id
    FROM inventory_movements
    GROUP BY product_id
  ) AS last_movements
    ON last_movements.max_id = im1.id
) AS m
  ON m.product_id = p.id;
```

**說明**
這種「先找每組最大鍵，再回表取完整資料」的模式很適合抓最後一筆狀態。

**資料庫注意事項**
- 若 `id` 不是時間順序代表值，就應改用真正的時間欄位加上唯一鍵組合判定最新資料。

**常見陷阱／實務建議**
- 最新一筆判斷標準要一致；有些系統是用 `created_at`，有些是用流水號，兩者不要混用。

## 案例 41：查詢近期已付款訂單與商品件數

**使用情境**
你想找出最近 30 天內已付款訂單的總件數與客戶資訊。

**SQL 範例**
```sql
SELECT
  o.order_no,
  c.full_name,
  SUM(oi.qty) AS total_qty,
  o.total_amount,
  o.order_date
FROM orders AS o
JOIN customers AS c
  ON c.id = o.customer_id
JOIN order_items AS oi
  ON oi.order_id = o.id
WHERE o.payment_status = 'PAID'
  AND o.order_date >= CURRENT_DATE - INTERVAL 30 DAY
GROUP BY o.id, o.order_no, c.full_name, o.total_amount, o.order_date;
```

**說明**
多表 join 後再聚合，是營運報表與 KPI 查詢最常見的組合型態。

**資料庫注意事項**
- 啟用 `ONLY_FULL_GROUP_BY` 類似規範時，`GROUP BY` 欄位要寫完整，避免語義含糊。

**常見陷阱／實務建議**
- 聚合前若 join 錯關聯，數字會被重複放大；寫報表 SQL 時要先驗證粒度。

## 案例 42：組出完整訂單檢視資料

**使用情境**
你要一次看見訂單、客戶、分類、商品與明細金額，方便做客服排查。

**SQL 範例**
```sql
SELECT
  o.order_no,
  c.full_name,
  cat.name AS category_name,
  p.product_name,
  oi.qty,
  oi.unit_price,
  oi.line_amount,
  o.order_status,
  o.payment_status
FROM orders AS o
JOIN customers AS c
  ON c.id = o.customer_id
JOIN order_items AS oi
  ON oi.order_id = o.id
JOIN products AS p
  ON p.id = oi.product_id
JOIN categories AS cat
  ON cat.id = p.category_id
WHERE o.id = 1;
```

**說明**
這類查詢在客服與營運排查時非常常見，因為它能把多個維度一次攤平檢視。

**資料庫注意事項**
- 攤平後列數會跟明細筆數一樣多，不適合直接拿來當主檔列表結果。

**常見陷阱／實務建議**
- 若畫面只需要一筆訂單概況，不要直接用明細級資料渲染整個列表。

## 第 6 章：聚合、分組與 HAVING

## 案例 43：依訂單狀態統計筆數與金額

**使用情境**
你要快速了解目前各種訂單狀態的分布情形。

**SQL 範例**
```sql
SELECT
  order_status,
  COUNT(*) AS order_count,
  SUM(total_amount) AS total_amount
FROM orders
GROUP BY order_status;
```

**說明**
最基礎的 `GROUP BY` 報表能快速建立全局視角，常用在每日營運檢查。

**資料庫注意事項**
- 若某狀態沒有任何資料，結果不會自動顯示 0；必要時需用維度表或手動補值。

**常見陷阱／實務建議**
- 指標定義要先談清楚，例如退款訂單金額是否還算在營收裡。

## 案例 44：使用 `HAVING` 篩選高價值客戶

**使用情境**
你要找出累積已付款消費超過門檻的客戶。

**SQL 範例**
```sql
SELECT
  customer_id,
  SUM(total_amount) AS total_spent
FROM orders
WHERE payment_status = 'PAID'
GROUP BY customer_id
HAVING SUM(total_amount) >= 30000;
```

**說明**
`WHERE` 篩原始列，`HAVING` 篩聚合結果。兩者各司其職，能讓報表語意更清晰。

**資料庫注意事項**
- 能先在 `WHERE` 過濾的條件就先過濾，通常可減少 group 成本。

**常見陷阱／實務建議**
- 不要把本來可放 `WHERE` 的條件通通塞進 `HAVING`，那常會讓查詢多做很多白工。

## 案例 45：統計有下單的唯一客戶數

**使用情境**
你要知道某段期間實際有下單行為的客戶數，而不是訂單數。

**SQL 範例**
```sql
SELECT
  COUNT(DISTINCT customer_id) AS active_customer_count
FROM orders
WHERE order_date >= CURRENT_DATE - INTERVAL 30 DAY;
```

**說明**
`COUNT(DISTINCT ...)` 可避免把同一客戶的多筆訂單重複計數，常用於活躍用戶與轉換率指標。

**資料庫注意事項**
- `DISTINCT` 在高基數資料上可能比較昂貴，必要時可用彙總表提前計算。

**常見陷阱／實務建議**
- 指標名稱要準確，活躍客戶數與訂單數是兩個完全不同的概念。

## 案例 46：做條件式聚合

**使用情境**
你要在一張報表裡同時看已付款、已出貨、已取消的訂單數量。

**SQL 範例**
```sql
SELECT
  COUNT(*) AS total_orders,
  SUM(CASE WHEN payment_status = 'PAID' THEN 1 ELSE 0 END) AS paid_orders,
  SUM(CASE WHEN order_status = 'SHIPPED' THEN 1 ELSE 0 END) AS shipped_orders,
  SUM(CASE WHEN order_status = 'CANCELLED' THEN 1 ELSE 0 END) AS cancelled_orders
FROM orders;
```

**說明**
條件式聚合可把多個 KPI 一次算出來，減少重複掃描資料表。

**資料庫注意事項**
- 若條件很多且會重複使用，應考慮抽成 view 或物化結果，避免多處重寫。

**常見陷阱／實務建議**
- 條件式聚合很容易越寫越長，超過一定複雜度就應分層處理，否則維護成本很高。

## 案例 47：使用 `WITH ROLLUP` 產生小計與總計

**使用情境**
你要看各分類銷售額，同時想在同一份結果中拿到總計。

**SQL 範例**
```sql
SELECT
  COALESCE(cat.name, '全部分類') AS category_name,
  SUM(oi.line_amount) AS sales_amount
FROM order_items AS oi
JOIN products AS p
  ON p.id = oi.product_id
JOIN categories AS cat
  ON cat.id = p.category_id
GROUP BY cat.name WITH ROLLUP;
```

**說明**
`WITH ROLLUP` 可以在 group 結果最後補上彙總列，做管理報表時相當方便。

**資料庫注意事項**
- rollup 產生的總計列分組欄位通常會是 `NULL`，呈現時要自行轉譯。

**常見陷阱／實務建議**
- 看到 `NULL` 分組列時先確認那是不是 rollup 總計，不要誤判成髒資料。

## 案例 48：依月份統計營收

**使用情境**
你要產出月營收趨勢圖的資料來源。

**SQL 範例**
```sql
SELECT
  DATE_FORMAT(order_date, '%Y-%m') AS revenue_month,
  SUM(total_amount) AS monthly_revenue
FROM orders
WHERE payment_status = 'PAID'
GROUP BY DATE_FORMAT(order_date, '%Y-%m')
ORDER BY revenue_month;
```

**說明**
把日期欄位轉成月份字串，是月報表最常見的做法之一。

**資料庫注意事項**
- 直接對日期欄位做函式運算通常不利索引；若是高頻報表，可考慮用日期維度表或預先彙總。

**常見陷阱／實務建議**
- 月報表若牽涉時區切換，應先定義是以系統時區、商務時區或 UTC 為準。

## 案例 49：計算不同會員等級的平均訂單金額

**使用情境**
你要比較不同會員等級的客單價差異。

**SQL 範例**
```sql
SELECT
  c.tier,
  ROUND(AVG(o.total_amount), 2) AS avg_order_amount
FROM orders AS o
JOIN customers AS c
  ON c.id = o.customer_id
WHERE o.payment_status = 'PAID'
GROUP BY c.tier;
```

**說明**
這類平均值報表常用於會員策略、促銷成效與價格帶分析。

**資料庫注意事項**
- 若資料偏態嚴重，平均值可能不夠代表真實情況，可再搭配中位數或分位數分析。

**常見陷阱／實務建議**
- 統計前先確認是否要排除退款、取消或測試訂單，不然平均值會失真。

## 案例 50：統計每個分類的最高與最低商品售價

**使用情境**
你要快速檢查分類內價格帶是否合理。

**SQL 範例**
```sql
SELECT
  c.name AS category_name,
  MIN(p.price) AS min_price,
  MAX(p.price) AS max_price
FROM products AS p
JOIN categories AS c
  ON c.id = p.category_id
GROUP BY c.name;
```

**說明**
`MIN` 與 `MAX` 適合快速找出資料範圍，用來檢查異常值或價格策略。

**資料庫注意事項**
- 若商品狀態有啟用/停用差異，統計前應先決定是否只看上架商品。

**常見陷阱／實務建議**
- 看到極端值時先確認是否是錯價、資料同步錯誤或幣別未統一。

## 第 7 章：子查詢、CTE 與集合操作

## 案例 51：找出高於平均客單價的訂單

**使用情境**
你要標出超過整體平均客單價的訂單，做高價訂單分析。

**SQL 範例**
```sql
SELECT
  id,
  order_no,
  total_amount
FROM orders
WHERE total_amount > (
  SELECT AVG(total_amount)
  FROM orders
  WHERE payment_status = 'PAID'
);
```

**說明**
純量子查詢會先算出單一值，再拿來跟外層列逐一比較，是很常見的分析模式。

**資料庫注意事項**
- 若子查詢本身很重且外層高頻執行，應考慮先彙總成暫存結果或報表表。

**常見陷阱／實務建議**
- 平均值容易被極端值影響，若用於決策，最好搭配分位數一起看。

## 案例 52：找出每位客戶最近一次訂單

**使用情境**
你要看每位客戶最後一次下單時間與訂單編號。

**SQL 範例**
```sql
SELECT
  o.customer_id,
  o.order_no,
  o.order_date,
  o.total_amount
FROM orders AS o
WHERE o.order_date = (
  SELECT MAX(o2.order_date)
  FROM orders AS o2
  WHERE o2.customer_id = o.customer_id
);
```

**說明**
相關子查詢會根據外層列逐筆計算，是表達「每一組各自最晚/最大/最小值」的經典寫法。

**資料庫注意事項**
- 若同一客戶同一時間有多筆訂單，這個寫法會回傳多列；需要唯一列時應再加主鍵排序規則。

**常見陷阱／實務建議**
- 當資料量大時，改用 window function 往往更清楚也更容易優化。

## 案例 53：使用 `IN (subquery)` 找出有交易的商品

**使用情境**
你要列出至少賣出過一次的商品名單。

**SQL 範例**
```sql
SELECT
  id,
  sku,
  product_name,
  price
FROM products
WHERE id IN (
  SELECT DISTINCT product_id
  FROM order_items
);
```

**說明**
`IN (subquery)` 能表達成員是否屬於某集合，對讀者而言通常很直覺。

**資料庫注意事項**
- 實際執行效率仍要看子查詢結果大小與索引狀況；有時 `EXISTS` 或 join 更合適。

**常見陷阱／實務建議**
- 若子查詢可能回傳很多重複值，先 `DISTINCT` 能讓語意更清楚，也可能減少不必要處理。

## 案例 54：使用 CTE 提高查詢可讀性

**使用情境**
你要先定義最近 30 天的已付款訂單，再往下做客戶統計。

**SQL 範例**
```sql
WITH recent_paid_orders AS (
  SELECT
    id,
    customer_id,
    total_amount
  FROM orders
  WHERE payment_status = 'PAID'
    AND order_date >= CURRENT_DATE - INTERVAL 30 DAY
)
SELECT
  customer_id,
  COUNT(*) AS order_count,
  SUM(total_amount) AS total_amount
FROM recent_paid_orders
GROUP BY customer_id;
```

**說明**
CTE 能把多階段邏輯拆開，對維護複雜查詢非常有幫助。

**資料庫注意事項**
- CTE 在 MariaDB 中不是萬能加速器，重點仍是可讀性與正確性，效能要靠 `EXPLAIN` 驗證。

**常見陷阱／實務建議**
- 當 SQL 已經難以閱讀時，先用 CTE 重構通常比硬塞更多巢狀子查詢更務實。

## 案例 55：使用遞迴 CTE 查分類樹

**使用情境**
分類是樹狀結構，你要展開完整路徑給後台管理或前台導覽使用。

**SQL 範例**
```sql
WITH RECURSIVE category_tree AS (
  SELECT
    id,
    parent_id,
    name,
    CAST(name AS CHAR(500)) AS path,
    0 AS depth
  FROM categories
  WHERE parent_id IS NULL

  UNION ALL

  SELECT
    c.id,
    c.parent_id,
    c.name,
    CONCAT(ct.path, ' > ', c.name) AS path,
    ct.depth + 1 AS depth
  FROM categories AS c
  JOIN category_tree AS ct
    ON c.parent_id = ct.id
)
SELECT
  id,
  parent_id,
  name,
  path,
  depth
FROM category_tree
ORDER BY path;
```

**說明**
遞迴 CTE 是處理樹狀資料最直觀的 SQL 工具，能比固定層數的 self join 更彈性。

**資料庫注意事項**
- 階層過深或資料有循環參照時，遞迴查詢可能異常放大；資料完整性要先保證。

**常見陷阱／實務建議**
- 若樹狀資料是高頻查詢，可再評估 closure table 或 path cache 等策略。

## 案例 56：使用 `UNION ALL` 合併多組事件資料

**使用情境**
你要把已付款與已退款訂單合併成同一份事件流，保留所有紀錄。

**SQL 範例**
```sql
SELECT
  id,
  'PAID' AS event_type,
  order_date AS occurred_at,
  total_amount
FROM orders
WHERE payment_status = 'PAID'

UNION ALL

SELECT
  id,
  'REFUNDED' AS event_type,
  order_date AS occurred_at,
  total_amount
FROM orders
WHERE payment_status = 'REFUNDED';
```

**說明**
`UNION ALL` 會直接串接結果，不做去重，適合保留完整事件資料。

**資料庫注意事項**
- 各個 `SELECT` 的欄位數與型別必須可對齊，否則 MariaDB 會報錯或隱式轉型。

**常見陷阱／實務建議**
- 如果你不需要去重，就用 `UNION ALL`，不要白白付出 `UNION` 的額外成本。

## 案例 57：使用 `UNION` 合併不同來源的客戶清單並去重

**使用情境**
你要整理最近 30 天的新客戶與最近 30 天曾下單客戶，並去掉重複名單。

**SQL 範例**
```sql
SELECT id AS customer_id
FROM customers
WHERE created_at >= CURRENT_DATE - INTERVAL 30 DAY

UNION

SELECT customer_id
FROM orders
WHERE order_date >= CURRENT_DATE - INTERVAL 30 DAY;
```

**說明**
`UNION` 會自動去重，很適合建立多來源但希望唯一化的名單。

**資料庫注意事項**
- 去重通常要排序或雜湊，資料量大時比 `UNION ALL` 昂貴。

**常見陷阱／實務建議**
- 先確認業務上是否真的需要去重，避免多做不必要的成本。

## 案例 58：用衍生表包住中間結果再做篩選

**使用情境**
你先算出每位客戶的總消費，再從中挑出高價值客戶。

**SQL 範例**
```sql
SELECT
  ranked.customer_id,
  ranked.total_spent
FROM (
  SELECT
    customer_id,
    SUM(total_amount) AS total_spent
  FROM orders
  WHERE payment_status = 'PAID'
  GROUP BY customer_id
) AS ranked
WHERE ranked.total_spent >= 10000
ORDER BY ranked.total_spent DESC;
```

**說明**
衍生表是把中間計算當成一張臨時結果集來用，常見於分層聚合與二次篩選。

**資料庫注意事項**
- 複雜衍生表同樣可能造成暫存表或額外成本，仍需靠執行計畫確認。

**常見陷阱／實務建議**
- 當查詢已經需要兩層以上中間結果時，考慮改用 CTE 可讓結構更清楚。

## 第 8 章：字串、日期、數值與分析函式

## 案例 59：組合顯示文字欄位

**使用情境**
你要在後台把客戶代碼、姓名與城市組成一個容易辨識的顯示欄位。

**SQL 範例**
```sql
SELECT
  id,
  CONCAT('[', customer_code, '] ', full_name) AS customer_label,
  CONCAT_WS(' / ', city, tier) AS city_and_tier
FROM customers;
```

**說明**
`CONCAT` 與 `CONCAT_WS` 是字串整形最常用的工具，適合做匯出與檢查用途。

**資料庫注意事項**
- 若任一參數為 `NULL`，`CONCAT` 結果可能受到影響；需要時可搭配 `IFNULL` 或 `COALESCE`。

**常見陷阱／實務建議**
- 報表展示邏輯若太複雜，仍建議交給應用層處理，避免 SQL 變成模板語言。

## 案例 60：切割與遮罩字串

**使用情境**
你要在管理後台顯示部分遮罩過的 email，避免暴露完整個資。

**SQL 範例**
```sql
SELECT
  id,
  CONCAT(LEFT(email, 3), '***@', SUBSTRING_INDEX(email, '@', -1)) AS masked_email
FROM customers;
```

**說明**
`LEFT`、`RIGHT`、`SUBSTRING_INDEX` 等函式很適合做簡單遮罩與格式化。

**資料庫注意事項**
- 這只是展示層遮罩，不等於真正的資料保護措施；底層資料仍是明文。

**常見陷阱／實務建議**
- 涉及個資時，先確認資料最小揭露原則，不要因為查詢方便就全量曝光。

## 案例 61：清理字串中的空白與符號

**使用情境**
匯入來源資料的電話格式不一致，你想先在查詢中做初步標準化。

**SQL 範例**
```sql
SELECT
  id,
  phone,
  REPLACE(REPLACE(TRIM(phone), '-', ''), ' ', '') AS normalized_phone
FROM customers;
```

**說明**
`TRIM` 與 `REPLACE` 是處理輸入品質問題的基本工具，適合清理簡單格式雜訊。

**資料庫注意事項**
- 若這種清理會長期使用，最好在寫入流程就標準化，而不是每次查詢都現場處理。

**常見陷阱／實務建議**
- 查詢時清理只能治標；資料品質問題應盡量在 ETL 或應用層入口解決。

## 案例 62：計算預計到期日或活動截止日

**使用情境**
你要從下單時間推算 7 天後的付款截止日或 30 天後的保固到期日。

**SQL 範例**
```sql
SELECT
  order_no,
  order_date,
  DATE_ADD(order_date, INTERVAL 7 DAY) AS payment_due_at,
  DATE_ADD(order_date, INTERVAL 30 DAY) AS warranty_due_at
FROM orders;
```

**說明**
`DATE_ADD` 與 `DATE_SUB` 常用於 SLA、優惠期間與通知時間計算。

**資料庫注意事項**
- 時區與夏令時間若與商務規則有關，單純日期加減前要先確認時區基準。

**常見陷阱／實務建議**
- 期限計算若牽涉法規或合約，不要只靠簡單日期相加，規則要先講清楚。

## 案例 63：計算相差天數與分鐘數

**使用情境**
你要分析從下單到出貨花了多久，以便追蹤出貨 SLA。

**SQL 範例**
```sql
SELECT
  order_no,
  order_date,
  shipped_at,
  TIMESTAMPDIFF(HOUR, order_date, shipped_at) AS shipping_hours,
  TIMESTAMPDIFF(DAY, order_date, shipped_at) AS shipping_days
FROM orders
WHERE shipped_at IS NOT NULL;
```

**說明**
`TIMESTAMPDIFF` 適合量化流程耗時，是營運分析與告警邏輯的基礎。

**資料庫注意事項**
- 若 `shipped_at` 可能為 `NULL`，務必先過濾，不然結果會是 `NULL`。

**常見陷阱／實務建議**
- SLA 指標最好明確定義是自然日、工作日還是營業時段，不然數字容易被誤解。

## 案例 64：處理空值與避免除以零

**使用情境**
你要計算商品毛利率，但不希望成本為 0 或空值時讓查詢失敗。

**SQL 範例**
```sql
SELECT
  sku,
  product_name,
  price,
  cost,
  ROUND((price - cost) / NULLIF(cost, 0) * 100, 2) AS margin_percent,
  COALESCE(weight_grams, 0) AS weight_grams
FROM products;
```

**說明**
`NULLIF` 可避免除數為 0，`COALESCE` 可把空值換成預設值，都是報表必備技巧。

**資料庫注意事項**
- 這種保護是避免錯誤，不代表商業意義正確；成本為 0 往往本身就是資料問題。

**常見陷阱／實務建議**
- 看見大量 `NULLIF` 或 `COALESCE` 時，反而要回頭檢查上游資料治理是否出了問題。

## 案例 65：做金額的四捨五入與進位

**使用情境**
你要按不同規則顯示售價、整數箱數或促銷門檻。

**SQL 範例**
```sql
SELECT
  sku,
  price,
  ROUND(price, 0) AS rounded_price,
  CEIL(price) AS ceil_price,
  FLOOR(price) AS floor_price
FROM products;
```

**說明**
`ROUND`、`CEIL`、`FLOOR` 是價格展示、倉儲換算與門檻計算常用的數值函式。

**資料庫注意事項**
- 金額欄位應優先使用 `DECIMAL`，不要用浮點數處理正式交易金額。

**常見陷阱／實務建議**
- 金額四捨五入規則若會影響帳務，必須與財務規則一致，不能隨意切換。

## 案例 66：明確做型別轉換

**使用情境**
匯入來源把數值當字串送進來，你要在查詢中暫時轉成數值比較。

**SQL 範例**
```sql
SELECT
  sku,
  product_name,
  CAST(price AS DECIMAL(12, 2)) AS price_decimal,
  CONVERT(stock_qty, SIGNED) AS stock_signed
FROM products;
```

**說明**
`CAST` 與 `CONVERT` 能讓查詢意圖更清楚，也能避免隱式轉型造成不可預期結果。

**資料庫注意事項**
- 隱式轉型有時會讓索引失效，或導致字串與數值比較結果不如預期。

**常見陷阱／實務建議**
- 型別不對通常應在 schema 或 ETL 就解決，不要長期靠查詢時轉型補救。

## 案例 67：使用正規表示式篩選格式異常資料

**使用情境**
你要找出 email 格式明顯異常的客戶資料做清理。

**SQL 範例**
```sql
SELECT
  id,
  full_name,
  email
FROM customers
WHERE email NOT REGEXP '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Za-z]{2,}$';
```

**說明**
`REGEXP` 適合做資料品質檢查、格式驗證與簡單模式搜尋。

**資料庫注意事項**
- 正規表示式通常比一般索引查詢昂貴，不適合當高頻前台查詢主力。

**常見陷阱／實務建議**
- 正規表示式只能做基本格式檢查，不代表 email 真正存在或可投遞。

## 案例 68：使用 window function 取每位客戶最近三筆訂單

**使用情境**
你要在客戶檔旁邊顯示最近三次下單紀錄，而不是全部訂單。

**SQL 範例**
```sql
SELECT
  ranked.customer_id,
  ranked.order_no,
  ranked.order_date,
  ranked.total_amount
FROM (
  SELECT
    o.customer_id,
    o.order_no,
    o.order_date,
    o.total_amount,
    ROW_NUMBER() OVER (
      PARTITION BY o.customer_id
      ORDER BY o.order_date DESC, o.id DESC
    ) AS rn
  FROM orders AS o
) AS ranked
WHERE ranked.rn <= 3;
```

**說明**
window function 很適合處理每群前 N 筆、排名、移動平均等需求，通常比相關子查詢更清楚。

**資料庫注意事項**
- 視窗函式通常需要排序，對大資料集要搭配索引與執行計畫一起評估。

**常見陷阱／實務建議**
- 排名條件一定要穩定，否則資料同分時結果可能不一致。

## 第 9 章：交易控制、鎖定與一致性

## 案例 69：用交易包住扣庫存與建立訂單

**使用情境**
你要確保扣庫存與建立訂單同時成功或同時失敗，避免資料不一致。

**SQL 範例**
```sql
START TRANSACTION;

UPDATE products
SET stock_qty = stock_qty - 2
WHERE id = 1
  AND stock_qty >= 2;

INSERT INTO orders (
  customer_id,
  order_no,
  order_status,
  payment_status,
  order_date,
  total_amount
) VALUES (
  1,
  'SO-20260322-0002',
  'PENDING',
  'UNPAID',
  NOW(),
  1398.00
);

COMMIT;
```

**說明**
交易讓多個步驟形成原子操作，是保護金流、庫存與訂單一致性的基本機制。

**資料庫注意事項**
- 若 `UPDATE` 沒有成功命中任何列，代表庫存不足；應由應用層檢查受影響筆數再決定是否回滾。

**常見陷阱／實務建議**
- 不要只靠應用程式先查庫存再扣庫存；沒有交易保護時仍可能被競爭條件打穿。

## 案例 70：使用 `SAVEPOINT` 做局部回滾

**使用情境**
同一個交易裡有多個步驟，其中某一步失敗時你只想回滾部分操作。

**SQL 範例**
```sql
START TRANSACTION;

UPDATE products
SET stock_qty = stock_qty - 1
WHERE id = 1;

SAVEPOINT after_stock_update;

INSERT INTO inventory_movements (
  product_id,
  movement_type,
  qty,
  reason
) VALUES (
  1,
  'OUT',
  1,
  'order shipment'
);

ROLLBACK TO SAVEPOINT after_stock_update;

COMMIT;
```

**說明**
`SAVEPOINT` 讓你在長交易裡保留可回退節點，適合流程較複雜的資料處理。

**資料庫注意事項**
- 回滾到 savepoint 並不會結束整個交易，後續仍要決定 `COMMIT` 或 `ROLLBACK`。

**常見陷阱／實務建議**
- savepoint 很好用，但也可能掩蓋流程設計過於複雜的問題；交易越短越好。

## 案例 71：使用 `SELECT ... FOR UPDATE` 鎖住即將修改的列

**使用情境**
多個工作程序可能同時扣同一筆商品庫存，你要先鎖住這列資料。

**SQL 範例**
```sql
START TRANSACTION;

SELECT
  id,
  stock_qty
FROM products
WHERE id = 1
FOR UPDATE;

UPDATE products
SET stock_qty = stock_qty - 1
WHERE id = 1;

COMMIT;
```

**說明**
`FOR UPDATE` 會在交易期間鎖住命中的列，避免其他交易同時修改造成競爭條件。

**資料庫注意事項**
- 行鎖是否精準，取決於查詢條件是否能走索引；條件不佳時可能放大鎖範圍。

**常見陷阱／實務建議**
- 沒有索引的 `FOR UPDATE` 很危險，可能意外鎖住大量資料並拖垮併發。

## 案例 72：使用共享鎖確保讀取期間不被改寫

**使用情境**
你要在交易中讀取某筆資料，並希望其他交易不能先修改它。

**SQL 範例**
```sql
START TRANSACTION;

SELECT
  id,
  total_amount,
  payment_status
FROM orders
WHERE id = 1
LOCK IN SHARE MODE;

COMMIT;
```

**說明**
共享鎖適合需要一致讀取但不立即更新的情境，例如進一步做業務判斷前先確保資料穩定。

**資料庫注意事項**
- 共享鎖會阻止他人取得排他更新權，仍需留意交易時間長短。

**常見陷阱／實務建議**
- 如果後面一定會更新，通常直接 `FOR UPDATE` 比先共享鎖再轉排他鎖更乾脆。

## 案例 73：設定交易隔離等級

**使用情境**
你要針對某段交易改成 `READ COMMITTED`，降低不必要的鎖競爭或讀取舊快照問題。

**SQL 範例**
```sql
SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED;

START TRANSACTION;

SELECT
  id,
  order_no,
  payment_status
FROM orders
WHERE customer_id = 1;

COMMIT;
```

**說明**
隔離等級會影響交易讀到什麼版本的資料，以及併發時的行為。對交易一致性與效能都有直接影響。

**資料庫注意事項**
- InnoDB 常見預設是 `REPEATABLE READ`；臨時調整前要先理解你的業務是否能接受不同一致性模型。

**常見陷阱／實務建議**
- 不要為了解鎖競爭就草率調低隔離等級，先弄清楚要避免的是哪一類現象。

## 案例 74：暫時關閉自動提交控制一批操作

**使用情境**
你在 SQL client 裡手動做一批相關操作，希望自己決定何時一起提交。

**SQL 範例**
```sql
SET autocommit = 0;

UPDATE products
SET stock_qty = stock_qty + 50
WHERE id = 2;

INSERT INTO inventory_movements (
  product_id,
  movement_type,
  qty,
  reason
) VALUES (
  2,
  'IN',
  50,
  'manual stock refill'
);

COMMIT;

SET autocommit = 1;
```

**說明**
在互動式維運場景，關閉 autocommit 可避免每條語句都立即生效，讓你保留回滾空間。

**資料庫注意事項**
- 忘記重新打開 autocommit 可能讓後續操作都落在同一長交易裡。

**常見陷阱／實務建議**
- 維運手動操作結束後一定要把 session 狀態恢復，避免下一個人接手時踩坑。

## 案例 75：使用 `LOCK TABLES` 做短時間批次維護

**使用情境**
你要在極短時間內對某幾張表做一致性的批次維護操作。

**SQL 範例**
```sql
LOCK TABLES products WRITE, inventory_movements WRITE;

UPDATE products
SET stock_qty = stock_qty + 10
WHERE id = 3;

INSERT INTO inventory_movements (
  product_id,
  movement_type,
  qty,
  reason
) VALUES (
  3,
  'ADJUST',
  10,
  'stock reconciliation'
);

UNLOCK TABLES;
```

**說明**
表級鎖適合非常明確且短暫的維護窗口，但對並行系統影響很大，應謹慎使用。

**資料庫注意事項**
- `LOCK TABLES` 會影響其他 session 的讀寫能力，不適合高流量時段隨意使用。

**常見陷阱／實務建議**
- 能用行級鎖解決的問題，就不要升級成表級鎖。

## 案例 76：排查鎖等待與 InnoDB 狀態

**使用情境**
你懷疑系統卡住是因為鎖競爭或死鎖，需要先看目前資料庫狀態。

**SQL 範例**
```sql
SHOW PROCESSLIST;
SHOW ENGINE INNODB STATUS;
```

**說明**
`SHOW PROCESSLIST` 能看到當前連線與執行狀態，`SHOW ENGINE INNODB STATUS` 則能提供更細的鎖與死鎖資訊。

**資料庫注意事項**
- `SHOW ENGINE INNODB STATUS` 輸出很長，適合配合當下時間點與慢查、應用日誌一起判讀。

**常見陷阱／實務建議**
- 只看到鎖等待現象還不夠，要回頭找出哪支 SQL、哪個交易沒有及時提交。

## 第 10 章：索引、執行效能與查詢優化

## 案例 77：建立常用查詢索引

**使用情境**
你發現訂單常按客戶與日期、或按狀態與日期查詢，想補上索引。

**SQL 範例**
```sql
ALTER TABLE orders
  ADD INDEX idx_orders_customer_date (customer_id, order_date),
  ADD INDEX idx_orders_status_date (order_status, order_date);
```

**說明**
索引設計應跟著查詢模式走，而不是看欄位名字猜。複合索引常比多條單欄索引更有價值。

**資料庫注意事項**
- 複合索引遵守最左前綴原則，欄位順序直接影響可用性。

**常見陷阱／實務建議**
- 不要看到條件欄位就各加一條索引，寫入成本與維護成本會很快失控。

## 案例 78：使用 `EXPLAIN` 看查詢執行計畫

**使用情境**
你要確認某支查詢有沒有走到預期索引，以及大概會掃多少列。

**SQL 範例**
```sql
EXPLAIN
SELECT
  order_no,
  total_amount,
  order_date
FROM orders
WHERE order_status = 'PAID'
  AND order_date >= '2026-03-01 00:00:00';
```

**說明**
`EXPLAIN` 是 SQL 調校起點，不該憑感覺加索引。你至少要看 `type`、`key`、`rows`、`Extra`。

**資料庫注意事項**
- `EXPLAIN` 顯示的是估算與計畫，不一定等同實際執行成本，但足夠用來找方向。

**常見陷阱／實務建議**
- 沒看計畫就直接加索引，通常是把問題複雜化，不是解決問題。

## 案例 79：使用 JSON 格式執行計畫做更細分析

**使用情境**
你需要更細的優化資訊，而不是只看傳統表格型 `EXPLAIN`。

**SQL 範例**
```sql
EXPLAIN FORMAT=JSON
SELECT
  o.order_no,
  c.full_name,
  o.total_amount
FROM orders AS o
JOIN customers AS c
  ON c.id = o.customer_id
WHERE o.payment_status = 'PAID'
  AND o.order_date >= CURRENT_DATE - INTERVAL 30 DAY;
```

**說明**
JSON 格式更容易看出 join 順序、條件下推與估算細節，適合較複雜的查詢分析。

**資料庫注意事項**
- 不同 MariaDB 版本輸出的 JSON 欄位細節可能略有差異，閱讀時要以實際版本為準。

**常見陷阱／實務建議**
- 別只看 JSON 很完整就覺得已經優化完，關鍵仍是能否據此做出有效的 SQL 或索引調整。

## 案例 80：查看資料表索引狀態

**使用情境**
你要確認某張表目前有哪些索引、欄位順序與基數估計。

**SQL 範例**
```sql
SHOW INDEX FROM orders;
```

**說明**
這能快速檢查索引是否存在、順序是否正確，以及優化器可能如何估計選擇性。

**資料庫注意事項**
- `Cardinality` 是估計值，不是精確值，但對判斷索引選擇性仍有參考價值。

**常見陷阱／實務建議**
- 看見很多相似索引時，要懷疑是否已有冗餘索引造成寫入負擔。

## 案例 81：更新統計資訊

**使用情境**
大量匯入或刪除資料後，查詢計畫突然變差，你要先刷新統計資訊。

**SQL 範例**
```sql
ANALYZE TABLE orders, products, order_items;
```

**說明**
`ANALYZE TABLE` 會更新表與索引統計，讓優化器有比較新的資料做判斷。

**資料庫注意事項**
- 統計資訊不是萬靈丹，但在資料分布明顯改變後，這常是低成本且合理的第一步。

**常見陷阱／實務建議**
- 不要把所有慢查都怪罪在統計資訊過舊；更常見的根因仍是 SQL 寫法與索引不匹配。

## 案例 82：建立覆蓋查詢用索引

**使用情境**
某個高頻列表只會按客戶與日期查詢，並返回日期與金額，你想讓查詢盡量只讀索引。

**SQL 範例**
```sql
ALTER TABLE orders
  ADD INDEX idx_orders_cover_customer_date_total (customer_id, order_date, total_amount);

SELECT
  order_date,
  total_amount
FROM orders
WHERE customer_id = 1
  AND order_date >= CURRENT_DATE - INTERVAL 30 DAY
ORDER BY order_date DESC;
```

**說明**
若查詢所需欄位都能從同一索引取得，MariaDB 有機會避免回表，降低 I/O。

**資料庫注意事項**
- 覆蓋索引會增加索引體積，不能為了追求 cover 而無限制堆疊欄位。

**常見陷阱／實務建議**
- 先確認這真的是高頻且值得投資的查詢，再為它設計專屬索引。

## 案例 83：改寫會破壞索引的查詢

**使用情境**
你發現查詢寫法對索引欄位套函式，導致明明有索引卻沒被用上。

**SQL 範例**
```sql
SELECT
  order_no,
  total_amount
FROM orders
WHERE DATE(order_date) = '2026-03-22';

SELECT
  order_no,
  total_amount
FROM orders
WHERE order_date >= '2026-03-22 00:00:00'
  AND order_date < '2026-03-23 00:00:00';
```

**說明**
第二種寫法通常更能保留索引可用性，是日期查詢調校的常見關鍵點。

**資料庫注意事項**
- 不是所有函式都一定讓索引失效，但對欄位直接套函式時要高度警覺。

**常見陷阱／實務建議**
- 先把 SQL 寫對，再談加索引；錯誤寫法加再多索引都可能沒用。

## 案例 84：建立全文索引做站內搜尋

**使用情境**
商品名稱需要基本全文搜尋能力，單靠 `%keyword%` 已經不夠用。

**SQL 範例**
```sql
ALTER TABLE products
  ADD FULLTEXT INDEX ftx_products_name (product_name);

SELECT
  id,
  sku,
  product_name,
  MATCH(product_name) AGAINST ('無線 耳機' IN NATURAL LANGUAGE MODE) AS score
FROM products
WHERE MATCH(product_name) AGAINST ('無線 耳機' IN NATURAL LANGUAGE MODE)
ORDER BY score DESC;
```

**說明**
Full-Text 對搜尋型需求通常比 `%LIKE%` 更像樣，也更容易隨結果排序。

**資料庫注意事項**
- 中文斷詞效果與全文搜尋品質會受到 parser 與資料特性影響，正式需求仍可能要外部搜尋系統。

**常見陷阱／實務建議**
- 若搜尋是核心功能，不要過度高估資料庫原生全文索引；先做準確度與效能驗證。

## 案例 85：必要時用 `FORCE INDEX` 驗證索引策略

**使用情境**
優化器沒有選到你預期的索引，你要做對照測試。

**SQL 範例**
```sql
SELECT
  order_no,
  order_date,
  total_amount
FROM orders FORCE INDEX (idx_orders_status_date)
WHERE order_status = 'PAID'
  AND order_date >= CURRENT_DATE - INTERVAL 30 DAY;
```

**說明**
`FORCE INDEX` 可用來做測試與驗證，幫助你理解不同索引選擇的效果。

**資料庫注意事項**
- 強制索引是提示，不該當成長期萬用解方；資料分布改變後，今天的最佳選擇可能明天就不是。

**常見陷阱／實務建議**
- 若你常需要 `FORCE INDEX` 才能救得動查詢，更該回頭重看索引設計與統計資訊。

## 第 11 章：View、Procedure、Function、Trigger、Event

## 案例 86：建立常用查詢 view

**使用情境**
你要把「有效商品清單」封裝成固定查詢，供報表與後台重複使用。

**SQL 範例**
```sql
CREATE OR REPLACE VIEW vw_active_products AS
SELECT
  p.id,
  p.sku,
  p.product_name,
  p.price,
  p.stock_qty,
  c.name AS category_name
FROM products AS p
JOIN categories AS c
  ON c.id = p.category_id
WHERE p.status = 'ACTIVE';
```

**說明**
view 能把重複的查詢語意集中管理，對穩定共用查詢很有幫助。

**資料庫注意事項**
- view 不是效能工具本身；底層 SQL 若很重，view 一樣會重。

**常見陷阱／實務建議**
- 把 view 當成 API 邊界而不是魔法快取，才能避免錯誤期待。

## 案例 87：建立客戶訂單摘要 view

**使用情境**
你希望團隊直接查一張整理好的客戶消費摘要，不用每次重寫聚合 SQL。

**SQL 範例**
```sql
CREATE OR REPLACE VIEW vw_customer_order_summary AS
SELECT
  c.id AS customer_id,
  c.full_name,
  COUNT(o.id) AS order_count,
  IFNULL(SUM(o.total_amount), 0) AS total_spent,
  MAX(o.order_date) AS last_order_at
FROM customers AS c
LEFT JOIN orders AS o
  ON o.customer_id = c.id
  AND o.payment_status = 'PAID'
GROUP BY c.id, c.full_name;
```

**說明**
摘要型 view 對商務團隊很友善，能把常用統計口徑固定下來。

**資料庫注意事項**
- view 背後若依賴大表即時計算，頻繁查詢時仍可能需要改成彙總表。

**常見陷阱／實務建議**
- 指標口徑一定要有共識，例如 `total_spent` 是否只算已付款訂單。

## 案例 88：建立 stored procedure 封裝庫存異動

**使用情境**
你要把固定的庫存進出邏輯封裝起來，讓多個系統用同一套規則。

**SQL 範例**
```sql
DELIMITER //

CREATE PROCEDURE sp_apply_inventory_movement(
  IN p_product_id BIGINT UNSIGNED,
  IN p_movement_type VARCHAR(10),
  IN p_qty INT,
  IN p_reason VARCHAR(100)
)
BEGIN
  INSERT INTO inventory_movements (
    product_id,
    movement_type,
    qty,
    reason
  ) VALUES (
    p_product_id,
    p_movement_type,
    p_qty,
    p_reason
  );

  IF p_movement_type = 'IN' THEN
    UPDATE products
    SET stock_qty = stock_qty + p_qty
    WHERE id = p_product_id;
  ELSEIF p_movement_type = 'OUT' THEN
    UPDATE products
    SET stock_qty = stock_qty - p_qty
    WHERE id = p_product_id;
  END IF;
END//

DELIMITER ;
```

**說明**
stored procedure 適合封裝穩定且靠近資料的邏輯，例如批次維護、狀態同步與簡單驗證。

**資料庫注意事項**
- Procedure 會增加資料庫端邏輯負擔，版本控管與部署流程要先想清楚。

**常見陷阱／實務建議**
- 不要把整個應用程式商業邏輯都搬進 procedure；只保留真正需要靠近資料的部分。

## 案例 89：呼叫 stored procedure

**使用情境**
你要實際執行前面封裝好的庫存異動流程。

**SQL 範例**
```sql
CALL sp_apply_inventory_movement(1, 'OUT', 3, 'order shipment');
```

**說明**
`CALL` 是 stored procedure 的使用入口，讓上層只需傳參數，不必重寫內部細節。

**資料庫注意事項**
- 呼叫 procedure 的帳號需要有對應權限；正式環境應避免給過大資料庫權限。

**常見陷阱／實務建議**
- procedure 若會改動正式資料，先在測試環境驗證副作用，再導入工作流程。

## 案例 90：建立 stored function 回傳訂單毛利

**使用情境**
你要在查詢中重複取得某張訂單的毛利值。

**SQL 範例**
```sql
DELIMITER //

CREATE FUNCTION fn_order_profit(p_order_id BIGINT UNSIGNED)
RETURNS DECIMAL(12, 2)
DETERMINISTIC
READS SQL DATA
BEGIN
  DECLARE v_profit DECIMAL(12, 2);

  SELECT
    SUM((oi.unit_price - p.cost) * oi.qty)
  INTO v_profit
  FROM order_items AS oi
  JOIN products AS p
    ON p.id = oi.product_id
  WHERE oi.order_id = p_order_id;

  RETURN IFNULL(v_profit, 0.00);
END//

DELIMITER ;
```

**說明**
stored function 適合回傳單一值，方便在報表或查詢中重複使用固定計算邏輯。

**資料庫注意事項**
- function 若邏輯太重，可能讓大型查詢每列都多做昂貴計算，使用時要評估成本。

**常見陷阱／實務建議**
- 不要把高成本多表查詢塞進每列都會呼叫的 function，否則很容易出現隱形效能問題。

## 案例 91：建立 trigger 自動計算訂單明細金額

**使用情境**
你希望 `order_items.line_amount` 在寫入前由資料庫自動計算。

**SQL 範例**
```sql
DELIMITER //

CREATE TRIGGER trg_order_items_bi
BEFORE INSERT ON order_items
FOR EACH ROW
BEGIN
  SET NEW.line_amount = NEW.qty * NEW.unit_price;
END//

DELIMITER ;
```

**說明**
trigger 能把簡單且固定的衍生欄位邏輯收斂到資料庫層，減少應用端漏算風險。

**資料庫注意事項**
- trigger 是隱性邏輯，排錯時要記得把它納入考量。

**常見陷阱／實務建議**
- 只對簡單、穩定、可預期的規則使用 trigger；複雜流程通常不適合藏在 trigger 裡。

## 案例 92：建立狀態異動稽核 trigger

**使用情境**
你要在訂單狀態或付款狀態變更時，自動寫入稽核紀錄。

**SQL 範例**
```sql
DELIMITER //

CREATE TRIGGER trg_orders_au
AFTER UPDATE ON orders
FOR EACH ROW
BEGIN
  IF OLD.order_status <> NEW.order_status
     OR OLD.payment_status <> NEW.payment_status THEN
    INSERT INTO admin_audit_logs (
      actor,
      action_name,
      target_table,
      target_id,
      detail_text
    ) VALUES (
      'system',
      'ORDER_STATUS_CHANGED',
      'orders',
      NEW.id,
      CONCAT(
        'order_status: ', OLD.order_status, ' -> ', NEW.order_status,
        ', payment_status: ', OLD.payment_status, ' -> ', NEW.payment_status
      )
    );
  END IF;
END//

DELIMITER ;
```

**說明**
自動稽核對交易系統很重要，特別是在多人操作與跨系統同步環境下。

**資料庫注意事項**
- 稽核表本身會持續成長，記得搭配保留策略與清理機制。

**常見陷阱／實務建議**
- 若需要知道真正操作者，不能永遠只寫 `system`；應想辦法把應用層身分帶入。

## 案例 93：使用 event scheduler 做每日清理

**使用情境**
你要讓 MariaDB 每天自動清理保留期已過的稽核資料。

**SQL 範例**
```sql
SET GLOBAL event_scheduler = ON;

CREATE EVENT ev_purge_old_audit_logs
ON SCHEDULE EVERY 1 DAY
STARTS CURRENT_TIMESTAMP + INTERVAL 1 DAY
DO
  DELETE FROM admin_audit_logs
  WHERE changed_at < NOW() - INTERVAL 180 DAY;
```

**說明**
事件排程適合簡單且固定週期的資料庫內部維護工作，例如清理、彙總或狀態同步。

**資料庫注意事項**
- event scheduler 若未開啟，事件即使建立成功也不會執行。

**常見陷阱／實務建議**
- 事件裡的刪除或更新也屬高風險操作，先在測試環境驗證影響範圍。

## 第 12 章：使用者、角色、權限與安全

## 案例 94：建立應用程式專用帳號

**使用情境**
你要為正式應用建立一個最小權限的資料庫帳號，而不是直接用管理者帳號。

**SQL 範例**
```sql
CREATE USER 'shop_app'@'10.%'
IDENTIFIED BY 'ChangeMe_2026!';
```

**說明**
每個應用或服務都應有自己的 DB 帳號，便於控管權限、追蹤來源與分離風險。

**資料庫注意事項**
- 主機來源條件會影響可從哪裡連線；`'10.%'` 只是示範，正式環境應更精準。

**常見陷阱／實務建議**
- 不要讓應用程式使用 `root` 或高權限管理帳號，這是非常常見也非常糟糕的錯誤。

## 案例 95：授權最小必要權限

**使用情境**
應用程式只需要讀寫某個資料庫，不需要管理伺服器或操作其他 schema。

**SQL 範例**
```sql
GRANT SELECT, INSERT, UPDATE, DELETE
ON shop_demo.*
TO 'shop_app'@'10.%';

FLUSH PRIVILEGES;
```

**說明**
最小權限原則能把帳號被濫用或外洩後的影響面壓到最低。

**資料庫注意事項**
- 某些版本與權限變更流程下不一定需要 `FLUSH PRIVILEGES`，但在維運上保留明確刷新動作很常見。

**常見陷阱／實務建議**
- 授權前先問自己：這個帳號真的需要 `CREATE`、`DROP`、`ALTER` 嗎？通常答案是不要。

## 案例 96：使用角色集中管理權限

**使用情境**
你有多個只讀或報表帳號，想集中管理一套共用權限。

**SQL 範例**
```sql
CREATE ROLE reporting_reader;

GRANT SELECT
ON shop_demo.*
TO reporting_reader;

GRANT reporting_reader
TO 'shop_app'@'10.%';

SET DEFAULT ROLE reporting_reader
FOR 'shop_app'@'10.%';
```

**說明**
角色能把權限管理集中化，當帳號數量變多時比逐個帳號授權更容易維護。

**資料庫注意事項**
- 角色功能可用性與細節需依 MariaDB 版本確認，導入前最好先在測試環境演練。

**常見陷阱／實務建議**
- 角色不是只讀專用功能；重點是把授權模型做成可管理的結構。

## 案例 97：強化帳號安全設定並檢查權限

**使用情境**
你要要求某個帳號必須使用加密連線，並檢查它目前實際拿到哪些權限。

**SQL 範例**
```sql
ALTER USER 'shop_app'@'10.%'
  REQUIRE SSL
  PASSWORD EXPIRE INTERVAL 180 DAY;

SHOW GRANTS FOR 'shop_app'@'10.%';
```

**說明**
安全設定不只是在建立帳號那一刻，還包含連線保護、密碼週期與實際授權盤點。

**資料庫注意事項**
- `REQUIRE SSL` 要建立在伺服器端 TLS 已正確配置的前提下，否則帳號可能無法登入。

**常見陷阱／實務建議**
- 別只看你「以為」授了什麼權限，實際上要用 `SHOW GRANTS` 驗證。

## 第 13 章：匯入匯出、備份與管理操作

## 案例 98：使用 `LOAD DATA INFILE` 匯入 CSV

**使用情境**
你要把外部提供的商品 CSV 快速匯入 MariaDB。

**SQL 範例**
```sql
LOAD DATA INFILE '/var/lib/mysql-files/products_20260322.csv'
INTO TABLE products
FIELDS TERMINATED BY ','
ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 LINES
(sku, product_name, price, cost, stock_qty)
SET category_id = 1,
    status = 'ACTIVE',
    created_at = NOW(),
    updated_at = NOW();
```

**說明**
`LOAD DATA INFILE` 是 MariaDB 大量匯入最常見也最高效的原生方式之一。

**資料庫注意事項**
- 伺服器端通常受 `secure_file_priv` 限制，檔案可讀位置與權限要先確認。

**常見陷阱／實務建議**
- 匯入前先在 staging table 驗證資料格式，比直接灌進正式主表安全得多。

## 案例 99：使用 `SELECT ... INTO OUTFILE` 匯出報表

**使用情境**
你要把已付款訂單匯出成 CSV，交給其他系統或分析人員。

**SQL 範例**
```sql
SELECT
  order_no,
  customer_id,
  total_amount,
  order_date
INTO OUTFILE '/var/lib/mysql-files/paid_orders_20260322.csv'
FIELDS TERMINATED BY ','
ENCLOSED BY '"'
LINES TERMINATED BY '\n'
FROM orders
WHERE payment_status = 'PAID';
```

**說明**
這是最直接的資料庫側匯出方式，適合一次性報表與資料交付。

**資料庫注意事項**
- 輸出路徑必須是資料庫伺服器可寫位置，而且目標檔通常不能先存在。

**常見陷阱／實務建議**
- 匯出涉及個資或交易資料時，要先確認目的、權限與傳輸保護，不要把 CSV 當成無害格式。

## 案例 100：建立一致性備份前的座標點

**使用情境**
你要在做邏輯備份或主從初始化前，先取得一致性的 binary log 座標資訊。

**SQL 範例**
```sql
FLUSH TABLES WITH READ LOCK;
SHOW MASTER STATUS;
UNLOCK TABLES;
```

**說明**
這組操作常用於取得當下可追蹤的複寫座標或備份切點，方便後續還原與追資料。

**資料庫注意事項**
- `SHOW MASTER STATUS` 需要 binary log 已啟用；純 InnoDB 邏輯備份常也會搭配 `mariadb-dump --single-transaction`。

**常見陷阱／實務建議**
- `FLUSH TABLES WITH READ LOCK` 會阻擋寫入，不要在高流量時段長時間持有；真正備份流程要先演練並縮短鎖持有時間。

## 附錄

- 本手冊示範的是 MariaDB 常見 OLTP 與後台維運場景，實際欄位與索引設計仍應回到你的真實查詢模式。
- 高風險操作包含 `TRUNCATE`、大範圍 `UPDATE`、大範圍 `DELETE`、權限變更與備份切點管理；正式執行前請先在測試環境驗證。
- 若你的系統高度依賴全文搜尋、複雜分析、超大規模匯入匯出或近即時報表，通常需要搭配搜尋引擎、數倉或資料管線，而不是只靠交易資料庫硬撐。