"""Helpers: hashing, validation, JSON I/O."""

from __future__ import annotations

import hashlib
import json
import secrets
import string
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parents[2] / "data"


def generate_salt(length: int = 8) -> str:
    alphabet = string.ascii_letters + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(length))


def hash_password(password: str, salt: str) -> str:
    return hashlib.sha256(f"{password}{salt}".encode()).hexdigest()


def validate_username(username: str) -> str:
    if not isinstance(username, str) or not username.strip():
        raise ValueError("Имя не может быть пустым")
    return username.strip()


def validate_password(password: str) -> str:
    if not isinstance(password, str) or len(password) < 4:
        raise ValueError("Пароль должен быть не короче 4 символов")
    return password


def validate_amount(amount: float) -> float:
    if not isinstance(amount, (int, float)) or isinstance(amount, bool):
        raise ValueError("'amount' должен быть положительным числом")
    value = float(amount)
    if value <= 0:
        raise ValueError("'amount' должен быть положительным числом")
    return value


def validate_currency_code(code: str) -> str:
    if not isinstance(code, str) or not code.strip():
        raise ValueError("Код валюты не может быть пустым")
    return code.strip().upper()


def load_json(path: Path, default):
    if not path.exists():
        return default
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def save_json(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def users_path() -> Path:
    return DATA_DIR / "users.json"


def portfolios_path() -> Path:
    return DATA_DIR / "portfolios.json"


def rates_path() -> Path:
    return DATA_DIR / "rates.json"