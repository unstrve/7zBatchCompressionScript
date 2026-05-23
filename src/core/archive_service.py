from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path
from typing import Callable, List, Optional

from src.models import CompressPreset


class ArchiveService:
    def find_7z(self, custom_path: str = "") -> Optional[str]:
        if custom_path:
            p = Path(custom_path)
            if p.exists():
                return str(p)

        candidates = ["7z", "7za", "7z.exe", "7za.exe"]
        for name in candidates:
            exe = shutil.which(name)
            if exe:
                return exe

        path_dirs = os.environ.get("PATH", "").split(os.pathsep)
        for d in path_dirs:
            d = d.strip('"')
            if not d:
                continue
            for name in ["7z.exe", "7za.exe"]:
                p = os.path.join(d, name)
                if Path(p).exists():
                    return p

        common = [
            os.path.join(os.environ.get("ProgramW6432", "C:\\Program Files"), "7-Zip", "7z.exe"),
            os.path.join(os.environ.get("ProgramFiles(x86)", "C:\\Program Files (x86)"), "7-Zip", "7z.exe"),
            os.path.join(os.environ.get("ProgramFiles", "C:\\Program Files"), "7-Zip", "7z.exe"),
            r"C:\Program Files\7-Zip\7z.exe",
            r"C:\Program Files (x86)\7-Zip\7z.exe",
        ]
        for p in common:
            if Path(p).exists():
                return p
        return None

    def _norm_path(self, p: str) -> str:
        return os.path.normpath(p)

    def build_7z_command(
        self,
        sevenz_path: str,
        archive_path: str,
        sources: List[str],
        preset: CompressPreset,
    ) -> List[str]:
        cmd = [sevenz_path, "a"]
        cmd.append("-t7z")
        cmd.append("-mx=" + str(preset.level))

        if preset.compression_method != "LZMA2":
            cmd.append(f"-m0={preset.compression_method}")
        if preset.dictionary_size:
            cmd.append(f"-md={preset.dictionary_size}")
        if preset.word_size:
            cmd.append(f"-mfb={preset.word_size}")

        if preset.solid_archive and preset.solid_block_size:
            cmd.append(f"-ms={preset.solid_block_size}")
        elif not preset.solid_archive:
            cmd.append("-ss-")

        if preset.num_threads:
            cmd.append(f"-mmt={preset.num_threads}")

        if preset.password:
            cmd.append("-p" + preset.password)
            if preset.encrypt_filenames:
                cmd.append("-mhe=on")
            if preset.encryption_method != "AES-256":
                enc = {"AES-128": "AES128", "AES-256": "AES256"}
                method = enc.get(preset.encryption_method)
                if method:
                    cmd.append(f"-mem={method}")

        if preset.split_volumes:
            cmd.append("-v" + preset.split_volumes)

        if preset.recursive:
            cmd.append("-r")

        if preset.additional_args:
            cmd.extend(preset.additional_args.split())

        cmd.append("-y")
        cmd.append(self._norm_path(archive_path))
        for s in sources:
            cmd.append(self._norm_path(s))
        return cmd

    def run_7z(
        self,
        cmd: List[str],
        line_callback: Callable[[str], None] | None = None,
        proc_holder: list | None = None,
        cwd: str | None = None,
    ) -> int:
        cmdline = subprocess.list2cmdline(cmd)
        startup = subprocess.STARTUPINFO()
        startup.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        proc = subprocess.Popen(
            cmdline,
            cwd=cwd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            errors="replace",
            startupinfo=startup,
            creationflags=subprocess.CREATE_NO_WINDOW,
        )
        if proc_holder is not None:
            proc_holder.append(proc)
        for line in proc.stdout:
            line = line.rstrip("\n\r")
            if line_callback:
                line_callback(line)
        proc.wait()
        return proc.returncode
