# SEQUENCE.md

# シーケンス図

---

## UC-起動: アプリ起動シーケンス（バージョン確認・バックアップ）

```mermaid
sequenceDiagram
    actor User as 利用者
    participant App as アプリ
    participant FS as 共有フォルダ
    participant DB as SQLite DB

    User->>App: Koudouhyo.exe 起動 (app\current)
    App->>FS: latest.json を読み込む
    alt 新版あり
        App-->>User: 「新版があります。管理者に確認してください。」
    else 最新版
        Note over App: 案内なし
    end

    App->>FS: backup\ フォルダを確認
    alt 当日のバックアップが存在しない
        App->>FS: koudouhyo_YYYYMMDD_HHMMSS.db を作成
        Note over App,FS: 30世代を超える場合は古いものを削除
    else 当日分が存在する
        Note over App: バックアップをスキップ
    end

    App->>DB: PRAGMA foreign_keys = ON
    App->>DB: schema_version を確認
    alt マイグレーションが必要
        App->>DB: マイグレーション実行
    end

    App->>DB: 社員一覧・現在状態を取得
    App-->>User: メイン画面を表示
```

---

## UC-01/02: 社員一覧閲覧（電話応対時）

```mermaid
sequenceDiagram
    actor User as 電話応対者
    participant App as アプリ
    participant DB as SQLite DB

    User->>App: メイン画面を開く
    App->>DB: SELECT employee_master + current_status (is_active=1)
    DB-->>App: 社員一覧・状態データ
    App-->>User: 一覧表示（氏名背景色・状態札・行先・内線・備考）

    User->>App: 対象社員の行を確認
    Note over User,App: 氏名背景色で出社状態を判断（白=出社中, 赤=退社済み）
    Note over User,App: 状態札で所在状態を確認（退社済み時は退社済み優先表示）
    Note over User,App: 行先・備考で補足を確認
```

---

## UC-03/04: 社員の状態を更新する（ロック取得〜保存〜解除）

```mermaid
sequenceDiagram
    actor User as 更新者
    participant App as アプリ
    participant FS as 共有フォルダ
    participant DB as SQLite DB

    User->>App: 編集ボタンをクリック
    App->>FS: edit.lock の存在確認
    alt ロックファイルが存在する
        App->>FS: edit.lock の更新時刻を確認
        alt 更新時刻から60分未満（有効なロック）
            App-->>User: 「現在 [利用者名] が編集中です（閲覧専用）」
            Note over User,App: 編集不可・閲覧専用モード
        else 更新時刻から60分以上経過（期限切れ）
            App-->>User: 「期限切れのロックが存在します」
            Note over App: 管理者のみ解除可能（後述）
        end
    else ロックファイルが存在しない
        App->>FS: edit.lock を作成（利用者名・PC名・開始時刻・版数を記録）
        App-->>User: 編集画面を表示

        loop 5分ごと（編集中）
            App->>FS: edit.lock の更新時刻を更新
        end

        User->>App: 対象社員を選択し状態を入力
        User->>App: 保存ボタンをクリック

        App->>DB: status_history に変更前データを INSERT
        App->>DB: current_status を UPDATE（updated_by=Windowsログオンユーザー名）
        DB-->>App: 保存完了

        App->>FS: edit.lock を削除
        App->>DB: 社員一覧・現在状態を再取得
        App-->>User: メイン画面へ戻る（一覧更新済み）
    end
```

---

## UC-03: 更新キャンセル・アプリ終了時のロック解除

```mermaid
sequenceDiagram
    actor User as 更新者
    participant App as アプリ
    participant FS as 共有フォルダ

    alt キャンセルボタンをクリック
        User->>App: キャンセル
    else アプリを閉じる
        User->>App: ウィンドウを閉じる
    end

    App->>FS: edit.lock を削除
    App-->>User: メイン画面へ戻る（またはアプリ終了）
```

---

## UC-04: 期限切れロックを管理者が解除する

```mermaid
sequenceDiagram
    actor Admin as 管理者
    participant App as アプリ
    participant FS as 共有フォルダ
    participant CF as config.json

    Admin->>App: 編集ボタンをクリック
    App->>FS: edit.lock の存在・更新時刻を確認
    Note over App: 更新時刻から60分以上経過 → 期限切れ
    App->>CF: admin_users を確認
    CF-->>App: 管理者ユーザー名一覧

    alt 現在のWindowsログオンユーザーが admin_users に含まれる
        App-->>Admin: 「期限切れロックがあります。解除しますか？」
        Admin->>App: 解除を承認
        App->>FS: edit.lock を削除
        App->>FS: 新しい edit.lock を作成
        App-->>Admin: 編集画面を表示
    else 管理者でない
        App-->>Admin: 「期限切れロックがあります。管理者に解除を依頼してください。」
    end
```

---

## UC-05: 管理者が社員マスタを変更する

```mermaid
sequenceDiagram
    actor Admin as 管理者
    participant App as アプリ
    participant FS as 共有フォルダ
    participant DB as SQLite DB

    Admin->>App: 管理画面を開く
    App->>DB: 社員マスタ全件取得（is_active 0/1 両方）
    DB-->>App: 社員一覧（無効社員含む）
    App-->>Admin: 管理画面を表示

    Admin->>App: 社員情報を編集（氏名・所属・内線・表示順・使用中フラグ）
    Admin->>App: 保存ボタンをクリック

    App->>FS: バックアップ作成（koudouhyo_YYYYMMDD_HHMMSS.db）
    App->>DB: PRAGMA foreign_keys = ON
    App->>DB: employee_master を UPDATE
    DB-->>App: 保存完了

    App-->>Admin: メイン画面へ戻る

    alt 新規社員追加の場合
        App->>DB: current_status に初期レコードを INSERT
        Note over App,DB: 出社中・在席・行先空・備考空
    end
```

---

## UC-06: バックアップを取得する（マスタ変更前の自動バックアップ）

```mermaid
sequenceDiagram
    participant App as アプリ
    participant FS as 共有フォルダ

    Note over App: マスタ変更保存前に実行
    App->>FS: backup\ フォルダのファイル一覧を取得
    App->>FS: koudouhyo_YYYYMMDD_HHMMSS.db をコピー作成

    App->>FS: バックアップファイル一覧を確認
    alt 30世代を超える
        App->>FS: 最古のバックアップファイルを削除
    end
```

---

## UC-07: 更新版を確認する（起動時）

```mermaid
sequenceDiagram
    actor User as 利用者
    participant App as アプリ
    participant FS as 共有フォルダ

    User->>App: app\current\Koudouhyo.exe を起動
    App->>FS: update\latest.json を読み込む
    FS-->>App: { "version": "x.x.x", "path": "...", "notes": "..." }

    App->>App: 現在の版数と latest.json の version を比較

    alt 新版がある（latest > current）
        App-->>User: 「新版があります。管理者に確認してください。」
        Note over User: 案内のみ。自動更新は行わない（初版）
    else 最新版
        Note over App: 案内なし・起動処理を続行
    end
```
