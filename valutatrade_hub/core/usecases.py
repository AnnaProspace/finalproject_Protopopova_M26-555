"""Business use cases for the wallet app."""

from datetime import datetime

from valutatrade_hub.core import utils
from valutatrade_hub.core.currencies import get_currency
from valutatrade_hub.core.exceptions import (
    ApiRequestError,
    InsufficientFundsError,
)
from valutatrade_hub.core.models import Portfolio, User, Wallet
from valutatrade_hub.decorators import log_action
from valutatrade_hub.infra.settings import SettingsLoader

_current_user: User | None = None


def get_current_user() -> User | None:
    return _current_user


def require_login() -> User:
    if _current_user is None:
        raise PermissionError("Сначала выполните login")
    return _current_user


def _load_users() -> list[dict]:
    return utils.load_json(utils.users_path(), [])


def _save_users(users: list[dict]) -> None:
    utils.save_json(utils.users_path(), users)


def _load_portfolios() -> list[dict]:
    return utils.load_json(utils.portfolios_path(), [])


def _save_portfolios(portfolios: list[dict]) -> None:
    utils.save_json(utils.portfolios_path(), portfolios)


def _user_from_dict(data: dict) -> User:
    return User(
        user_id=data["user_id"],
        username=data["username"],
        password="",
        salt=data["salt"],
        registration_date=datetime.fromisoformat(data["registration_date"]),
        hashed_password=data["hashed_password"],
    )


def _portfolio_from_dict(data: dict) -> Portfolio:
    wallets: dict[str, Wallet] = {}
    for code, wdata in data.get("wallets", {}).items():
        wallets[code] = Wallet(code, float(wdata.get("balance", 0.0)))
    return Portfolio(user_id=data["user_id"], wallets=wallets)


def _portfolio_to_dict(portfolio: Portfolio) -> dict:
    return {
        "user_id": portfolio.user_id,
        "wallets": {
            code: {"balance": wallet.balance}
            for code, wallet in portfolio.wallets.items()
        },
    }


def _get_portfolio(user_id: int) -> Portfolio:
    for item in _load_portfolios():
        if item["user_id"] == user_id:
            return _portfolio_from_dict(item)
    return Portfolio(user_id=user_id)


def _save_portfolio(portfolio: Portfolio) -> None:
    items = _load_portfolios()
    for i, item in enumerate(items):
        if item["user_id"] == portfolio.user_id:
            items[i] = _portfolio_to_dict(portfolio)
            _save_portfolios(items)
            return
    items.append(_portfolio_to_dict(portfolio))
    _save_portfolios(items)


def _is_stale(updated_at: str, ttl: int) -> bool:
    try:
        ts = datetime.fromisoformat(updated_at)
    except ValueError:
        return True
    return (datetime.now() - ts).total_seconds() > ttl


def _refresh_rates_stub(raw: dict) -> dict:
    """Учебный stub: курсы те же, обновляем метки времени."""
    now = datetime.now().replace(microsecond=0).isoformat()
    for key, value in list(raw.items()):
        if isinstance(value, dict) and "rate" in value:
            value["updated_at"] = now
    raw["last_refresh"] = now
    raw["source"] = "stub-refresh"
    utils.save_json(utils.rates_path(), raw)
    return raw


def _load_rates_raw() -> dict:
    settings = SettingsLoader()
    ttl = int(settings.get("rates_ttl_seconds", 300))
    raw = utils.load_json(utils.rates_path(), {})
    if not raw:
        raise ApiRequestError("файл курсов пуст или недоступен")

    last = raw.get("last_refresh")
    if last is None or _is_stale(str(last), ttl):
        try:
            raw = _refresh_rates_stub(raw)
        except OSError as exc:
            raise ApiRequestError(str(exc)) from exc
    return raw


def _rates_to_usd_map() -> dict[str, float]:
    rates = _load_rates_raw()
    result = {"USD": 1.0}
    for key, value in rates.items():
        if not isinstance(value, dict) or "rate" not in value:
            continue
        if key.endswith("_USD"):
            code = key[: -len("_USD")]
            result[code] = float(value["rate"])
    return result


def _require_known_currency(code: str) -> str:
    """Формат + реестр валют (CurrencyNotFoundError из get_currency)."""
    normalized = utils.validate_currency_code(code)
    get_currency(normalized)
    return normalized


def register(username: str, password: str) -> str:
    username = utils.validate_username(username)
    password = utils.validate_password(password)
    users = _load_users()
    if any(u["username"] == username for u in users):
        raise ValueError(f"Имя пользователя '{username}' уже занято")

    user_id = max((u["user_id"] for u in users), default=0) + 1
    salt = utils.generate_salt()
    user = User(user_id=user_id, username=username, password=password, salt=salt)
    users.append(
        {
            "user_id": user.user_id,
            "username": user.username,
            "hashed_password": user.hashed_password,
            "salt": user.salt,
            "registration_date": user.registration_date.isoformat(),
        }
    )
    _save_users(users)
    _save_portfolio(Portfolio(user_id=user_id))
    return (
        f"Пользователь '{username}' зарегистрирован (id={user_id}). "
        f"Войдите: login --username {username} --password ****"
    )


