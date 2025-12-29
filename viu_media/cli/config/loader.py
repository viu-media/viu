import logging
import tomllib
from pathlib import Path
from typing import Dict

import click
from pydantic import ValidationError

from ...core.config import AppConfig
from ...core.constants import USER_CONFIG
from ...core.exceptions import ConfigError

logger = logging.getLogger(__name__)


class ConfigLoader:
    """
    Handles loading the application configuration from a .toml file.

    It ensures a default configuration exists, reads the .toml file,
    and uses Pydantic to parse and validate the data into a type-safe
    AppConfig object.
    """

    def __init__(self, config_path: Path = USER_CONFIG):
        """
        Initializes the loader with the path to the configuration file.

        Args:
            config_path: The path to the user's config.toml file.
        """
        self.config_path = config_path

    def _handle_first_run(self) -> AppConfig:
        """Handles the configuration process when no config.toml file is found."""
        click.echo(
            "[bold yellow]Welcome to Viu![/bold yellow] No configuration file found."
        )
        from InquirerPy import inquirer

        from .editor import InteractiveConfigEditor
        from .generate import generate_config_toml_from_app_model

        choice = inquirer.select(  # type: ignore
            message="How would you like to proceed?",
            choices=[
                "Use default settings (Recommended for new users)",
                "Configure settings interactively",
            ],
            default="Use default settings (Recommended for new users)",
        ).execute()

        if "interactively" in choice:
            editor = InteractiveConfigEditor(AppConfig())
            app_config = editor.run()
        else:
            app_config = AppConfig()

        config_toml_content = generate_config_toml_from_app_model(app_config)
        try:
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            self.config_path.write_text(config_toml_content, encoding="utf-8")
            click.echo(
                f"Configuration file created at: [green]{self.config_path}[/green]"
            )
        except Exception as e:
            raise ConfigError(
                f"Could not create configuration file at {self.config_path!s}. "
                f"Please check permissions. Error: {e}",
            )

        return app_config

    def load(self, update: Dict = {}, allow_setup=True) -> AppConfig:
        """
        Loads the configuration and returns a populated, validated AppConfig object.

        Args:
            update: A dictionary of CLI overrides to apply to the loaded config.

        Returns:
            An instance of AppConfig with values from the user's .toml file.

        Raises:
            ConfigError: If the configuration file contains validation or parsing errors.
        """
        if not self.config_path.exists() and allow_setup:
            return self._handle_first_run()

        try:
            with self.config_path.open("rb") as f:
                config_dict = tomllib.load(f)
        except tomllib.TOMLDecodeError as e:
            raise ConfigError(
                f"Error parsing configuration file '{self.config_path}':\n{e}"
            )

        # Apply CLI overrides on top of the loaded configuration
        if update:
            for section, values in update.items():
                if section in config_dict:
                    config_dict[section].update(values)
                else:
                    config_dict[section] = values

        try:
            app_config = AppConfig.model_validate(config_dict)
            return app_config
        except ValidationError as e:
            error_message = (
                f"Configuration error in '{self.config_path}'!\n"
                f"Please correct the following issues:\n\n{e}"
            )
            raise ConfigError(error_message)
