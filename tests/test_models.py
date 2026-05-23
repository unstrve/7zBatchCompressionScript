from __future__ import annotations

from src.models import (
    CompressPreset,
    LEVEL_NAMES,
    COMPRESS_METHODS,
    ENCRYPTION_OPTIONS,
    OUTPUT_MODES,
)


class TestCompressPreset:
    def test_default_creation(self):
        p = CompressPreset()
        assert p.name == "默认"
        assert p.level_name == "标准"
        assert p.level == 5
        assert p.password == ""
        assert p.compression_method == "LZMA2"
        assert p.encrypt_filenames is True
        assert p.encryption_method == "AES-256"

    def test_custom_preset(self):
        p = CompressPreset(
            name="自定义",
            level_name="极限",
            password="secret123",
            compression_method="PPMd",
            encrypt_filenames=False,
        )
        assert p.name == "自定义"
        assert p.level_name == "极限"
        assert p.level == 9
        assert p.password == "secret123"
        assert p.compression_method == "PPMd"
        assert p.encrypt_filenames is False

    def test_level_property(self):
        for name, expected in LEVEL_NAMES.items():
            p = CompressPreset(level_name=name)
            assert p.level == expected, f"{name} -> {p.level} != {expected}"

    def test_to_dict_round_trip(self):
        original = CompressPreset(name="测试", password="mypw", level_name="最大")
        d = original.to_dict()
        restored = CompressPreset.from_dict(d)
        assert restored.name == original.name
        assert restored.password == original.password
        assert restored.level_name == original.level_name
        assert restored.level == original.level

    def test_from_dict_ignores_unknown_keys(self):
        d = {"name": "自定义", "unknown_field": "应该被忽略"}
        p = CompressPreset.from_dict(d)
        assert p.name == "自定义"

    def test_from_dict_empty(self):
        p = CompressPreset.from_dict({})
        assert p.name == "默认"

    def test_default_classmethod(self):
        p = CompressPreset.default()
        assert isinstance(p, CompressPreset)
        assert p.name == "默认"

    def test_to_dict_contains_all_fields(self):
        p = CompressPreset()
        d = p.to_dict()
        fields = set(CompressPreset.__dataclass_fields__)
        assert fields.issubset(d.keys())

    def test_output_modes_structure(self):
        assert len(OUTPUT_MODES) == 3
        keys = [k for k, _ in OUTPUT_MODES]
        assert "source" in keys
        assert "custom" in keys
        assert "ask" in keys

    def test_encryption_options(self):
        assert "AES-128" in ENCRYPTION_OPTIONS
        assert "AES-256" in ENCRYPTION_OPTIONS

    def test_compress_methods(self):
        assert "LZMA2" in COMPRESS_METHODS
        assert "LZMA" in COMPRESS_METHODS
