from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

from .config import _platform_config_dir


STATE_FILE = _platform_config_dir() / "state.json"


def set_current_workflow(name: str) -> None:
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    data = {"current_workflow": name}
    STATE_FILE.write_text(json.dumps(data), encoding="utf-8")


def get_current_workflow() -> Optional[str]:
    try:
        if STATE_FILE.exists():
            data = json.loads(STATE_FILE.read_text(encoding="utf-8"))
            return data.get("current_workflow")
    except Exception:
        return None
    return None
