"""Main window for koudouhyo application."""
from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, ttk
from typing import Callable, Optional

from koudouhyo.models import AppSettings, AttendanceStatus, LocationStatus


class MainWindow:
    def __init__(
        self,
        root: tk.Tk,
        app_settings: AppSettings,
        emp_repo,
        status_repo,
        lock_mgr,
        user_ctx,
    ) -> None:
        self._root = root
        self._app_settings = app_settings
        self._emp_repo = emp_repo
        self._status_repo = status_repo
        self._lock_mgr = lock_mgr
        self._user_ctx = user_ctx
        self._search_var = tk.StringVar()
        self._frame: Optional[ttk.Frame] = None

    def show(self) -> None:
        """Build and display the main window."""
        self._root.title("行動予定表")
        self._root.geometry("800x600")
        self._build_ui()
        self.refresh()

    def _build_ui(self) -> None:
        """Build the UI layout."""
        # Toolbar
        toolbar = ttk.Frame(self._root)
        toolbar.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)

        ttk.Button(toolbar, text="編集", command=self._on_edit_click).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="管理", command=self._on_admin_click).pack(side=tk.LEFT, padx=2)

        search_entry = ttk.Entry(toolbar, textvariable=self._search_var)
        search_entry.pack(side=tk.RIGHT, padx=2)
        self._search_var.trace_add("write", lambda *_: self._on_search(self._search_var.get()))

        # Main frame for rows
        self._frame = ttk.Frame(self._root)
        self._frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

    def refresh(self) -> None:
        """Refresh the display with latest data."""
        employees = self._emp_repo.get_all_active()
        statuses = self._status_repo.get_all_current()
        query = self._search_var.get() if self._search_var else ""
        if query:
            employees = [e for e in employees if query in e.employee_name or query in (e.department or "")]
        self._render_rows(employees, statuses)

    def _on_edit_click(self) -> None:
        """Open the edit window."""
        from koudouhyo.ui.edit_window import EditWindow
        win = EditWindow(
            parent=self._root,
            emp_repo=self._emp_repo,
            status_service=None,
            on_close_callback=self.refresh,
        )
        win.show()

    def _on_admin_click(self) -> None:
        """Open the admin window (admin only)."""
        if not self._user_ctx.is_admin(self._app_settings.admin_users):
            messagebox.showwarning("権限エラー", "管理者のみアクセスできます。")
            return
        from koudouhyo.ui.admin_window import AdminWindow
        win = AdminWindow(
            parent=self._root,
            emp_repo=self._emp_repo,
            admin_service=None,
            on_close_callback=self.refresh,
        )
        win.show()

    def _on_search(self, query: str) -> None:
        """Handle search input."""
        self.refresh()

    def _render_rows(self, employees, statuses) -> None:
        """Render employee rows in the main frame."""
        if self._frame is None:
            return
        for widget in self._frame.winfo_children():
            widget.destroy()

        status_map = {s.employee_id: s for s in statuses}

        headers = ["名前", "部署", "内線", "勤怠", "状態", "行先", "備考"]
        for col, header in enumerate(headers):
            ttk.Label(self._frame, text=header, font=("", 10, "bold")).grid(row=0, column=col, padx=4, pady=2, sticky="w")

        for row_idx, emp in enumerate(employees, start=1):
            status = status_map.get(emp.id)
            attendance = status.attendance_status if status else AttendanceStatus.IN_OFFICE
            location = status.location_status if status else LocationStatus.AT_DESK
            bg = self._get_row_bg_color(attendance)
            label_text = self._get_location_label(attendance, location)

            values = [
                emp.employee_name,
                emp.department or "",
                emp.extension_number or "",
                attendance.value if attendance else "",
                label_text,
                status.destination if status else "",
                status.note if status else "",
            ]
            for col, val in enumerate(values):
                lbl = tk.Label(self._frame, text=val, bg=bg)
                lbl.grid(row=row_idx, column=col, padx=4, pady=1, sticky="w")

    def _get_row_bg_color(self, attendance: AttendanceStatus) -> str:
        """Return background color based on attendance status."""
        if attendance == AttendanceStatus.LEFT:
            return "#ffcccc"
        return "white"

    def _get_location_label(self, attendance: AttendanceStatus, location: LocationStatus) -> str:
        """Return display label combining attendance and location status."""
        if attendance == AttendanceStatus.LEFT:
            return AttendanceStatus.LEFT.value
        return location.value if location else ""
