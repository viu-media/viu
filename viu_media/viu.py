#!/usr/bin/env python3
import os
import sys

# Add the application root directory to Python path
if getattr(sys, "frozen", False):
    application_path = os.path.dirname(sys.executable)
    sys.path.insert(0, application_path)

# Import and run the main application
from viu_media import Cli

if __name__ == "__main__":
    Cli()
