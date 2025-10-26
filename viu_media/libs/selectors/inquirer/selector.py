from InquirerPy.prompts import FuzzyPrompt  # pyright: ignore[reportPrivateImportUsage]
from rich.prompt import Confirm, Prompt

from ..base import BaseSelector


class InquirerSelector(BaseSelector):
    def choose(self, prompt, choices, *, preview=None, header=None):
        if header:
            print(f"[bold cyan]{header}[/bold cyan]")
        return FuzzyPrompt(
            message=prompt,
            choices=choices,
            height="100%",
            border=True,
            validate=lambda result: result in choices,
        ).execute()

    def confirm(self, prompt, *, default=False):
        return Confirm.ask(prompt, default=default)

    def ask(self, prompt, *, default=None):
        return Prompt.ask(prompt=prompt, default=default or None)

    def choose_multiple(
        self, prompt: str, choices: list[str], preview: str | None = None
    ) -> list[str]:
        return FuzzyPrompt(
            message=prompt,
            choices=choices,
            height="100%",
            multiselect=True,
            border=True,
        ).execute()


if __name__ == "__main__":
    selector = InquirerSelector()
    choice = selector.ask("Hello dev :)")
    print(choice)
    choice = selector.confirm("Hello dev :)")
    print(choice)
    choice = selector.choose_multiple("What comes first", ["a", "b"])
    print(choice)
    choice = selector.choose("What comes first", ["a", "b"])
    print(choice)
