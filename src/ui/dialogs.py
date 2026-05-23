from __future__ import annotations

import json
import tkinter as tk
from pathlib import Path
from tkinter import ttk, filedialog, messagebox
from typing import List, Optional

from src.models import (
    CompressPreset,
    LEVEL_NAMES,
    COMPRESS_METHODS,
    DICT_SIZES,
    WORD_SIZES,
    SOLID_BLOCK_SIZES,
    THREAD_OPTIONS,
    ENCRYPTION_OPTIONS,
    OUTPUT_MODES,
)
from src.settings import Settings


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


class PresetDialog(tk.Toplevel):
    def __init__(self, parent, preset: CompressPreset, title: str = "编辑预设"):
        super().__init__(parent)
        self.title(title)
        self.transient(parent)
        self.grab_set()
        self.resizable(False, False)
        self._preset = preset
        self.result: Optional[CompressPreset] = None
        self._build()
        self._load()
        self.wait_window()

    def _field(self, row, label, widget, hint=""):
        ttk.Label(self, text=label).grid(row=row, column=0, sticky=tk.W, padx=5, pady=2)
        widget.grid(row=row, column=1, columnspan=2, sticky=tk.EW, padx=5, pady=2)
        if hint:
            ttk.Label(self, text=hint, foreground="gray").grid(row=row, column=2, sticky=tk.W, padx=2)
        return widget

    def _check(self, row, text, var):
        ttk.Checkbutton(self, text=text, variable=var).grid(
            row=row, column=0, columnspan=3, sticky=tk.W, padx=5, pady=2
        )

    def _sep(self, row):
        ttk.Separator(self, orient=tk.HORIZONTAL).grid(
            row=row, column=0, columnspan=3, sticky=tk.EW, padx=5, pady=5
        )

    def _build(self):
        row = 0
        self._name = self._field(row, "名称：", ttk.Entry(self, width=35))
        row += 1
        self._level = self._field(row, "压缩级别：",
                                  ttk.Combobox(self, values=list(LEVEL_NAMES.keys()), state="readonly", width=32))
        row += 1; self._sep(row)
        row += 1
        self._method = self._field(row, "压缩算法：",
                                   ttk.Combobox(self, values=COMPRESS_METHODS, state="readonly", width=32))
        row += 1
        self._dict_size = self._field(row, "字典大小：",
                                      ttk.Combobox(self, values=DICT_SIZES, state="readonly", width=32), "留空=自动")
        row += 1
        self._word_size = self._field(row, "快速字节数：",
                                      ttk.Combobox(self, values=WORD_SIZES, state="readonly", width=32), "留空=自动")
        row += 1
        solid_frame = ttk.Frame(self)
        solid_frame.grid(row=row, column=0, columnspan=3, sticky=tk.W, padx=5, pady=2)
        self._solid = tk.BooleanVar(value=True)
        ttk.Checkbutton(solid_frame, text="固实压缩", variable=self._solid).pack(side=tk.LEFT)
        ttk.Label(solid_frame, text="  固实块大小：").pack(side=tk.LEFT, padx=(10, 0))
        self._solid_block = ttk.Combobox(solid_frame, values=SOLID_BLOCK_SIZES, state="readonly", width=10)
        self._solid_block.pack(side=tk.LEFT)
        ttk.Label(solid_frame, text="留空=自动", foreground="gray").pack(side=tk.LEFT, padx=2)
        row += 1
        self._threads = self._field(row, "CPU 线程：",
                                    ttk.Combobox(self, values=THREAD_OPTIONS, state="readonly", width=32), "留空=自动")
        row += 1; self._sep(row)
        row += 1
        pw_frame = ttk.Frame(self)
        pw_frame.grid(row=row, column=1, columnspan=2, sticky=tk.EW, padx=5, pady=2)
        self._password = ttk.Entry(pw_frame, width=22, show="*")
        self._password.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self._show_pw = tk.BooleanVar(value=False)
        ttk.Checkbutton(pw_frame, text="显示", variable=self._show_pw, command=self._toggle_pw).pack(side=tk.RIGHT)
        ttk.Label(self, text="密码：").grid(row=row, column=0, sticky=tk.W, padx=5, pady=2)
        row += 1
        self._encrypt_names = tk.BooleanVar(value=True)
        self._check(row, "加密文件名", self._encrypt_names)
        row += 1
        self._encrypt_method = self._field(row, "加密方法：",
                                           ttk.Combobox(self, values=ENCRYPTION_OPTIONS, state="readonly", width=32))
        row += 1; self._sep(row)
        row += 1
        self._split = self._field(row, "分卷大小：", ttk.Entry(self, width=35), "例如 100m, 1g")
        row += 1
        self._output_mode = tk.StringVar(value="source")
        ttk.Label(self, text="输出模式：").grid(row=row, column=0, sticky=tk.NW, padx=5, pady=2)
        om_frame = ttk.Frame(self)
        om_frame.grid(row=row, column=1, columnspan=2, sticky=tk.W, padx=5, pady=2)
        for key, label in OUTPUT_MODES:
            ttk.Radiobutton(om_frame, text=label, variable=self._output_mode, value=key).pack(anchor=tk.W)
        row += 1
        self._custom_dir_frame = ttk.Frame(self)
        self._custom_dir_frame.grid(row=row, column=0, columnspan=3, sticky=tk.EW, padx=5, pady=2)
        ttk.Label(self._custom_dir_frame, text="目录：").pack(side=tk.LEFT)
        self._custom_dir = ttk.Entry(self._custom_dir_frame, width=25)
        self._custom_dir.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2)
        ttk.Button(self._custom_dir_frame, text="浏览", command=self._browse_dir).pack(side=tk.RIGHT)
        row += 1
        self._pattern = self._field(row, "命名模板：", ttk.Entry(self, width=35), "{name} {suffix}")
        row += 1
        self._suffix = self._field(row, "后缀：", ttk.Entry(self, width=35))
        row += 1; self._sep(row)
        row += 1
        self._delete_after = tk.BooleanVar(value=False)
        self._check(row, "压缩后删除原始文件", self._delete_after)
        row += 1
        self._verify = tk.BooleanVar(value=False)
        self._check(row, "压缩后验证完整性", self._verify)
        row += 1
        self._recursive = tk.BooleanVar(value=True)
        self._check(row, "递归包含子文件夹", self._recursive)
        row += 1
        self._extra = self._field(row, "额外参数：", ttk.Entry(self, width=35))
        row += 1
        btn_frame = ttk.Frame(self)
        btn_frame.grid(row=row, column=0, columnspan=3, pady=10)
        ttk.Button(btn_frame, text="保存", command=self._save).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="取消", command=self.destroy).pack(side=tk.LEFT, padx=5)

        self.columnconfigure(1, weight=1)
        _center_on_parent(self, self.master)

    def _toggle_pw(self):
        self._password.config(show="" if self._show_pw.get() else "*")

    def _browse_dir(self):
        path = filedialog.askdirectory()
        if path:
            self._custom_dir.delete(0, tk.END)
            self._custom_dir.insert(0, path)

    def _load(self):
        p = self._preset
        self._name.insert(0, p.name)
        self._level.set(p.level_name)
        self._method.set(p.compression_method)
        self._dict_size.set(p.dictionary_size)
        self._word_size.set(p.word_size)
        self._solid.set(p.solid_archive)
        self._solid_block.set(p.solid_block_size)
        self._threads.set(p.num_threads)
        self._password.insert(0, p.password)
        self._encrypt_names.set(p.encrypt_filenames)
        self._encrypt_method.set(p.encryption_method)
        self._split.insert(0, p.split_volumes)
        self._output_mode.set(p.output_mode)
        self._custom_dir.insert(0, p.custom_output_dir)
        self._pattern.insert(0, p.naming_pattern)
        self._suffix.insert(0, p.suffix)
        self._delete_after.set(p.delete_after)
        self._verify.set(p.verify_archive)
        self._recursive.set(p.recursive)
        self._extra.insert(0, p.additional_args)

    def _save(self):
        self.result = CompressPreset(
            name=self._name.get().strip() or "未命名",
            level_name=self._level.get(),
            compression_method=self._method.get(),
            dictionary_size=self._dict_size.get(),
            word_size=self._word_size.get(),
            solid_archive=self._solid.get(),
            solid_block_size=self._solid_block.get(),
            num_threads=self._threads.get(),
            password=self._password.get(),
            encrypt_filenames=self._encrypt_names.get(),
            encryption_method=self._encrypt_method.get(),
            split_volumes=self._split.get().strip(),
            output_mode=self._output_mode.get(),
            custom_output_dir=self._custom_dir.get().strip(),
            naming_pattern=self._pattern.get().strip() or "{name}_{suffix}",
            suffix=self._suffix.get().strip() or "compressed",
            delete_after=self._delete_after.get(),
            verify_archive=self._verify.get(),
            recursive=self._recursive.get(),
            additional_args=self._extra.get().strip(),
        )
        self.destroy()


