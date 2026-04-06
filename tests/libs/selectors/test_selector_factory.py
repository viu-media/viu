from typing import Any, cast
from unittest.mock import patch

import pytest

from viu_media.core.config import AppConfig
from viu_media.libs.selectors.selector import SelectorFactory


def _config_with_selector(selector_name: str) -> AppConfig:
    config = AppConfig()
    config.general.selector = cast(Any, selector_name)
    return config


def test_selector_factory_creates_fzf_selector():
    config = _config_with_selector("fzf")

    with patch("viu_media.libs.selectors.fzf.FzfSelector", return_value="fzf-selector"):
        result = SelectorFactory.create(config)

    assert result == "fzf-selector"


def test_selector_factory_creates_rofi_selector():
    config = _config_with_selector("rofi")

    with patch(
        "viu_media.libs.selectors.rofi.RofiSelector",
        return_value="rofi-selector",
    ):
        result = SelectorFactory.create(config)

    assert result == "rofi-selector"


def test_selector_factory_creates_default_inquirer_selector():
    config = _config_with_selector("default")

    with patch(
        "viu_media.libs.selectors.inquirer.InquirerSelector",
        return_value="inquirer-selector",
    ):
        result = SelectorFactory.create(config)

    assert result == "inquirer-selector"


def test_selector_factory_raises_for_unsupported_selector():
    config = _config_with_selector("unknown")

    with pytest.raises(ValueError, match="Unsupported selector"):
        SelectorFactory.create(config)
