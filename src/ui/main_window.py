from __future__ import annotations

import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from typing import Optional

from src.models import CompressPreset
from src.core.settings_service import SettingsService
from src.core.archive_service import ArchiveService
from src.core.compression_service import CompressionService
from src.core.progress_events import ProgressEventBus
from src.ui.theme import apply_theme
from src.ui.widgets import FileListFrame
from src.ui.dialogs import ManagePresetsDialog
from src.ui.progress_window import ProgressWindow


class MainWindow:
    def __init__(self, root: tk.Tk, settings: SettingsService,
                 archiver: ArchiveService, compression: CompressionService):
        self.root = root
        self.settings = settings
        self._archiver = archiver
        self._compression = compression
        self._task: Optional[threading.Thread] = None
        self._pw: Optional[ProgressWindow] = None
        self._build_ui()
        self._refresh_presets()

    def _build_ui(self):
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill=tk.BOTH, expand=True, padx=4, pady=(4, 0))
        self._build_file_tab(notebook)
        self._build_tool_tab(notebook)
        self._build_help_tab(notebook)

        self._statusbar = ttk.Label(self.root, text="就绪", relief=tk.SUNKEN, anchor=tk.W, padding=(6, 2))
        self._statusbar.pack(fill=tk.X, padx=4, pady=(2, 4))

    def _build_file_tab(self, notebook):
        tab = ttk.Frame(notebook)
        notebook.add(tab, text="文件")

        opt_frame = ttk.LabelFrame(tab, text="压缩选项")
        opt_frame.pack(fill=tk.X)

        row = ttk.Frame(opt_frame)
        row.pack(fill=tk.X, padx=8, pady=6)
        ttk.Label(row, text="预设：").pack(side=tk.LEFT)
        self._preset_combo = ttk.Combobox(row, state="readonly", width=25)
        self._preset_combo.pack(side=tk.LEFT, padx=6)
        self._preset_combo.bind("<<ComboboxSelected>>", lambda e: self._update_statusbar())

        ttk.Separator(row, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=10)

        self._mode = tk.StringVar(value="individual")
        self._mode.trace_add("write", lambda *_: self._update_statusbar())
        ttk.Label(row, text="模式：").pack(side=tk.LEFT)
        ttk.Radiobutton(row, text="独立", variable=self._mode, value="individual").pack(side=tk.LEFT, padx=3)
        ttk.Radiobutton(row, text="合并", variable=self._mode, value="merge").pack(side=tk.LEFT, padx=3)

        action_frame = ttk.Frame(tab)
        action_frame.pack(fill=tk.X, pady=(6, 0))
        self._start_btn = ttk.Button(action_frame, text="开始压缩", style="Accent.TButton", command=self._start)
        self._start_btn.pack(side=tk.LEFT, padx=3)
        self._cancel_btn = ttk.Button(action_frame, text="取消", command=self._cancel, state=tk.DISABLED)
        self._cancel_btn.pack(side=tk.LEFT, padx=3)

        self.file_list = FileListFrame(tab)
        self.file_list.pack(fill=tk.BOTH, expand=True, pady=(6, 0))

    def _build_tool_tab(self, notebook):
        tab = ttk.Frame(notebook)
        notebook.add(tab, text="工具")

        ttk.Label(tab, text="7-Zip 路径", style="Title.TLabel").pack(anchor=tk.W, pady=(12, 0))
        path_frame = ttk.Frame(tab)
        path_frame.pack(fill=tk.X, pady=(6, 4))
        self._path_var = tk.StringVar(value=self.settings.sevenz_path)
        ttk.Entry(path_frame, textvariable=self._path_var, width=50).pack(side=tk.LEFT)
        ttk.Button(path_frame, text="浏览", command=self._browse_7z).pack(side=tk.LEFT, padx=4)
        ttk.Button(path_frame, text="保存", command=self._save_7z_path).pack(side=tk.LEFT)
        ttk.Label(tab, text="留空则自动搜索 PATH 和常见安装目录。", foreground="gray").pack(anchor=tk.W)

        ttk.Separator(tab, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=16)
        ttk.Label(tab, text="预设管理", style="Title.TLabel").pack(anchor=tk.W)
        ttk.Button(tab, text="打开预设管理器...", command=self._manage_presets).pack(anchor=tk.W, pady=(6, 0))

        ttk.Separator(tab, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=16)
        ttk.Label(tab, text="主题", style="Title.TLabel").pack(anchor=tk.W)
        theme_row = ttk.Frame(tab)
        theme_row.pack(fill=tk.X, pady=(6, 0))
        ttk.Label(theme_row, text="界面风格：").pack(side=tk.LEFT)
        self._theme_combo = ttk.Combobox(theme_row, state="readonly", width=16,
                                         values=["现代风格", "默认风格"])
        self._theme_combo.pack(side=tk.LEFT, padx=4)
        self._theme_combo.bind("<<ComboboxSelected>>", self._on_theme_change)

    def _build_help_tab(self, notebook):
        tab = ttk.Frame(notebook)
        notebook.add(tab, text="帮助")

        ttk.Label(tab, text="7z 批量压缩工具", font=("", 13, "bold")).pack(anchor=tk.W, pady=(12, 0))
        ttk.Label(tab, text="v1.0", foreground="gray").pack(anchor=tk.W, pady=(2, 12))
        ttk.Label(tab, text="基于 7-Zip 的轻量级批量文件压缩桌面工具。").pack(anchor=tk.W)
        ttk.Label(tab, text="使用 Python + tkinter 构建。").pack(anchor=tk.W)
        ttk.Separator(tab, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=16)
        ttk.Label(tab, text="快捷键", style="Title.TLabel").pack(anchor=tk.W)
        ttk.Label(tab, text="  Delete  移除选中文件").pack(anchor=tk.W, pady=(4, 0))
        ttk.Label(tab, text="  右键    显示文件操作菜单").pack(anchor=tk.W)

    def _refresh_presets(self):
        presets = self.settings.presets
        names = [p.name for p in presets]
        self._preset_combo["values"] = names
        if names:
            idx = min(self.settings.default_preset_index, len(names) - 1)
            self._preset_combo.current(idx)
        theme_idx = 0 if self.settings.current_theme == "modern" else 1
        self._theme_combo.current(theme_idx)
        self._update_statusbar()

    def _on_theme_change(self, event=None):
        name = ["modern", "default"][self._theme_combo.current()]
        self.settings.current_theme = name
        apply_theme(self.root, name)

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

        bus = ProgressEventBus()
        bus.on_progress(lambda s, p: pw.after(0, pw.on_progress, s, p))
        bus.on_log(lambda m: pw.after(0, pw.on_log, m))
        bus.on_done(lambda r: pw.after(0, pw.on_done, r))

        self._pw = pw
        self._bus = bus
        sources = list(files)
        custom_path = self.settings.sevenz_path

        def _run():
            self._compression.run(sources, preset, mode, custom_path, bus)
            self.root.after(0, self._on_task_done)

        self._task = threading.Thread(target=_run, daemon=True)
        self._task.start()

    def _on_task_done(self):
        self._task = None
        self._set_busy(False)
        self._update_statusbar("已完成")

    def _update_statusbar(self, msg: str = ""):
        files = self.file_list.get_files()
        count = len(files)
        mode = "独立" if self._mode.get() == "individual" else "合并"
        preset = self._get_selected_preset()
        preset_name = preset.name if preset else "无"
        status = msg or "就绪"
        self._statusbar.config(text=f"{status}  |  共 {count} 项  |  {mode}  |  {preset_name}")

    def _cancel(self):
        if self._task:
            self._compression.cancel()
            self._task = None
            self._set_busy(False)
            if self._pw and self._pw.winfo_exists():
                self._pw.on_cancel()

    def _set_busy(self, busy: bool):
        state = tk.DISABLED if busy else tk.NORMAL
        self._start_btn.config(state=state)
        self._cancel_btn.config(state=tk.NORMAL if busy else tk.DISABLED)
        self.file_list.set_enabled(not busy)
        self._update_statusbar("正在压缩..." if busy else "就绪")

    def _on_closing(self):
        if self._task:
            self._compression.cancel()
        self.settings.window_geometry = self.root.geometry()
        self.root.destroy()



