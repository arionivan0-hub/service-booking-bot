# Telegram-бот записи в автосервис

Бот для записи на услуги автосервиса с админ-панелью.

## Стек

- Python 3.12 + aiogram 3
- PostgreSQL 16 (asyncpg)
- Redis 7 (FSM storage)
- FastAPI (админ-панель)
- Docker Compose

## Быстрый старт

### 1. Настройка .env

```bash
cp .env.example .env
# Отредактируйте .env:
# - BOT_TOKEN: токен бота от @BotFather
# - ADMIN_IDS: ваш Telegram ID (через запятую)
```

### 2. Запуск

```bash
docker compose up -d --build
```

### 3. Проверка

```bash
# Логи бота
docker compose logs bot --tail -f

# Бот запущен когда видно:
# "Starting bot polling..."
```

## Команды бота

| Команда | Описание |
|---------|----------|
| `/start` | Главное меню / регистрация |
| `/help` | Список команд |
| `/cancel` | Отмена текущего действия |
| `/admin` | Админ-панель (только для ADMIN_IDS) |
| `/stats` | Статистика (админ) |

## Конфигурация (.env)

| Переменная | По умолчанию | Описание |
|------------|-------------|----------|
| `BOT_TOKEN` | - | Токен Telegram бота (обязательно) |
| `DATABASE_URL` | sqlite... | URL PostgreSQL |
| `REDIS_URL` | redis://redis:6379/0 | URL Redis |
| `ADMIN_IDS` | - | Telegram ID администраторов (через запятую) |
| `WORK_START` | 9 | Начало рабочего дня |
| `WORK_END` | 18 | Конец рабочего дня |
| `SAT_WORK_END` | 14 | Конец рабочего дня в субботу |
| `SUNDAY_CLOSED` | true | Выходной в воскресенье |
| `TZ_OFFSET` | 3 | Часовой пояс (часы от UTC) |
| `BOOKING_AHEAD_DAYS` | 14 | На сколько дней вперёд можно записаться |
| `REMINDER_HOURS` | 24,2 | Напоминания (часы до визита) |

## Архитектура

```
bot.py              -- точка входа, настройка бота
config.py           -- конфигурация из .env
database/
  models.py         -- SQLAlchemy модели (User, Service, Appointment)
  crud.py           -- запросы к БД
  engine.py         -- подключение к БД
handlers/
  keyboards.py      -- общие клавиатуры
  menu.py           -- главное меню
  registration.py   -- регистрация / профиль
  services.py       -- выбор услуги
  booking.py        -- бронирование (выбор даты/времени/подтверждение)
  my_appointments.py -- просмотр/отмена/перенос записей
  contacts.py       -- контакты
  admin.py          -- админ-команды
middleware/
  auth.py           -- проверка пользователя в БД
  rate_limit.py     -- anti-spam
services/
  time_slots.py     -- расчёт свободных слотов
  notifications.py  -- напоминания (APScheduler)
tests/
  test_time_slots.py -- unit-тесты
```

## Перезапуск

```bash
# Полный пересбор
docker compose up -d --build

# Только перезапуск (без пересбора)
docker compose restart bot

# Логи в реальном времени
docker compose logs bot -f
```

## Админ-панель

Доступна на `http://localhost:9090` (порт из docker-compose.yml).

Логин/пароль: `ADMIN_USER` / `ADMIN_PASS` из .env.
