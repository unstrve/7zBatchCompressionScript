from __future__ import annotations

import tkinter as tk
from tkinter import ttk, filedialog

from src.core.progress_events import PROGRESS_ERROR, PROGRESS_INDETERMINATE
from src.utils.formats import format_bytes, format_duration


def _center_on_parent(window: tk.Toplevel, parent: tk.Misc):
    window.withdraw()
    window.update_idletasks()
    pw = parent.winfo_width()
    ph = parent.winfo_height()
    px = parent.winfo_x()
    py = parent.winfo_y()
    ww = window.winfo_width()
    wh = window.winfo_height()
    x = px + max(0, (pw - ww) // 2)
    y = py + max(0, (ph - wh) // 2)
    window.geometry(f"+{x}+{y}")
    window.deiconify()


class ProgressWindow(tk.Toplevel):
    def __init__(self, parent: tk.Misc):
        super().__init__(parent)
        self.title("压缩进度")
        self.transient(parent)
        self.resizable(True, True)
        self.minsize(500, 300)
        self.geometry("580x460")
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self._running = False
        self._build()
        _center_on_parent(self, parent)

    def _build(self):
        status_frame = ttk.Frame(self)
        status_frame.pack(fill=tk.X, padx=10, pady=(10, 2))
        self._status_label = ttk.Label(status_frame, text="准备就绪", style="Status.TLabel")
        self._status_label.pack(side=tk.LEFT)
        self._pct_label = ttk.Label(status_frame, text="", width=6, anchor=tk.E)
        self._pct_label.pack(side=tk.RIGHT)

        self._progress = ttk.Progressbar(self, mode="determinate", value=0)
        self._progress.pack(fill=tk.X, padx=10, pady=2)

        self._summary_label = ttk.Label(self, text="", style="Summary.TLabel")
        self._summary_label.pack(fill=tk.X, padx=10, pady=(0, 2))

        tree_frame = ttk.LabelFrame(self, text="文件详情")
        self._tree_frame = tree_frame
        cols = ("name", "time", "orig", "comp", "ratio")
        self._tree = ttk.Treeview(tree_frame, columns=cols, show="headings", height=5)
        self._tree.heading("name", text="文件名")
        self._tree.heading("time", text="用时")
        self._tree.heading("orig", text="原大小")
        self._tree.heading("comp", text="压缩后")
        self._tree.heading("ratio", text="压缩比")
        self._tree.column("name", width=200, minwidth=120)
        self._tree.column("time", width=70, minwidth=60, anchor=tk.CENTER)
        self._tree.column("orig", width=85, minwidth=70, anchor=tk.E)
        self._tree.column("comp", width=85, minwidth=70, anchor=tk.E)
        self._tree.column("ratio", width=70, minwidth=60, anchor=tk.CENTER)
        tv_scroll = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self._tree.yview)
        self._tree.configure(yscrollcommand=tv_scroll.set)
        self._tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        tv_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self._tree_frame.pack_forget()

        log_frame = ttk.LabelFrame(self, text="日志")
        log_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(2, 8))

        scroll = ttk.Scrollbar(log_frame)
        self._log_widget = tk.Text(
            log_frame, height=8, yscrollcommand=scroll.set,
            state=tk.DISABLED, wrap=tk.WORD,
        )
        scroll.config(command=self._log_widget.yview)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self._log_widget.pack(fill=tk.BOTH, expand=True)

        btn_frame = ttk.Frame(self)
        btn_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        ttk.Button(btn_frame, text="导出日志", command=self._export_log).pack(side=tk.LEFT, padx=2)
        self._close_btn = ttk.Button(btn_frame, text="关闭", command=self._on_close, state=tk.DISABLED)
        self._close_btn.pack(side=tk.RIGHT, padx=2)

    def set_running(self, running: bool):
        self._running = running
        self._close_btn.config(state=tk.DISABLED if running else tk.NORMAL)

    def on_progress(self, status: str, pct: int):
        if pct == PROGRESS_INDETERMINATE:
            self._progress.configure(mode="indeterminate")
            self._progress.start(10)
            self._status_label.config(text=status, style="Status.TLabel")
            self._pct_label.config(text="...")
            return
        if pct == PROGRESS_ERROR:
            self._progress.stop()
            self._progress.configure(mode="determinate")
            self._progress["value"] = 0
            self._status_label.config(text="出错", style="Status.Error.TLabel")
            self._pct_label.config(text="错误")
            self.set_running(False)
            return
        if status == "所有任务已完成！" and pct >= 100:
            self._progress.stop()
            self._progress.configure(mode="determinate")
            self._progress["value"] = 100
            self._status_label.config(text="已完成！", style="Status.Success.TLabel")
            self._pct_label.config(text="100%")
            self.set_running(False)
            return
        self._progress.stop()
        self._progress.configure(mode="determinate")
        self._status_label.config(text=status, style="Status.TLabel")
        self._progress["value"] = pct
        self._pct_label.config(text=f"{pct}%")

    def on_log(self, message: str):
        self._log_widget.config(state=tk.NORMAL)
        self._log_widget.insert(tk.END, message + "\n")
        self._log_widget.see(tk.END)
        self._log_widget.config(state=tk.DISABLED)

    def on_done(self, report: dict):
        parts = []
        total = report.get("total_seconds", 0)
        parts.append(f"总用时：{format_duration(total)}")
        orig = report.get("original_size", 0)
        comp = report.get("compressed_size", 0)
        if orig > 0:
            ratio = comp / orig * 100
            saved = orig - comp
            parts.append(f"压缩比：{ratio:.1f}%")
            parts.append(f"节省空间：{format_bytes(saved)}")
        self._summary_label.config(text="  |  ".join(parts), style="Summary.TLabel", foreground="black")

        files = report.get("files", [])
        if report.get("mode") == "individual" and len(files) > 0:
            self._populate_tree(files)

    def _populate_tree(self, files: list):
        for item in self._tree.get_children():
            self._tree.delete(item)
        for f in files:
            orig = f.get("original_size", 0)
            arch = f.get("archive_size", 0)
            t = f.get("seconds", 0)
            time_str = format_duration(t)
            orig_str = format_bytes(orig) if orig > 0 else "-"
            arch_str = format_bytes(arch) if arch > 0 else "-"
            ratio_str = f"{arch / orig * 100:.1f}%" if orig > 0 and arch > 0 else "-"
            self._tree.insert("", tk.END, values=(f["name"], time_str, orig_str, arch_str, ratio_str))
        self._tree_frame.pack(fill=tk.X, padx=10, pady=(2, 4))

    def on_cancel(self):
        self._status_label.config(text="已取消", style="Status.Warning.TLabel")
        self._pct_label.config(text="")
        self._progress.stop()
        self._progress.configure(mode="determinate")
        self.set_running(False)

    def _export_log(self):
        content = self._log_widget.get(1.0, tk.END).strip()
        if not content:
            return
        path = filedialog.asksaveasfilename(
            title="导出日志", defaultextension=".txt",
            filetypes=[("文本文件", "*.txt"), ("所有文件", "*.*")],
            parent=self,
        )
        if path:
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)

    def _on_close(self):
        if self._running:
            return
        self.destroy()

