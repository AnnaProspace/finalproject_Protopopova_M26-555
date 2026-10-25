# ValutaTrade Hub

Консольный валютный кошелёк: регистрация/вход, портфель, покупка и продажа валют, курсы с TTL-кэшем.

## Структура

```text
finalproject_Protopopova_M26-555/
├── pyproject.toml
├── demo.cast                 # asciinema-демо CLI
├── data/
│   ├── users.json
│   ├── portfolios.json
│   └── rates.json            # кэш курсов + updated_at / last_refresh
├── logs/                     # actions.log (в .gitignore)
└── valutatrade_hub/
    ├── cli/interface.py      # CLI
    ├── core/                 # модели, usecases, валюты, ошибки
    ├── infra/                # SettingsLoader, DatabaseManager (Singleton)
    ├── logging_config.py
    ├── decorators.py         # @log_action
    └── parser_service/       # (не реализован сейчас, будет добавлен  к хард DL)
```
## Установка
Нужны Python >= 3.12 и uv.
```bash
cd finalproject_Protopopova_M26-555
uv sync
```
## Запуск
```bash
uv run finalproject-wallet
```
## Примеры команд CLI
```text
register --username alice --password 1234
login --username alice --password 1234
update-rates
buy --currency USD --amount 2000
buy --currency BTC --amount 0.01
show-portfolio --base USD
sell --currency BTC --amount 0.005
get-rate --from USD --to BTC
exit
```
В приложении также: `help`.
## Кэш курсов и TTL
- Курсы в `data/rates.json` (пары `CODE_USD`: `rate`, `updated_at`; поле `last_refresh`).
- TTL: `rates_ttl_seconds` в SettingsLoader (по умолчанию 300 секунд).
- Если кэш устарел — ошибка с подсказкой выполнить `update-rates`.
- Сейчас `update-rates` обновляет stub-метки; реальные API — в Parser Service.
## Parser Service
Будет добавлен позже: клиенты API, updater, ключ из переменной окружения (например `EXCHANGE_RATE_API_KEY`), без коммита секретов.
## Логирование
`buy` / `sell` пишутся в `logs/actions.log` через `@log_action`.
## Демо
Файл: `demo.cast`
```bash
asciinema play demo.cast
```
## Проверка стиля
```bash
uv run ruff check .
```