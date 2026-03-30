# DB.md

# データベース設計

## 1. 方針

- SQLite を使用する
- DB は共有サーバー上に配置する
- 更新頻度は低く、編集時はロック機能を使用する
- 現在状態と履歴を分離して管理する

## 2. テーブル一覧

- employee_master
- current_status
- status_history
- app_config

## 3. employee_master

### 3.1 役割

社員の固定情報を保持する。

### 3.2 カラム

- id INTEGER PRIMARY KEY
- employee_name TEXT NOT NULL
- department TEXT
- extension_number TEXT NOT NULL
- display_order INTEGER NOT NULL DEFAULT 0
- is_active INTEGER NOT NULL DEFAULT 1
- created_at TEXT NOT NULL
- updated_at TEXT NOT NULL

### 3.3 制約

- employee_name は空不可
- extension_number は空不可
- is_active は 0 または 1

## 4. current_status

### 4.1 役割

各社員の現在状態を保持する。

### 4.2 カラム

- id INTEGER PRIMARY KEY
- employee_id INTEGER NOT NULL
- attendance_status TEXT NOT NULL
- location_status TEXT NOT NULL
- destination TEXT
- note TEXT
- updated_by TEXT NOT NULL
- updated_at TEXT NOT NULL

### 4.3 備考

- 1社員につき1レコードを基本とする
- employee_master と外部キー相当で関連付ける

## 5. status_history

### 5.1 役割

状態変更履歴を保存する。

### 5.2 カラム

- id INTEGER PRIMARY KEY
- employee_id INTEGER NOT NULL
- old_attendance_status TEXT
- new_attendance_status TEXT NOT NULL
- old_location_status TEXT
- new_location_status TEXT NOT NULL
- old_destination TEXT
- new_destination TEXT
- old_note TEXT
- new_note TEXT
- updated_by TEXT NOT NULL
- updated_at TEXT NOT NULL

## 6. app_config

### 6.1 役割

アプリ内設定やスキーマバージョンを保持する。

### 6.2 カラム

- id INTEGER PRIMARY KEY
- config_key TEXT NOT NULL
- config_value TEXT NOT NULL
- updated_at TEXT NOT NULL

## 7. CREATE TABLE 案

```sql
CREATE TABLE employee_master (
    id INTEGER PRIMARY KEY,
    employee_name TEXT NOT NULL,
    department TEXT,
    extension_number TEXT NOT NULL,
    display_order INTEGER NOT NULL DEFAULT 0,
    is_active INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE current_status (
    id INTEGER PRIMARY KEY,
    employee_id INTEGER NOT NULL,
    attendance_status TEXT NOT NULL,
    location_status TEXT NOT NULL,
    destination TEXT,
    note TEXT,
    updated_by TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE status_history (
    id INTEGER PRIMARY KEY,
    employee_id INTEGER NOT NULL,
    old_attendance_status TEXT,
    new_attendance_status TEXT NOT NULL,
    old_location_status TEXT,
    new_location_status TEXT NOT NULL,
    old_destination TEXT,
    new_destination TEXT,
    old_note TEXT,
    new_note TEXT,
    updated_by TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE app_config (
    id INTEGER PRIMARY KEY,
    config_key TEXT NOT NULL,
    config_value TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
```

## 8. インデックス案

```sql
CREATE INDEX idx_employee_master_display_order
ON employee_master(display_order);

CREATE INDEX idx_current_status_employee_id
ON current_status(employee_id);

CREATE INDEX idx_status_history_employee_id
ON status_history(employee_id);

CREATE INDEX idx_status_history_updated_at
ON status_history(updated_at);
```

## 9. データ更新方針

- current_status は最新状態のみ保持する
- 更新前の情報は status_history に保存する
- 内線番号は employee_master の固定情報として扱う
- 出社状態と所在状態は分離して保持する

## 10. スキーマバージョン管理

- app_config に schema_version を保持する
- 起動時に schema_version を確認し、必要に応じて migration を実施する
