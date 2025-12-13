from __future__ import annotations

import sys

try:
    # Ensure ANSI on Windows terminals
    from colorama import just_fix_windows_console

    just_fix_windows_console()
except Exception:
    pass

from .cli import run


if __name__ == "__main__":
    run()
