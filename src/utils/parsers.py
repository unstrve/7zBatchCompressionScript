from __future__ import annotations

import re


def parse_7z_progress(line: str) -> int | None:
    m = re.search(r"(\d+)%\s*$", line)
    if m:
        return int(m.group(1))
    return None
