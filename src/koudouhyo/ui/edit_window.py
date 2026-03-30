"""Edit window for koudouhyo application."""
from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, ttk
from typing import Callable, Optional


class EditWindow:
    def __init__(
        self,
        parent: tk.Widget,
        emp_repo,
        status_service,
        on_close_callback: Optional[Callable] = None,
    ) -> None:
        self._parent = parent
        self._emp_repo = emp_repo
        self._status_service = status_service
        self._on_close_callback = on_close_callback
        self._window: Optional[tk.Toplevel] = None
        self._selected_employee_id: Optional[int] = None

    def show(self) -> None:
        """Display the edit window."""
        self._window = tk.Toplevel(self._parent)
        self._window.title("状態編集")
        self._window.geometry("400x300")
        self._window.protocol("WM_DELETE_WINDOW", self._on_cancel)
        self._build_ui()

    def _build_ui(self) -> None:
        """Build the edit window UI."""
        frame = ttk.Frame(self._window, padding=10)
        frame.pack(fill=tk.BOTH, expand=True)

        # Employee selection
        ttk.Label(frame, text="社員:").grid(row=0, column=0, sticky="w", pady=4)
        self._emp_var = tk.StringVar()
        employees = self._emp_repo.get_all_active()
        emp_names = [f"{e.id}: {e.employee_name}" for e in employees]
        self._emp_combo = ttk.Combobox(frame, textvariable=self._emp_var, values=emp_names, state="readonly")
        self._emp_combo.grid(row=0, column=1, sticky="ew", pady=4)
        self._emp_combo.bind("<<ComboboxSelected>>", self._on_employee_select)

        # Status fields
        ttk.Label(frame, text="勤怠状態:").grid(row=1, column=0, sticky="w", pady=4)
        self._attendance_var = tk.StringVar()
        ttk.Combobox(frame, textvariable=self._attendance_var,
                     values=["出社中", "退社済み"], state="readonly").grid(row=1, column=1, sticky="ew", pady=4)

        ttk.Label(frame, text="在席状態:").grid(row=2, column=0, sticky="w", pady=4)
        self._location_var = tk.StringVar()
        ttk.Combobox(frame, textvariable=self._location_var,
                     values=["在席", "外出", "出張", "休暇", "会議", "直行", "直帰", "その他"],
                     state="readonly").grid(row=2, column=1, sticky="ew", pady=4)

        ttk.Label(frame, text="行先:").grid(row=3, column=0, sticky="w", pady=4)
        self._destination_var = tk.StringVar()
        ttk.Entry(frame, textvariable=self._destination_var).grid(row=3, column=1, sticky="ew", pady=4)

        ttk.Label(frame, text="備考:").grid(row=4, column=0, sticky="w", pady=4)
        self._note_var = tk.StringVar()
        ttk.Entry(frame, textvariable=self._note_var).grid(row=4, column=1, sticky="ew", pady=4)

        # Buttons
        btn_frame = ttk.Frame(frame)
        btn_frame.grid(row=5, column=0, columnspan=2, pady=10)
        ttk.Button(btn_frame, text="保存", command=self._on_save).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="キャンセル", command=self._on_cancel).pack(side=tk.LEFT, padx=5)

    def _on_save(self) -> None:
        """Handle save button click."""
        if self._selected_employee_id is None:
            messagebox.showwarning("入力エラー", "社員を選択してください。")
            return
        try:
            from koudouhyo.models import AttendanceStatus, LocationStatus
            attendance = AttendanceStatus(self._attendance_var.get())
            location = LocationStatus(self._location_var.get())
            self._status_service.change_status(
                employee_id=self._selected_employee_id,
                attendance_status=attendance,
                location_status=location,
                destination=self._destination_var.get(),
                note=self._note_var.get(),
            )
            if self._on_close_callback:
                self._on_close_callback()
            self._window.destroy()
        except Exception as e:
            messagebox.showerror("エラー", str(e))

    def _on_cancel(self) -> None:
        """Handle cancel button click."""
        if self._window:
            self._window.destroy()

    def _on_employee_select(self, event) -> None:
        """Handle employee selection from combobox."""
        selected = self._emp_var.get()
        if selected:
            emp_id = int(selected.split(":")[0])
            self._load_employee_data(emp_id)

    def _load_employee_data(self, employee_id: int) -> None:
        """Load existing status data for selected employee."""
        self._selected_employee_id = employee_id
