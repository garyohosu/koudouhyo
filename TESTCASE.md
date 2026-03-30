# TESTCASE.md

# テストケース一覧（TDD用）

テスト対象はサービス層・データアクセス層を中心とする。
UI層（Tkinter）は原則テスト対象外とし、ロジックをサービス層・Repository層に集約することで間接的にカバーする。

---

## 凡例

| 列 | 内容 |
|----|------|
| ID | テストケースID（TC-クラス略称-連番） |
| 前提 | テスト実行前の状態 |
| 操作 | 実行する処理 |
| 期待 | 正しく動作したときの結果 |

---

## 1. ConfigLoader

| ID | テスト名 | 前提 | 操作 | 期待 |
|----|---------|------|------|------|
| TC-CL-01 | 正常な config.json を読み込める | 有効な config.json が存在する | `load()` を呼ぶ | `shared_root` と `admin_users` が正しく返る |
| TC-CL-02 | admin_users が空リストでも読み込める | `admin_users: []` の config.json | `load()` を呼ぶ | `admin_users` が空リストで返る |
| TC-CL-03 | config.json が存在しない場合はエラー | ファイルが存在しない | `load()` を呼ぶ | 適切な例外が発生する |
| TC-CL-04 | 不正な JSON の場合はエラー | 壊れた JSON ファイルが存在する | `load()` を呼ぶ | 適切な例外が発生する |
| TC-CL-05 | shared_root が未定義の場合はエラー | `shared_root` キーが無い config.json | `load()` を呼ぶ | 適切な例外が発生する |

---

## 2. DatabaseManager

| ID | テスト名 | 前提 | 操作 | 期待 |
|----|---------|------|------|------|
| TC-DB-01 | インメモリDBに接続できる | `:memory:` を指定 | `connect()` を呼ぶ | 例外なく接続される |
| TC-DB-02 | PRAGMA foreign_keys = ON が有効になる | DB接続済み | `execute_pragma()` を呼んだ後 `PRAGMA foreign_keys` を確認 | 値が `1` である |
| TC-DB-03 | 接続を閉じられる | DB接続済み | `close()` を呼ぶ | 例外なく切断される |
| TC-DB-04 | 存在しないDBファイルを指定した場合は新規作成される | ファイルが存在しない | `connect()` を呼ぶ | ファイルが作成され接続される |

---

## 3. EmployeeRepository

| ID | テスト名 | 前提 | 操作 | 期待 |
|----|---------|------|------|------|
| TC-ER-01 | is_active=1 の社員のみ取得できる | is_active=1 の社員2名、is_active=0 の社員1名が存在する | `get_all_active()` を呼ぶ | is_active=1 の2件のみ返る |
| TC-ER-02 | 全社員（is_active 問わず）を取得できる | is_active=1 の社員2名、is_active=0 の社員1名が存在する | `get_all()` を呼ぶ | 3件すべて返る |
| TC-ER-03 | IDで1件取得できる | 社員が存在する | `get_by_id(id)` を呼ぶ | 対象社員のデータが返る |
| TC-ER-04 | 存在しないIDを指定した場合は None が返る | 該当IDが存在しない | `get_by_id(999)` を呼ぶ | `None` が返る |
| TC-ER-05 | 新規社員を追加できる | テーブルが空 | `insert(employee)` を呼ぶ | レコードが追加される |
| TC-ER-06 | 社員情報を更新できる | 社員が存在する | `update(employee)` を呼ぶ | 対象レコードが更新される |
| TC-ER-07 | display_order 順で取得される | display_order が異なる複数社員が存在する | `get_all_active()` を呼ぶ | display_order の昇順で返る |

---

## 4. StatusRepository