def login(username: str, password: str) -> str:
    global _current_user
    username = utils.validate_username(username)
    users = _load_users()
    match = next((u for u in users if u["username"] == username), None)
    if match is None:
        raise ValueError(f"Пользователь '{username}' не найден")
    user = _user_from_dict(match)
    if not user.verify_password(password):
        raise ValueError("Неверный пароль")
    _current_user = user
    return f"Вы вошли как '{username}'"


def show_portfolio(base: str = "USD") -> str:
    user = require_login()
    base_code = _require_known_currency(base)
    rates = _rates_to_usd_map()
    if base_code not in rates:
        raise ValueError(f"Неизвестная базовая валюта '{base}'")

    portfolio = _get_portfolio(user.user_id)
    if not portfolio.wallets:
        return f"Портфель пользователя '{user.username}' пуст."

    lines = [f"Портфель пользователя '{user.username}' (база: {base_code}):"]
    total = portfolio.get_total_value(base_code, rates)
    for code, wallet in sorted(portfolio.wallets.items()):
        if code == "USD":
            value_usd = wallet.balance
        else:
            value_usd = wallet.balance * rates[code]
        value_base = value_usd if base_code == "USD" else value_usd / rates[base_code]
        lines.append(
            f"- {code}: {wallet.balance:.4f}  → {value_base:.2f} {base_code}"
        )
    lines.append("---------------------------------")
    lines.append(f"ИТОГО: {total:,.2f} {base_code}")
    return "\n".join(lines)
@log_action("buy")
def buy(currency: str, amount: float) -> str:
    user = require_login()
    code = _require_known_currency(currency)
    qty = utils.validate_amount(amount)
    rates = _rates_to_usd_map()
    if code not in rates:
        raise ApiRequestError(f"нет курса для {code}->USD")

    portfolio = _get_portfolio(user.user_id)
    if code not in portfolio.wallets:
        portfolio.add_currency(code)
    if "USD" not in portfolio.wallets:
        portfolio.add_currency("USD")

    rate = rates[code]
    cost_usd = qty * rate if code != "USD" else qty
    usd_wallet = portfolio.get_wallet("USD")
    before = portfolio.get_wallet(code).balance

    if code != "USD":
        if usd_wallet.balance < cost_usd:
            raise InsufficientFundsError(usd_wallet.balance, cost_usd, "USD")
        usd_wallet.withdraw(cost_usd)
    portfolio.get_wallet(code).deposit(qty)
    after = portfolio.get_wallet(code).balance
    _save_portfolio(portfolio)

    return (
        f"Покупка выполнена: {qty:.4f} {code} по курсу {rate:.2f} USD/{code}\n"
        f"Изменения в портфеле:\n"
        f"- {code}: было {before:.4f} → стало {after:.4f}\n"
        f"Оценочная стоимость покупки: {cost_usd:,.2f} USD"
    )

@log_action("sell")
def sell(currency: str, amount: float) -> str:
    user = require_login()
    code = _require_known_currency(currency)
    qty = utils.validate_amount(amount)
    rates = _rates_to_usd_map()
    if code not in rates:
        raise ApiRequestError(f"нет курса для {code}->USD")

    portfolio = _get_portfolio(user.user_id)
    if code not in portfolio.wallets:
        raise ValueError(
            f"У вас нет кошелька '{code}'. Добавьте валюту: "
            "она создаётся автоматически при первой покупке."
        )

    wallet = portfolio.get_wallet(code)
    before = wallet.balance
    if qty > before:
        raise InsufficientFundsError(before, qty, code)

    rate = rates[code]
    revenue = qty * rate if code != "USD" else qty
    wallet.withdraw(qty)
    if code != "USD":
        if "USD" not in portfolio.wallets:
            portfolio.add_currency("USD")
        portfolio.get_wallet("USD").deposit(revenue)
    after = wallet.balance
    _save_portfolio(portfolio)

    return (
        f"Продажа выполнена: {qty:.4f} {code} по курсу {rate:.2f} USD/{code}\n"
        f"Изменения в портфеле:\n"
        f"- {code}: было {before:.4f} → стало {after:.4f}\n"
        f"Оценочная выручка: {revenue:,.2f} USD"
    )


def get_rate(from_currency: str, to_currency: str) -> str:
    src = _require_known_currency(from_currency)
    dst = _require_known_currency(to_currency)
    rates = _rates_to_usd_map()
    if src not in rates or dst not in rates:
        raise ApiRequestError(f"курс {src}->{dst} недоступен")

    # 1 SRC in DST: (SRC in USD) / (DST in USD)
    src_usd = rates[src]
    dst_usd = rates[dst]
    direct = src_usd / dst_usd
    reverse = dst_usd / src_usd
    data = utils.load_json(utils.rates_path(), {})
    updated = data.get("last_refresh", "n/a")
    return (
        f"Курс {src}→{dst}: {direct:.8f} (обновлено: {updated})\n"
        f"Обратный курс {dst}→{src}: {reverse:.8f}"
    )