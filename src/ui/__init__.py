from __future__ import annotations

import tkinter as tk


def center_on_parent(window: tk.Toplevel, parent: tk.Misc):
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
