# Telegram бот для шаблонного отзыва (aiogram 3.x)

Бот пошагово собирает данные отзыва у администратора и возвращает итог в фиксированном формате одним сообщением.

## Стек

- Python 3.10+
- aiogram 3.x
- aiosqlite
- python-dotenv

## Возможности

- Доступ только для `ADMIN_IDS` из `.env`.
- Команды:
  - `/start` — меню
  - `/new` — начать создание отзыва
  - `/cancel` — отмена на любом шаге
- FSM шаги:
  1. username
  2. payment_date (`DD.MM.YYYY`, с валидацией)
  3. review_text (до 800 символов)
  4. rating (inline 1..5 ⭐)
  5. confirm (подтверждение / редактирование / отмена)
- Номер заказа увеличивается **только после подтверждения**.
- Хранение счетчика и логов в SQLite.

## Структура

- `main.py`
- `config.py`
- `db.py`
- `states.py`
- `keyboards.py`
- `handlers.py`
- `requirements.txt`
- `.env.example`

## Установка и запуск

```bash
python3.10 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# отредактируйте .env
python main.py
```

## Пример `.env`

```env
BOT_TOKEN=123456:ABCDEF...
ADMIN_IDS=123456789,987654321
TIMEZONE=Europe/Moscow
```

Можно использовать `TIMEZONE=UTC`.

## Формат итогового сообщения

```text
📝 Обратная связь
👤 Юзернейм: <username>
🕒 Дата платежа: <DD.MM.YYYY>
🔢 Номер заказа: <00001>
📄 Отзыв: <review_text>
Оценка: <stars>
```

Где `<stars>` — строка вида `⭐⭐⭐⭐`.
