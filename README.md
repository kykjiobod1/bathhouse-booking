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
- **Запрет бронирований в прошлое** - автоматическая валидация времени начала
- **Ценообразование по часам** - настройка HOURLY_PRICE в SystemConfig
- **Обработка номера телефона** - опциональный ввод при бронировании
- **Уведомления администратора** - сообщения о новых оплатах в Telegram
- **Логирование** - подробные логи в файлы и консоль

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

## Логирование
Система настроена на запись логов в файлы (`logs/` директория) и вывод в консоль:

### Файлы логов:
- `logs/django.log` - логи Django приложения
- `logs/errors.log` - ошибки Django
- `logs/bot.log` - логи Telegram бота

### Docker команды для просмотра логов:
```bash
# Все логи контейнеров
make logs

# Только логи бота
make bot-logs

# Последние 200 строк логов бота
docker compose logs -f --tail=200 bot
```

Логи также доступны через стандартные команды `docker compose logs`.

## Разработка

### Настройка окружения
```bash
# Создать виртуальное окружение
python3 -m venv .venv
source .venv/bin/activate

# Установить зависимости
pip install Django~=5.0 pytest pytest-django dj-database-url python-dotenv
```

### Запуск тестов
```bash
# Активировать виртуальное окружение
source .venv/bin/activate

# Запустить все тесты
pytest

# Запустить тесты с подробным выводом
pytest -v

# Запустить тесты из конкретной директории
pytest tests/
```

### Запуск Django
```bash
# Перейти в директорию Django проекта
cd bathhouse_booking

# Применить миграции
python manage.py migrate

# Создать суперпользователя
python manage.py createsuperuser

# Запустить сервер разработки
python manage.py runserver
```

### TDD подход
- Все компоненты разрабатываются через TDD
- Бизнес-логика в `bookings/services.py`
- Тесты в `tests/` и `bookings/tests/`
