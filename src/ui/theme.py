from __future__ import annotations

import tkinter as tk
from tkinter import ttk

PRIMARY = "#0078d4"
PRIMARY_HOVER = "#005a9e"
SUCCESS = "#107c10"
ERROR_COLOR = "#d32f2f"
WARNING = "#ff8c00"
BG_LIGHT = "#f5f5f5"
TROUGH = "#e0e0e0"
BORDER = "#c0c0c0"


def apply_theme(root: tk.Tk, theme_name: str = "modern"):
    style = ttk.Style(root)
    available = style.theme_names()

    if theme_name == "modern" and "clam" in available:
        style.theme_use("clam")
        _configure_modern(style)
    else:
        for t in ("vista", "xpnative", "winnative", "default"):
            if t in available:
                style.theme_use(t)
                break


def _configure_modern(style: ttk.Style):
    panedbg = style.lookup("TPanedwindow", "background") or ""

    style.configure("TNotebook", background=panedbg, borderwidth=0)
    style.configure("TNotebook.Tab", padding=[14, 5], focuscolor="")
    style.map("TNotebook.Tab",
              background=[("selected", BG_LIGHT), ("active", "#e8e8e8")],
              foreground=[("selected", PRIMARY)])

    style.configure("TLabelframe", background=panedbg)
    style.configure("TLabelframe.Label", foreground="#444444")

    style.configure("Accent.TButton", background=PRIMARY, foreground="white",
                    font=("", 10, "bold"), borderwidth=1, focusthickness=0)
    style.map("Accent.TButton",
              background=[("active", PRIMARY_HOVER), ("disabled", "#b0b0b0")],
              foreground=[("disabled", "#e0e0e0")])

    style.configure("Cancel.TButton", font=("", 9))
    style.configure("Toolbar.TButton", padding=[6, 2])

    style.configure("Title.TLabel", font=("", 10, "bold"), foreground="#333333")

    style.configure("Status.TLabel", font=("", 9))
    style.configure("Status.Success.TLabel", foreground=SUCCESS, font=("", 9, "bold"))
    style.configure("Status.Error.TLabel", foreground=ERROR_COLOR, font=("", 9, "bold"))
    style.configure("Status.Warning.TLabel", foreground=WARNING, font=("", 9))

    style.configure("Summary.TLabel", font=("", 9), foreground="#555555")

    style.configure("TProgressbar", thickness=18, troughcolor=TROUGH,
                    background=PRIMARY, pbarrelief="flat", borderwidth=0)

    style.configure("Treeview", rowheight=24, background="#fafafa",
                    fieldbackground="#fafafa", borderwidth=0)
    style.map("Treeview", background=[("selected", PRIMARY)],
              foreground=[("selected", "white")])
    style.configure("Treeview.Heading", font=("", 9, "bold"), relief="flat",
                    padding=[4, 3])
    style.map("Treeview.Heading", background=[("active", "#e8e8e8")])

    style.configure("TCombobox", padding=[4, 2])
    style.map("TCombobox", fieldbackground=[("readonly", "white")],
              background=[("readonly", BG_LIGHT)])

    style.configure("TEntry", padding=[4, 2], fieldbackground="white")
    style.configure("TSeparator", background=BORDER)
    style.configure("Vertical.TScrollbar", gripcount=0, borderwidth=0)
    style.configure("TRadiobutton", background=panedbg)
