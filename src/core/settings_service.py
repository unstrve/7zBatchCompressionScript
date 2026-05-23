from __future__ import annotations

import json
import os
from pathlib import Path
from typing import List

from src.models import CompressPreset


class SettingsService:
    def __init__(self, config_dir: str | None = None):
        if config_dir is None:
            appdata = os.environ.get("APPDATA", "")
            config_dir = os.path.join(appdata, "7zBatchCompressionScript")
        self._dir = Path(config_dir)
        self._dir.mkdir(parents=True, exist_ok=True)
        self._presets_file = self._dir / "presets.json"
        self._config_file = self._dir / "config.json"
        self._sevenz_path: str = ""
        self._default_preset_index: int = 0
        self._window_geometry: str = "800x620"
        self._current_theme: str = "modern"
        self._presets: List[CompressPreset] = []
        self._load()

    def _load(self):
        if self._config_file.exists():
            try:
                with open(self._config_file, "r", encoding="utf-8") as f:
                    cfg = json.load(f)
                self._sevenz_path = cfg.get("sevenz_path", "")
                self._default_preset_index = cfg.get("default_preset_index", 0)
                self._window_geometry = cfg.get("window_geometry", "800x620")
                self._current_theme = cfg.get("current_theme", "modern")
            except Exception:
                pass

        if self._presets_file.exists():
            try:
                with open(self._presets_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self._presets = [CompressPreset.from_dict(p) for p in data]
            except Exception:
                self._presets = [CompressPreset.default()]
        else:
            self._presets = [CompressPreset.default()]

    def _save(self):
        cfg = {
            "sevenz_path": self._sevenz_path,
            "default_preset_index": self._default_preset_index,
            "window_geometry": self._window_geometry,
            "current_theme": self._current_theme,
        }
        with open(self._config_file, "w", encoding="utf-8") as f:
            json.dump(cfg, f, indent=2)
        with open(self._presets_file, "w", encoding="utf-8") as f:
            json.dump(
                [p.to_dict() for p in self._presets],
                f,
                indent=2,
                ensure_ascii=False,
            )

    @property
    def sevenz_path(self) -> str:
        return self._sevenz_path

    @sevenz_path.setter
    def sevenz_path(self, value: str):
        self._sevenz_path = value
        self._save()

    @property
    def default_preset_index(self) -> int:
        return self._default_preset_index

    @default_preset_index.setter
    def default_preset_index(self, value: int):
        if 0 <= value < len(self._presets):
            self._default_preset_index = value
            self._save()

    @property
    def window_geometry(self) -> str:
        return self._window_geometry

    @window_geometry.setter
    def window_geometry(self, value: str):
        self._window_geometry = value
        self._save()

    @property
    def current_theme(self) -> str:
        return self._current_theme

    @current_theme.setter
    def current_theme(self, value: str):
        if value in ("modern", "default"):
            self._current_theme = value
            self._save()

    @property
    def presets(self) -> List[CompressPreset]:
        return list(self._presets)

    def add_preset(self, preset: CompressPreset):
        self._presets.append(preset)
        self._save()

    def update_preset(self, index: int, preset: CompressPreset):
        if 0 <= index < len(self._presets):
            self._presets[index] = preset
            self._save()

    def delete_preset(self, index: int):
        if 0 <= index < len(self._presets):
            self._presets.pop(index)
            if not self._presets:
                self._presets.append(CompressPreset.default())
            if self._default_preset_index >= len(self._presets):
                self._default_preset_index = 0
            self._save()
