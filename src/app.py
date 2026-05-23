from __future__ import annotations

import tkinter as tk

from src.core.settings_service import SettingsService
from src.core.archive_service import ArchiveService
from src.core.compression_service import CompressionService
from src.ui.main_window import MainWindow
from src.ui.theme import apply_theme


def run_app():
    root = tk.Tk()
    settings = SettingsService()
    archiver = ArchiveService()
    compression = CompressionService(archiver)
    apply_theme(root, settings.current_theme)
    dnd_available = False
    try:
        from src.dnd import enable_dnd_for_app
        enable_dnd_for_app(root)
        dnd_available = True
    except Exception as e:
        print(f"[DnD] tkinterdnd2 not available, using file dialogs: {e}")

    root.title("7z 批量压缩工具")
    root.geometry(settings.window_geometry)

    app = MainWindow(root, settings, archiver, compression)
    if dnd_available:
        app.file_list.enable_drag_drop()
    else:
        app.file_list.set_drag_drop_hint(False)

    root.mainloop()
