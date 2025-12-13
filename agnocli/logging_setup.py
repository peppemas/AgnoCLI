from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional


def setup_logging(log_dir: Path, level: int = logging.INFO, name: str = "agnocli") -> logging.Logger:
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / f"{name}.log"

    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.propagate = False

    if not any(isinstance(h, RotatingFileHandler) for h in logger.handlers):
        fh = RotatingFileHandler(str(log_file), maxBytes=10 * 1024 * 1024, backupCount=5, encoding="utf-8")
        fmt = logging.Formatter(
            fmt="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        fh.setFormatter(fmt)
        logger.addHandler(fh)

    if not any(isinstance(h, logging.StreamHandler) for h in logger.handlers):
        sh = logging.StreamHandler()
        sh.setLevel(level)
        sh.setFormatter(logging.Formatter("%(levelname)s: %(message)s"))
        logger.addHandler(sh)

    return logger
