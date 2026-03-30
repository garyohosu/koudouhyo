"""Main entry point for koudouhyo application."""
import sys
import tkinter as tk
from pathlib import Path

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))


def main():
    from koudouhyo.services.config_loader import ConfigLoader
    from koudouhyo.database import DatabaseManager
    from koudouhyo.repositories import EmployeeRepository, StatusRepository, AppConfigRepository
    from koudouhyo.services.migration_manager import MigrationManager
    from koudouhyo.services.version_checker import VersionChecker
    from koudouhyo.services.backup_manager import BackupManager
    from koudouhyo.services.lock_manager import LockManager
    from koudouhyo.services.user_context import UserContext
    from koudouhyo.ui.main_window import MainWindow

    # Load configuration
    config_loader = ConfigLoader()
    try:
        app_settings = config_loader.load()
    except Exception as e:
        import tkinter.messagebox as mb
        root = tk.Tk()
        root.withdraw()
        mb.showerror("設定エラー", f"config.json の読み込みに失敗しました:\n{e}")
        sys.exit(1)

    # Initialize database
    db = DatabaseManager(app_settings.db_path)
    db.connect()

    # Run migrations
    config_repo = AppConfigRepository(db)
    migration_mgr = MigrationManager(db, config_repo)
    migration_mgr.run_if_needed()

    # Check for updates
    version_checker = VersionChecker(app_settings.update_json_path, "1.0.0")
    result = version_checker.check()
    if result.has_update and result.latest:
        import tkinter.messagebox as mb
        root_tmp = tk.Tk()
        root_tmp.withdraw()
        mb.showinfo("アップデート", f"新しいバージョン {result.latest.version} が利用可能です。")
        root_tmp.destroy()

    # Run startup backup
    backup_mgr = BackupManager(app_settings.db_path, app_settings.backup_dir)
    try:
        backup_mgr.run_startup_backup()
    except FileNotFoundError:
        pass  # DB not yet created on first run

    # Initialize services
    user_ctx = UserContext()
    lock_mgr = LockManager(app_settings.lock_path, user_ctx)
    emp_repo = EmployeeRepository(db)
    status_repo = StatusRepository(db)

    # Acquire lock
    if not lock_mgr.try_acquire():
        lock_info = lock_mgr.get_lock_info()
        import tkinter.messagebox as mb
        root_tmp = tk.Tk()
        root_tmp.withdraw()
        msg = "アプリケーションは既に起動されています。"
        if lock_info:
            msg += f"\nユーザー: {lock_info.user_name} ({lock_info.pc_name})"
        mb.showwarning("起動エラー", msg)
        root_tmp.destroy()
        db.close()
        sys.exit(1)

    # Start main window
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
