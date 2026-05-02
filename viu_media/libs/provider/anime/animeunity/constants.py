import re

ANIMEUNITY = "animeunity.so"
ANIMEUNITY_BASE = f"https://www.{ANIMEUNITY}"

MAX_TIMEOUT = 10
TOKEN_REGEX = re.compile(r'<meta.*?name="csrf-token".*?content="([^"]*)".*?>')

REPLACEMENT_WORDS = {"Season ": "", "Cour": "Part"}

# Server Specific
AVAILABLE_VIDEO_QUALITY = ["1080", "720", "480"]
VIDEO_INFO_REGEX = re.compile(r"window.video\s*=\s*(\{[^\}]*\})")
VIDEO_INFO_CLEAN_REGEX = re.compile(r'(?<!["\'])(\b\w+\b)(?=\s*:)')
DOWNLOAD_FILENAME_REGEX = re.compile(r"[?&]filename=([^&]+)")
QUALITY_REGEX = re.compile(r"/(\d{3,4}p)")
DOWNLOAD_URL_REGEX = re.compile(r"window.downloadUrl\s*=\s*'([^']*)'")
