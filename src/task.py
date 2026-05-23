from __future__ import annotations

import os
import subprocess
import threading
import time
from pathlib import Path
from typing import Any, Callable, List, Optional

from src.models import CompressPreset
from src.archiver import find_7z, build_7z_command, run_7z, _norm_path
from src.utils import (
    format_duration,
    resolve_conflict_path,
    make_output_path,
    delete_path,
    parse_7z_progress,
    compute_total_size,
    sha256sum,
    format_bytes,
)

PROGRESS_ERROR = -1
PROGRESS_INDETERMINATE = -2


class CompressionTask:
    def __init__(self, sources: List[str], preset: CompressPreset, mode: str = "individual", custom_7z_path: str = ""):
        self.sources = sources
        self.preset = preset
        self.mode = mode
        self.custom_7z_path = custom_7z_path
        self.cancelled = False
        self._thread: Optional[threading.Thread] = None
        self._file_times: List[dict[str, Any]] = []
        self._overall_start: float = 0.0
        self._procs: list[subprocess.Popen] = []
        self._archive_paths: list[str] = []

    def cancel(self):
        self.cancelled = True
        for proc in self._procs:
            try:
                proc.terminate()
            except Exception:
                pass

    def start(self, progress_cb: Callable, log_cb: Callable, done_cb: Optional[Callable] = None):
        self._thread = threading.Thread(
            target=self._run,
            args=(progress_cb, log_cb, done_cb),
            daemon=True,
        )
        self._thread.start()

    def _run(self, progress_cb: Callable[[str, int], None], log_cb: Callable[[str], None],
             done_cb: Optional[Callable] = None):
        sevenz_path = find_7z(self.custom_7z_path)
        if not sevenz_path:
            log_cb("错误：未找到 7-Zip。")
            log_cb("已搜索 PATH、常见安装目录以及自定义路径。")
            log_cb("解决方案：")
            log_cb("  1. 确保已安装 7-Zip (https://www.7-zip.org/)")
            log_cb("  2. 将 7-Zip 目录添加到系统 PATH 变量")
            log_cb("  3. 在设置中手动指定 7z.exe 路径")
            progress_cb("", PROGRESS_ERROR)
            return

        log_cb(f"7-Zip: {sevenz_path}")
        mode_text = "合并压缩" if self.mode == "merge" else "独立压缩"
        log_cb(f"模式：{mode_text}")
        log_cb(f"预设：{self.preset.name}")
        log_cb(f"项目数：{len(self.sources)}")
        original_size = compute_total_size(self.sources)
        log_cb(f"原大小：{format_bytes(original_size)}")

        self._overall_start = time.perf_counter()
        self._file_times.clear()
        self._archive_paths.clear()

        if self.mode == "merge":
            self._run_merge(sevenz_path, progress_cb, log_cb)
        else:
            self._run_individual(sevenz_path, progress_cb, log_cb)

        if not self.cancelled:
            elapsed = time.perf_counter() - self._overall_start
            report = {
                "mode": self.mode,
                "total_seconds": elapsed,
                "files": list(self._file_times),
                "original_size": original_size,
                "archive_paths": list(self._archive_paths),
            }

            for ft in self._file_times:
                log_cb(f"  {ft['name']}：{format_duration(ft['seconds'])}")

            total_compressed = 0
            for ap in self._archive_paths:
                try:
                    sz = Path(ap).stat().st_size
                    total_compressed += sz
                    h = sha256sum(ap)
                    log_cb(f"  SHA256 [{Path(ap).name}]：{h}")
                except OSError:
                    pass
            report["compressed_size"] = total_compressed

            if original_size > 0:
                ratio = total_compressed / original_size * 100
                saved = original_size - total_compressed
                log_cb(f"压缩前：{format_bytes(original_size)}")
                log_cb(f"压缩后：{format_bytes(total_compressed)}")
                log_cb(f"压缩比：{ratio:.1f}%")
                log_cb(f"节省空间：{format_bytes(saved)}")

            log_cb(f"总用时：{format_duration(elapsed)}")
            progress_cb("所有任务已完成！", 100)
            log_cb("完成。")
            if done_cb:
                done_cb(report)

    def _get_source_size(self, path: str) -> int:
        p = Path(path)
        if p.is_file():
            return p.stat().st_size
        if p.is_dir():
            return compute_total_size([path])
        return 0

    def _run_individual(self, sevenz_path, progress_cb, log_cb):
        total = len(self.sources)
        for i, src in enumerate(self.sources):
            if self.cancelled:
                return
            original_size = self._get_source_size(src)
            name = Path(src).stem if Path(src).is_file() else Path(src).name
            file_start = time.perf_counter()
            output_path = make_output_path(src, name, self.preset, self.mode)
            output_path = resolve_conflict_path(output_path)
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            base_pct = int((i / total) * 100)
            scale = 100 / total
            progress_cb(f"[{i+1}/{total}] {Path(src).name}", int(base_pct))
            log_cb(f"[{i+1}/{total}] {src} -> {output_path}")
            cmd = build_7z_command(sevenz_path, output_path, [src], self.preset)
            ok = self._execute(cmd, progress_cb, log_cb, sources=[src],
                               progress_offset=base_pct, progress_scale=scale)
            elapsed = time.perf_counter() - file_start
            archive_size = Path(output_path).stat().st_size if Path(output_path).exists() else 0
            self._file_times.append({
                "name": Path(src).name,
                "seconds": elapsed,
                "original_size": original_size,
                "archive_size": archive_size,
            })
            self._archive_paths.append(output_path)
            if ok and self.preset.verify_archive and not self.cancelled:
                self._verify(sevenz_path, output_path, progress_cb, log_cb,
                             progress_offset=base_pct, progress_scale=scale)

    def _run_merge(self, sevenz_path, progress_cb, log_cb):
        if not self.sources:
            return
        output_path = make_output_path(self.sources[0], "archive", self.preset, self.mode)
        output_path = resolve_conflict_path(output_path)
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        log_cb(f"压缩包：{output_path}")

        common_ancestor = self._get_common_ancestor()
        if common_ancestor:
            rel_sources = [os.path.relpath(s, common_ancestor) for s in self.sources]
            cmd = build_7z_command(sevenz_path, output_path, rel_sources, self.preset)
            ok = self._execute(cmd, progress_cb, log_cb, sources=self.sources,
                               cwd=common_ancestor)
        else:
            cmd = build_7z_command(sevenz_path, output_path, self.sources, self.preset)
            ok = self._execute(cmd, progress_cb, log_cb, sources=self.sources)

        self._archive_paths.append(output_path)
        if ok and self.preset.verify_archive and not self.cancelled:
            self._verify(sevenz_path, output_path, progress_cb, log_cb)
        elapsed = time.perf_counter() - self._overall_start
        self._file_times.append({"name": Path(output_path).name, "seconds": elapsed})

    def _get_common_ancestor(self) -> str | None:
        try:
            dirs = []
            for s in self.sources:
                p = Path(s)
                dirs.append(str(p.parent) if p.is_file() else str(p))
            return os.path.commonpath(dirs)
        except (ValueError, OSError):
            return None

    def _execute(self, cmd, progress_cb, log_cb, sources,
                 progress_offset=0, progress_scale=100, cwd=None) -> bool:
        log_cb(f"  > {' '.join(cmd)}")

        def on_line(line: str):
            if self.cancelled:
                return
            pct = parse_7z_progress(line)
            if pct is not None:
                scaled = int(progress_offset + (pct * progress_scale / 100))
                progress_cb(f"正在压缩... {pct}%", scaled)
            log_cb(f"  {line}")

        returncode = run_7z(cmd, on_line, proc_holder=self._procs, cwd=cwd)

        if returncode != 0:
            log_cb(f"  7-Zip 退出代码：{returncode}")
            if returncode == 2:
                log_cb("  建议：")
                log_cb("    - 检查路径是否含有特殊字符")
                log_cb("    - 尝试在设置中关闭「加密文件名」")
                log_cb("    - 尝试将输出目录设为与源文件不同的位置")
            return False

        if not self.cancelled and self.preset.delete_after:
            for src in sources:
                delete_path(src, log_cb)
        return not self.cancelled

    def _verify(self, sevenz_path, archive_path, progress_cb, log_cb,
                progress_offset=0, progress_scale=100):
        log_cb(f"  验证压缩包完整性: {archive_path}")
        cmd = [sevenz_path, "t", _norm_path(archive_path), "-y"]
        if self.preset.password:
            cmd.append("-p" + self.preset.password)

        progress_cb("正在验证...", PROGRESS_INDETERMINATE)
        found_pct = False

        def on_line(line: str):
            nonlocal found_pct
            if self.cancelled:
                return
            pct = parse_7z_progress(line)
            if pct is not None:
                found_pct = True
                scaled = int(progress_offset + (pct * progress_scale / 100))
                progress_cb(f"正在验证... {pct}%", scaled)
            log_cb(f"  {line}")

        log_cb(f"  > {' '.join(cmd)}")
        returncode = run_7z(cmd, on_line, proc_holder=self._procs)
        if returncode == 0:
            log_cb("  ✓ 完整性验证通过")
        else:
            log_cb(f"  ✗ 完整性验证失败 (退出码 {returncode})")
