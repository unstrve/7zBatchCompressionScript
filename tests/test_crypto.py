from __future__ import annotations

from src.crypto import encrypt_password, decrypt_password


class TestCrypto:
    def test_encrypt_decrypt_round_trip(self):
        plain = "testpassword123"
        encrypted = encrypt_password(plain)
        assert encrypted != ""
        assert encrypted != plain
        decrypted = decrypt_password(encrypted)
        assert decrypted == plain

    def test_empty_string(self):
        assert encrypt_password("") == ""
        assert decrypt_password("") == ""

    def test_special_characters(self):
        plain = "p@$$w0rd! 你好 👋"
        encrypted = encrypt_password(plain)
        decrypted = decrypt_password(encrypted)
        assert decrypted == plain

    def test_long_password(self):
        plain = "a" * 100
        encrypted = encrypt_password(plain)
        decrypted = decrypt_password(encrypted)
        assert decrypted == plain

    def test_multiple_encryptions_different(self):
        plain = "samepassword"
        e1 = encrypt_password(plain)
        e2 = encrypt_password(plain)
        assert e1 != e2

    def test_decrypt_invalid_data_returns_empty(self):
        assert decrypt_password("not-valid-base64!!") == ""
        assert decrypt_password("") == ""

    def test_decrypt_corrupted_base64(self):
        encrypted = encrypt_password("test")
        corrupted = encrypted[:-5] + "AAAAA"
        result = decrypt_password(corrupted)
        assert result == "" or result != "test"