| ID | テスト名 | 前提 | 操作 | 期待 |
|----|---------|------|------|------|
| TC-SR-01 | 全社員の現在状態を取得できる | current_status に3件存在する | `get_all_current()` を呼ぶ | 3件返る |
| TC-SR-02 | employee_id で現在状態を1件取得できる | 対象社員の current_status が存在する | `get_by_employee_id(id)` を呼ぶ | 対象社員の状態が返る |
| TC-SR-03 | 状態変更が current_status に反映される | 社員の current_status が「出社中・在席」 | `save_status_change(new_status)` を呼ぶ | current_status が更新される |
| TC-SR-04 | 状態変更時に status_history に履歴が保存される | 社員の current_status が存在する | `save_status_change(new_status)` を呼ぶ | status_history に1件追加される |
| TC-SR-05 | 状態変更は current_status 更新と history INSERT が同一トランザクション | current_status が存在する | `save_status_change()` 途中でエラーを注入 | どちらも変更されず整合性が保たれる |
| TC-SR-06 | 初期 current_status を作成できる | current_status が存在しない | `create_initial_status(employee_id, updated_by)` を呼ぶ | 「出社中・在席・行先空・備考空」のレコードが作成される |
| TC-SR-07 | 同一 employee_id への2件目の insert は失敗する | 対象社員の current_status が既に存在する | 直接 INSERT を試みる | UNIQUE 制約エラーが発生する |

---

## 5. AppConfigRepository

| ID | テスト名 | 前提 | 操作 | 期待 |
|----|---------|------|------|------|
| TC-AC-01 | schema_version を取得できる | app_config に schema_version が存在する | `get_schema_version()` を呼ぶ | 設定値が返る |
| TC-AC-02 | schema_version を設定できる | app_config が空 | `set_schema_version("1.0.0")` を呼ぶ | `get_schema_version()` が "1.0.0" を返す |
| TC-AC-03 | 存在しないキーは None または default を返す | 該当キーが存在しない | `get("unknown_key")` を呼ぶ | `None` または指定 default が返る |

---

## 6. LockManager

| ID | テスト名 | 前提 | 操作 | 期待 |
|----|---------|------|------|------|
| TC-LM-01 | ロックファイルが存在しない場合にロック取得できる | lock ファイルが存在しない | `try_acquire()` を呼ぶ | `True` が返り lock ファイルが作成される |
| TC-LM-02 | ロックファイルに lock_id・利用者名・PC名・開始時刻・版数が記録される | ロック取得後 | lock ファイルを読む | 上記5項目すべてが含まれる |
| TC-LM-03 | 有効なロックが存在する場合はロック取得失敗 | 更新時刻が現在から10分前の lock ファイルが存在する | `try_acquire()` を呼ぶ | `False` が返る |
| TC-LM-04 | 更新時刻から60分未満のロックは有効とみなす | 更新時刻が現在から59分前の lock ファイルが存在する | `is_expired()` を呼ぶ | `False` が返る |
| TC-LM-05 | 更新時刻から60分以上のロックは期限切れとみなす | 更新時刻が現在から61分前の lock ファイルが存在する | `is_expired()` を呼ぶ | `True` が返る |
| TC-LM-06 | 自セッションの lock_id と一致する場合のみ解除できる | 自セッションが取得した lock ファイルが存在する | `release()` を呼ぶ | lock ファイルが削除される |
| TC-LM-07 | 他セッションの lock_id の場合は解除しない | 異なる lock_id の lock ファイルが存在する | `release()` を呼ぶ | lock ファイルが残る |
| TC-LM-08 | 管理者は期限切れロックを強制解除できる | 期限切れ lock ファイルが存在する、ユーザーが admin_users に含まれる | `force_release_if_admin(admin_users)` を呼ぶ | `True` が返り lock ファイルが削除される |
| TC-LM-09 | 非管理者は期限切れロックを強制解除できない | 期限切れ lock ファイルが存在する、ユーザーが admin_users に含まれない | `force_release_if_admin(admin_users)` を呼ぶ | `False` が返り lock ファイルが残る |
| TC-LM-10 | ロックが存在しない状態で release を呼んでもエラーにならない | lock ファイルが存在しない | `release()` を呼ぶ | 例外が発生しない |
| TC-LM-11 | ハートビートスレッドを開始・停止できる | LockManager 初期化済み | `_start_heartbeat()` → `_stop_heartbeat()` を呼ぶ | スレッドが起動し、停止後は終了している |
| TC-LM-12 | ハートビートは多重起動しない | ハートビートスレッドが稼働中 | `_start_heartbeat()` を再度呼ぶ | スレッドが1本のみ稼働している |

---

