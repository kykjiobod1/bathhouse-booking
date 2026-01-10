# specs/agent_tasks.md — Bathhouse Booking (для OpenCode)

> Этот файл — **исполняемые задачи** для агента.
>
> Выполнять строго по порядку.

---

## Глобальные правила

1) Делай пункты строго по порядку.
2) Каждый пункт выполнять **строго по TDD**:
   - сначала тесты
   - потом реализация
   - `pytest` должен быть зелёный
3) Пункт считается выполненным **только если тесты проходят**.
4) После выполнения пункта — написать краткий отчёт:
   - что изменено
   - какие команды прогнаны
5) После отчёта — **STOP** и ждать ревью.
6) Коммиты **не делать**, пока явно не попросят.
7) Квадратные скобки `[ ]` в заголовках задач — для отметки выполнения. Агент должен оставить `[ ]` как есть, пользователь поставит `[x]` после ревью.

---

## A0) Repo scaffolding

### A0.1 [ ] Создать структуру репозитория
Создай структуру в текущей директории (`bathhouse-booking/`):
- `bathhouse_booking/` — корень Python проекта (здесь будут manage.py, config/, bookings/, bot/)
- `specs/` (уже существует с файлами)
- `README.md` (уже существует, заполнить базовое описание)
- `.gitignore` для Python/Django (node_modules, __pycache__, .env, *.pyc, etc.)
- `.env.example` с переменными:
  ```
  SECRET_KEY=your-secret-key-here
  DATABASE_URL=postgres://user:pass@db:5432/bathhouse_booking
  DEBUG=True
  TELEGRAM_BOT_TOKEN=your-telegram-bot-token-here
  ```

STOP.

---

### A0.2 [ ] Создать pyproject.toml с зависимостями
Создать `pyproject.toml` с:
- секцией `[project]` с именем, версией, зависимостями
- секцией `[build-system]`
- секцией `[tool.pytest.ini_options]` для конфигурации pytest

Зависимости:
- Django~=5.0
- psycopg2-binary
- dj-database-url
- python-dotenv
- pytest
- pytest-django
- aiogram~=3.0
- python-dateutil

STOP.

---

## A1) Django init

### A1.1 [ ] Создать Django проект
Внутри `bathhouse_booking/`:
- Создать Django project `config` (`django-admin startproject config .`)
- Создать Django app `bookings` (`python manage.py startapp bookings`)
- Добавить `'bookings'` в `INSTALLED_APPS` в `config/settings.py`
- Настроить `DATABASES` для использования переменной окружения `DATABASE_URL` с помощью `dj_database_url.config()` (можно временно использовать sqlite3 для проверки)
- Выполнить миграции: `python manage.py migrate`
- Создать суперпользователя: `python manage.py createsuperuser`
- Убедиться, что Django Admin подключен (по умолчанию)

Проверка:
- `python manage.py runserver`
- `/admin` открывается (залогиниться суперпользователем)

STOP.

---

## A2) Dependencies + pytest

### A2.1 [ ] Подключить pytest
В pyproject.toml (созданном в A0.2) уже указаны зависимости pytest и pytest-django.

Сделать:
- Настроить `pytest.ini` или секцию `[tool.pytest.ini_options]` в `pyproject.toml`:
  ```
  DJANGO_SETTINGS_MODULE = config.settings
  python_files = tests.py test_*.py *_tests.py
  ```
- Создать `tests/test_smoke.py` с простым smoke-тестом (например, проверка, что 2+2=4)
- Убедиться, что pytest работает с Django: создать тест, который использует `django.test.TestCase`

Команды проверки:
- `pytest -q`
- `pytest tests/ -v`

STOP.

---

## A3) Docker

### A3.1 [ ] Dockerfile + docker compose
Добавь:
- `Dockerfile` для Django приложения (основа: python:3.12-slim, установка зависимостей, копирование кода, запуск `python manage.py runserver 0.0.0.0:8000`)
- `docker-compose.yml` с сервисами:
  - `db` (postgres:15)
  - `web` (сборка из Dockerfile)
- named volume для postgres данных (например `pgdata`)
- `.env` файл должен подхватываться обоими сервисами
- Настроить healthcheck для postgres
- Команды использовать как `docker compose ...`

Проверка:
- `docker compose up --build` (запускается без ошибок)
- `docker compose exec web python manage.py migrate` (миграции применяются)

STOP.

---

## A4) Models + invariants (TDD)

