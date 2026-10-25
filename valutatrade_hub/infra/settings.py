"""Singleton SettingsLoader."""

from __future__ import annotations

from pathlib import Path
from typing import Any


class SettingsLoader:
    """Единая точка конфигурации.

    Реализовано через __new__: один экземпляр на весь процесс,
    т.к. необходим один SettingsLoader и DatabaseManager
    достаточно __new__без метакласса
    дополнительно - проще в отладке 
    """

    _instance: SettingsLoader | None = None

    def __new__(cls) -> SettingsLoader:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        if getattr(self, "_initialized", False):
            return
        self._initialized = True
        self._config: dict[str, Any] = {}
        self.reload()

    def reload(self) -> None:
        root = Path(__file__).resolve().parents[2]
        self._config = {
            "data_dir": root / "data",
            "users_path": root / "data" / "users.json",
            "portfolios_path": root / "data" / "portfolios.json",
            "rates_path": root / "data" / "rates.json",
            "logs_dir": root / "logs",
            "actions_log_path": root / "logs" / "actions.log",
            "rates_ttl_seconds": 300,
            "default_base_currency": "USD",
            "log_level": "INFO",
            "log_format": "text",
        }

    def get(self, key: str, default: Any = None) -> Any:
        return self._config.get(key, default)