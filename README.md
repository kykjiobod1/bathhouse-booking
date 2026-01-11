# Bathhouse Booking System

Система бронирования бань для малого бизнеса.

## Архитектура
- **Backend**: Django 5.0 + PostgreSQL
- **Admin**: Django Admin для управления бронированиями
- **Client**: Telegram bot (aiogram 3) для бронирования
- **Deployment**: Docker Compose

## Основные возможности
- Управление банями и клиентами через админку
- Бронирование через Telegram бота
- Проверка пересечений бронирований
- Подтверждение брони через предоплату (ручная проверка)
- Расчет доступных слотов времени

## Структура проекта
```
bathhouse-booking/
├── bathhouse_booking/          # Python корень
│   ├── manage.py
│   ├── config/                # Django проект
│   ├── bookings/              # Django приложение
│   └── bot/                   # Telegram бот
├── specs/                     # Спецификации
├── docker-compose.yml
├── Dockerfile
├── pyproject.toml
├── .env.example
└── README.md
```

## Быстрый старт
1. Клонировать репозиторий
2. Скопировать `.env.example` в `.env` и заполнить переменные
3. Запустить `docker compose up --build`
4. Открыть http://localhost:8000/admin

## Разработка
- Тесты: `pytest`
- TDD подход для всех компонентов
- Бизнес-логика в `bookings/services.py`
