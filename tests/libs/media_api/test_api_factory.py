from types import SimpleNamespace
from unittest.mock import patch

import pytest

from viu_media.core.config import AppConfig
from viu_media.libs.media_api import api as api_module
from viu_media.libs.media_api.api import create_api_client


class FakeClient:
    def __init__(self, scoped_config, http_client):
        self.scoped_config = scoped_config
        self.http_client = http_client


def test_create_api_client_unsupported_client_raises_value_error():
    config = AppConfig()

    with pytest.raises(ValueError, match="Unsupported API client"):
        create_api_client("unknown", config)


def test_create_api_client_returns_instance_with_scoped_config(monkeypatch):
    config = AppConfig()
    monkeypatch.setattr(
        api_module,
        "API_CLIENTS",
        {"dummy": ("dummy.module.FakeClient", "anilist")},
    )

    fake_module = SimpleNamespace(FakeClient=FakeClient)

    monkeypatch.setattr(api_module.importlib, "import_module", lambda _name: fake_module)
    monkeypatch.setattr(api_module, "random_user_agent", lambda: "test-agent")

    client = create_api_client("dummy", config)

    assert isinstance(client, FakeClient)
    assert client.scoped_config == config.anilist
    assert client.http_client.headers["User-Agent"] == "test-agent"
    client.http_client.close()


def test_create_api_client_import_failure_raises_import_error(monkeypatch):
    config = AppConfig()
    monkeypatch.setattr(
        api_module,
        "API_CLIENTS",
        {"dummy": ("dummy.module.FakeClient", "anilist")},
    )

    with patch(
        "viu_media.libs.media_api.api.importlib.import_module",
        side_effect=ImportError("boom"),
    ):
        with pytest.raises(ImportError, match="Could not load API client 'dummy'"):
            create_api_client("dummy", config)
