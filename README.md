<p align="center">
  <h1 align="center">Viu</h1>
</p>
<p align="center">
  <sup>
  Your browser anime experience, from the terminal.
  </sup>
</p>
<div align="center">

[![PyPI - Version](https://img.shields.io/pypi/v/viu-media)](https://pypi.org/project/viu-media/)
[![PyPI - Downloads](https://img.shields.io/pypi/dm/viu-media)](https://pypi.org/project/viu-media/)
[![GitHub Actions Workflow Status](https://img.shields.io/github/actions/workflow/status/viu-media/Viu/test.yml?label=Tests)](https://github.com/viu-media/Viu/actions)
[![Discord](https://img.shields.io/discord/1250887070906323096?label=Discord&logo=discord)](https://discord.gg/HBEmAwvbHV)
[![GitHub Issues](https://img.shields.io/github/issues/viu-media/Viu)](https://github.com/viu-media/Viu/issues)
[![PyPI - License](https://img.shields.io/pypi/l/viu)](https://github.com/viu-media/Viu/blob/master/LICENSE)

</div>

<p align="center">
  <a href="https://discord.gg/HBEmAwvbHV">
    <img src="https://invidget.switchblade.xyz/C4rhMA4mmK" alt="Discord Server Invite">
  </a>
</p>

[viu-showcase.webm](https://github.com/user-attachments/assets/5da0ec87-7780-4310-9ca2-33fae7cadd5f)

<details>
<summary>Rofi</summary>
  
  [viu-showcase-rofi.webm](https://github.com/user-attachments/assets/01f197d9-5ac9-45e6-a00b-8e8cd5ab459c)

</details>

> [!IMPORTANT]
> This project scrapes public-facing websites for its streaming / downloading capabilities and primarily acts as an anilist, jikan and many other media apis tui client. The developer(s) of this application have no affiliation with these content providers. This application hosts zero content and is intended for educational and personal use only. Use at your own risk.
> 
> [**Read the Full Disclaimer**](DISCLAIMER.md)

## Core Features

*   📺 **Interactive TUI:** Browse, search, and manage your AniList library in a rich terminal interface powered by `fzf`, `rofi`, or a built-in selector.
*   ⚡ **Powerful Search:** Filter the entire AniList database with over 20 different criteria, including genres, tags, year, status, and score.
*   💾 **Local Registry:** Maintain a fast, local database of your anime for offline access, detailed stats, and robust data management.
*   ⚙️ **Background Downloader:** Queue episodes for download and let a persistent background worker handle the rest.
*   📜 **Scriptable CLI:** Automate streaming and downloading with powerful, non-interactive commands perfect for scripting.
*   🔧 **Highly Customizable:** Tailor every aspect—from UI colors and providers to playback behavior—via a simple, well-documented configuration file.
*   🔌 **Extensible Architecture:** Easily add new providers, media players, and UI selectors to fit your workflow.

## Installation

Viu runs on any platform with Python 3.10+, including Windows, macOS, Linux, and Android (via Termux, see other installation methods).

### Prerequisites

For the best experience, please install these external tools:

*   **Required for Streaming:**
    *   [**mpv**](https://mpv.io/installation/) - The primary and recommended media player.
*   **Recommended for UI & Previews:**
    *   [**fzf**](https://github.com/junegunn/fzf) - For the best fuzzy-finder interface.
    *   [**chafa**](https://github.com/hpjansson/chafa) or [**kitty's icat**](https://sw.kovidgoyal.net/kitty/kittens/icat/) - For image previews in the terminal.
*   **Recommended for Downloads & Advanced Features:**
    *   [**ffmpeg**](https://www.ffmpeg.org/) - Required for downloading HLS streams and merging subtitles.
    *   [**webtorrent-cli**](https://github.com/webtorrent/webtorrent-cli) - For streaming torrents directly.

### Recommended Installation (uv)

The best way to install Viu is with [**uv**](https://github.com/astral-sh/uv), a lightning-fast Python package manager.

```bash
# Install with all optional features for the full experience
uv tool install "viu-media[standard]"

# Or, pick and choose the extras you need:
uv tool install viu-media  # Core functionality only
uv tool install "viu-media[download]"  # For advanced downloading with yt-dlp
uv tool install "viu-media[discord]"   # For Discord Rich Presence
uv tool install "viu-media[notifications]" # For desktop notifications
```

### Other Installation Methods

<details>
  <summary><b>Platform-Specific and Alternative Installers</b></summary>
  
  #### Nix / NixOS
  ##### Ephemeral / One-Off Run (No Installation)
  ```bash
  nix run github:viu-media/viu
  ```
  ##### Imperative Installation
  ```bash
  nix profile install github:viu-media/viu
  ```
  ##### Declarative Installation
  ###### in your flake.nix
  ```nix
  viu.url = "github:viu-media/viu";
  ```
  ###### in your system or home-manager packages
  ```nix
  inputs.viu.packages.${pkgs.system}.default
  ```

  #### Arch Linux (AUR)
  Use an AUR helper like `yay` or `paru`.
  ```bash
  # Stable version (recommended)
  yay -S viu-media

  # Git version (latest commit)
  yay -S viu-media-git
  ```
  #### Termux
  You may have to have rust installed see this issue: https://github.com/pydantic/pydantic-core/issues/1012#issuecomment-2511269688.
  ```bash
pkg install python # though uv will probably install python for you, but doesn't hurt to have it :)
pkg install rust # maybe required cause of pydantic


# Recommended (with pip due to more control)
pip install viu-media

# you may need to install pydantic manually
python -m pip install pydantic --extra-index-url https://termux-user-repository.github.io/pypi/ # may also be necessary incase the above fails

# add yt-dlp by
pip install yt-dlp[default,curl-cffi]

# prefer without standard and manually install the things you need lxml, yt-dlp and
pip install viu-media[standard]

# you may need to manually install lxml and plyer manually eg
python -m pip install lxml --extra-index-url https://termux-user-repository.github.io/pypi/ # may also be necessary incase the above fails

# Alternative With Uv may work, no promises
pkg install uv

uv tool install viu-media

# and to add yt-dlp only you can do
uv tool install viu-media --with yt-dlp[default,curl-cffi]

# or though may fail, cause of lxml and plyer, in that case try to install manually
uv tool install viu-media[standard]

  ```

  #### Using pipx (for isolated environments)
  ```bash
  pipx install "viu-media[standard]"
  ```
  
  #### Using pip
  ```bash
  pip install "viu-media[standard]"
  ```
</details>

<details>
  <summary><b>Building from Source</b></summary>
  
  Requires [Git](https://git-scm.com/), [Python 3.10+](https://www.python.org/), and [uv](https://astral.sh/blog/uv).
  ```bash
  git clone https://github.com/viu-media/Viu.git --depth 1
  cd Viu
  uv tool install .
  viu --version
  ```
</details>

> [!TIP]
> Enable shell completions for a much better experience by running `viu completions` and following the on-screen instructions for your shell.

## Getting Started: Quick Start

Get up and running in three simple steps:

1.  **Authenticate with AniList:**
    ```bash
    viu anilist auth
    ```
    This will open your browser. Authorize the app and paste the obtained token back into the terminal. Alternatively, you can pass the token directly as an argument, or provide a path to a text file containing the token.

2.  **Launch the Interactive TUI:**
    ```bash
    viu anilist
    ```

3.  **Browse & Play:** Use your arrow keys to navigate the menus, select an anime, and choose an episode to stream instantly.

## Usage Guide

### The Interactive TUI (`viu anilist`)

This is the main, user-friendly way to use Viu. It provides a rich terminal experience where you can:
*   Browse trending, popular, and seasonal anime.
*   Manage your personal lists (Watching, Completed, Paused, etc.).
*   Search for any anime in the AniList database.
*   View detailed information, characters, recommendations, reviews, and airing schedules.
*   Stream or download episodes directly from the menus.

### Powerful Searching (`viu anilist search`)

Filter the entire AniList database with powerful command-line flags.

```bash
# Search for anime from 2024, sorted by popularity, that is releasing and not on your list
viu anilist search -y 2024 -s POPULARITY_DESC --status RELEASING --not-on-list

# Find the most popular movies with the "Fantasy" genre
viu anilist search -g Fantasy -f MOVIE -s POPULARITY_DESC

# Dump search results as JSON instead of launching the TUI
viu anilist search -t "Demon Slayer" --dump-json
```

### Background Downloads (`viu queue` & `worker`)

Viu includes a robust background downloading system.

1.  **Add episodes to the queue:**
    ```bash
    # Add episodes 1-12 of Jujutsu Kaisen to the download queue
    viu queue add -t "Jujutsu Kaisen" -r "0:12"
    ```
2.  **Start the worker process:**
    ```bash
    # Run the worker in the foreground (press Ctrl+C to stop)
    viu worker

    # Or run it as a background process
    viu worker &
    ```The worker will now process the queue, download your episodes, and check for notifications.

### Scriptable Commands (`download` & `search`)

These commands are designed for automation and quick, non-interactive tasks.

#### `download` Examples
```bash
# Download the latest 5 episodes of One Piece
viu download -t "One Piece" -r "-5"

# Download episodes 1 to 24, merge subtitles, and clean up original files
viu download -t "Jujutsu Kaisen" -r "0:24" --merge --clean
```

#### `search` (Binging) Examples
```bash
# Start binging an anime from the first episode
viu search -t "Attack on Titan" -r ":"

# Watch the latest episode directly
viu search -t "My Hero Academia" -r "-1"
```

### Local Data Management (`viu registry`)

Viu maintains a local database of your anime for offline access and enhanced performance.

*   `registry sync`: Synchronize your local data with your remote AniList account.
*   `registry stats`: Show detailed statistics about your viewing habits.
*   `registry backup`: Create a compressed backup of your entire registry.
*   `registry restore`: Restore your data from a backup file.
*   `registry export/import`: Export/import your data to JSON/CSV for use in other applications.
*   `registry clean`: Clean up orphaned or invalid entries from your local database.

## Configuration

Viu is highly customizable. A default configuration file with detailed comments is created on the first run.

*   **Find your config file:** `viu config --path`
*   **Edit in your default editor:** `viu config`
*   **Use the interactive wizard:** `viu config --interactive`

Most settings in the config file can be temporarily overridden with command-line flags (e.g., `viu --provider animepahe anilist`).

<details>
  <summary><b>Default Configuration (`config.ini`) Explained</b></summary>

```ini
# [general] Section: Controls overall application behavior.
[general]
provider = allanime          ; The default anime provider (allanime, animepahe).
selector = fzf               ; The interactive UI tool (fzf, rofi, default).
preview = full               ; Preview type in selectors (full, text, image, none).
image_renderer = icat        ; Tool for terminal image previews (icat, chafa).
icons = True                 ; Display emoji icons in the UI.
auto_select_anime_result = True ; Automatically select the best search match.
...

# [stream] Section: Controls playback and streaming.
[stream]
player = mpv                 ; The media player to use (mpv, vlc).
quality = 1080               ; Preferred stream quality (1080, 720, 480, 360).
translation_type = sub       ; Preferred audio/subtitle type (sub, dub).
auto_next = False            ; Automatically play the next episode.
continue_from_watch_history = True ; Resume playback from where you left off.
use_ipc = True               ; Enable in-player controls via MPV's IPC.
...

# [downloads] Section: Controls the downloader.
[downloads]
downloader = auto            ; Downloader to use (auto, default, yt-dlp).
downloads_dir = ...          ; Directory to save downloaded anime.
max_concurrent_downloads = 3 ; Number of parallel downloads in the worker.
merge_subtitles = True       ; Automatically merge subtitles into the video file.
cleanup_after_merge = True   ; Delete original files after merging.
...

# [worker] Section: Controls the background worker process.
[worker]
enabled = True
notification_check_interval = 15 ; How often to check for new episodes (minutes).
download_check_interval = 5      ; How often to process the download queue (minutes).
...
```
</details>

## Advanced Features

### MPV IPC Integration

When `use_ipc = True` is set in your config, Viu provides powerful in-player controls without needing to close MPV.

**Key Bindings:**
*   `Shift+N`: Play the next episode.
*   `Shift+P`: Play the previous episode.
*   `Shift+R`: Reload the current episode.
*   `Shift+A`: Toggle auto-play for the next episode.
*   `Shift+T`: Toggle between `dub` and `sub`.

**Script Messages (For MPV Console):**
*   `script-message select-episode <number>`: Jump to a specific episode.
*   `script-message select-server <name>`: Switch to a different streaming server.

### Running as a Service (Linux/systemd)

You can run the background worker as a systemd service for persistence.

1.  Create a service file at `~/.config/systemd/user/viu-worker.service`:
    ```ini
    [Unit]
    Description=Viu Background Worker
    After=network-online.target

    [Service]
    Type=simple
    ExecStart=/path/to/your/viu worker --log
    Restart=always
    RestartSec=30

    [Install]
    WantedBy=default.target
    ```
    *Replace `/path/to/your/viu` with the output of `which viu`.*

2.  Enable and start the service:
    ```bash
    systemctl --user daemon-reload
    systemctl --user enable --now viu-worker.service
    ```
    
## Project using it
**[Inazuma](https://github.com/viu-media/Inazuma)** - official gui wrapper over viu built in kivymd

## Contributing

Contributions are welcome! Whether it's reporting a bug, proposing a feature, or writing code, your help is appreciated. Please read our [**Contributing Guidelines**](CONTRIBUTIONS.md) to get started.
