"""
IINA player integration for Viu.

This module provides the IinaPlayer class, which implements the BasePlayer interface for the IINA media player.
"""

import logging
from pathlib import Path

from ....core.config import IinaConfig
from ..base import BasePlayer
from ..params import PlayerParams

logger = logging.getLogger(__name__)

IINA_APP_EXECUTABLES = (
    Path("/Applications/IINA.app/Contents/MacOS/iina-cli"),
    Path("/Applications/IINA.app/Contents/MacOS/IINA"),
)


class IinaPlayer(BasePlayer):
    def __init__(self, config: IinaConfig):
        pass

    def play(self, params: PlayerParams):
        pass
