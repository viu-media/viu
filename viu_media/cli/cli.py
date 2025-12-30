import logging
import shutil
import sys
from typing import TYPE_CHECKING

import click
from click.core import ParameterSource

from ..core.config import AppConfig
from ..core.constants import CLI_NAME, USER_CONFIG, __version__
from .config import ConfigLoader
from .options import options_from_model
from .utils.exception import setup_exceptions_handler
from .utils.lazyloader import LazyGroup
from .utils.logging import setup_logging

if TYPE_CHECKING:
    from typing import TypedDict

    from typing_extensions import Unpack

    class Options(TypedDict):
        no_config: bool | None
        trace: bool | None
        dev: bool | None
        log: bool | None
        rich_traceback: bool | None
        rich_traceback_theme: str


logger = logging.getLogger(__name__)

commands = {
    "config": "config.config",
    "search": "search.search",
    "anilist": "anilist.anilist",
    "download": "download.download",
    "update": "update.update",
    "registry": "registry.registry",
    "worker": "worker.worker",
    "queue": "queue.queue",
    "completions": "completions.completions",
}


@click.group(
    cls=LazyGroup,
    root="viu_media.cli.commands",
    invoke_without_command=True,
    lazy_subcommands=commands,
    context_settings=dict(auto_envvar_prefix=CLI_NAME),
)
@click.version_option(__version__, "--version")
@click.option("--no-config", is_flag=True, help="Don't load the user config file.")
@click.option(
    "--trace", is_flag=True, help="Controls Whether to display tracebacks or not"
)
@click.option("--dev", is_flag=True, help="Controls Whether the app is in dev mode")
@click.option("--log", is_flag=True, help="Controls Whether to log")
@click.option(
    "--rich-traceback",
    is_flag=True,
    help="Controls Whether to display a rich traceback",
)
@click.option(
    "--rich-traceback-theme",
    default="github-dark",
    help="Controls Whether to display a rich traceback",
)
@options_from_model(AppConfig)
@click.pass_context
def cli(ctx: click.Context, **options: "Unpack[Options]"):
    """
    The main entry point for the Viu CLI.
    """
    setup_logging(options["log"])
    setup_exceptions_handler(
        options["trace"],
        options["dev"],
        options["rich_traceback"],
        options["rich_traceback_theme"],
    )

    logger.info(f"Current Command: {' '.join(sys.argv)}")
    cli_overrides = {}
    param_lookup = {p.name: p for p in ctx.command.params}

    for param_name, param_value in ctx.params.items():
        source = ctx.get_parameter_source(param_name)
        if source in (ParameterSource.ENVIRONMENT, ParameterSource.COMMANDLINE):
            parameter = param_lookup.get(param_name)

            if (
                parameter
                and hasattr(parameter, "model_name")
                and hasattr(parameter, "field_name")
            ):
                model_name = getattr(parameter, "model_name")
                field_name = getattr(parameter, "field_name")

                if model_name not in cli_overrides:
                    cli_overrides[model_name] = {}
                cli_overrides[model_name][field_name] = param_value

    loader = ConfigLoader(config_path=USER_CONFIG)
    config = (
        AppConfig.model_validate(cli_overrides)
        if options["no_config"]
        else loader.load(cli_overrides)
    )
    ctx.obj = config

    if config.general.welcome_screen:
        import time

        from ..core.constants import APP_CACHE_DIR, USER_NAME, SUPPORT_PROJECT_URL

        last_welcomed_at_file = APP_CACHE_DIR / ".last_welcome"
        should_welcome = False
        if last_welcomed_at_file.exists():
            try:
                last_welcomed_at = float(
                    last_welcomed_at_file.read_text(encoding="utf-8")
                )
                # runs once a month
                if (time.time() - last_welcomed_at) > 30 * 24 * 3600:
                    should_welcome = True

            except Exception as e:
                logger.warning(f"Failed to read welcome screen timestamp: {e}")

        else:
            should_welcome = True
        if should_welcome:
            last_welcomed_at_file.write_text(str(time.time()), encoding="utf-8")

            from rich.prompt import Confirm

            if Confirm.ask(f"""\
[green]How are you, {USER_NAME} 🙂?
If you enjoy the project and would like to support it, you can buy me a coffee at {SUPPORT_PROJECT_URL}.
Would you like to open the support page? Select yes to continue — otherwise, enjoy your terminal-anime browsing experience 😁.[/]
You can disable this message by turning off the welcome_screen option in the config. It only appears once a month.
"""):
                from webbrowser import open

                open(SUPPORT_PROJECT_URL)

    if config.general.show_new_release:
        import time

        from ..core.constants import APP_CACHE_DIR

        last_release_file = APP_CACHE_DIR / ".last_release"
        should_print_release_notes = False
        if last_release_file.exists():
            last_release = last_release_file.read_text(encoding="utf-8")
            current_version = list(map(int, __version__.replace("v", "").split(".")))
            last_saved_version = list(
                map(int, last_release.replace("v", "").split("."))
            )
            if (
                (current_version[0] > last_saved_version[0])
                or (
                    current_version[1] > last_saved_version[1]
                    and current_version[0] == last_saved_version[0]
                )
                or (
                    current_version[2] > last_saved_version[2]
                    and current_version[0] == last_saved_version[0]
                    and current_version[1] == last_saved_version[1]
                )
            ):
                should_print_release_notes = True

        else:
            should_print_release_notes = True
        if should_print_release_notes:
            last_release_file.write_text(__version__, encoding="utf-8")
            from .service.feedback import FeedbackService
            from .utils.update import check_for_updates, print_release_json, update_app
            from rich.prompt import Confirm

            feedback = FeedbackService(config)
            feedback.info("Getting release notes...")
            is_latest, release_json = check_for_updates()
            if Confirm.ask(
                "Would you also like to update your config with the latest options and config notes"
            ):
                import subprocess

                _cli_cmd_name = "viu" if not shutil.which("viu-media") else "viu-media"
                cmd = [_cli_cmd_name, "config", "--update"]
                print(f"running '{' '.join(cmd)}'...")
                subprocess.run(cmd)

            if is_latest:
                print_release_json(release_json)
            else:
                print_release_json(release_json)
                print("It seems theres another update waiting for you as well 😁")
            click.pause("Press Any Key To Proceed...")

    if config.general.check_for_updates:
        import time

        from ..core.constants import APP_CACHE_DIR

        last_updated_at_file = APP_CACHE_DIR / ".last_update"
        should_check_for_update = False
        if last_updated_at_file.exists():
            try:
                last_updated_at_time = float(
                    last_updated_at_file.read_text(encoding="utf-8")
                )
                if (
                    time.time() - last_updated_at_time
                ) > config.general.update_check_interval * 3600:
                    should_check_for_update = True

            except Exception as e:
                logger.warning(f"Failed to check for update: {e}")

        else:
            should_check_for_update = True
        if should_check_for_update:
            last_updated_at_file.write_text(str(time.time()), encoding="utf-8")
            from .service.feedback import FeedbackService
            from .utils.update import check_for_updates, print_release_json, update_app

            feedback = FeedbackService(config)
            feedback.info("Checking for updates...")
            is_latest, release_json = check_for_updates()
            if not is_latest:
                from ..libs.selectors.selector import create_selector

                selector = create_selector(config)
                if release_json and selector.confirm(
                    "Theres an update available would you like to see the release notes before deciding to update?"
                ):
                    print_release_json(release_json)
                    selector.ask("Enter to continue...")
                if selector.confirm("Would you like to update?"):
                    update_app()

    if ctx.invoked_subcommand is None:
        from .commands.anilist import cmd

        ctx.invoke(cmd.anilist)
