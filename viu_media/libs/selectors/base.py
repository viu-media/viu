from abc import ABC, abstractmethod
from typing import List, Optional


class BaseSelector(ABC):
    """
    Abstract Base Class for user-facing selectors (FZF, Rofi, etc.).
    Defines the common interface for all selection operations.
    """

    @abstractmethod
    def choose(
        self,
        prompt: str,
        choices: List[str],
        *,
        preview: Optional[str] = None,
        header: Optional[str] = None,
    ) -> str | None:
        """
        Prompts the user to choose one item from a list.

        Args:
            prompt: The message to display to the user.
            choices: A list of strings for the user to choose from.
            preview: An optional command or string for a preview window.
            header: An optional header to display above the choices.

        Returns:
            The string of the chosen item.
        """
        pass

    @abstractmethod
    def choose_multiple(
        self,
        prompt: str,
        choices: List[str],
        preview: Optional[str] = None,
    ) -> List[str]:
        """
        Prompts the user to choose multiple items from a list.
        Default implementation falls back to single selection.

        Args:
            prompt: The message to display to the user.
            choices: A list of strings for the user to choose from.
            preview: An optional command or string for a preview window.
            header: An optional header to display above the choices.

        Returns:
            A list of the chosen items.
        """
        pass

    @abstractmethod
    def confirm(self, prompt: str, *, default: bool = False) -> bool:
        """
        Asks the user a yes/no question.

        Args:
            prompt: The question to ask the user.
            default: The default return value if the user just presses Enter.

        Returns:
            True for 'yes', False for 'no'.
        """
        pass

    @abstractmethod
    def ask(self, prompt: str, *, default: Optional[str] = None) -> str | None:
        """
        Asks the user for free-form text input.

        Args:
            prompt: The question to ask the user.
            default: An optional default value.

        Returns:
            The string entered by the user.
        """
        pass

    def search(
        self,
        prompt: str,
        search_command: str,
        *,
        preview: Optional[str] = None,
        header: Optional[str] = None,
        initial_query: Optional[str] = None,
        initial_results: Optional[List[str]] = None,
    ) -> str | None:
        """
        Provides dynamic search functionality that reloads results based on user input.

        Args:
            prompt: The message to display to the user.
            search_command: The command to execute for searching/reloading results.
            preview: An optional command or string for a preview window.
            header: An optional header to display above the choices.
            initial_query: An optional initial query to pre-populate the search.
            initial_results: Optional list of results to display initially (avoids network request).

        Returns:
            The string of the chosen item.

        Raises:
            NotImplementedError: If the selector doesn't support dynamic search.
        """
        raise NotImplementedError("Dynamic search is not supported by this selector")
