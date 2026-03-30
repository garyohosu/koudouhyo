# CONFIG.md

# 設定仕様

## 1. 基本方針

設定値は最小限とし、初版は以下の項目のみとする。

- `shared_root`
- `admin_users`

### 配置場所

- `app\current\config.json` に配置する
- 初版では利用者ごとの個別設定は持たず、共有運用向けの共通設定ファイルとして扱う
- 設定変更は管理者のみが実施する（`app\current` は管理者のみ書き換え可、一般利用者は読み取り専用前提）

## 2. 例

```json
{
  "shared_root": "\\\\server\\share\\koudouhyo",
  "admin_users": ["yamada", "suzuki"]
}
```

## 3. shared_root から決定するパス

- DB: `data\koudouhyo.db`
- backup: `backup\`
- lock: `lock\edit.lock`
- update: `update\latest.json`
- app: `app\`

## 4. config.json と app_config の使い分け

| 設定項目 | 保持場所 | 理由 |
|----------|----------|------|
| shared_root | config.json | DB接続前に必要な外部設定 |
| admin_users | config.json | クライアントごとに参照する設定 |
| schema_version | app_config（DB内） | DBに依存する内部設定 |

## 5. メリット

- 設定ミスを減らせる
- 運用担当者が覚える情報が少ない
- サーバー移設時も修正箇所が少ない
