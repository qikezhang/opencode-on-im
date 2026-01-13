import pytest


@pytest.fixture
def sample_settings():
    from opencode_on_im.core.config import Settings
    return Settings(
        data_dir="/tmp/test-data",
        telegram={"token": "test-token"},
    )
