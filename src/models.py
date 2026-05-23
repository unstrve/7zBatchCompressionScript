from __future__ import annotations

from dataclasses import dataclass, asdict


LEVEL_NAMES = {
    "存储": 0,
    "最快": 1,
    "快速": 3,
    "标准": 5,
    "最大": 7,
    "极限": 9,
}

COMPRESS_METHODS = ["LZMA2", "LZMA", "PPMd", "BZip2", "Deflate"]
DICT_SIZES = ["", "64k", "128k", "256k", "512k", "1m", "2m", "4m", "8m", "16m", "32m", "64m"]
WORD_SIZES = ["", "8", "16", "32", "64", "128", "192", "255", "273"]
SOLID_BLOCK_SIZES = ["", "4m", "8m", "16m", "32m", "64m", "128m", "256m", "512m", "1g", "2g", "4g"]
THREAD_OPTIONS = ["", "1", "2", "4", "8", "16"]
ENCRYPTION_OPTIONS = ["AES-128", "AES-256"]
OUTPUT_MODES = [
    ("source", "与源文件同目录"),
    ("custom", "自定义目录"),
    ("ask", "每次询问"),
]


@dataclass
class CompressPreset:
    name: str = "默认"
    level_name: str = "标准"
    password: str = ""
    encrypt_filenames: bool = True
    encryption_method: str = "AES-256"
    compression_method: str = "LZMA2"
    dictionary_size: str = ""
    word_size: str = ""
    solid_archive: bool = True
    solid_block_size: str = ""
    num_threads: str = ""
    split_volumes: str = ""
    output_mode: str = "source"
    custom_output_dir: str = ""
    naming_pattern: str = "{name}_{suffix}"
    suffix: str = "compressed"
    delete_after: bool = False
    verify_archive: bool = False
    recursive: bool = True
    additional_args: str = ""

    @property
    def level(self) -> int:
        return LEVEL_NAMES.get(self.level_name, 5)

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> CompressPreset:
        valid = set(cls.__dataclass_fields__)
        return cls(**{k: v for k, v in d.items() if k in valid})

    @classmethod
    def default(cls) -> CompressPreset:
        return cls()
