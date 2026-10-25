"""Logging setup for ValutaTrade Hub."""

from __future__ import annotations

import logging
from pathlib import Path

from valutatrade_hub.infra.settings import SettingsLoader

_configured = False


def setup_logging() -> None:
    global _configured
    if _configured:
        return

    settings = SettingsLoader()
    log_path: Path = settings.get("actions_log_path")
    log_path.parent.mkdir(parents=True, exist_ok=True)

    level_name = str(settings.get("log_level", "INFO")).upper()
    level = getattr(logging, level_name, logging.INFO)

    logger = logging.getLogger("valutatrade_hub")
    logger.setLevel(level)
    logger.handlers.clear()

    handler = logging.FileHandler(log_path, encoding="utf-8")
    handler.setLevel(level)
    handler.setFormatter(
        logging.Formatter("%(asctime)s | %(levelname)s | %(message)s")
    )
    logger.addHandler(handler)
    logger.propagate = False

    _configured = True


def get_logger(name: str = "valutatrade_hub") -> logging.Logger:
    setup_logging()
    return logging.getLogger(name)