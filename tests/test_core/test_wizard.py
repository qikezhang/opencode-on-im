"""Tests for setup wizard."""

from unittest.mock import MagicMock, patch

from opencode_on_im.core.wizard import (
    prompt_with_validation,
    validate_not_empty,
    validate_proxy_url,
    validate_telegram_token,
)


class TestValidators:
    def test_validate_telegram_token(self):
        # 35 chars token part
        valid_token = "123456789:ABCdefGHIjklMNOpqrsTUVwxyz123456789"
        is_valid, msg = validate_telegram_token(valid_token)
        assert is_valid is True
        assert msg == ""

        invalid_token = "invalid"
        is_valid, msg = validate_telegram_token(invalid_token)
        assert is_valid is False
        assert "Invalid format" in msg

    def test_validate_proxy_url(self):
        valid = "socks5://user:pass@host:1080"
        is_valid, msg = validate_proxy_url(valid)
        assert is_valid is True

        invalid_scheme = "ftp://host"
        is_valid, msg = validate_proxy_url(invalid_scheme)
        assert is_valid is False
        assert "start with one of" in msg

        invalid_format = "http://user@host"  # Missing password/port structure for auth
        is_valid, msg = validate_proxy_url(invalid_format)
        assert is_valid is False
        assert "Format" in msg

    def test_validate_not_empty(self):
        is_valid, msg = validate_not_empty("value", "Field")
        assert is_valid is True

        is_valid, msg = validate_not_empty("   ", "Field")
        assert is_valid is False
        assert "cannot be empty" in msg


class TestPromptWithValidation:
    def test_prompt_success_first_try(self):
        with patch("opencode_on_im.core.wizard.Prompt.ask") as mock_ask:
            mock_ask.return_value = "valid"
            validator = MagicMock(return_value=(True, ""))

            result = prompt_with_validation("Prompt", validator)

            assert result == "valid"
            mock_ask.assert_called_once()

    def test_prompt_retry_on_invalid(self):
        with (
            patch("opencode_on_im.core.wizard.Prompt.ask") as mock_ask,
            patch("opencode_on_im.core.wizard.console.print") as mock_print,
        ):
            # First return invalid, then valid
            mock_ask.side_effect = ["invalid", "valid"]

            def validator(val):
                return (val == "valid", "Error msg")

            result = prompt_with_validation("Prompt", validator)

            assert result == "valid"
            assert mock_ask.call_count == 2
            mock_print.assert_called_with("[red]Error: Error msg[/red]")
