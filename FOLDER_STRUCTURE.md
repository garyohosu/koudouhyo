# FOLDER_STRUCTURE.md

# フォルダ構成案

```text
\\server\share\koudouhyo\
├─ app\
│  ├─ current\
│  │  └─ Koudouhyo.exe
│  └─ releases\
│     ├─ 1.0.0\
│     │  └─ Koudouhyo.exe
│     └─ 1.1.0\
│        └─ Koudouhyo.exe
├─ data\
│  └─ koudouhyo.db
├─ backup\
│  └─ koudouhyo_YYYYMMDD_HHMMSS.db
├─ lock\
│  └─ edit.lock
└─ update\
   └─ latest.json
```

## 備考

- DBは共有フォルダ上の1ファイルを利用する
- 更新頻度は低く、編集時はロックを取る
- アプリとDBのルートは `shared_root` 1つで管理する
- 利用者は常に `app\current\Koudouhyo.exe` を起動する
- `app\releases` は管理者向けの版管理・保管用とし、一般利用者は直接起動しない