class SettingsDialog(tk.Toplevel):
    def __init__(self, parent, current_path: str):
        super().__init__(parent)
        self.title("设置")
        self.transient(parent)
        self.grab_set()
        self.resizable(False, False)
        self.result = current_path
        self._build(current_path)
        self.wait_window()

    def _build(self, current_path: str):
        ttk.Label(self, text="7-Zip 路径：").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        path_var = tk.StringVar(value=current_path)
        entry = ttk.Entry(self, textvariable=path_var, width=40)
        entry.grid(row=0, column=1, sticky=tk.EW, padx=5, pady=5)

        def browse():
            p = filedialog.askopenfilename(
                title="选择 7z.exe",
                filetypes=[("可执行文件", "*.exe"), ("所有文件", "*.*")],
                parent=self,
            )
            if p:
                path_var.set(p)

        ttk.Button(self, text="浏览", command=browse).grid(row=0, column=2, padx=5, pady=5)

        ttk.Label(
            self,
            text="留空则自动搜索 PATH 和常见安装目录。",
            foreground="gray",
        ).grid(row=1, column=0, columnspan=3, sticky=tk.W, padx=5)

        def save():
            self.result = path_var.get().strip()
            self.destroy()

        btn_frame = ttk.Frame(self)
        btn_frame.grid(row=2, column=0, columnspan=3, pady=10)
        ttk.Button(btn_frame, text="保存", command=save).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="取消", command=self.destroy).pack(side=tk.LEFT, padx=5)
        _center_on_parent(self, self.master)