## 7. BackupManager

| ID | テスト名 | 前提 | 操作 | 期待 |
|----|---------|------|------|------|
| TC-BM-01 | 当日バックアップが存在しない場合はバックアップを作成する | backup フォルダに当日のファイルが存在しない | `run_startup_backup()` を呼ぶ | 当日日付を含むバックアップファイルが作成される |
| TC-BM-02 | 当日バックアップが存在する場合はスキップする | backup フォルダに当日のファイルが既に存在する | `run_startup_backup()` を呼ぶ | 新たなファイルが作成されない |
| TC-BM-03 | マスタ更新前バックアップは毎回作成する | backup フォルダに当日ファイルが既に存在する | `run_pre_master_backup()` を呼ぶ | 追加のバックアップファイルが作成される |
| TC-BM-04 | 30世代を超えた場合は最古ファイルを削除する | backup フォルダに30件のファイルが存在する | `run_startup_backup()` を呼ぶ | 最古の1件が削除され合計30件を保つ |
| TC-BM-05 | バックアップファイル名に日時が含まれる | バックアップ実行後 | ファイル名を確認 | `koudouhyo_YYYYMMDD_HHMMSS.db` 形式である |
| TC-BM-06 | DBファイルが存在しない場合はエラー | db_path に DB が存在しない | `run_startup_backup()` を呼ぶ | 適切な例外が発生する |

---

## 8. VersionChecker

| ID | テスト名 | 前提 | 操作 | 期待 |
|----|---------|------|------|------|
| TC-VC-01 | latest.json のバージョンが新しい場合は has_update=True | current="1.0.0"、latest.json に "1.1.0" が存在する | `check()` を呼ぶ | `has_update=True`、`latest.version="1.1.0"` が返る |
| TC-VC-02 | latest.json のバージョンが同じ場合は has_update=False | current="1.1.0"、latest.json に "1.1.0" が存在する | `check()` を呼ぶ | `has_update=False` が返る |
| TC-VC-03 | latest.json のバージョンが古い場合は has_update=False | current="1.2.0"、latest.json に "1.1.0" が存在する | `check()` を呼ぶ | `has_update=False` が返る |
| TC-VC-04 | latest.json が存在しない場合は has_update=False（スキップ扱い） | latest.json が存在しない | `check()` を呼ぶ | `has_update=False` が返り例外は発生しない |
| TC-VC-05 | latest.json が不正な JSON の場合はエラー | 壊れた latest.json が存在する | `check()` を呼ぶ | 適切な例外が発生する |

---

## 9. MigrationManager

| ID | テスト名 | 前提 | 操作 | 期待 |
|----|---------|------|------|------|
| TC-MM-01 | schema_version が最新の場合はマイグレーションを実行しない | app_config の schema_version が最新 | `run_if_needed()` を呼ぶ | DB スキーマが変更されない |
| TC-MM-02 | schema_version が古い場合はマイグレーションを実行する | app_config の schema_version が古い | `run_if_needed()` を呼ぶ | 対象のマイグレーションが実行される |
| TC-MM-03 | マイグレーション後に schema_version が更新される | schema_version が古い状態でマイグレーション実行後 | `get_schema_version()` を呼ぶ | 最新バージョンに更新されている |
| TC-MM-04 | マイグレーション失敗時はロールバックされる | マイグレーションSQL の一部にエラーがある | `run_if_needed()` を呼ぶ | 部分的な変更が残らない |

---

## 10. StatusService

| ID | テスト名 | 前提 | 操作 | 期待 |
|----|---------|------|------|------|
| TC-SS-01 | ロック取得済みの状態で状態変更が成功する | ロック取得済み、対象社員の current_status が存在する | `change_status(employee_id, ...)` を呼ぶ | current_status が更新され status_history に履歴が追加される |
| TC-SS-02 | 退社済みに変更すると current_status の attendance_status が更新される | 出社中の社員が存在する | `change_status(id, 退社済み, ...)` を呼ぶ | attendance_status が退社済みに更新される |
| TC-SS-03 | updated_by に Windowsログオンユーザー名が記録される | UserContext にユーザー名が設定済み | `change_status(...)` を呼ぶ | current_status.updated_by と history.updated_by が一致する |
| TC-SS-04 | ロックが取得されていない場合はエラー | lock ファイルが存在しない（ロック未取得） | `change_status(...)` を呼ぶ | 適切な例外が発生する |
| TC-SS-05 | 存在しない employee_id を指定した場合はエラー | 該当社員が存在しない | `change_status(999, ...)` を呼ぶ | 適切な例外が発生する |

