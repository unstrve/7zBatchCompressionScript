from __future__ import annotations

from src.utils.parsers import parse_7z_progress


class TestParse7zProgress:
    def test_basic_progress(self):
        assert parse_7z_progress("42%") == 42
        assert parse_7z_progress("  100%  ") == 100
        assert parse_7z_progress("0%") == 0

    def test_progress_end_of_line(self):
        assert parse_7z_progress(" 42%") == 42
        assert parse_7z_progress("Some prefix 73%") == 73
        assert parse_7z_progress("Compressing 85%   ") == 85

    def test_no_progress(self):
        assert parse_7z_progress("") is None
        assert parse_7z_progress("Everything is Ok") is None
        assert parse_7z_progress("Enter password (will not be echoed):") is None
        assert parse_7z_progress("Scanning the drive:") is None

    def test_multiline_no_match(self):
        lines = [
            "7-Zip 26.01 (x64) : Copyright (c) 1999-2026 Igor Pavlov",
            "Creating archive: test.7z",
            "Files read from disk: 1",
            "Archive size: 186 bytes",
            "Sub items Errors: 1",
        ]
        for line in lines:
            assert parse_7z_progress(line) is None
