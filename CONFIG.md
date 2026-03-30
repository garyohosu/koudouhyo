# CONFIG.md

# 設定仕様

## 1. 基本方針

設定値は最小限とし、初版は以下の項目のみとする。

- `shared_root`
- `admin_users`

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
