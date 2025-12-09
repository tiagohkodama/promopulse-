import os

import pytest

from promopulse.core import config as config_module
from promopulse.core import security as security_module
from promopulse.core.security import EncryptionService

# Deterministic Fernet key for tests (generated once for this project).
TEST_FERNET_KEY = "elc59cqN98MZ6eoTgpD6VcqIoVclnCD8hiuBeGvJZPg="


def _reset_caches() -> None:
    """
    Clear cached settings/encryption service between tests.
    """
    config_module.get_settings.cache_clear()
    security_module.get_encryption_service.cache_clear()


def test_round_trip_encryption() -> None:
    service = EncryptionService(TEST_FERNET_KEY)

    samples = [
        "test@example.com",
        "+15551234567",
        "",
    ]

    for value in samples:
        token = service.encrypt(value)
        assert isinstance(token, str)
        assert token != value  # ciphertext must differ from plaintext

        decrypted = service.decrypt(token)
        assert decrypted == value


def test_encrypt_decrypt_none_is_none() -> None:
    service = EncryptionService(TEST_FERNET_KEY)

    assert service.encrypt(None) is None
    assert service.decrypt(None) is None


def test_get_encryption_service_missing_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("PII_ENCRYPTION_KEY", raising=False)
    _reset_caches()

    with pytest.raises(RuntimeError) as exc:
        security_module.get_encryption_service()

    assert "not configured" in str(exc.value)


def test_get_encryption_service_invalid_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("PII_ENCRYPTION_KEY", "not-a-valid-fernet-key")
    _reset_caches()

    with pytest.raises(RuntimeError) as exc:
        security_module.get_encryption_service()

    assert "invalid" in str(exc.value)


def test_get_encryption_service_valid_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("PII_ENCRYPTION_KEY", TEST_FERNET_KEY)
    _reset_caches()

    service = security_module.get_encryption_service()

    value = "user@example.com"
    token = service.encrypt(value)
    assert token != value
    assert service.decrypt(token) == value