### A4.1 [ ] Реализовать модели
Модели (в `bookings/models.py`):
- `Client`: 
  - `name` (CharField, max_length=200)
  - `phone` (CharField, max_length=20)
  - `telegram_id` (BigIntegerField, null=True, blank=True)
  - `comment` (TextField, blank=True)
  - `created_at` (DateTimeField, auto_now_add=True)
- `Bathhouse`:
  - `name` (CharField, max_length=200)
  - `capacity` (IntegerField, null=True, blank=True)
  - `is_active` (BooleanField, default=True)
- `Booking`:
  - `client` (ForeignKey to Client, on_delete=models.CASCADE)
  - `bathhouse` (ForeignKey to Bathhouse, on_delete=models.CASCADE)
  - `start_datetime` (DateTimeField)
  - `end_datetime` (DateTimeField)
  - `status` (CharField, max_length=20, choices=STATUS_CHOICES)
  - `price_total` (DecimalField, max_digits=10, decimal_places=2, null=True, blank=True)
  - `prepayment_amount` (DecimalField, max_digits=10, decimal_places=2, null=True, blank=True)
  - `comment` (TextField, blank=True)
  - `created_at` (DateTimeField, auto_now_add=True)
- `SystemConfig`:
  - `key` (CharField, max_length=100, unique=True)
  - `value` (TextField)
  - `description` (TextField, blank=True)

Status Booking (choices):
- pending
- payment_reported
- approved
- rejected
- cancelled

Действия:
- Создать модели с указанными полями
- Добавить `__str__` методы
- Создать миграции: `python manage.py makemigrations bookings`
- Применить миграции: `python manage.py migrate`

STOP.

---

### A4.2 [ ] Инварианты в Booking.clean (TDD)
Реализовать в `Booking.clean()`:
1. Проверка: `start_datetime < end_datetime` (иначе ValidationError)
2. Запрет пересечений **только для approved**:
   - Если статус `approved`, проверить, что нет других approved бронирований для той же бани в перекрывающийся интервал
   - Исключить из проверки сам объект (при обновлении существующей записи)
   - Использовать `Q` objects для проверки пересечения: `(start < existing.end) AND (end > existing.start)`
   - Если пересечение найдено — вызвать ValidationError

Тесты (в `bookings/tests/test_models.py`):
- invalid range (start >= end) вызывает ValidationError
- approved overlap запрещён (создание нового approved поверх существующего approved)
- approved overlap запрещён (обновление существующего booking на approved при пересечении)
- pending overlap допускается
- payment_reported overlap допускается
- rejected/cancelled overlap допускается

Важно:
- это нужно для Django Admin: админ не должен сохранить пересечение
- метод `clean` вызывается автоматически в Django Admin при сохранении

Команды проверки:
- `pytest bookings/tests/test_models.py -q`
- `pytest -xvs` (подробный вывод)

STOP.

---

## A5) Services (TDD)

### A5.1 [ ] Реализовать services.py
Создать `bookings/services.py`:

Функции:
- `create_booking_request(client, bathhouse, start, end, comment=None)`
  - создаёт Booking(status=pending)
  - вызывает `full_clean()` перед сохранением
  - возвращает созданный объект Booking
- `report_payment(booking)`
  - переводит в `payment_reported`
  - сохраняет объект
- `approve_booking(booking)`
  - переводит в `approved` (должно упасть на overlap, так как `clean()` проверит)
  - сохраняет объект
- `reject_booking(booking, reason=None)`
  - переводит в `rejected`
  - сохраняет объект

Правила:
- всегда перед `save()` вызывать `full_clean()`
- функции должны обрабатывать возможные ValidationError и пробрасывать их выше

Тесты (в `bookings/tests/test_services.py`):
- create_booking_request создаёт pending
- report_payment меняет статус
- approve_booking запрещает overlap (должен вызвать ValidationError)
- reject_booking меняет статус

STOP.

---

### A5.2 [ ] Сервис расчёта доступных слотов
Создать функцию в `bookings/services.py`:
- `get_available_slots(bathhouse, date)`
  - Принимает объект Bathhouse и дату (datetime.date)
  - Возвращает список доступных интервалов (start, end) на эту дату
  - Учитывает:
    - Рабочие часы из SystemConfig (OPEN_HOUR, CLOSE_HOUR, по умолчанию 9-22)
    - Шаг слота из SystemConfig (SLOT_STEP_MINUTES, по умолчанию 30)
    - Минимальное время брони из SystemConfig (MIN_BOOKING_MINUTES, по умолчанию 120)
    - Занятые слоты: approved бронирования на эту баню в эту дату
  - Алгоритм:
    1. Определить рабочие часы (например 9:00-22:00)
    2. Разбить на слоты по SLOT_STEP_MINUTES
    3. Исключить слоты, которые пересекаются с approved бронированиями
    4. Оставить только слоты длиной >= MIN_BOOKING_MINUTES