---

## 11. AdminService

| ID | テスト名 | 前提 | 操作 | 期待 |
|----|---------|------|------|------|
| TC-AS-01 | 社員新規追加が成功する | ロック取得済み | `save_employee(new_employee, is_new=True)` を呼ぶ | employee_master に追加される |
| TC-AS-02 | 社員新規追加時に current_status が自動作成される | ロック取得済み | `save_employee(new_employee, is_new=True)` を呼ぶ | current_status に初期レコード（出社中・在席・空欄）が追加される |
| TC-AS-03 | 社員追加と current_status 作成は同一トランザクション | ロック取得済み | `save_employee()` 中の current_status INSERT でエラーを注入 | employee_master にも追加されない |
| TC-AS-04 | 社員情報更新が成功する | ロック取得済み、社員が存在する | `save_employee(employee, is_new=False)` を呼ぶ | employee_master が更新される |
| TC-AS-05 | 保存前にバックアップが実行される | ロック取得済み | `save_employee(...)` を呼ぶ | BackupManager の `run_pre_master_backup` が呼ばれる |
| TC-AS-06 | ロックが取得されていない場合はエラー | lock ファイルが存在しない | `save_employee(...)` を呼ぶ | 適切な例外が発生する |

---

## 12. 統合テスト（シナリオ）

### TC-INT-01: 状態更新フロー（UC-03）

| ステップ | 操作 | 期待 |
|---------|------|------|
| 1 | `LockManager.try_acquire()` | ロック取得成功 |
| 2 | `StatusService.change_status(employee_id, 退社済み, 在席, "", "")` | current_status 更新、history 追加 |
| 3 | `LockManager.release()` | ロックファイルが削除される |
| 4 | `StatusRepository.get_by_employee_id(employee_id)` | attendance_status が退社済みに変わっている |
| 5 | `StatusRepository.get_all_current()` で履歴確認 | status_history に1件追加されている |

### TC-INT-02: 社員追加フロー（UC-05）

| ステップ | 操作 | 期待 |
|---------|------|------|
| 1 | `LockManager.try_acquire()` | ロック取得成功 |
| 2 | `AdminService.save_employee(new_employee, is_new=True)` | employee_master 追加、current_status 初期作成 |
| 3 | `LockManager.release()` | ロックファイルが削除される |
| 4 | `EmployeeRepository.get_all_active()` | 追加した社員が含まれる |
| 5 | `StatusRepository.get_by_employee_id(new_id)` | 初期 current_status（出社中・在席）が存在する |

### TC-INT-03: 編集中に別セッションがロック取得を試みる

| ステップ | 操作 | 期待 |
|---------|------|------|
| 1 | セッションAが `try_acquire()` | ロック取得成功 |
| 2 | セッションBが `try_acquire()` | `False` が返る |
| 3 | セッションAが `release()` | ロックファイルが削除される |
| 4 | セッションBが `try_acquire()` | ロック取得成功 |

### TC-INT-04: 起動時バックアップフロー（UC-起動）

| ステップ | 操作 | 期待 |
|---------|------|------|
| 1 | backup フォルダが空の状態で `run_startup_backup()` | バックアップファイルが作成される |
| 2 | 同日に `run_startup_backup()` を再度呼ぶ | 新たなファイルは作成されない |
| 3 | 翌日扱いで `run_startup_backup()` を呼ぶ | 新たなバックアップが作成される |

### TC-INT-05: 外部キー制約の整合性確認

| ステップ | 操作 | 期待 |
|---------|------|------|
| 1 | `PRAGMA foreign_keys = ON` の状態で存在しない employee_id を current_status に INSERT | 外部キー制約エラーが発生する |
| 2 | is_active=0 にした社員（論理削除）の current_status が残存する | 参照整合性が保たれている |
