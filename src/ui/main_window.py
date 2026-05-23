from __future__ import annotations

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from typing import Optional

from src.models import CompressPreset
from src.task import CompressionTask
from src.settings import Settings
from src.ui.widgets import FileListFrame
from src.ui.dialogs import ManagePresetsDialog
from src.ui.progress_window import ProgressWindow


class MainWindow:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("7z 批量压缩工具")
        self.root.minsize(560, 500)
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)
        self.settings = Settings()
        self._task: Optional[CompressionTask] = None
        self._pw: Optional[ProgressWindow] = None
        self._build_ui()
        self._refresh_presets()

    def _build_ui(self):
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)
        self._build_file_tab(notebook)
        self._build_tool_tab(notebook)
        self._build_help_tab(notebook)

    def _build_file_tab(self, notebook):
        tab = ttk.Frame(notebook, padding=(6, 4))
        notebook.add(tab, text="文件")

        self.file_list = FileListFrame(tab)
        self.file_list.pack(fill=tk.BOTH, expand=True)

        opt_frame = ttk.LabelFrame(tab, text="压缩选项")
        opt_frame.pack(fill=tk.X, pady=(6, 0))

        row = ttk.Frame(opt_frame)
        row.pack(fill=tk.X, padx=5, pady=5)
        ttk.Label(row, text="预设：").pack(side=tk.LEFT)
        self._preset_combo = ttk.Combobox(row, state="readonly", width=25)
        self._preset_combo.pack(side=tk.LEFT, padx=5)

        ttk.Separator(row, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=8)

        self._mode = tk.StringVar(value="individual")
        ttk.Label(row, text="模式：").pack(side=tk.LEFT)
        ttk.Radiobutton(row, text="独立", variable=self._mode, value="individual").pack(side=tk.LEFT, padx=2)
        ttk.Radiobutton(row, text="合并", variable=self._mode, value="merge").pack(side=tk.LEFT, padx=2)

        action_frame = ttk.Frame(tab)
        action_frame.pack(fill=tk.X, pady=(6, 0))
        self._start_btn = ttk.Button(action_frame, text="开始压缩", command=self._start)
        self._start_btn.pack(side=tk.LEFT, padx=2)
        self._cancel_btn = ttk.Button(action_frame, text="取消", command=self._cancel, state=tk.DISABLED)
        self._cancel_btn.pack(side=tk.LEFT, padx=2)

    def _build_tool_tab(self, notebook):
        tab = ttk.Frame(notebook, padding=(12, 10))
        notebook.add(tab, text="工具")

        ttk.Label(tab, text="7-Zip 路径", font=("", 10, "bold")).pack(anchor=tk.W)
        path_frame = ttk.Frame(tab)
        path_frame.pack(fill=tk.X, pady=(4, 12))
        self._path_var = tk.StringVar(value=self.settings.sevenz_path)
        ttk.Entry(path_frame, textvariable=self._path_var, width=50).pack(side=tk.LEFT)
        ttk.Button(path_frame, text="浏览", command=self._browse_7z).pack(side=tk.LEFT, padx=4)
        ttk.Button(path_frame, text="保存", command=self._save_7z_path).pack(side=tk.LEFT)
        ttk.Label(tab, text="留空则自动搜索 PATH 和常见安装目录。", foreground="gray").pack(anchor=tk.W)

        ttk.Separator(tab, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=12)
        ttk.Label(tab, text="预设管理", font=("", 10, "bold")).pack(anchor=tk.W)
        ttk.Button(tab, text="打开预设管理器...", command=self._manage_presets).pack(anchor=tk.W, pady=(4, 0))

    def _build_help_tab(self, notebook):
        tab = ttk.Frame(notebook, padding=(12, 10))
        notebook.add(tab, text="帮助")

        ttk.Label(tab, text="7z 批量压缩工具", font=("", 12, "bold")).pack(anchor=tk.W)
        ttk.Label(tab, text="v1.0").pack(anchor=tk.W, pady=(0, 8))
        ttk.Label(tab, text="基于 7-Zip 的轻量级批量文件压缩桌面工具。").pack(anchor=tk.W)
        ttk.Label(tab, text="使用 Python + tkinter 构建。").pack(anchor=tk.W)
        ttk.Separator(tab, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=12)
        ttk.Label(tab, text="快捷键", font=("", 10, "bold")).pack(anchor=tk.W)
        ttk.Label(tab, text="  Delete  移除选中文件").pack(anchor=tk.W, pady=(2, 0))
        ttk.Label(tab, text="  右键    显示文件操作菜单").pack(anchor=tk.W)

    def _refresh_presets(self):
        presets = self.settings.presets
        names = [p.name for p in presets]
        self._preset_combo["values"] = names
        if names:
            idx = min(self.settings.default_preset_index, len(names) - 1)
            self._preset_combo.current(idx)

    def _get_selected_preset(self) -> Optional[CompressPreset]:
        idx = self._preset_combo.current()
        presets = self.settings.presets
        if 0 <= idx < len(presets):
            return presets[idx]
        return None

    def _manage_presets(self):
        ManagePresetsDialog(self.root, self.settings)
        self._refresh_presets()

    def _browse_7z(self):
        p = filedialog.askopenfilename(
            title="选择 7z.exe",
            filetypes=[("可执行文件", "*.exe"), ("所有文件", "*.*")],
            parent=self.root,
        )
        if p:
            self._path_var.set(p)

    def _save_7z_path(self):
        self.settings.sevenz_path = self._path_var.get().strip()

    def _start(self):
        if self._task is not None:
            return

        files = self.file_list.get_files()
        if not files:
            messagebox.showwarning("无文件", "请先添加要压缩的文件或文件夹。", parent=self.root)
            return

        preset = self._get_selected_preset()
        if not preset:
            messagebox.showwarning("未选择预设", "请先选择一个压缩预设。", parent=self.root)
            return

        mode = self._mode.get()

        if preset.output_mode == "ask":
            path = filedialog.askdirectory(title="选择输出目录", parent=self.root)
            if not path:
                return
            d = preset.to_dict()
            d["output_mode"] = "custom"
            d["custom_output_dir"] = path
            preset = CompressPreset.from_dict(d)

        self._set_busy(True)

        pw = ProgressWindow(self.root)
        pw.set_running(True)

        def on_progress(status, pct):
            pw.after(0, pw.on_progress, status, pct)

        def on_log(message):
            pw.after(0, pw.on_log, message)

        def on_done(report):
            pw.after(0, pw.on_done, report)
            self.root.after(0, self._on_task_done)

        self._pw = pw
        self._task = CompressionTask(files, preset, mode, custom_7z_path=self.settings.sevenz_path)
        self._task.start(progress_cb=on_progress, log_cb=on_log, done_cb=on_done)

    def _on_task_done(self):
        self._task = None
        self._set_busy(False)

    def _cancel(self):
        if self._task:
            self._task.cancel()
            self._task = None
            self._set_busy(False)
            if self._pw and self._pw.winfo_exists():
                self._pw.on_cancel()

    def _set_busy(self, busy: bool):
        state = tk.DISABLED if busy else tk.NORMAL
        self._start_btn.config(state=state)
        self._cancel_btn.config(state=tk.NORMAL if busy else tk.DISABLED)
        self.file_list.set_enabled(not busy)

    def _on_closing(self):
        if self._task:
            self._task.cancel()
        self.settings.window_geometry = self.root.geometry()
        self.root.destroy()


def run_app():
    root = tk.Tk()
    settings = Settings()
    dnd_available = False
    try:
        from src.dnd import enable_dnd_for_app
        enable_dnd_for_app(root)
        dnd_available = True
    except Exception as e:
        print(f"[DnD] tkinterdnd2 not available, using file dialogs: {e}")

    root.title("7z 批量压缩工具")
    root.geometry(settings.window_geometry)

    app = MainWindow(root)
    if dnd_available:
        app.file_list.enable_drag_drop()
    else:
        app.file_list.set_drag_drop_hint(False)

    root.mainloop()
