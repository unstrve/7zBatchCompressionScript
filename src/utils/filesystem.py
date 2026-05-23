from __future__ import annotations

import hashlib
import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import Callable, List


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


def delete_path(path: str, log_cb: Callable):
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
