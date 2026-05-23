from __future__ import annotations

import os
import subprocess
import threading
import time
from pathlib import Path
from typing import Any, List, Optional

from src.models import CompressPreset
from src.core.archive_service import ArchiveService
from src.core.progress_events import ProgressEventBus, PROGRESS_ERROR, PROGRESS_INDETERMINATE
from src.utils.filesystem import (
    resolve_conflict_path,
    make_output_path,
    delete_path,
    compute_total_size,
    sha256sum,
)
from src.utils.formats import format_duration, format_bytes
from src.utils.parsers import parse_7z_progress


def _mask_cmd(cmd: list) -> list:
    return [
        "-p***" if (arg.startswith("-p") and len(arg) > 2) or arg == "-p" else arg
        for arg in cmd
    ]


class CompressionService:
    def __init__(self, archiver: ArchiveService):
        self._archiver = archiver
        self.cancelled = False
        self._procs: List[subprocess.Popen] = []
        self._lock = threading.Lock()

    def cancel(self):
        with self._lock:
            self.cancelled = True
            for proc in self._procs:
                try:
                    proc.terminate()
                except Exception:
                    pass

    def run(
        self,
        sources: List[str],
        preset: CompressPreset,
        mode: str,
        custom_7z_path: str,
        bus: ProgressEventBus,
    ):
        sevenz_path = self._archiver.find_7z(custom_7z_path)
        if not sevenz_path:
            bus.emit_log("错误：未找到 7-Zip。")
            bus.emit_log("已搜索 PATH、常见安装目录以及自定义路径。")
            bus.emit_log("解决方案：")
            bus.emit_log("  1. 确保已安装 7-Zip (https://www.7-zip.org/)")
            bus.emit_log("  2. 将 7-Zip 目录添加到系统 PATH 变量")
            bus.emit_log("  3. 在设置中手动指定 7z.exe 路径")
            bus.emit_progress("", PROGRESS_ERROR)
            return

        bus.emit_log(f"7-Zip: {sevenz_path}")
        mode_text = "合并压缩" if mode == "merge" else "独立压缩"
        bus.emit_log(f"模式：{mode_text}")
        bus.emit_log(f"预设：{preset.name}")
        bus.emit_log(f"项目数：{len(sources)}")
        original_size = compute_total_size(sources)
        bus.emit_log(f"原大小：{format_bytes(original_size)}")

        overall_start = time.perf_counter()
        file_times: List[dict[str, Any]] = []
        archive_paths: List[str] = []

        if mode == "merge":
            self._run_merge(sevenz_path, sources, preset, bus,
                            archive_paths, file_times, overall_start)
        else:
            self._run_individual(sevenz_path, sources, preset, bus,
                                 archive_paths, file_times)

        if not self.cancelled:
            elapsed = time.perf_counter() - overall_start

            for ft in file_times:
                bus.emit_log(f"  {ft['name']}：{format_duration(ft['seconds'])}")

            total_compressed = 0
            for ap in archive_paths:
                try:
                    sz = Path(ap).stat().st_size
                    total_compressed += sz
                    bus.emit_log(f"  计算 SHA256... [{Path(ap).name}]")
                    h = sha256sum(ap)
                    bus.emit_log(f"  SHA256 [{Path(ap).name}]：{h}")
                except OSError:
                    pass

            if original_size > 0:
                ratio = total_compressed / original_size * 100
                saved = original_size - total_compressed
                bus.emit_log(f"压缩前：{format_bytes(original_size)}")
                bus.emit_log(f"压缩后：{format_bytes(total_compressed)}")
                bus.emit_log(f"压缩比：{ratio:.1f}%")
                bus.emit_log(f"节省空间：{format_bytes(saved)}")

            bus.emit_log(f"总用时：{format_duration(elapsed)}")
            bus.emit_progress("所有任务已完成！", 100)
            bus.emit_log("完成。")

            report = {
                "mode": mode,
                "total_seconds": elapsed,
                "files": list(file_times),
                "original_size": original_size,
                "compressed_size": total_compressed,
                "archive_paths": list(archive_paths),
            }
            bus.emit_done(report)

    def _get_source_size(self, path: str) -> int:
        p = Path(path)
        if p.is_file():
            return p.stat().st_size
        if p.is_dir():
            return compute_total_size([path])
        return 0

    def _run_individual(
        self,
        sevenz_path: str,
        sources: List[str],
        preset: CompressPreset,
        bus: ProgressEventBus,
        archive_paths: List[str],
        file_times: List[dict],
    ):
        total = len(sources)
        for i, src in enumerate(sources):
            if self.cancelled:
                return
            original_size = self._get_source_size(src)
            name = Path(src).stem if Path(src).is_file() else Path(src).name
            file_start = time.perf_counter()
            output_path = make_output_path(src, name, preset, "individual")
            output_path = resolve_conflict_path(output_path)
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            base_pct = int((i / total) * 100)
            scale = 100 / total
            bus.emit_progress(f"[{i+1}/{total}] {Path(src).name}", int(base_pct))
            bus.emit_log(f"[{i+1}/{total}] {src} -> {output_path}")
            cmd = self._archiver.build_7z_command(sevenz_path, output_path, [src], preset)
            ok = self._execute(cmd, preset, bus, sources=[src],
                               progress_offset=base_pct, progress_scale=scale)
            elapsed = time.perf_counter() - file_start
            archive_size = Path(output_path).stat().st_size if Path(output_path).exists() else 0
            file_times.append({
                "name": Path(src).name,
                "seconds": elapsed,
                "original_size": original_size,
                "archive_size": archive_size,
            })
            archive_paths.append(output_path)
            if ok and preset.verify_archive and not self.cancelled:
                self._verify(sevenz_path, output_path, preset, bus,
                             progress_offset=base_pct, progress_scale=scale)

    def _run_merge(
        self,
        sevenz_path: str,
        sources: List[str],
        preset: CompressPreset,
        bus: ProgressEventBus,
        archive_paths: List[str],
        file_times: List[dict],
        overall_start: float,
    ):
        if not sources:
            return
        output_path = make_output_path(sources[0], "archive", preset, "merge")
        output_path = resolve_conflict_path(output_path)
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        bus.emit_log(f"压缩包：{output_path}")

        common_ancestor = self._get_common_ancestor(sources)
        if common_ancestor:
            rel_sources = [os.path.relpath(s, common_ancestor) for s in sources]
            cmd = self._archiver.build_7z_command(sevenz_path, output_path, rel_sources, preset)
            ok = self._execute(cmd, preset, bus, sources=sources, cwd=common_ancestor)
        else:
            cmd = self._archiver.build_7z_command(sevenz_path, output_path, sources, preset)
            ok = self._execute(cmd, preset, bus, sources=sources)

        archive_paths.append(output_path)
        if ok and preset.verify_archive and not self.cancelled:
            self._verify(sevenz_path, output_path, preset, bus)

        elapsed = time.perf_counter() - overall_start
        file_times.append({"name": Path(output_path).name, "seconds": elapsed})

    def _get_common_ancestor(self, sources: List[str]) -> str | None:
        try:
            dirs = []
            for s in sources:
                p = Path(s)
                dirs.append(str(p.parent) if p.is_file() else str(p))
            return os.path.commonpath(dirs)
        except (ValueError, OSError):
            return None

    def _execute(
        self,
        cmd: List[str],
        preset: CompressPreset,
        bus: ProgressEventBus,
        sources: List[str],
        progress_offset: int = 0,
        progress_scale: int = 100,
        cwd: str | None = None,
    ) -> bool:
        bus.emit_log(f"  > {' '.join(_mask_cmd(cmd))}")

        def on_line(line: str):
            if self.cancelled:
                return
            pct = parse_7z_progress(line)
            if pct is not None:
                scaled = int(progress_offset + (pct * progress_scale / 100))
                bus.emit_progress(f"正在压缩... {pct}%", scaled)
            bus.emit_log(f"  {line}")

        returncode = self._archiver.run_7z(cmd, preset.password, on_line, proc_holder=self._procs, cwd=cwd)

        if returncode != 0:
            bus.emit_log(f"  7-Zip 退出代码：{returncode}")
            if returncode == 2:
                bus.emit_log("  建议：")
                bus.emit_log("    - 检查路径是否含有特殊字符")
                bus.emit_log("    - 尝试在设置中关闭「加密文件名」")
                bus.emit_log("    - 尝试将输出目录设为与源文件不同的位置")
            return False

        with self._lock:
            if self.cancelled:
                return False
            if preset.delete_after:
                for src in sources:
                    delete_path(src, bus.emit_log)
            return True

    def _verify(
        self,
        sevenz_path: str,
        archive_path: str,
        preset: CompressPreset,
        bus: ProgressEventBus,
        progress_offset: int = 0,
        progress_scale: int = 100,
    ):
        bus.emit_log(f"  验证压缩包完整性: {archive_path}")
        cmd = [sevenz_path, "t", os.path.normpath(archive_path), "-y"]

        bus.emit_progress("正在验证...", PROGRESS_INDETERMINATE)
        found_pct = False

        def on_line(line: str):
            nonlocal found_pct
            if self.cancelled:
                return
            pct = parse_7z_progress(line)
            if pct is not None:
                found_pct = True
                scaled = int(progress_offset + (pct * progress_scale / 100))
                bus.emit_progress(f"正在验证... {pct}%", scaled)
            bus.emit_log(f"  {line}")

        bus.emit_log(f"  > {' '.join(_mask_cmd(cmd))}")
        returncode = self._archiver.run_7z(cmd, preset.password, on_line, proc_holder=self._procs)
        if returncode == 0:
            bus.emit_log("  ✓ 完整性验证通过")
        else:
            bus.emit_log(f"  ✗ 完整性验证失败 (退出码 {returncode})")
