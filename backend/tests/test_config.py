from config import get_settings


def test_mongodb_strict_startup_defaults_to_true(monkeypatch):
    monkeypatch.delenv("MONGODB_STRICT_STARTUP", raising=False)

    settings = get_settings()

    assert settings.mongodb_strict_startup is True
