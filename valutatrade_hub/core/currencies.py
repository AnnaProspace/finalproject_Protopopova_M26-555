"""Currency hierarchy: Currency, Fiat, Crypto."""

from __future__ import annotations

from abc import ABC, abstractmethod

from valutatrade_hub.core.exceptions import CurrencyNotFoundError


class Currency(ABC):
    def __init__(self, name: str, code: str) -> None:
        if not isinstance(name, str) or not name.strip():
            raise ValueError("name — не пустая строка")
        normalized = code.strip().upper() if isinstance(code, str) else ""
        if not (2 <= len(normalized) <= 5) or " " in normalized:
            raise ValueError("code — 2–5 символов, верхний регистр, без пробелов")
        self.name = name.strip()
        self.code = normalized

    @abstractmethod
    def get_display_info(self) -> str:
        raise NotImplementedError


class FiatCurrency(Currency):
    def __init__(self, name: str, code: str, issuing_country: str) -> None:
        super().__init__(name, code)
        if not isinstance(issuing_country, str) or not issuing_country.strip():
            raise ValueError("issuing_country не может быть пустым")
        self.issuing_country = issuing_country.strip()

    def get_display_info(self) -> str:
        return (
            f"[FIAT] {self.code} — {self.name} "
            f"(Issuing: {self.issuing_country})"
        )


class CryptoCurrency(Currency):
    def __init__(
        self,
        name: str,
        code: str,
        algorithm: str,
        market_cap: float,
    ) -> None:
        super().__init__(name, code)
        if not isinstance(algorithm, str) or not algorithm.strip():
            raise ValueError("algorithm не может быть пустым")
        if not isinstance(market_cap, (int, float)) or market_cap < 0:
            raise ValueError("market_cap должен быть неотрицательным числом")
        self.algorithm = algorithm.strip()
        self.market_cap = float(market_cap)

    def get_display_info(self) -> str:
        return (
            f"[CRYPTO] {self.code} — {self.name} "
            f"(Algo: {self.algorithm}, MCAP: {self.market_cap:.2e})"
        )


_REGISTRY: dict[str, Currency] = {
    "USD": FiatCurrency("US Dollar", "USD", "United States"),
    "EUR": FiatCurrency("Euro", "EUR", "Eurozone"),
    "RUB": FiatCurrency("Russian Ruble", "RUB", "Russia"),
    "BTC": CryptoCurrency("Bitcoin", "BTC", "SHA-256", 1.12e12),
    "ETH": CryptoCurrency("Ethereum", "ETH", "Ethash", 4.5e11),
}


def get_currency(code: str) -> Currency:
    key = code.strip().upper() if isinstance(code, str) else ""
    currency = _REGISTRY.get(key)
    if currency is None:
        raise CurrencyNotFoundError(key or str(code))
    return currency


def list_supported_codes() -> list[str]:
    return sorted(_REGISTRY)