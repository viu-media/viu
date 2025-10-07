# Contributing to Viu

First off, thank you for considering contributing to Viu! We welcome any help, whether it's reporting a bug, proposing a feature, or writing code. This document will guide you through the process.

## How Can I Contribute?

There are many ways to contribute to the Viu project:

*   **Reporting Bugs:** If you find a bug, please create an issue in our [issue tracker](https://github.com/viu-media/Viu/issues).
*   **Suggesting Enhancements:** Have an idea for a new feature or an improvement to an existing one? We'd love to hear it.
*   **Writing Code:** Help us fix bugs or implement new features.
*   **Improving Documentation:** Enhance our README, add examples, or clarify our contribution guidelines.
*   **Adding a Provider, Player, or Selector:** Extend Viu's capabilities by integrating new tools and services.

## Contribution Workflow

We follow the standard GitHub Fork & Pull Request workflow.

1.  **Create an Issue:** Before starting work on a new feature or a significant bug fix, please [create an issue](https://github.com/viu-media/Viu/issues/new/choose) to discuss your idea. This allows us to give feedback and prevent duplicate work. For small bugs or documentation typos, you can skip this step.

2.  **Fork the Repository:** Create your own fork of the Viu repository.

3.  **Clone Your Fork:**
    ```bash
    git clone https://github.com/YOUR_USERNAME/Viu.git
    cd Viu
    ```

4.  **Create a Branch:** Create a new branch for your changes. Use a descriptive name.
    ```bash
    # For a new feature
    git checkout -b feat/my-new-feature

    # For a bug fix
    git checkout -b fix/bug-description
    ```

5.  **Make Your Changes:** Write your code, following the guidelines below.

6.  **Run Quality Checks:** Before committing, ensure your code passes all quality checks.
    ```bash
    # Format, lint, and sort imports
    uv run ruff check --fix .
    uv run ruff format .

    # Run type checking
    uv run pyright

    # Run tests
    uv run pytest
    ```

7.  **Commit Your Changes:** We follow the [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/) specification. This helps us automate releases and makes the commit history more readable.
    ```bash
    # Example commit messages
    git commit -m "feat: add support for XYZ provider"
    git commit -m "fix(anilist): correctly parse episode numbers with decimals"
    git commit -m "docs: update installation instructions in README"
    git commit -m "chore: upgrade httpx to version 0.28.1"
    ```

8.  **Push to Your Fork:**
    ```bash
    git push origin feat/my-new-feature
    ```

9.  **Submit a Pull Request:** Open a pull request from your branch to the `master` branch of the main Viu repository. Provide a clear title and description of your changes.

## Setting Up Your Development Environment

### Prerequisites
*   Git
*   Python 3.10+
*   [uv](https://github.com/astral-sh/uv) (recommended)
*   **External Tools (for full functionality):** `mpv`, `fzf`, `rofi`, `webtorrent-cli`, `ffmpeg`.

### Nix / NixOS Users
The easiest way to get a development environment with all dependencies is to use our Nix flake.
```bash
nix develop
```
This command will drop you into a shell with all the necessary tools and a Python environment ready to go.

### Standard Setup (uv + venv)

1.  **Clone your fork** (as described above).

2.  **Create and activate a virtual environment:**
    ```bash
    uv venv
    source .venv/bin/activate
    ```

3.  **Install all dependencies:** This command installs both runtime and development dependencies, including all optional extras.
    ```bash
    uv sync --all-extras --dev
    ```

4.  **Set up pre-commit hooks:** This will automatically run linters and formatters before each commit, ensuring your code meets our quality standards.
    ```bash
    pre-commit install
    ```

## Coding Guidelines

To maintain code quality and consistency, please adhere to the following guidelines.

*   **Formatting:** We use **Black** for code formatting and **isort** (via Ruff) for import sorting. The pre-commit hooks will handle this for you.
*   **Linting:** We use **Ruff** for linting. Please ensure your code has no linting errors before submitting a PR.
*   **Type Hinting:** All new code should be fully type-hinted and pass `pyright` checks. We rely on Pydantic for data validation and configuration, so leverage it where possible.
*   **Modularity and Architecture:**
    *   **Services:** Business logic is organized into services (e.g., `PlayerService`, `DownloadService`).
    *   **Factories:** Use factory patterns (`create_provider`, `create_selector`) for creating instances of different implementations.
    *   **Configuration:** All configuration is managed through Pydantic models in `viu/core/config/model.py`. When adding new config options, update the model, defaults, and descriptions.
*   **Commit Messages:** Follow the [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/) standard.
*   **Testing:** New features should be accompanied by tests. Bug fixes should ideally include a regression test.

## How to Add a New Provider

Adding a new anime provider is a great way to contribute. Here are the steps:

1.  **Create a New Provider Directory:** Inside `viu/libs/provider/anime/`, create a new directory with the provider's name (e.g., `viu/libs/provider/anime/newprovider/`).

2.  **Implement the Provider:**
    *   Create a `provider.py` file.
    *   Define a class (e.g., `NewProviderApi`) that inherits from `BaseAnimeProvider`.
    *   Implement the abstract methods: `search`, `get`, and `episode_streams`.
    *   Create `mappers.py` to convert the provider's data structures into the generic types defined in `viu/libs/provider/anime/types.py`.
    *   Create `types.py` for any provider-specific data structures you need.
    *   If the provider requires complex scraping, place extractor logic in an `extractors/` subdirectory.

3.  **Register the Provider:**
    *   Add your new provider to the `ProviderName` enum in `viu/libs/provider/anime/types.py`.
    *   Register it in the `PROVIDERS_AVAILABLE` dictionary in `viu/libs/provider/anime/provider.py`.

4.  **Add Normalization Rules (Optional):** If the provider uses different anime titles than AniList, add mappings to `viu/assets/normalizer.json`.

## How to Add a New Player

1.  **Create a New Player Directory:** Inside `viu/libs/player/`, create a directory for your player (e.g., `viu/libs/player/myplayer/`).

2.  **Implement the Player Class:**
    *   In `myplayer/player.py`, create a class (e.g., `MyPlayer`) that inherits from `BasePlayer`.
    *   Implement the required abstract methods: `play(self, params: PlayerParams)` and `play_with_ipc(self, params: PlayerParams, socket_path: str)`. The IPC method is optional but recommended for advanced features.
    *   The `play` method should handle launching the player as a subprocess and return a `PlayerResult`.

3.  **Add Configuration (if needed):**
    *   If your player has configurable options, add a new Pydantic model (e.g., `MyPlayerConfig`) in `viu/core/config/model.py`. It should inherit from `OtherConfig`.
    *   Add this new config model as a field in the main `AppConfig` model.
    *   Add default values in `defaults.py` and descriptions in `descriptions.py`.

4.  **Register the Player:**
    *   Add your player's name to the `PLAYERS` list in `viu/libs/player/player.py`.
    *   Add the logic to instantiate your player class within the `PlayerFactory.create` method.

## How to Add a New Selector

1.  **Create a New Selector Directory:** Inside `viu/libs/selectors/`, create a new directory (e.g., `viu/libs/selectors/myselector/`).

2.  **Implement the Selector Class:**
    *   In `myselector/selector.py`, create a class (e.g., `MySelector`) that inherits from `BaseSelector`.
    *   Implement the abstract methods: `choose`, `confirm`, and `ask`.
    *   Optionally, you can override `choose_multiple` and `search` for more advanced functionality.

3.  **Add Configuration (if needed):** Follow the same configuration steps as for adding a new player.

4.  **Register the Selector:**
    *   Add your selector's name to the `SELECTORS` list in `viu/libs/selectors/selector.py`.
    *   Add the instantiation logic to the `SelectorFactory.create` method.
    *   Update the `Literal` type hint for the `selector` field in `GeneralConfig` (`viu/core/config/model.py`).

## How to Add a New CLI Command or Service

Our CLI uses `click` and a `LazyGroup` class to load commands on demand.

### Adding a Top-Level Command (e.g., `viu my-command`)

1.  **Create the Command File:** Create a new Python file in `viu/cli/commands/` (e.g., `my_command.py`). This file should contain your `click.command()` function.

2.  **Register the Command:** In `viu/cli/cli.py`, add your command to the `commands` dictionary.
    ```python
    commands = {
        # ... existing commands
        "my-command": "my_command.my_command_function",
    }
    ```

### Adding a Subcommand (e.g., `viu anilist my-subcommand`)

1.  **Create the Command File:** Place your new command file inside the appropriate subdirectory, for example, `viu/cli/commands/anilist/commands/my_subcommand.py`.

2.  **Register the Subcommand:** In the parent command's entry point file (e.g., `viu/cli/commands/anilist/cmd.py`), add your subcommand to the `commands` dictionary within the `LazyGroup`.
    ```python
    @click.group(
        cls=LazyGroup,
        # ... other options
        lazy_subcommands={
            # ... existing subcommands
            "my-subcommand": "my_subcommand.my_subcommand_function",
        }
    )
    ```

### Creating a Service
If your command involves complex logic, consider creating a service in `viu/cli/service/` to keep the business logic separate from the command-line interface. This service can then be instantiated and used within your `click` command function. This follows the existing pattern for services like `DownloadService` and `PlayerService`.

---
Thank you for contributing to Viu
