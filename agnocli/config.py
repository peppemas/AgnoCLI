from __future__ import annotations

import os
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Optional

import yaml


DEFAULT_CONFIG_FILE = "agnocli.yaml"


def _platform_config_dir() -> Path:
    if sys.platform.startswith("win"):
        base = os.getenv("APPDATA", str(Path.home() / "AppData" / "Roaming"))
        return Path(base) / "agnocli"
    elif sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / "agnocli"
    else:
        return Path.home() / ".config" / "agnocli"


def _platform_log_dir() -> Path:
    # Default logs under config dir
    return _platform_config_dir() / "logs"


@dataclass
class MarkdownSettings:
    render: bool = True


@dataclass
class AnsiSettings:
    force: bool = False


@dataclass
class Config:
    workflows_module: Optional[str] = None
    log_dir: Path = field(default_factory=_platform_log_dir)
    default_workflow: Optional[str] = None
    markdown: MarkdownSettings = field(default_factory=MarkdownSettings)
    ansi: AnsiSettings = field(default_factory=AnsiSettings)

    @staticmethod
    def from_dict(d: Dict[str, Any]) -> "Config":
        markdown = d.get("markdown", {}) or {}
        ansi = d.get("ansi", {}) or {}
        return Config(
            workflows_module=d.get("workflows_module"),
            log_dir=Path(d.get("log_dir")) if d.get("log_dir") else _platform_log_dir(),
            default_workflow=d.get("default_workflow"),
            markdown=MarkdownSettings(render=bool(markdown.get("render", True))),
            ansi=AnsiSettings(force=bool(ansi.get("force", False))),
        )


def load_config(explicit_path: Optional[str] = None) -> Config:
    candidates = []
    if explicit_path:
        candidates.append(Path(explicit_path))
    # CWD
    candidates.append(Path.cwd() / DEFAULT_CONFIG_FILE)
    # Platform config
    candidates.append(_platform_config_dir() / DEFAULT_CONFIG_FILE)

    data: Dict[str, Any] = {}
    for p in candidates:
        try:
            if p.exists():
                with p.open("r", encoding="utf-8") as f:
                    loaded = yaml.safe_load(f) or {}
                    if isinstance(loaded, dict):
                        data.update(loaded)
                        break
        except Exception:
            # Ignore malformed config; continue to defaults
            continue

    cfg = Config.from_dict(data)
    # Ensure directories exist
    try:
        cfg.log_dir.mkdir(parents=True, exist_ok=True)
        _platform_config_dir().mkdir(parents=True, exist_ok=True)
    except Exception:
        pass
    return cfg
