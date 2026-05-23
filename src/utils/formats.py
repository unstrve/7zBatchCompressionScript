from __future__ import annotations

from pathlib import Path


def format_size(path: str) -> str:
    try:
        p = Path(path)
        if p.is_dir():
            count = sum(1 for _ in p.rglob("*"))
            return f"({count} \u9879)"
        size = p.stat().st_size
        return format_bytes(size)
    except OSError:
        return ""


def format_bytes(size: int) -> str:
    for unit in ("B", "KB", "MB", "GB"):
        if size < 1024:
            return f"{size:.1f} {unit}" if unit != "B" else f"{size} B"
        size /= 1024
    return f"{size:.1f} TB"


def format_duration(seconds: float) -> str:
    if seconds < 60:
        return f"{seconds:.1f} \u79d2"
    minutes = int(seconds // 60)
    secs = seconds % 60
    return f"{minutes} \u5206 {secs:.0f} \u79d2"
