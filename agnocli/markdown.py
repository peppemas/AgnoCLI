from __future__ import annotations

from typing import Optional

from rich.console import Console
from rich.markdown import Markdown


def get_console(force_ansi: bool = False) -> Console:
    # Rich auto-detects most terminals; allow forcing if requested
    return Console(force_terminal=force_ansi or None)


def render_markdown(console: Console, text: str) -> None:
    console.print(Markdown(text))


def render_plain(console: Console, text: str) -> None:
    console.print(text)