Тесты (в `bookings/tests/test_services.py`):
- Без approved бронирований — возвращаются все слоты
- С approved бронированием — соответствующие слоты исключаются
- Учёт рабочих часов
- Учёт минимальной длительности

STOP.

---

## A6) Admin

### A6.1 [ ] Настроить Django Admin
Зарегистрировать модели в `bookings/admin.py`.

BookingAdmin:
- `list_display`: bathhouse, client, start_datetime, end_datetime, status, created_at
- `list_filter`: bathhouse, status
- `search_fields`: client__name, client__phone
- `date_hierarchy`: start_datetime
- `ordering`: -start_datetime
- `readonly_fields`: ('created_at',)

Для Client, Bathhouse, SystemConfig — использовать `admin.site.register` с базовыми настройками.

Проверка:
- Зайти в `/admin`, убедиться, что все модели отображаются
- Создать тестовые данные через админку

STOP.

---

### A6.2 [ ] Admin actions approve/reject
Сделать admin actions в `BookingAdmin`:
- `approve` — вызывает `services.approve_booking(booking)`
- `reject` — вызывает `services.reject_booking(booking, reason="Отклонено через админку")`

Важно:
- actions должны вызывать **services**, а не менять поля напрямую.
- Обрабатывать возможные ValidationError (например, при overlap) и показывать сообщение об ошибке.
- После успешного действия — сообщение "Бронирование X подтверждено/отклонено".

Проверка:
- В админке выбрать несколько бронирований, применить actions
- Убедиться, что статус меняется
- Убедиться, что approve с пересечением вызывает ошибку

STOP.

---

## A7) Telegram bot (aiogram 3)

### A7.1 [ ] Структура бота
Создать `bathhouse_booking/bot/`:
- `main.py` — entrypoint (инициализация бота, диспетчера, запуск polling)
- `routers.py` — сборка routers из handlers
- `handlers/` директория с модулями:
  - `start.py` — команда /start
  - `booking.py` — FSM сценарий бронирования
- `states.py` — FSM состояния (например, `BookingStates`)
- `keyboards.py` — inline кнопки (клавиатуры)
- `dependencies.py` — dependency injection (например, get_session для БД)

Требования:
- запуск отдельной командой: `python -m bot.main`
- токен берётся из env переменной `TELEGRAM_BOT_TOKEN`
- хендлеры не ходят напрямую в ORM (не импортируют модели напрямую), вызывают `bookings.services`
- это обеспечивает отделение бизнес-логики и тестируемость
- использовать aiogram 3.x

Проверка:
- Запуск бота: `python -m bot.main` (должен стартовать без ошибок)

STOP.

---

### A7.2 [ ] FSM сценарий бронирования (кнопки)
FSM flow (реализовать в `handlers/booking.py`):
1. `/start` → главное меню с кнопкой "Забронировать баню"
2. Выбрать баню (кнопки со списком активных бань из БД)
3. Выбрать дату (кнопки: сегодня, завтра, послезавтра + календарь)
4. Выбрать интервал (кнопки с доступными слотами на выбранную дату, используя `services.get_available_slots`)
5. Создать booking (pending) через `services.create_booking_request`
6. Показать инструкцию оплаты (текст из `SystemConfig` или захардкоженный)
7. Кнопка «Я оплатил» → вызывает `services.report_payment`
8. Сообщение "Ожидайте подтверждения от администратора"

Требования:
- Все шаги через inline keyboard
- Использовать FSM (aiogram.fsm.state)
- Валидация данных (проверка доступности слотов)

Проверка:
- Пройти весь flow в боте (можно через тесты или ручной запуск)

STOP.

---

## A8) Hardening

### A8.1 [ ] Ошибки + логи
Добавить базовую обработку ошибок:

1. **Логирование**:
   - Настроить logging в Django (консоль + файл)
   - Логировать исключения в сервисах и хендлерах
   - Использовать разные уровни (INFO, ERROR)

2. **Обработка ошибок в боте**:
   - Глобальный error handler в aiogram
   - При возникновении исключения — логировать и отправлять пользователю безопасное сообщение ("Произошла ошибка, попробуйте позже")
   - Не показывать stack trace пользователю

3. **Обработка ошибок в сервисах**:
   - ValidationError пробрасывать выше
   - Логировать бизнес-ошибки

Проверка:
- Создать тест, который вызывает ошибку в сервисе
- Убедиться, что логи пишутся
- Убедиться, что бот не падает на исключении

STOP.

