"""Main entry point for koudouhyo application."""
import sys
import tkinter as tk
import tkinter.messagebox as mb
from pathlib import Path

# Add src to Python path (for script mode)
sys.path.insert(0, str(Path(__file__).parent / "src"))


def main():
    from koudouhyo.services.config_loader import ConfigLoader
    from koudouhyo.services.setup_service import ensure_shared_dirs, is_running_from_current, deploy_to_current
    from koudouhyo.database import DatabaseManager
    from koudouhyo.repositories import EmployeeRepository, StatusRepository, AppConfigRepository
    from koudouhyo.services.migration_manager import MigrationManager
    from koudouhyo.services.version_checker import VersionChecker
    from koudouhyo.services.backup_manager import BackupManager
    from koudouhyo.services.lock_manager import LockManager
    from koudouhyo.services.user_context import UserContext
    from koudouhyo.ui.main_window import MainWindow

    # --- 設定読み込み ---
    config_loader = ConfigLoader()
    try:
        app_settings = config_loader.load()
    except Exception as e:
        root = tk.Tk()
        root.withdraw()
        mb.showerror("設定エラー", f"config.json の読み込みに失敗しました:\n{e}")
        sys.exit(1)

    # --- 共有フォルダのディレクトリ構造を自動作成 ---
    try:
        ensure_shared_dirs(app_settings)
    except Exception as e:
        root = tk.Tk()
        root.withdraw()
        mb.showerror("フォルダ作成エラー", f"共有フォルダの初期化に失敗しました:\n{e}\n\n共有フォルダにアクセスできるか確認してください。\n{app_settings.shared_root}")
        sys.exit(1)

    # --- 初回起動時: app\current\ へ自動デプロイ ---
    if not is_running_from_current(app_settings):
        root = tk.Tk()
        root.withdraw()
        answer = mb.askyesno(
            "初期セットアップ",
            f"このexeを共有フォルダへコピーしますか？\n\n"
            f"コピー先:\n{app_settings.shared_root}\\app\\current\\\n\n"
            f"以降は共有フォルダのexeを起動してください。"
        )
        root.destroy()
        if answer:
            try:
                deploy_to_current(app_settings)
                root2 = tk.Tk()
                root2.withdraw()
                mb.showinfo("セットアップ完了", "共有フォルダへのコピーが完了しました。\n共有フォルダのexeを起動してください。")
                root2.destroy()
            except Exception as e:
                root2 = tk.Tk()
                root2.withdraw()
                mb.showerror("コピーエラー", f"コピーに失敗しました:\n{e}")
                root2.destroy()
        sys.exit(0)

    # --- バージョン確認 ---
    version_checker = VersionChecker(app_settings.update_json_path, "1.0.0")
    result = version_checker.check()
    if result.has_update and result.latest:
        root_tmp = tk.Tk()
        root_tmp.withdraw()
        mb.showinfo("アップデート", f"新しいバージョン {result.latest.version} が利用可能です。\n管理者に確認してください。")
        root_tmp.destroy()

    # --- DB 初期化・マイグレーション ---
    db = DatabaseManager(app_settings.db_path)
    db.connect()
    config_repo = AppConfigRepository(db)
    migration_mgr = MigrationManager(db, config_repo)
    migration_mgr.run_if_needed()

    # --- 起動時バックアップ ---
    backup_mgr = BackupManager(app_settings.db_path, app_settings.backup_dir)
    try:
        backup_mgr.run_startup_backup()
    except FileNotFoundError:
        pass  # 初回起動時はDBがまだない

    # --- サービス初期化 ---
    user_ctx = UserContext()
    lock_mgr = LockManager(app_settings.lock_path, user_ctx)
    emp_repo = EmployeeRepository(db)
    status_repo = StatusRepository(db)

    # --- ロック取得 ---
    if not lock_mgr.try_acquire():
        lock_info = lock_mgr.get_lock_info()
        root_tmp = tk.Tk()
        root_tmp.withdraw()
        msg = "現在、他のユーザーが編集中のため閲覧専用モードで起動します。"
        if lock_info:
            msg += f"\n編集中ユーザー: {lock_info.user_name} ({lock_info.pc_name})"
        mb.showinfo("閲覧専用モード", msg)
        root_tmp.destroy()

    # --- メイン画面起動 ---
    root = tk.Tk()
    app = MainWindow(root, app_settings, emp_repo, status_repo, lock_mgr, user_ctx)
    app.show()

    def on_close():
        lock_mgr.release()
        db.close()
        root.destroy()

    root.protocol("WM_DELETE_WINDOW", on_close)
    root.mainloop()


if __name__ == "__main__":
    main()
