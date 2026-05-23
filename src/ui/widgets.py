from __future__ import annotations

import os
import re
import tkinter as tk
from tkinter import ttk, filedialog
from pathlib import Path

from src.utils import format_size, format_bytes


ICON_ADD_FILE = "\U0001F4C4"
ICON_ADD_DIR = "\U0001F4C1"
ICON_DELETE = "\U0001F5D1"


class FileListFrame(ttk.LabelFrame):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, text="待压缩文件", **kwargs)
        self._files: list[str] = []
        self._sort_col: str = ""
        self._sort_rev: bool = False
        self._build_ui()

    def _build_ui(self):
        toolbar = ttk.Frame(self)
        toolbar.pack(fill=tk.X, padx=5, pady=(5, 0))

        ttk.Button(toolbar, text=f"{ICON_ADD_FILE} 添加文件", style="Toolbar.TButton",
                   command=self._add_files).pack(side=tk.LEFT, padx=1)
        ttk.Button(toolbar, text=f"{ICON_ADD_DIR} 添加文件夹", style="Toolbar.TButton",
                   command=self._add_folder).pack(side=tk.LEFT, padx=1)
        ttk.Button(toolbar, text=f"{ICON_DELETE} 清空", style="Toolbar.TButton",
                   command=self._clear).pack(side=tk.LEFT, padx=1)

        self._hint = ttk.Label(toolbar, text="", foreground="gray")
        self._hint.pack(side=tk.LEFT, padx=10)

        self._count_label = ttk.Label(toolbar, text="共 0 项")
        self._count_label.pack(side=tk.RIGHT, padx=5)

        list_frame = ttk.Frame(self)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        scroll = ttk.Scrollbar(list_frame, orient=tk.VERTICAL)
        cols = ("name", "type", "size")
        self._tree = ttk.Treeview(list_frame, columns=cols, show="headings",
                                  yscrollcommand=scroll.set, selectmode="extended")
        scroll.config(command=self._tree.yview)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self._tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self._tree.heading("name", text="文件名", command=lambda: self._sort_by("name"))
        self._tree.heading("type", text="类型", command=lambda: self._sort_by("type"))
        self._tree.heading("size", text="大小", command=lambda: self._sort_by("size"))
        self._tree.column("name", width=320, minwidth=160)
        self._tree.column("type", width=70, minwidth=60, anchor=tk.CENTER)
        self._tree.column("size", width=90, minwidth=70, anchor=tk.E)
        self._tree.bind("<Button-3>", self._show_menu)
        self._tree.bind("<Delete>", lambda e: self._remove_selected())
        self._tree.bind("<Control-a>", lambda e: self._select_all())
        self._tree.bind("<Button-1>", self._on_click_header)

    def _on_click_header(self, event):
        region = self._tree.identify_region(event.x, event.y)
        if region == "heading":
            col = self._tree.identify_column(event.x)
            col_map = {"#1": "name", "#2": "type", "#3": "size"}
            self._sort_by(col_map.get(col, "name"))

    def _sort_by(self, col: str):
        if self._sort_col == col:
            self._sort_rev = not self._sort_rev
        else:
            self._sort_col = col
            self._sort_rev = False

        def key(f):
            p = Path(f)
            if col == "name":
                return (0, p.name.lower()) if p.is_file() else (1, p.name.lower())
            if col == "type":
                return 0 if p.is_file() else 1
            if col == "size":
                try:
                    return -p.stat().st_size if p.is_file() else -sum(f.stat().st_size for f in p.rglob("*") if f.is_file()) if any(p.rglob("*")) else 0
                except OSError:
                    return 0
            return 0

        self._files.sort(key=key, reverse=self._sort_rev)
        self._refresh()

    def set_drag_drop_hint(self, available: bool):
        if available:
            self._hint.config(text="将文件/文件夹拖放到此处", foreground="green")
        else:
            self._hint.config(text="请使用「添加文件」「添加文件夹」按钮", foreground="gray")

    def enable_drag_drop(self):
        try:
            import tkinterdnd2
            self._tree.drop_target_register(tkinterdnd2.DND_FILES)
            self._tree.dnd_bind("<<Drop>>", self._on_drop)
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
        sel = self._tree.selection()
        indices = sorted([int(item) for item in sel], reverse=True)
        for i in indices:
            self._files.pop(i)
        self._refresh()

    def _show_menu(self, event):
        sel = self._tree.selection()
        region = self._tree.identify_region(event.x, event.y)
        if region == "cell" or region == "tree":
            if not sel:
                item = self._tree.identify_row(event.y)
                if item:
                    self._tree.selection_set(item)
                    sel = (item,)
        if sel:
            m = tk.Menu(self, tearoff=0)
            m.add_command(label="移除选中", command=self._remove_selected)
            m.add_command(label="打开所在文件夹", command=self._open_folder)
            m.add_separator()
            m.add_command(label="全选", command=self._select_all)
            m.add_command(label="反选", command=self._invert_selection)
            m.add_separator()
            m.add_command(label="清空全部", command=self._clear)
            m.post(event.x_root, event.y_root)
        else:
            m = tk.Menu(self, tearoff=0)
            m.add_command(label="全选", command=self._select_all)
            m.add_command(label="反选", command=self._invert_selection)
            m.add_separator()
            m.add_command(label="清空全部", command=self._clear)
            m.post(event.x_root, event.y_root)

    def _open_folder(self):
        sel = self._tree.selection()
        if not sel:
            return
        idx = int(sel[0])
        path = self._files[idx]
        folder = os.path.dirname(path) if Path(path).is_file() else path
        os.startfile(folder)

    def _select_all(self):
        self._tree.selection_set(self._tree.get_children())

    def _invert_selection(self):
        all_items = set(self._tree.get_children())
        sel = set(self._tree.selection())
        for item in all_items - sel:
            self._tree.selection_add(item)
        for item in sel & all_items:
            self._tree.selection_remove(item)

    def _refresh(self):
        for item in self._tree.get_children():
            self._tree.delete(item)
        for i, f in enumerate(self._files):
            p = Path(f)
            is_dir = p.is_dir()
            name = p.name if is_dir else p.name
            type_str = "文件夹" if is_dir else "文件"
            try:
                if is_dir:
                    count = sum(1 for _ in p.rglob("*"))
                    size_str = f"({count} 项)"
                else:
                    size = p.stat().st_size
                    size_str = format_bytes(size)
            except OSError:
                size_str = ""
            self._tree.insert("", tk.END, iid=str(i),
                              values=(name, type_str, size_str))
        self._count_label.config(text=f"共 {len(self._files)} 项")

    def get_files(self) -> list[str]:
        return list(self._files)

    def set_enabled(self, enabled: bool):
        state = "normal" if enabled else "disabled"
        self._tree.configure(selectmode="extended" if enabled else "none")
        self._tree.configure(cursor="" if enabled else "no")
