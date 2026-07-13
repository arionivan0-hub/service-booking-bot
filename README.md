# Service Booking Bot

Telegram-бот для записи клиентов на услуги автосервиса. Построен на aiogram 3.x с использованием SQLAlchemy и Google Sheets.

## Возможности

- **Регистрация пользователя** — имя и телефон собираются при первом запуске
- **Выбор услуги** — список услуг с ценами и длительностью
- **Выбор даты и времени** — ближайшие 7 дней, свободные слоты 09:00–18:00
- **Подтверждение записи** — саммари перед сохранением
- **Мои записи** — просмотр активных записей с возможностью отмены
- **Контакты** — адрес, телефон, часы работы
- **Google Sheets** — автоматическая выгрузка записей в таблицу

## Структура проекта

```
service-booking-bot/
├── bot.py                      # Точка входа
├── config.py                   # Конфигурация (токен, БД, Google API)
├── requirements.txt            # Зависимости
├── database/
│   ├── engine.py               # AsyncEngine + sessionmaker
│   ├── models.py               # User, Service, Appointment
│   └── crud.py                 # Функции работы с БД
├── handlers/
│   ├── menu.py                 # /start, главное меню
│   ├── registration.py         # FSM-регистрация (имя + телефон)
│   ├── services.py             # Выбор услуги
│   ├── booking.py              # FSM-сценарий бронирования
│   ├── my_appointments.py      # Просмотр / отмена записей
│   └── contacts.py             # Контакты автосервиса
└── services/
    ├── google_sheets.py        # Интеграция с Google Sheets
    └── time_slots.py           # Генерация свободных слотов
```

## Установка и запуск

### 1. Клонировать репозиторий

```bash
git clone https://github.com/arionivan0-hub/service-booking-bot.git
cd service-booking-bot
```

### 2. Установить зависимости

```bash
pip install -r requirements.txt
```

### 3. Настроить переменные окружения

Создайте файл `.env` в корне проекта:

```env
BOT_TOKEN=ваш_токен_от_BotFather
DATABASE_URL=sqlite+aiosqlite:///database/bookings.db
GOOGLE_SHEET_ID=id_вашей_таблицы
GOOGLE_CREDENTIALS_FILE=credentials.json
```

Или задайте переменные в системе:

```bash
# Windows (PowerShell)
$env:BOT_TOKEN="ваш_токен"

# Linux/macOS
export BOT_TOKEN="ваш_токен"
```

### 4. Настроить Google Sheets (опционально)

1. Создайте проект в [Google Cloud Console](https://console.cloud.google.com)
2. Включите **Google Sheets API** и **Google Drive API**
3. Создайте **Service Account** и скачайте JSON-ключ как `credentials.json`
4. Создайте Google Таблицу и скопируйте её ID из URL
5. Расшарьте таблицу на email сервис-аккаунта (с правами редактора)

### 5. Запустить бота

```bash
python bot.py
```

При первом запуске автоматически:
- Создаются таблицы SQLite (users, services, appointments)
- Заполняются 5 стандартных услуг

## Используемые технологии

| Компонент | Технология |
|-----------|-----------|
| Telegram Bot API | aiogram 3.x |
| База данных | SQLAlchemy 2.0 (async) + SQLite |
| Google Sheets | gspread + google-auth |
| Хранение FSM | aiogram FSM (MemoryStorage) |

## Лицензия

MIT
