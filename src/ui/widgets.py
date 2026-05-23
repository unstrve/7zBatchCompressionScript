from __future__ import annotations

import os
import re
import tkinter as tk
from tkinter import ttk, filedialog
from pathlib import Path

from src.utils import format_size


class FileListFrame(ttk.LabelFrame):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, text="待压缩文件", **kwargs)
        self._files: list[str] = []
        self._build_ui()

    def _build_ui(self):
        toolbar = ttk.Frame(self)
        toolbar.pack(fill=tk.X, padx=5, pady=(5, 0))

        ttk.Button(toolbar, text="添加文件", command=self._add_files).pack(side=tk.LEFT, padx=1)
        ttk.Button(toolbar, text="添加文件夹", command=self._add_folder).pack(side=tk.LEFT, padx=1)
        ttk.Button(toolbar, text="清空", command=self._clear).pack(side=tk.LEFT, padx=1)

        self._hint = ttk.Label(toolbar, text="", foreground="gray")
        self._hint.pack(side=tk.LEFT, padx=10)

        self._count_label = ttk.Label(toolbar, text="共 0 项")
        self._count_label.pack(side=tk.RIGHT, padx=5)

        list_frame = ttk.Frame(self)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        scroll = ttk.Scrollbar(list_frame, orient=tk.VERTICAL)
        self._listbox = tk.Listbox(list_frame, yscrollcommand=scroll.set, height=6)
        scroll.config(command=self._listbox.yview)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self._listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self._menu = tk.Menu(self, tearoff=0)
        self._menu.add_command(label="移除选中", command=self._remove_selected)
        self._menu.add_command(label="打开所在文件夹", command=self._open_folder)
        self._menu.add_separator()
        self._menu.add_command(label="全选", command=self._select_all)
        self._menu.add_command(label="反选", command=self._invert_selection)
        self._menu.add_separator()
        self._menu.add_command(label="清空全部", command=self._clear)
        self._listbox.bind("<Button-3>", self._show_menu)
        self._listbox.bind("<Delete>", lambda e: self._remove_selected())
        self._listbox.bind("<Control-a>", lambda e: self._select_all())

    def set_drag_drop_hint(self, available: bool):
        if available:
            self._hint.config(text="将文件/文件夹拖放到此处", foreground="green")
        else:
            self._hint.config(text="请使用「添加文件」「添加文件夹」按钮", foreground="gray")

    def enable_drag_drop(self):
        try:
            import tkinterdnd2
            self._listbox.drop_target_register(tkinterdnd2.DND_FILES)
            self._listbox.dnd_bind("<<Drop>>", self._on_drop)
            self.set_drag_drop_hint(True)
        except ImportError:
            self.set_drag_drop_hint(False)
        except Exception as e:
            print(f"[DnD init error] {e}")
            self.set_drag_drop_hint(False)

    def _add_path(self, p: str):
        p = os.path.normpath(p)
        if p not in self._files:
            self._files.append(p)

    def _on_drop(self, event):
        raw = event.data
        items = re.findall(r"\{([^}]*)\}|(\S+)", raw)
        for match in items:
            p = (match[0] or match[1]).strip('"').strip()
            if Path(p).exists():
                self._add_path(p)
        self._refresh()

    def _add_files(self):
        paths = filedialog.askopenfilenames(title="选择要压缩的文件")
        for p in paths:
            self._add_path(p)
        self._refresh()

    def _add_folder(self):
        path = filedialog.askdirectory(title="选择要压缩的文件夹")
        if path:
            self._add_path(path)
            self._refresh()

    def _clear(self):
        self._files.clear()
        self._refresh()

    def _remove_selected(self):
        sel = self._listbox.curselection()
        for i in reversed(sel):
            self._files.pop(i)
        self._refresh()

    def _show_menu(self, event):
        if self._listbox.curselection():
            self._menu.post(event.x_root, event.y_root)
        else:
            m = tk.Menu(self, tearoff=0)
            m.add_command(label="全选", command=self._select_all)
            m.add_command(label="反选", command=self._invert_selection)
            m.add_separator()
            m.add_command(label="清空全部", command=self._clear)
            m.post(event.x_root, event.y_root)

    def _open_folder(self):
        sel = self._listbox.curselection()
        if not sel:
            return
        path = self._files[sel[0]]
        folder = os.path.dirname(path) if Path(path).is_file() else path
        os.startfile(folder)

    def _select_all(self):
        self._listbox.selection_set(0, tk.END)

    def _invert_selection(self):
        end = int(self._listbox.index(tk.END)) - 1
        for i in range(end + 1):
            if i in self._listbox.curselection():
                self._listbox.selection_clear(i)
            else:
                self._listbox.selection_set(i)

    def _refresh(self):
        self._listbox.delete(0, tk.END)
        for f in self._files:
            p = Path(f)
            prefix = "[文件夹]" if p.is_dir() else "[文件]"
            size = format_size(f)
            label = f"{prefix} {f}  {size}" if size else f"{prefix} {f}"
            self._listbox.insert(tk.END, label)
        self._count_label.config(text=f"共 {len(self._files)} 项")

    def get_files(self) -> list[str]:
        return list(self._files)

    def set_enabled(self, enabled: bool):
        state = tk.NORMAL if enabled else tk.DISABLED
        self._listbox.config(state=state)
