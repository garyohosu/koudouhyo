"""Admin window for koudouhyo application."""
from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, ttk
from typing import Callable, Optional


class AdminWindow:
    def __init__(
        self,
        parent: tk.Widget,
        emp_repo,
        admin_service,
        on_close_callback: Optional[Callable] = None,
    ) -> None:
        self._parent = parent
        self._emp_repo = emp_repo
        self._admin_service = admin_service
        self._on_close_callback = on_close_callback
        self._window: Optional[tk.Toplevel] = None
        self._selected_employee_id: Optional[int] = None

    def show(self) -> None:
        """Display the admin window."""
        self._window = tk.Toplevel(self._parent)
        self._window.title("社員マスタ管理")
        self._window.geometry("600x400")
        self._window.protocol("WM_DELETE_WINDOW", self._on_cancel)
        self._build_ui()

    def _build_ui(self) -> None:
        """Build the admin window UI."""
        frame = ttk.Frame(self._window, padding=10)
        frame.pack(fill=tk.BOTH, expand=True)

        # Employee list
        ttk.Label(frame, text="社員一覧:").grid(row=0, column=0, sticky="w", pady=4)
        self._emp_listbox = tk.Listbox(frame, height=10, width=40)
        self._emp_listbox.grid(row=1, column=0, columnspan=2, sticky="ew", pady=4)
        self._load_employee_list()

        # Form fields
        ttk.Label(frame, text="氏名:").grid(row=2, column=0, sticky="w", pady=4)
        self._name_var = tk.StringVar()
        ttk.Entry(frame, textvariable=self._name_var).grid(row=2, column=1, sticky="ew", pady=4)

        ttk.Label(frame, text="部署:").grid(row=3, column=0, sticky="w", pady=4)
        self._dept_var = tk.StringVar()
        ttk.Entry(frame, textvariable=self._dept_var).grid(row=3, column=1, sticky="ew", pady=4)

        ttk.Label(frame, text="内線:").grid(row=4, column=0, sticky="w", pady=4)
        self._ext_var = tk.StringVar()
        ttk.Entry(frame, textvariable=self._ext_var).grid(row=4, column=1, sticky="ew", pady=4)

        ttk.Label(frame, text="表示順:").grid(row=5, column=0, sticky="w", pady=4)
        self._order_var = tk.StringVar(value="0")
        ttk.Entry(frame, textvariable=self._order_var).grid(row=5, column=1, sticky="ew", pady=4)

        # Buttons
        btn_frame = ttk.Frame(frame)
        btn_frame.grid(row=6, column=0, columnspan=2, pady=10)
        ttk.Button(btn_frame, text="追加", command=self._on_add).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="更新", command=self._on_save).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="無効化", command=lambda: self._on_deactivate(self._selected_employee_id)).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="有効化", command=lambda: self._on_reactivate(self._selected_employee_id)).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="閉じる", command=self._on_cancel).pack(side=tk.LEFT, padx=5)

    def _load_employee_list(self) -> None:
        """Load and display all employees in the listbox."""
        self._emp_listbox.delete(0, tk.END)
        employees = self._emp_repo.get_all()
        self._employees = employees
        for emp in employees:
            status_str = "有効" if emp.is_active else "無効"
            self._emp_listbox.insert(tk.END, f"{emp.id}: {emp.employee_name} ({status_str})")

    def _on_save(self) -> None:
        """Handle update button click."""
        if self._selected_employee_id is None:
            messagebox.showwarning("入力エラー", "社員を選択してください。")
            return
        try:
            from koudouhyo.models import EmployeeMaster
            emp = EmployeeMaster(
                id=self._selected_employee_id,
                employee_name=self._name_var.get(),
                department=self._dept_var.get(),
                extension_number=self._ext_var.get(),
                display_order=int(self._order_var.get() or "0"),
            )
            self._admin_service.save_employee(emp, is_new=False)
            self._load_employee_list()
            if self._on_close_callback:
                self._on_close_callback()
        except Exception as e:
            messagebox.showerror("エラー", str(e))

    def _on_add(self) -> None:
        """Handle add button click."""
        try:
            from koudouhyo.models import EmployeeMaster
            emp = EmployeeMaster(
                employee_name=self._name_var.get(),
                department=self._dept_var.get(),
                extension_number=self._ext_var.get(),
                display_order=int(self._order_var.get() or "0"),
            )
            self._admin_service.save_employee(emp, is_new=True)
            self._load_employee_list()
            if self._on_close_callback:
                self._on_close_callback()
        except Exception as e:
            messagebox.showerror("エラー", str(e))

    def _on_deactivate(self, employee_id: Optional[int]) -> None:
        """Deactivate an employee."""
        if employee_id is None:
            messagebox.showwarning("入力エラー", "社員を選択してください。")
            return
        try:
            emp = self._emp_repo.get_by_id(employee_id)
            if emp:
                emp.is_active = 0
                self._admin_service.save_employee(emp, is_new=False)
                self._load_employee_list()
        except Exception as e:
            messagebox.showerror("エラー", str(e))

    def _on_reactivate(self, employee_id: Optional[int]) -> None:
        """Reactivate an employee."""
        if employee_id is None:
            messagebox.showwarning("入力エラー", "社員を選択してください。")
            return
        try:
            emp = self._emp_repo.get_by_id(employee_id)
            if emp:
                emp.is_active = 1
                self._admin_service.save_employee(emp, is_new=False)
                self._load_employee_list()
        except Exception as e:
            messagebox.showerror("エラー", str(e))

    def _on_cancel(self) -> None:
        """Handle cancel/close button click."""
        if self._window:
            self._window.destroy()
