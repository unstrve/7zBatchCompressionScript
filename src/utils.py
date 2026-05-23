from __future__ import annotations

import hashlib
import os
import re
import shutil
from datetime import datetime
from pathlib import Path
from typing import List


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


def resolve_conflict_path(path: str) -> str:
    p = Path(path)
    if not p.exists():
        return path
    ts = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:21]
    return str(p.with_stem(f"{p.stem}_{ts}"))


def make_output_path(source: str, default_name: str, preset, mode: str) -> str:
    if preset.output_mode == "custom" and preset.custom_output_dir:
        out_dir = preset.custom_output_dir
    else:
        out_dir = os.path.dirname(source)

    stem = Path(source).stem if Path(source).is_file() else Path(source).name
    name = preset.naming_pattern.format(
        name=stem if mode == "individual" else default_name,
        suffix=preset.suffix,
    )
    return str(Path(out_dir) / f"{name}.7z")


def delete_path(path: str, log_cb):
    try:
        p = Path(path)
        if p.is_dir():
            shutil.rmtree(p)
        else:
            p.unlink()
        log_cb(f"  \u5df2\u5220\u9664\uff1a{path}")
    except Exception as e:
        log_cb(f"  \u5220\u9664\u5931\u8d25 {path}\uff1a{e}")


def compute_total_size(sources: List[str]) -> int:
    total = 0
    for s in sources:
        p = Path(s)
        if p.is_file():
            total += p.stat().st_size
        elif p.is_dir():
            for f in p.rglob("*"):
                if f.is_file():
                    total += f.stat().st_size
    return total


def sha256sum(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while True:
            chunk = f.read(65536)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def parse_7z_progress(line: str) -> int | None:
    m = re.search(r"(\d+)%\s*$", line)
    if m:
        return int(m.group(1))
    return None
