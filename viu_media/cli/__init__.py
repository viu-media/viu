from .cli import cli as run_cli
import sys
import os

if sys.platform.startswith("win"):
    os.environ.setdefault("PYTHONUTF8", "1")


__all__ = ["run_cli"]
