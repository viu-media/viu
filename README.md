<p align="center">
  <h1 align="center">FastAnime</h1>
</p>
<p align="center">
  <sup>
  Browse anime from the terminal
  </sup>
</p>
<div align="center">
  
![PyPI - Downloads](https://img.shields.io/pypi/dm/fastanime) ![GitHub Actions Workflow Status](https://img.shields.io/github/actions/workflow/status/FastAnime/FastAnime/test.yml?label=Tests)
![Discord](https://img.shields.io/discord/1250887070906323096?label=Discord)
![GitHub Issues or Pull Requests](https://img.shields.io/github/issues/FastAnime/FastAnime)
![GitHub deployments](https://img.shields.io/github/deployments/FastAnime/fastanime/pypi?label=PyPi%20Publish)
![PyPI - License](https://img.shields.io/pypi/l/fastanime)
![Static Badge](https://img.shields.io/badge/lines%20of%20code-13k%2B-green)
</div>

<p align="center">
<a href="https://discord.gg/HBEmAwvbHV">
<img src="https://invidget.switchblade.xyz/C4rhMA4mmK">
</a>
</p>

![fastanime](https://github.com/user-attachments/assets/9ab09f26-e4a8-4b70-a315-7def998cec63)

<details>
  <summary>
    <b>How it looks</b>
  </summary>

**Anilist results menu:**
![image](https://github.com/user-attachments/assets/240023a7-7e4e-47dd-80ff-017d65081ee1)

**Episodes menu preview:**
![image](https://github.com/user-attachments/assets/580f86ef-326f-4ab3-9bd8-c1cb312fbfa6)

**Without preview images enabled:**
![image](https://github.com/user-attachments/assets/e1248a85-438f-4758-ae34-b0e0b224addd)

**Desktop notifications + episodes menu without image preview:**
![image](https://github.com/user-attachments/assets/b7802ef1-ca0d-45f5-a13a-e39c96a5d499)

</details>


## Installation

![Windows](https://img.shields.io/badge/-Windows_x64-blue.svg?style=for-the-badge&logo=windows)
![Linux/BSD](https://img.shields.io/badge/-Linux/BSD-red.svg?style=for-the-badge&logo=linux)
<a href="#installation-on-arch-linux" target="_blank"> <img src="https://img.shields.io/badge/-Arch_Linux-black.svg?style=for-the-badge&logo=archlinux" alt="Arch Linux"> </a>
![MacOS](https://img.shields.io/badge/-MacOS-lightblue.svg?style=for-the-badge&logo=apple)
![Android](https://img.shields.io/badge/-Android-green.svg?style=for-the-badge&logo=android)

The app can run wherever python can run. So all you need to have is python installed on your device.
On android you can use [termux](https://github.com/termux/termux-app).
If you have any difficulty consult for help on the [discord channel](https://discord.gg/HBEmAwvbHV)

### Installation on NixOS

![Static Badge](https://img.shields.io/badge/NixOs-black?style=flat&logo=nixos)

```bash
nix profile install github:Benexl/fastanime
```

### Installation on Arch Linux

> [!CAUTION]  
> Avoid mixing installation methods. If you install FastAnime using the installation script, do not install it from the AUR. Similarly, if you use the AUR, avoid using the installation script. 
> 
> If you want to switch between methods, first uninstall the existing installation using the `--uninstall` command from the installation script, as explained below.  

#### **Using the Installation Script**  

To install FastAnime via the installation script, run: 

```bash
bash <(curl -L https://raw.githubusercontent.com/Benexl/FastAnime/refs/heads/master/install.sh) 
```

To uninstall FastAnime installed via the script, use:  

```bash
bash <(curl -L https://raw.githubusercontent.com/Benexl/FastAnime/refs/heads/master/install.sh) --uninstall
```

#### **Using the AUR Package**  

FastAnime is available in the [AUR](https://aur.archlinux.org/) repository:  

- [FastAnime](https://aur.archlinux.org/packages/fastanime) - Stable Build  
- [FastAnime-Git](https://aur.archlinux.org/packages/fastanime-git) - Latest GitHub Build  

You can install these packages using an AUR helper like `paru` or `yay`.  

**With `paru`:** 

```bash
paru -S fastanime
#or
paru -S fastanime-git

```
**With `yay`:** 

```bash 
yay -S fastanime
#or
yay -S fastanime-git
```

### Installation using your favourite package manager

Currently the app is only published on [pypi](https://pypi.org/project/fastanime/).
With the following extras available:

- standard -which installs all dependencies
- api - which installs dependencies required to use `fastanime serve`
- mpv - which installs python mpv
- notifications - which installs plyer required for desktop notifications
  
#### Using uv

Recommended method of installation is using [uv](https://docs.astral.sh/uv/).

```bash
# generally:
uv tool install "fastanime[standard]"

# or stripped down installations:
uv tool install fastanime
uv tool install "fastanime[api]"
uv tool install "fastanime[mpv]"
uv tool install "fastanime[notifications]"

```

#### Using pipx

```bash

pipx install fastanime
# -- or for the development version --
pipx install 'fastanime==<latest-pre-release-tag>.dev1'
# example
# pipx install 'fastanime==0.60.1.dev1'

```

#### Using pip

```bash
pip install fastanime
# -- or for the development version --
pip install 'fastanime==<latest-pre-release-tag>.dev1'
# example
# pip install 'fastanime==0.60.1.dev1'
```

### Installing the bleeding edge version

To install the latest build which are created on every push by GitHub actions, download the [fastanime_debug_build](https://github.com/FastAnime/FastAnime/actions) of your choosing from the GitHub actions page.
Then:

```bash
unzip fastanime_debug_build

# outputs fastanime<version>.tar.gz

pipx install fastanime<version>.tar.gz

# --- or ---

pip install fastanime<version>.tar.gz
```

### Building from the source

Requirements:

- [git](https://git-scm.com/)
- [python 3.10 and above](https://www.python.org/)
- [uv](https://astral.sh/blog/uv)

To build from the source, follow these steps:

1. Clone the repository: `git clone https://github.com/Benexl/FastAnime.git --depth 1`
2. Navigate into the folder: `cd FastAnime`
3. Then build and Install the app:

```bash
# build and install fastanime with uv
uv tool install .
```

4. Enjoy! Verify installation with:

```bash
fastanime --version
```

> [!Tip]
>
> Download the completions from [here](https://github.com/FastAnime/FastAnime/tree/master/completions) for your shell.
> To add completions:
>
> - Fish Users: `cp $FASTANIME_PATH/completions/fastanime.fish ~/.config/fish/completions/`
> - Bash Users: Add `source $FASTANIME_PATH/completions/fastanime.bash` to your `.bashrc`
> - Zsh Users: Add `source $FASTANIME_PATH/completions/fastanime.zsh` to your `.zshrc`
>   or using the built in command `fastanime completions`

### External Dependencies

The only required external dependency, unless you won't be streaming, is [MPV](https://mpv.io/installation/), which i recommend installing with [uosc](https://github.com/tomasklaen/uosc) :fire: and [thumbfast](https://github.com/po5/thumbfast) for the best experience since they add a better interface to it.

> [!NOTE]
>
> The project currently sees no reason to support any other video
> player because we believe nothing beats **MPV** and it provides
> everything you could ever need with a small footprint.
> But if you have a reason feel free to encourage as to do so.
> However, on android this is not the case so vlc is also supported

**Other external dependencies that will just make your experience better:**

- [webtorrent-cli](https://github.com/webtorrent/webtorrent-cli) used when the provider is nyaa
- [ffmpeg](https://www.ffmpeg.org/) is required to be in your path environment variables to properly download [hls](https://www.cloudflare.com/en-gb/learning/video/what-is-http-live-streaming/) streams.
- [fzf](https://github.com/junegunn/fzf) 🔥 which is used as a better alternative to the ui.
- [rofi](https://github.com/davatorium/rofi) 🔥 which is used as another alternative ui + the desktop entry ui
- [chafa](https://github.com/hpjansson/chafa) currently the best cross platform and cross terminal image viewer for the terminal.
- [icat](https://sw.kovidgoyal.net/kitty/kittens/icat/) an image viewer that only works in [kitty terminal](https://sw.kovidgoyal.net/kitty/), which is currently the best terminal in my opinion, and by far the best image renderer for the terminal thanks to kitty's terminal graphics protocol. Its terminal graphics is so op that you can [run a browser on it](https://github.com/chase/awrit?tab=readme-ov-file)!!
- [bash](https://www.gnu.org/software/bash/) is used as the preview script language.
- [ani-skip](https://github.com/synacktraa/ani-skip) used for skipping the opening and ending theme songs
- [ffmpegthumbnailer](https://github.com/dirkvdb/ffmpegthumbnailer) used for local previews of downloaded anime
- [syncplay](https://syncplay.pl/) to enable watch together.
- [feh](https://github.com/derf/feh) used in manga mode


## Usage

The project offers a featureful command-line interface and MPV interface through the use of python-mpv.
The project also offers subs in different languages thanks to hianime provider.

### The Commandline interface :fire:

Designed for efficiency and automation. Plus has a beautiful pseudo-TUI in some of the commands.
If you are stuck anywhere just use `--help` before the command you would like to get help on

**Overview of main commands:**

- `fastanime anilist`: Powerful command for browsing and exploring anime due to AniList integration.
- `fastanime download`: Download anime.
- `fastanime search`: Powerful command meant for binging since it doesn't require the interfaces
- `fastanime downloads`: View downloaded anime and watch with MPV.
- `fastanime config`: Quickly edit configuration settings.
- `fastanime cache`: Quickly manage the cache fastanime uses
- `fastanime update`: Quickly update fastanime
- `fastanime grab`: print streams to stdout to use in non python application.

**Overview of options**

Most options are directly passed into fastanime directly and are shared by multiple subcommands.

Most of the options override your config file.

This is a convention to make the dev time faster since it reduces redundancy and also makes switching of subcommands with the same options easier to the end user.

In general `fastanime --<option-name>`

Available options for the fastanime include:

- `--server <server>` or `-s <server>` set the default server to auto select
- `--continue/--no-continue` or `-c/-no-c` whether to continue from the last episode you were watching
- `--local-history/--remote-history` whether to use remote or local history defaults to local
- `--quality <1080/720/480/360>` or `-q <1080/720/480/360>` the link to choose from server
- `--translation-type <dub/sub>` or `-t <dub/sub>` what language for anime
- `--dub` dubbed anime
- `--sub` subbed anime
- `--auto-select/--no-auto-select` or `-a/-no-a` auto select title from provider results
- `--auto-next/--no-auto-next` or `-A/-no-A` auto select next episode
- `-downloads-dir <path>` or `-d <path>` set the folder to download anime into
- `--fzf` use fzf for the ui
- `--default` use the default ui
- `--preview` show a preview when using fzf
- `--no-preview` dont show a preview when using fzf
- `--format <yt-dlp format string>` or `-f <yt-dlp format string>` set the format of anime downloaded and streamed based on [yt-dlp format](https://github.com/yt-dlp/yt-dlp#format-selection). Works when `--server gogoanime` or on providers that provide multi quality streams eg hianime
- `--icons/--no-icons` toggle the visibility of the icons
- `--skip/--no-skip` whether to skip the opening and ending theme songs.
- `--rofi` use rofi for the ui
- `--rofi-theme <path>` theme to use with rofi
- `--rofi-theme-input <path>` theme to use with rofi input
- `--rofi-theme-confirm <path>` theme to use with rofi confirm
- `--log` allow logging to stdout
- `--log-file` allow logging to a file
- `--rich-traceback` allow rich traceback
- `--use-mpv-mod/--use-default-player` whether to use python-mpv
- `--provider <allanime/animepahe/hianime/nyaa>` anime site of choice to scrape from
- `--sync-play` or `-sp` use syncplay for streaming anime so you can watch with your friends
- `--sub-lang <en/or any other common shortform for country>` regex is used to determine the appropriate. Only works when provider is hianime.
- `--normalize-titles/--no-normalize-titles` whether to normalize provider titles
- `--manga` toggle experimental manga mode

Example usage of the above options

```bash
# example of syncplay intergration
fastanime --sync-play --server sharepoint search -t <anime-title>

# --- or ---

# to watch with anilist intergration
fastanime --sync-play --server sharepoint anilist

# downloading dubbed anime
fastanime --dub download -t <anime>

# use  icons and fzf for a more elegant ui with preview
fastanime --icons --preview --fzf anilist

# use icons with default ui
fastanime --icons --default anilist

# viewing manga
fastanime --manga search -t <manga-title>
```

#### The anilist command :fire: :fire: :fire:

Uses the [AniList API](https://github.com/AniList/ApiV2-GraphQL-Docs) to create a terminal anilist client which is then intergrated with the scraping capabilities of the project.

##### Running without any subcommand

Run `fastanime anilist` to access the main interface.

##### Subcommands

The subcommands are mainly their as convenience. Since all the features already exist in the main interface.
Most of the subcommands share the common option `--dump-json` or `-d` which will print only the json data and suppress the ui.

- `fastanime anilist trending`: Top 15 trending anime.
- `fastanime anilist recent`: Top 15 recently updated anime.
- `fastanime anilist search`: Search for anime (top 50 results).
- `fastanime anilist upcoming`: Top 15 upcoming anime.
- `fastanime anilist popular`: Top 15 popular anime.
- `fastanime anilist favourites`: Top 15 favorite anime.
- `fastanime anilist random`: get random anime

**FastAnime Anilist Search subcommand** 🔥 🔥 🔥

It is by far one of the most powerful commands.
It offers the following options:

- `--sort <MediaSort>` or `-s <MediaSort>`
- `--title <anime-title>` or `-t <anime-title>`
- `--tags <tag>` or `-T <tag>` can be specified multiple times for different tags to filter by.
- `--year <year>` or `-y <year>`
- `--status <MediaStatus>` or `-S <MediaStatus>` can be specified multiple times
- `--media-format <MediaFormat>` or `-f <MediaFormat>`
- `--season <MediaSeason>`
- `--genres <genre>` or `-g <genre>` can be specified multiple times.
- `--on-list/--not-on-list`

Example:

```bash
# get anime with the tag of isekai
fastanime anilist search -T isekai

# get anime of 2024 and sort by popularity
# that has already finished airing or is releasing
# and is not in your anime lists
fastanime anilist search -y 2024 -s POPULARITY_DESC --status RELEASING --status FINISHED --not-on-list

# get anime of 2024 season WINTER
fastanime anilist search -y 2024 --season WINTER

# get anime genre action and tag isekai,magic
 fastanime anilist search -g Action -T Isekai -T Magic

# get anime of 2024 thats finished airing
fastanime anilist search -y 2024 -S FINISHED

# get the most favourite anime movies
fastanime anilist search -f MOVIE -s FAVOURITES_DESC
```

For more details visit the anilist docs or just get the completions which will improve the experience.

Like seriously **[get the completions](https://github.com/FastAnime/FastAnime#completions-subcommand)** and the experience will be a 💯 💯 better.

**Fastanime anilist download:**
Supports all the options for search except its used for downloading.
it also supports all options for `fastanime download`
Example:

```bash
# get anime with the tag of isekai
fastanime anilist download -T isekai

# get anime of 2024 and sort by popularity
# that has already finished airing or is releasing
# and is not in your anime lists
fastanime anilist download -y 2024 -s POPULARITY_DESC --status RELEASING --status FINISHED --not-on-list

# get anime of 2024 season WINTER
fastanime anilist download -y 2024 --season WINTER

# get anime genre action and tag isekai,magic
 fastanime anilist download -g Action -T Isekai -T Magic

# get anime of 2024 thats finished airing
fastanime anilist download -y 2024 -S FINISHED

# get the most favourite anime movies
fastanime anilist download -f MOVIE -s FAVOURITES_DESC
```

The following are commands you can only run if you are signed in to your AniList account:

- `fastanime anilist watching`
- `fastanime anilist planning`
- `fastanime anilist rewatching`
- `fastanime anilist dropped`
- `fastanime anilist paused`
- `fastanime anilist completed`

Plus: `fastanime anilist notifier` 🔥

```bash
# basic form
fastanime anilist notifier

# with logging to stdout
fastanime --log anilist notifier

# with logging to a file. stored in the same place as your config
fastanime --log-file anilist notifier
```

The above commands will start a loop that checks every 2 minutes if any of the anime in your watch list that are airing has just released a new episode.

The notification will consist of a cover image of the anime in none windows systems.

You can place the command among your machines startup scripts.

For fish users for example you can decide to put this in your `~/.config/fish/config.fish`:

```fish
if ! ps aux | grep -q '[f]astanime .* notifier'
  echo initializing fastanime anilist notifier
  nohup fastanime --log-file anilist notifier>/dev/null &
end
```

> [!NOTE]
> To sign in just run `fastanime anilist login` and follow the instructions.
> To view your login status `fastanime anilist login --status`
> To erase login data `fastanime anilist login --erase`

#### download subcommand

Download anime to watch later dub or sub with this one command.
Its optimized for scripting due to fuzzy matching; basically you don't have to manually select search results.

So every step of the way has been and can be automated.
Uses a list slicing syntax similar to that of python as the value for the `-r` option.

> [!NOTE]
>
> The download feature is powered by [yt-dlp](https://github.com/yt-dlp/yt-dlp) so all the bells and whistles that it provides are readily available in the project.
> Like continuing from where you left of while downloading, after lets say you lost your internet connection.

**Syntax:**

```bash
# Download all available episodes
# multiple titles can be specified with -t option
fastanime download -t <anime-title> -t <anime-title>
# -- or --
fastanime download -t <anime-title> -t <anime-title> -r ':'

# download latest episode for the two anime titles
# the number can be any no of latest episodes but a minus sign
# must be present
fastanime download -t <anime-title> -t <anime-title> -r '-1'

# latest 5
fastanime download -t <anime-title> -t <anime-title> -r '-5'

# Download specific episode range
# be sure to observe the range Syntax
fastanime download -t <anime-title> -r '<episodes-start>:<episodes-end>:<step>'

fastanime download -t <anime-title> -r '<episodes-start>:<episodes-end>'

fastanime download -t <anime-title> -r '<episodes-start>:'

fastanime download -t <anime-title> -r ':<episodes-end>'

# download specific episode
# remember python indexing starts at 0
fastanime download -t <anime-title> -r '<episode-1>:<episode>'

# merge subtitles with ffmpeg to mkv format; hianime tends to give subs as separate files
# and dont prompt for anything
# eg existing file in destination instead remove
# and clean
# ie remove original files (sub file and vid file)
# only keep merged files
fastanime download -t <anime-title> --merge --clean --no-prompt

# EOF is used since -t always expects a title
# you can supply anime titles from file or -t at the same time
#
# from stdin
echo -e "<anime-title>\n<anime-title>\n<anime-title>" | fastanime download -t "EOF" -r <range> -f -

# from file
fastanime download -t "EOF" -r <range> -f <file-path>


```

#### search subcommand

Powerful command mainly aimed at binging anime. Since it doesn't require interaction with the interfaces.

Uses a list slicing syntax similar to that of python as the value of the `-r` option.

**Syntax:**

```bash
# basic form where you will still be prompted for the episode number
# multiple titles can be specified with the -t option
fastanime search -t <anime-title> -t <anime-title>

# binge all episodes with this command
fastanime search -t <anime-title> -r ':'

# watch latest episode
fastanime search -t <anime-title> -r '-1'

# binge a specific episode range with this command
# be sure to observe the range Syntax
fastanime search -t <anime-title> -r '<start>:<stop>'

fastanime search -t <anime-title> -r '<start>:<stop>:<step>'

fastanime search -t <anime-title> -r '<start>:'

fastanime search -t <anime-title> -r ':<end>'
```

#### grab subcommand

Helper command to print streams to stdout so it can be used by non-python applications.

The format of the printed out data is json and can be either an array or object depending on how many anime titles have been specified in the command-line or through a subprocess.

> [!TIP]
> For python applications just use its python api, for even greater and easier control.
> So just add fastanime as one of your dependencies.

Uses a list slicing syntax similar to that of python as the value of the `-r` option.

**Syntax:**

```bash
# --- print anime info + episode streams ---

# multiple titles can be specified with the -t option
fastanime grab -t <anime-title> -t <anime-title>

# -- or --

# print all available episodes
fastanime grab -t <anime-title> -r ':'

# print the latest episode
fastanime grab -t <anime-title> -r '-1'

# print a specific episode range
# be sure to observe the range Syntax
fastanime grab -t <anime-title> -r '<start>:<stop>'

fastanime grab -t <anime-title> -r '<start>:<stop>:<step>'

fastanime grab -t <anime-title> -r '<start>:'

fastanime grab -t <anime-title> -r ':<end>'

# --- grab options ---

# print search results only
fastanime grab -t <anime-title> -r <range> --search-results-only

# print anime info only
fastanime grab -t <anime-title> -r <range> --anime-info-only

# print episode streams only
fastanime grab -t <anime-title> -r <range> --episode-streams-only

```

#### downloads subcommand

View and stream the anime you downloaded using MPV.

**Syntax:**

```bash
fastanime downloads

# view individual episodes
fastanime downloads --view-episodes
# --- or ---
fastanime downloads -v

# to set seek time when using ffmpegthumbnailer for local previews
# -1 means random and is the default
fastanime downloads --time-to-seek <intRange(-1,100)>
# --- or ---
fastanime downloads -t <intRange(-1,100)>

# to watch a specific title
# be sure to get the completions for the best experience
fastanime downloads --title <title>

# to get the path to the downloads folder set
fastanime downloads --path
# useful when you want to use the value for other programs

```

#### config subcommand

Edit FastAnime configuration settings using your preferred editor (based on `$EDITOR` environment variable so be sure to set it).

**Syntax:**

```bash
fastanime config

# to get config path which is useful if you want to use it for another program.
fastanime config --path

# add a desktop entry
fastanime config --desktop-entry

# view current contents of your configuration or can be used to get an example config
fastanime config --view
```

> [!Note]
>
> If it opens [vim](https://www.vim.org/download.php) you can exit by typing `:q` 😉.

#### cache subcommand

Easily manage the data fastanime has cached; for the previews.

**Syntax:**

```bash
# delete everything in the cache dir
fastanime cache --clean

# print the path to the cache dir and exit
fastanime cache --path

# print the current size of the cache dir and exit
fastanime cache --size

# open the cache dir and exit
fastanime cache
```

#### update subcommand

Easily update fastanime to latest

**Syntax:**

```bash
# update fastanime to latest
fastanime update

# check for latest release
fastanime update --check
```

#### completions subcommand

Helper command to setup shell completions

**Syntax:**

```bash
# try to detect your shell and print completions
fastanime completions
# print fish completions
fastanime completions --fish
# print bash completions
fastanime completions --bash
# print zsh completions
fastanime completions --zsh
```

#### fastanime serve

Helper command that starts a rest server.
This requires you to install fastanime with the api extra or standard extra.

```bash
# default options
fastanime serve

# specify host and port
fastanime serve --host <host> --port <port>
```

### MPV specific commands

The project now allows on the fly media controls directly from mpv. This means you can go to the next or previous episode without the window ever closing thus offering a seamless experience.
This is all powered with [python-mpv]() which enables writing mpv scripts with python just like how it would be done in lua.

#### Key Bindings

`<shift>+n` fetch the next episode

`<shift>+p` fetch the previous episode

`<shift>+t` toggle the translation type from dub to sub

`<shift>+a` toggle auto next episode

`<shit>+r` reload episode

#### Script Messages

Commands issued in the MPV console.

Examples:

```bash
# to select episode from mpv without window closing
script-message select-episode <episode-number>

# to select server from mpv without window closing
script-message select-server <server-name>

# to select quality
script-message select-quality <1080/720/480/360>
```

## styling the default interface

The default interface uses inquirerPy which is customizable. Read here to findout more <https://inquirerpy.readthedocs.io/en/latest/pages/env.html>

## Configuration

The app includes sensible defaults but can be customized extensively. Configuration is stored in `.ini` format at `~/.config/FastAnime/config.ini` on arch linux; for the other operating systems you can check by running `fastanime config --path`.

> [!TIP]
> You can now use the option `--update` to update your config file from the command-line
> For Example:
> `fastanime --icons --fzf --preview config --update`
> the above will set icons to true, use_fzf to true and preview to true in your config file

By default if a config file does not exist it will be auto created with comments to explain each and every option.
The default config:

```ini
[general]
icons = False

quality = 1080

normalize_titles = True

provider = allanime

preferred_language = english

downloads_dir = ~/Videos/FastAnime

preview = False

ffmpegthumbnailer_seek_time = -1

use_fzf = False

use_rofi = False

rofi_theme =

rofi_theme_input =

rofi_theme_confirm =

notification_duration = 2

sub_lang = eng

default_media_list_tracking = None

force_forward_tracking = True

cache_requests = True

use_persistent_provider_store = False

recent = 50


[stream]
continue_from_history = True

preferred_history = local

translation_type = sub

server = top

auto_next = False

auto_select = True

skip = False

episode_complete_at = 80

use_python_mpv = False

force_window = immediate

format = best[height<=1080]/bestvideo[height<=1080]+bestaudio/best

player = mpv
```

  
## Contributing

pr's are highly welcome

If you find an anime title that does not correspond with a provider or is just weird just [edit the data file](https://github.com/Benexl/FastAnime/blob/master/fastanime/Utility/data.py) and open a pr, issues will be ignored 😝.

## Supporting the Project

More pr's less issues 🙃

Show your support by starring the GitHub repository.

[![ko-fi](https://ko-fi.com/img/githubbutton_sm.svg)](https://ko-fi.com/Y8Y8ZAA7N)

## Disclaimer

> [!IMPORTANT]
>
> This project currently scrapes allanime, hianime, nyaa, yugen and animepahe.
> The developer(s) of this application does not have any affiliation with the content providers available, and this application hosts zero content.
> [DISCLAIMER](https://github.com/Benexl/FastAnime/blob/master/DISCLAIMER.md)
