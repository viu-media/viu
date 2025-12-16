from .cli import cli as run_cli
import sys
import os

if sys.platform.startswith("win"):
    os.environ.setdefault("PYTHONUTF8", "1")
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

__all__ = ["run_cli"]
