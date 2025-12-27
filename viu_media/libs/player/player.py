"""
Player factory and registration logic for Viu media players.

This module provides a factory for instantiating the correct player implementation based on configuration.
"""

from ...core.config import AppConfig
from .base import BasePlayer

PLAYERS = ["mpv", "vlc", "syncplay"]


class PlayerFactory:
    """
    Factory for creating player instances based on configuration.
    """

    @staticmethod
    def create(config: AppConfig) -> BasePlayer:
        """
        Create a player instance based on the configured player name.

        Args:
            config: The full application configuration object.

        Returns:
            BasePlayer: An instance of a class that inherits from BasePlayer.

        Raises:
            ValueError: If the player_name is not supported.
            NotImplementedError: If the player is recognized but not yet implemented.
        """
        player_name = config.stream.player

        if player_name not in PLAYERS:
            raise ValueError(
                f"Unsupported player: '{player_name}'. Supported players are: {PLAYERS}"
            )

        if player_name == "mpv":
            from .mpv.player import MpvPlayer

            return MpvPlayer(config.mpv)
        elif player_name == "vlc":
            from .vlc.player import VlcPlayer

            return VlcPlayer(config.vlc)
        raise NotImplementedError(
            f"Configuration logic for player '{player_name}' not implemented in factory."
        )


# Alias for convenient player creation
create_player = PlayerFactory.create