class ManagePresetsDialog(tk.Toplevel):
    def __init__(self, parent, settings: Settings):
        super().__init__(parent)
        self.title("管理预设")
        self.transient(parent)
        self.grab_set()
        self.minsize(520, 300)
        self.geometry("560x350")
        self._settings = settings
        self._build()
        self._refresh()
        self.wait_window()

    def _build(self):
        cols = ("name", "level", "password")
        self._tree = ttk.Treeview(self, columns=cols, show="headings", height=12)
        self._tree.heading("name", text="预设名")
        self._tree.heading("level", text="级别")
        self._tree.heading("password", text="密码")
        self._tree.column("name", width=280, minwidth=160)
        self._tree.column("level", width=70, minwidth=60, anchor=tk.CENTER)
        self._tree.column("password", width=60, minwidth=50, anchor=tk.CENTER)
        self._tree.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self._ctx_menu = tk.Menu(self, tearoff=0)
        self._ctx_menu.add_command(label="✎ 编辑", command=self._edit)
        self._ctx_menu.add_command(label="★ 设为默认", command=self._set_default)
        self._ctx_menu.add_separator()
        self._ctx_menu.add_command(label="📥 导出预设", command=self._export)
        self._ctx_menu.add_separator()
        self._ctx_menu.add_command(label="✕ 删除", command=self._delete)

        self._tree.bind("<Button-3>", self._show_context_menu)
        self._tree.bind("<Double-Button-1>", lambda e: self._edit())
        self._enable_drag_drop_import()

        btn_frame = ttk.Frame(self)
        btn_frame.pack(fill=tk.X, padx=5, pady=5)

        ttk.Button(btn_frame, text="＋ 新增", command=self._add).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="📥 导入", command=self._import).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="关闭", command=self.destroy).pack(side=tk.RIGHT, padx=2)
        _center_on_parent(self, self.master)

    def _enable_drag_drop_import(self):
        try:
            import tkinterdnd2
            self._tree.drop_target_register(tkinterdnd2.DND_FILES)
            self._tree.dnd_bind("<<Drop>>", self._on_drop_import)
        except Exception:
            pass

    def _on_drop_import(self, event):
        import re
        raw = event.data
        items = re.findall(r"\{([^}]*)\}|(\S+)", raw)
        for match in items:
            p = (match[0] or match[1]).strip('"').strip()
            if p.endswith(".json"):
                self._import_file(p)

    def _show_context_menu(self, event):
        item = self._tree.identify_row(event.y)
        if item:
            self._tree.selection_set(item)
        self._ctx_menu.post(event.x_root, event.y_root)

    def _selected_idx(self) -> int | None:
        sel = self._tree.selection()
        if not sel:
            return None
        return int(sel[0])

    def _refresh(self):
        for item in self._tree.get_children():
            self._tree.delete(item)
        default = self._settings.default_preset_index
        for i, p in enumerate(self._settings.presets):
            name = f"{p.name} ★" if i == default else p.name
            level = p.level_name
            pw = "🔒" if p.password else ""
            self._tree.insert("", tk.END, iid=str(i), values=(name, level, pw))

    def _add(self):
        count = len(self._settings.presets)
        new_p = CompressPreset(name=f"预设 {count + 1}")
        dlg = PresetDialog(self, new_p, title="新建预设")
        if dlg.result:
            self._settings.add_preset(dlg.result)
            self._refresh()

    def _edit(self):
        idx = self._selected_idx()
        if idx is None:
            return
        presets = self._settings.presets
        dlg = PresetDialog(self, presets[idx], title=f"编辑：{presets[idx].name}")
        if dlg.result:
            self._settings.update_preset(idx, dlg.result)
            self._refresh()

    def _delete(self):
        idx = self._selected_idx()
        if idx is None:
            return
        presets = self._settings.presets
        if messagebox.askyesno(
            "确认删除", f"确定要删除预设「{presets[idx].name}」吗？", parent=self
        ):
            self._settings.delete_preset(idx)
            self._refresh()

    def _set_default(self):
        idx = self._selected_idx()
        if idx is None:
            return
        self._settings.default_preset_index = idx
        self._refresh()

    def _export(self):
        idx = self._selected_idx()
        if idx is None:
            messagebox.showinfo("提示", "请先选中要导出的预设。", parent=self)
            return
        preset = self._settings.presets[idx]
        path = filedialog.asksaveasfilename(
            title="导出预设",
            defaultextension=".json",
            filetypes=[("JSON 文件", "*.json"), ("所有文件", "*.*")],
            parent=self,
        )
        if path:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(preset.to_dict(), f, ensure_ascii=False, indent=2)

    def _import(self):
        paths = filedialog.askopenfilenames(
            title="导入预设",
            filetypes=[("JSON 文件", "*.json"), ("所有文件", "*.*")],
            parent=self,
        )
        for path in paths:
            self._import_file(path)

    def _import_file(self, path: str):
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            p = CompressPreset.from_dict(data)
            p.name = p.name or Path(path).stem
            self._settings.add_preset(p)
            self._refresh()
        except Exception as e:
            messagebox.showerror("导入失败", f"导入 {path} 时出错：\n{e}", parent=self)
