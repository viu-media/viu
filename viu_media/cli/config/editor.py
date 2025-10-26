import textwrap
from pathlib import Path
from typing import Any, Literal, get_args, get_origin

# TODO: should we maintain a separate dependency for InquirerPy or write our own simple prompt system?
from InquirerPy import inquirer
from InquirerPy.validator import NumberValidator
from pydantic import BaseModel
from pydantic.fields import FieldInfo
from rich import print

from ...core.config.model import AppConfig


class InteractiveConfigEditor:
    """A wizard to guide users through setting up their configuration interactively."""

    def __init__(self, current_config: AppConfig):
        self.config = current_config.model_copy(deep=True)  # Work on a copy

    def run(self) -> AppConfig:
        """Starts the interactive configuration wizard."""
        print("[bold cyan]Welcome to the Viu Interactive Configurator![/bold cyan]")
        print("Let's set up your experience. Press Ctrl+C at any time to exit.")
        print("Current values will be shown as defaults.")

        try:
            for section_name, section_model in self.config:
                if not isinstance(section_model, BaseModel):
                    continue

                if not inquirer.confirm(  # pyright: ignore[reportPrivateImportUsage]
                    message=f"Configure '{section_name.title()}' settings?",
                    default=True,
                ).execute():
                    continue

                self._prompt_for_section(section_name, section_model)

            print("\n[bold green]Configuration complete![/bold green]")
            return self.config

        except KeyboardInterrupt:
            print("\n[bold yellow]Configuration cancelled.[/bold yellow]")
            # Return original config if user cancels
            return self.config

    def _prompt_for_section(self, section_name: str, section_model: BaseModel):
        """Generates prompts for all fields in a given config section."""
        print(f"\n--- [bold magenta]{section_name.title()} Settings[/bold magenta] ---")

        for field_name, field_info in section_model.model_fields.items():
            # Skip complex multi-line fields as agreed
            if section_name == "fzf" and field_name in ["opts", "header_ascii_art"]:
                continue

            current_value = getattr(section_model, field_name)
            prompt = self._create_prompt(field_name, field_info, current_value)

            if prompt:
                new_value = prompt.execute()

                # Explicitly cast the value to the correct type before setting it.
                field_type = field_info.annotation
                if new_value is not None:
                    if field_type is Path:
                        new_value = Path(new_value).expanduser()
                    elif field_type is int:
                        new_value = int(new_value)
                    elif field_type is float:
                        new_value = float(new_value)

                setattr(section_model, field_name, new_value)

    def _create_prompt(
        self, field_name: str, field_info: FieldInfo, current_value: Any
    ):
        """Creates the appropriate InquirerPy prompt for a given Pydantic field."""
        field_type = field_info.annotation
        help_text = textwrap.fill(
            field_info.description or "No description available.", width=80
        )
        message = f"{field_name.replace('_', ' ').title()}:"

        # Boolean fields
        if field_type is bool:
            return inquirer.confirm(  # pyright: ignore[reportPrivateImportUsage]
                message=message, default=current_value, long_instruction=help_text
            )

        # Literal (Choice) fields
        if hasattr(field_type, "__origin__") and get_origin(field_type) is Literal:
            choices = list(get_args(field_type))
            return inquirer.select(  # pyright: ignore[reportPrivateImportUsage]
                message=message,
                choices=choices,
                default=current_value,
                long_instruction=help_text,
            )

        # Numeric fields
        if field_type is int:
            return inquirer.number(  # pyright: ignore[reportPrivateImportUsage]
                message=message,
                default=int(current_value),
                long_instruction=help_text,
                min_allowed=getattr(field_info, "gt", None)
                or getattr(field_info, "ge", None),
                max_allowed=getattr(field_info, "lt", None)
                or getattr(field_info, "le", None),
                validate=NumberValidator(),
            )
        if field_type is float:
            return inquirer.number(  # pyright: ignore[reportPrivateImportUsage]
                message=message,
                default=float(current_value),
                float_allowed=True,
                long_instruction=help_text,
            )

        # Path fields
        if field_type is Path:
            # Use text prompt for paths to allow '~' expansion, as FilePathPrompt can be tricky
            return inquirer.text(  # pyright: ignore[reportPrivateImportUsage]
                message=message, default=str(current_value), long_instruction=help_text
            )

        # String fields
        if field_type is str:
            # Check for 'examples' to provide choices
            if hasattr(field_info, "examples") and field_info.examples:
                return inquirer.fuzzy(  # pyright: ignore[reportPrivateImportUsage]
                    message=message,
                    choices=field_info.examples,
                    default=str(current_value),
                    long_instruction=help_text,
                )
            return inquirer.text(  # pyright: ignore[reportPrivateImportUsage]
                message=message, default=str(current_value), long_instruction=help_text
            )

        return None
