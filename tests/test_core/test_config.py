from opencode_on_im.core.config import Settings


def test_settings_defaults():
    settings = Settings()
    assert settings.opencode_port == 4096
    assert settings.web_terminal == "ttyd"
    assert settings.message_image_threshold == 10


def test_settings_from_env(monkeypatch):
    monkeypatch.setenv("TELEGRAM_TOKEN", "test-token-123")
    settings = Settings()
    assert settings.telegram.token == "test-token-123"
