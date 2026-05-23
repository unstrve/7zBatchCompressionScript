from __future__ import annotations

from src.models import CompressPreset
from src.core.archive_service import ArchiveService


class TestBuild7zCommand:
    def setup_method(self):
        self.archiver = ArchiveService()
        self.preset = CompressPreset()

    def test_basic_command(self):
        cmd = self.archiver.build_7z_command(
            "7z.exe", "output.7z", ["input.txt"], self.preset
        )
        assert cmd[0] == "7z.exe"
        assert cmd[1] == "a"
        assert "-t7z" in cmd
        assert "-mx=5" in cmd
        assert "output.7z" in cmd
        assert "input.txt" in cmd

    def test_password_via_stdin(self):
        p = CompressPreset(password="secret")
        cmd = self.archiver.build_7z_command("7z.exe", "out.7z", ["f.txt"], p)
        assert "-p" in cmd
        assert "-psecret" not in cmd

    def test_encrypt_filenames(self):
        p = CompressPreset(password="secret", encrypt_filenames=True)
        cmd = self.archiver.build_7z_command("7z.exe", "out.7z", ["f.txt"], p)
        assert "-mhe=on" in cmd

    def test_encryption_method_aes128(self):
        p = CompressPreset(password="secret", encryption_method="AES-128")
        cmd = self.archiver.build_7z_command("7z.exe", "out.7z", ["f.txt"], p)
        assert "-mem=AES128" in cmd

    def test_compression_method(self):
        p = CompressPreset(compression_method="PPMd")
        cmd = self.archiver.build_7z_command("7z.exe", "out.7z", ["f.txt"], p)
        assert "-m0=PPMd" in cmd

    def test_dictionary_size(self):
        p = CompressPreset(dictionary_size="64m")
        cmd = self.archiver.build_7z_command("7z.exe", "out.7z", ["f.txt"], p)
        assert "-md=64m" in cmd

    def test_split_volumes(self):
        p = CompressPreset(split_volumes="100m")
        cmd = self.archiver.build_7z_command("7z.exe", "out.7z", ["f.txt"], p)
        assert "-v100m" in cmd

    def test_recursive(self):
        p1 = CompressPreset(recursive=True)
        p2 = CompressPreset(recursive=False)
        cmd1 = self.archiver.build_7z_command("7z.exe", "out.7z", ["dir"], p1)
        cmd2 = self.archiver.build_7z_command("7z.exe", "out.7z", ["dir"], p2)
        assert "-r" in cmd1
        assert "-r" not in cmd2

    def test_additional_args(self):
        p = CompressPreset(additional_args="-ssc -sccUTF-8")
        cmd = self.archiver.build_7z_command("7z.exe", "out.7z", ["f.txt"], p)
        assert "-ssc" in cmd
        assert "-sccUTF-8" in cmd

    def test_solid_archive_with_block_size(self):
        p = CompressPreset(solid_archive=True, solid_block_size="64m")
        cmd = self.archiver.build_7z_command("7z.exe", "out.7z", ["f.txt"], p)
        assert "-ms=64m" in cmd

    def test_solid_archive_disabled(self):
        p = CompressPreset(solid_archive=False)
        cmd = self.archiver.build_7z_command("7z.exe", "out.7z", ["f.txt"], p)
        assert "-ss-" in cmd

    def test_multiple_sources(self):
        cmd = self.archiver.build_7z_command(
            "7z.exe", "out.7z", ["a.txt", "b.txt", "c.txt"], self.preset
        )
        assert "a.txt" in cmd
        assert "b.txt" in cmd
        assert "c.txt" in cmd

    def test_num_threads(self):
        p = CompressPreset(num_threads="4")
        cmd = self.archiver.build_7z_command("7z.exe", "out.7z", ["f.txt"], p)
        assert "-mmt=4" in cmd

    def test_word_size(self):
        p = CompressPreset(word_size="128")
        cmd = self.archiver.build_7z_command("7z.exe", "out.7z", ["f.txt"], p)
        assert "-mfb=128" in cmd
