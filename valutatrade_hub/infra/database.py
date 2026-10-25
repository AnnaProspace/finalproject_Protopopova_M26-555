"""Singleton DatabaseManager over JSON storage."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from valutatrade_hub.infra.settings import SettingsLoader


class DatabaseManager:
    """Абстракция над JSON-файлами. Тоже Singleton через __new__."""

    _instance: DatabaseManager | None = None

    def __new__(cls) -> DatabaseManager:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        if getattr(self, "_initialized", False):
            return
        self._initialized = True
        self._settings = SettingsLoader()

    def read(self, path: Path, default: Any) -> Any:
        if not path.exists():
            return default
        with path.open(encoding="utf-8") as f:
            return json.load(f)

    def write(self, path: Path, data: Any) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def read_users(self) -> list:
        return self.read(self._settings.get("users_path"), [])

    def write_users(self, data: list) -> None:
        self.write(self._settings.get("users_path"), data)

    def read_portfolios(self) -> list:
        return self.read(self._settings.get("portfolios_path"), [])

    def write_portfolios(self, data: list) -> None:
        self.write(self._settings.get("portfolios_path"), data)

    def read_rates(self) -> dict:
        return self.read(self._settings.get("rates_path"), {})

    def write_rates(self, data: dict) -> None:
        self.write(self._settings.get("rates_path"), data)