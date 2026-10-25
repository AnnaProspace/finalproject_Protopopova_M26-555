"""CLI commands entrypoint."""

from __future__ import annotations

import shlex

from valutatrade_hub.core import usecases


def _parse_args(argv: list[str]) -> dict[str, str]:
    result: dict[str, str] = {}
    i = 0
    while i < len(argv):
        token = argv[i]
        if token.startswith("--"):
            key = token[2:]
            if i + 1 >= len(argv) or argv[i + 1].startswith("--"):
                raise ValueError(f"Для --{key} нужно значение")
            result[key] = argv[i + 1]
            i += 2
        else:
            raise ValueError(f"Неизвестный аргумент: {token}")
    return result


def _handle(command: str, args: dict[str, str]) -> str:
    if command == "register":
        if "username" not in args or "password" not in args:
            raise ValueError("Нужны --username и --password")
        return usecases.register(args["username"], args["password"])
    if command == "login":
        if "username" not in args or "password" not in args:
            raise ValueError("Нужны --username и --password")
        return usecases.login(args["username"], args["password"])
    if command in {"help", "?"}:
        return (
            "Команды: register, login, show-portfolio, buy, sell, get-rate, exit\n"
            "Примеры:\n"
            "  register --username alice --password 1234\n"
            "  login --username alice --password 1234"
        )
    raise ValueError(f"Неизвестная команда: {command}")


def main() -> None:
    print("ValutaTrade Hub. Введите help или exit.")
    while True:
        try:
            line = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if not line:
            continue
        if line in {"exit", "quit"}:
            print("До свидания.")
            break
        try:
            parts = shlex.split(line)
            command, *rest = parts
            message = _handle(command, _parse_args(rest))
            print(message)
        except Exception as exc:  # noqa: BLE001 - CLI показывает любую ошибку пользователю
            print(exc)


if __name__ == "__main__":
    main()