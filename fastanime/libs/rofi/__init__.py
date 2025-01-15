import subprocess
from shutil import which
from sys import exit

from fastanime import APP_NAME

from ...constants import ICON_PATH


class RofiApi:
    ROFI_EXECUTABLE = which("rofi")

    rofi_theme = ""
    rofi_theme_preview = ""
    rofi_theme_confirm = ""
    rofi_theme_input = ""

    def run_with_icons(self, options: list[str], prompt_text: str) -> str:
        rofi_input = "\n".join(options)

        if not self.ROFI_EXECUTABLE:
            raise Exception("Rofi not found")

        args = [self.ROFI_EXECUTABLE]
        if self.rofi_theme_preview:
            args.extend(["-no-config", "-theme", self.rofi_theme_preview])
        args.extend(["-p", f"{prompt_text.title()}", "-i", "-show-icons", "-dmenu"])
        result = subprocess.run(
            args,
            input=rofi_input,
            stdout=subprocess.PIPE,
            text=True,
        )

        choice = result.stdout.strip()
        if not choice:
            try:
                from plyer import notification
            except ImportError:
                print(
                    "Plyer is not installed; install it for desktop notifications to be enabled"
                )
                exit(1)
            notification.notify(
                app_name=APP_NAME,
                app_icon=ICON_PATH,
                message="FastAnime is shutting down",
                title="No Valid Input Provided",
            )  # pyright:ignore
            exit(1)

        return choice

    def run(self, options: list[str], prompt_text: str, preselect: int = 0) -> str:
        rofi_input = "\n".join(options)

        if not self.ROFI_EXECUTABLE:
            raise Exception("Rofi not found")

        args = [self.ROFI_EXECUTABLE]
        if self.rofi_theme:
            args.extend(["-no-config", "-theme", self.rofi_theme])
        if preselect:
            args.extend(["-selected-row", str(preselect)])
        args.extend(["-p", prompt_text, "-i", "-dmenu"])
        result = subprocess.run(
            args,
            input=rofi_input,
            stdout=subprocess.PIPE,
            text=True,
        )

        choice = result.stdout.strip()
        if not choice or choice not in options:
            try:
                from plyer import notification
            except ImportError:
                print(
                    "Plyer is not installed; install it for desktop notifications to be enabled"
                )
                exit(1)
            notification.notify(
                app_name=APP_NAME,
                app_icon=ICON_PATH,
                message="FastAnime is shutting down",
                title="No Valid Input Provided",
            )  # pyright:ignore
            exit(1)

        return choice

    def confirm(self, prompt_text: str) -> bool:
        rofi_choices = "Yes\nNo"
        if not self.ROFI_EXECUTABLE:
            raise Exception("Rofi not found")
        args = [self.ROFI_EXECUTABLE]
        if self.rofi_theme_confirm:
            args.extend(["-no-config", "-theme", self.rofi_theme_confirm])
        args.extend(["-p", prompt_text, "-i", "", "-no-fixed-num-lines", "-dmenu"])
        result = subprocess.run(
            args,
            input=rofi_choices,
            stdout=subprocess.PIPE,
            text=True,
        )

        choice = result.stdout.strip()
        if not choice:
            try:
                from plyer import notification
            except ImportError:
                print(
                    "Plyer is not installed; install it for desktop notifications to be enabled"
                )
                exit(1)
            notification.notify(
                app_name=APP_NAME,
                app_icon=ICON_PATH,
                message="FastAnime is shutting down",
                title="No Valid Input Provided",
            )  # pyright:ignore
            exit(1)
        if choice == "Yes":
            return True
        else:
            return False

    def ask(
        self, prompt_text: str, is_int: bool = False, is_float: bool = False
    ) -> str | float | int:
        if not self.ROFI_EXECUTABLE:
            raise Exception("Rofi not found")
        args = [self.ROFI_EXECUTABLE]
        if self.rofi_theme_input:
            args.extend(["-no-config", "-theme", self.rofi_theme_input])
        args.extend(["-p", prompt_text, "-i", "-no-fixed-num-lines", "-dmenu"])
        result = subprocess.run(
            args,
            stdout=subprocess.PIPE,
            text=True,
        )

        user_input = result.stdout.strip()
        if not user_input:
            try:
                from plyer import notification
            except ImportError:
                print(
                    "Plyer is not installed; install it for desktop notifications to be enabled"
                )
                exit(1)
            notification.notify(
                app_name=APP_NAME,
                app_icon=ICON_PATH,
                message="FastAnime is shutting down",
                title="No Valid Input Provided",
            )  # pyright:ignore
            exit(1)
        if is_float:
            user_input = float(user_input)
        elif is_int:
            user_input = int(user_input)

        return user_input


Rofi = RofiApi()
