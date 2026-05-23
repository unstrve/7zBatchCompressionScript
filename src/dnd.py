from __future__ import annotations

import os
import platform
import tkinter as tk


def enable_dnd_for_app(root: tk.Tk) -> None:
    """Load tkdnd Tcl extension on the given root window.
    Raises on failure so caller can fall back.
    """
    import tkinterdnd2.TkinterDnD as dndmod

    system = platform.system()
    if system == "Windows":
        machine = os.environ.get("PROCESSOR_ARCHITECTURE", platform.machine())
    else:
        machine = platform.machine()

    rep = _platform_rep(system, machine)
    pkg_dir = os.path.dirname(dndmod.__file__)
    module_path = os.path.join(pkg_dir, "tkdnd", rep)

    root.tk.call("lappend", "auto_path", module_path)
    version = root.tk.call("package", "require", "tkdnd")
    root.TkdndVersion = version


def _platform_rep(system: str, machine: str) -> str:
    pairs = [
        ("Darwin", "arm64", "osx-arm64"),
        ("Darwin", "x86_64", "osx-x64"),
        ("Linux", "aarch64", "linux-arm64"),
        ("Linux", "x86_64", "linux-x64"),
        ("Windows", "ARM64", "win-arm64"),
        ("Windows", "AMD64", "win-x64"),
        ("Windows", "x86", "win-x86"),
    ]
    for s, m, rep in pairs:
        if system == s and machine == m:
            return rep
    raise RuntimeError(f"Unsupported platform: {system} {machine}")
