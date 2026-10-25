"""Domain models: User, Wallet, Portfolio."""

from __future__ import annotations

import hashlib
from datetime import datetime


class User:
    def __init__(
        self,
        user_id: int,
        username: str,
        password: str,
        salt: str,
        registration_date: datetime | None = None,
        hashed_password: str | None = None,
    ) -> None:
        self._user_id = user_id
        self._salt = salt
        self._registration_date = registration_date or datetime.now()
        self.username = username
        if hashed_password is not None:
            self._hashed_password = hashed_password
        else:
            self.password = password

    @property
    def user_id(self) -> int:
        return self._user_id

    @property
    def username(self) -> str:
        return self._username

    @username.setter
    def username(self, value: str) -> None:
        if not isinstance(value, str) or not value.strip():
            raise ValueError("Имя не может быть пустым")
        self._username = value.strip()

    @property
    def salt(self) -> str:
        return self._salt

    @property
    def registration_date(self) -> datetime:
        return self._registration_date

    @property
    def hashed_password(self) -> str:
        return self._hashed_password

    @property
    def password(self) -> None:
        raise AttributeError("Пароль нельзя прочитать")

    @password.setter
    def password(self, value: str) -> None:
        if not isinstance(value, str) or len(value) < 4:
            raise ValueError("Пароль должен быть не короче 4 символов")
        self._hashed_password = self._make_hash(value)

    def _make_hash(self, password: str) -> str:
        return hashlib.sha256(f"{password}{self._salt}".encode()).hexdigest()

    def get_user_info(self) -> dict:
        return {
            "user_id": self._user_id,
            "username": self._username,
            "registration_date": self._registration_date.isoformat(),
        }

    def change_password(self, new_password: str) -> None:
        self.password = new_password

    def verify_password(self, password: str) -> bool:
        return self._hashed_password == self._make_hash(password)
class Wallet:
    def __init__(self, currency_code: str, balance: float = 0.0) -> None:
        if not isinstance(currency_code, str) or not currency_code.strip():
            raise ValueError("Код валюты не может быть пустым")
        self.currency_code = currency_code.strip().upper()
        self.balance = balance

    @property
    def balance(self) -> float:
        return self._balance

    @balance.setter
    def balance(self, value: float) -> None:
        if not isinstance(value, (int, float)) or isinstance(value, bool):
            raise TypeError("Баланс должен быть числом")
        if value < 0:
            raise ValueError("Баланс не может быть отрицательным")
        self._balance = float(value)

    def deposit(self, amount: float) -> None:
        if not isinstance(amount, (int, float)) or isinstance(amount, bool):
            raise TypeError("'amount' должен быть числом")
        if amount <= 0:
            raise ValueError("'amount' должен быть положительным числом")
        self.balance = self._balance + float(amount)

    def withdraw(self, amount: float) -> None:
        if not isinstance(amount, (int, float)) or isinstance(amount, bool):
            raise TypeError("'amount' должен быть числом")
        if amount <= 0:
            raise ValueError("'amount' должен быть положительным числом")
        if amount > self._balance:
            raise ValueError("Недостаточно средств")
        self.balance = self._balance - float(amount)

    def get_balance_info(self) -> dict:
        return {
            "currency_code": self.currency_code,
            "balance": self._balance,
        }

class Portfolio:
    def __init__(self, user_id: int, wallets: dict[str, Wallet] | None = None) -> None:
        self._user_id = user_id
        self._wallets: dict[str, Wallet] = dict(wallets) if wallets else {}

    @property
    def user_id(self) -> int:
        return self._user_id

    @property
    def wallets(self) -> dict[str, Wallet]:
        return dict(self._wallets)

    def add_currency(self, currency_code: str) -> Wallet:
        code = currency_code.strip().upper()
        if not code:
            raise ValueError("Код валюты не может быть пустым")
        if code in self._wallets:
            raise ValueError(f"Валюта '{code}' уже есть в портфеле")
        wallet = Wallet(code, 0.0)
        self._wallets[code] = wallet
        return wallet

    def get_wallet(self, currency_code: str) -> Wallet:
        code = currency_code.strip().upper()
        if code not in self._wallets:
            raise KeyError(f"Кошелёк '{code}' не найден")
        return self._wallets[code]

    def get_total_value(
        self,
        base_currency: str = "USD",
        exchange_rates: dict[str, float] | None = None,
    ) -> float:
        base = base_currency.strip().upper()
        rates = exchange_rates or {
            "USD": 1.0,
            "EUR": 1.08,
            "BTC": 59337.21,
            "ETH": 3720.0,
            "RUB": 0.01016,
        }
        if base not in rates and base != "USD":
            raise ValueError(f"Неизвестная базовая валюта '{base_currency}'")

        total_usd = 0.0
        for code, wallet in self._wallets.items():
            if code == "USD":
                total_usd += wallet.balance
                continue
            if code not in rates:
                raise ValueError(f"Нет курса для {code}")
            total_usd += wallet.balance * rates[code]

        if base == "USD":
            return total_usd
        return total_usd / rates[base]
    