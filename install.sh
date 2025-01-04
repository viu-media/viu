#!/bin/bash

set -e  # Exit on any error

if [[ $EUID -eq 0 ]]; then
    echo "Please do not run this script as root. Dependencies will be installed with sudo where necessary."
    exit 1
fi

REPO_URL="https://github.com/Benex254/FastAnime.git"
BUILD_DIR="/tmp/fastanime-build"
INSTALLED_RESOURCES=(
    "/usr/share/licenses/fastanime/LICENSE"
    "/usr/share/bash-completion/completions/fastanime"
    "/usr/share/zsh/site-functions/_fastanime"
    "/usr/share/fish/vendor_completions.d/fastanime.fish"
)
MISSING_DEPENDENCIES=(
    "python-fastapi"
    "python-inquirerpy"
    "libtorrent"
    "python-plyer"
    "python-pytest"
    "python-rich"
    "python-thefuzz"
    "python-pypresence"
    "python-click"
    "python-requests"
    "yt-dlp"
    "python-dbus"
)
OPTIONAL_DEPENDENCIES=(
    "mpv"
    "webtorrent-cli"
    "ffmpeg"
    "rofi"
    "fzf"
    "chafa"
    "icat"
    "ani-skip-git"
    "ffmpegthumbnailer"
    "syncplay"
    "feh"
)

install_gum() {
    if ! command -v gum >/dev/null 2>&1; then
        echo "Installing gum..."
        sudo pacman -S --needed --noconfirm gum
    else
        echo "gum is already installed."
    fi
}

# Install paru
install_paru() {
    echo "Installing paru..."
    sudo pacman -S --needed --noconfirm base-devel
    git clone https://aur.archlinux.org/paru.git /tmp/paru
    cd /tmp/paru || exit
    makepkg -si --noconfirm
    cd - || exit
    rm -rf /tmp/paru
}

# Install yay
install_yay() {
    echo "Installing yay..."
    sudo pacman -S --needed --noconfirm git base-devel
    git clone https://aur.archlinux.org/yay.git /tmp/yay
    cd /tmp/yay || exit
    makepkg -si --noconfirm
    cd - || exit
    rm -rf /tmp/yay
}

install_dependencies() {
    local dependencies=("$@")
    echo "Installing dependencies: ${dependencies[*]}"
    for DEP in "${dependencies[@]}"; do
        if ! pacman -Qi "$DEP" >/dev/null 2>&1; then
            echo "Installing $DEP..."
            $AUR_HELPER -S --noconfirm "$DEP"
        else
            echo "$DEP is already installed."
        fi
    done
}

uninstall_fastanime() {
    echo "Uninstalling FastAnime and its resources..."
    
    # remove fastanime directory ...
    for RESOURCE in "${INSTALLED_RESOURCES[@]}"; do
        if [[ -f "$RESOURCE" ]]; then
            sudo rm -f "$RESOURCE"
            echo "Removed: $RESOURCE"
        fi
    done

    if command -v fastanime >/dev/null 2>&1; then
        FASTANIME_BIN=$(which fastanime)
        sudo rm -f "$FASTANIME_BIN"
        echo "Removed: $FASTANIME_BIN"
    fi

    # Conflict Dir With FastAnime Aur Package
    sudo rm /usr/lib/python3.13/site-packages/fastanime -rf
    sudo rm /usr/lib/python3.13/site-packages/fastanime-2.8.6.dist-info -rf
    echo "FastAnime has been successfully uninstalled!"
}

main_install() {
    install_gum

    if command -v paru >/dev/null 2>&1; then
        AUR_HELPER="paru"
    elif command -v yay >/dev/null 2>&1; then
        AUR_HELPER="yay"
    else
        echo "Neither paru nor yay is installed."
        echo "By default, paru will be installed."
        INSTALL_CHOICE=$(gum choose "Install paru (default)" "Install yay")
        
        if [[ "$INSTALL_CHOICE" == "Install yay" ]]; then
            install_yay
            AUR_HELPER="yay"
        else
            install_paru
            AUR_HELPER="paru"
        fi
    fi

    echo "Using AUR helper: $AUR_HELPER"

    echo "Installing missing dependencies..."
    install_dependencies "${MISSING_DEPENDENCIES[@]}"

    echo
    echo "Optional dependencies enhance functionality (e.g., mpv for playback, ffmpeg for streams)."
    read -rp "Do you want to install optional dependencies? [y/N]: " INSTALL_OPTIONALS

    if [[ "$INSTALL_OPTIONALS" =~ ^[Yy]$ ]]; then
        install_dependencies "${OPTIONAL_DEPENDENCIES[@]}"
    fi

    echo "Cloning FastAnime repository..."
    rm -rf "$BUILD_DIR"
    git clone "$REPO_URL" "$BUILD_DIR"

    echo "Building and installing FastAnime..."
    cd "$BUILD_DIR" || exit
    uv build
    sudo python -m installer --destdir="/" dist/*.whl

    echo "Installing additional resources..."
    for RESOURCE in "${INSTALLED_RESOURCES[@]}"; do
        sudo install -Dm644 "$(basename "$RESOURCE")" "$RESOURCE"
    done

    echo
    echo "FastAnime has been installed successfully!"
    echo "You can now run FastAnime from the terminal by typing: fastanime"
}

case "$1" in
    --uninstall)
        uninstall_fastanime
        ;;
    *)
        main_install
        ;;
esac
