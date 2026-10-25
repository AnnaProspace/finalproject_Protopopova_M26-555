"""Business use cases for the wallet app."""

from __future__ import annotations

from datetime import datetime

from valutatrade_hub.core import utils
from valutatrade_hub.core.models import Portfolio, User, Wallet
from valutatrade_hub.decorators import log_action

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


def _rates_to_usd_map() -> dict[str, float]:
    rates = utils.load_json(utils.rates_path(), {})
    result = {"USD": 1.0}
    for key, value in rates.items():
        if not isinstance(value, dict) or "rate" not in value:
            continue
        if key.endswith("_USD"):
            code = key[: -len("_USD")]
            result[code] = float(value["rate"])
    return result


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
    base_code = utils.validate_currency_code(base)
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
    code = utils.validate_currency_code(currency)
    qty = utils.validate_amount(amount)
    rates = _rates_to_usd_map()
    if code not in rates:
        raise ValueError(f"Не удалось получить курс для {code}→USD")

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
            raise ValueError(
                f"Недостаточно средств: доступно {usd_wallet.balance:.4f} USD, "
                f"требуется {cost_usd:.4f} USD"
            )
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
    code = utils.validate_currency_code(currency)
    qty = utils.validate_amount(amount)
    rates = _rates_to_usd_map()
    if code not in rates:
        raise ValueError(f"Не удалось получить курс для {code}→USD")

    portfolio = _get_portfolio(user.user_id)
    if code not in portfolio.wallets:
        raise ValueError(
            f"У вас нет кошелька '{code}'. Добавьте валюту: "
            "она создаётся автоматически при первой покупке."
        )

    wallet = portfolio.get_wallet(code)
    before = wallet.balance
    if qty > before:
        raise ValueError(
            f"Недостаточно средств: доступно {before:.4f} {code}, "
            f"требуется {qty:.4f} {code}"
        )

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
    src = utils.validate_currency_code(from_currency)
    dst = utils.validate_currency_code(to_currency)
    rates = _rates_to_usd_map()
    if src not in rates or dst not in rates:
        raise ValueError(f"Курс {src}→{dst} недоступен. Повторите попытку позже.")

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