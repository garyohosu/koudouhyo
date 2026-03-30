# CONFIG.md

# 設定仕様

## 1. 基本方針

設定値は原則1つのみとする。

- `shared_root`

## 2. 例

```json
{
  "shared_root": "\\\\server\\share\\koudouhyo"
}
```

## 3. shared_root から決定するパス

- DB: `data\koudouhyo.db`
- backup: `backup\`
- lock: `lock\edit.lock`
- update: `update\latest.json`
- app: `app\`

## 4. メリット

- 設定ミスを減らせる
- 運用担当者が覚える情報が少ない
- サーバー移設時も修正箇所が少ない
