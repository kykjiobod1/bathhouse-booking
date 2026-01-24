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
6) Коммиты **не делать**, пока явно не попросят. Коммитить может ТОЛЬКО пользователь.
7) Квадратные скобки `[ ]` в заголовках задач — для отметки выполнения. Агент должен оставить `[ ]` как есть, пользователь поставит `[x]` после ревью. Галочки ставит ТОЛЬКО пользователь.
8) Перед выполнением любой команды агент должен написать её в виде строки в кавычках (например `"python manage.py migrate"`), чтобы пользователь видел её в чате и мог проверить.
9) В случае, если что-то идёт не по плану, расходится со спецификацией или есть потенциальные ошибки, агент ДОЛЖЕН написать об этом в чате до продолжения работы.
10) Перед внесением любых изменений в код (редактирование, удаление, создание файлов) агент ДОЛЖЕН спросить разрешения у пользователя, описав предлагаемые изменения. Только после получения явного согласия можно вносить изменения.
11) Если требуется уточнение у пользователя:
- задай вопрос обычным сообщением
- не используй tool question
- не блокируй выполнение

---

## A0) Repo scaffolding

### A0.1 [x] Создать структуру репозитория
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

### A0.2 [x] Создать pyproject.toml с зависимостями
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

### A1.1 [x] Создать Django проект
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

### A2.1 [x] Подключить pytest
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

### A3.1 [x] Dockerfile + docker compose
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

### A4.1 [x] Реализовать модели
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

### A4.2 [x] Инварианты в Booking.clean (TDD)
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

### A5.1 [x] Реализовать services.py
Создать `bookings/services.py`:

Функции:
- `create_booking_request(client, bathhouse, start, end, comment=None)`
  - создаёт Booking(status=pending)
  - вызывает `full_clean()` перед сохранением
  - возвращает созданный объект Booking
- `report_payment(booking_id)`
  - переводит в `payment_reported`
  - сохраняет объект
- `approve_booking(booking_id)`
  - переводит в `approved` (должно упасть на overlap, так как `clean()` проверит)
  - сохраняет объект
- `reject_booking(booking_id, reason=None)`
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

### A5.2 [x] Сервис расчёта доступных слотов

**Перед выполнением: перечитать Глобальные правила (пункты 1-10)**

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

### A6.1 [x] Настроить Django Admin

**Перед выполнением: перечитать Глобальные правила (пункты 1-10)**

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

### A6.2 [x] Admin actions approve/reject

**Перед выполнением: перечитать Глобальные правила (пункты 1-10)**

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

### A7.1 [x] Структура бота
**Перед выполнением: перечитать Глобальные правила (пункты 1-10)**

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

### A7.2 [x] FSM сценарий бронирования (кнопки)

**Перед выполнением: перечитать Глобальные правила (пункты 1-10)**

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

### A7.3 [x] Расширенные функции бота и админки

**Перед выполнением: перечитать Глобальные правила (пункты 1-10)**

Добавить расширенный функционал:

1. **Назначение администратора через Telegram**:
   - Добавить переменную окружения `ADMIN_PASSWORD` в `.env.example` и `.env` (значение должно совпадать с паролем суперпользователя Django админки).
   - Пользователь отправляет команду `/admin пароль` (например, `/admin mypassword`).
   - Бот сравнивает введённый пароль с переменной `ADMIN_PASSWORD` из окружения.
   - При совпадении Telegram ID пользователя сохраняется в SystemConfig (ключ `TELEGRAM_ADMIN_ID`).
   - Только этот пользователь получает уведомления о новых заявках и может отвечать на сообщения клиентов.
   - При первом запуске `TELEGRAM_ADMIN_ID` пуст (задаётся вручную через админку или команду `/admin`).

2. **Подтверждение оплаты только через экшен в админке**:
   - Сделать поле `prepayment_amount` readonly в админке, изменение только через кастомный экшен "Подтвердить оплату", который вызывает `services.report_payment`.

3. **Уведомление админу о новой заявке**:
   - При переходе бронирования в статус `payment_reported` отправлять уведомление Telegram-админу (ID из SystemConfig).

4. **Кнопка "мои бронирования"**:
   - Добавить в главное меню кнопку для просмотра активных бронирований пользователя с возможностью отмены (через `services.cancel_booking`).

5. **Чат с админом через пересылку сообщений**:
   - Пользователь отправляет сообщение админу через команду `/message` или кнопку "Написать админу".
   - Бот пересылает сообщение администратору (Telegram ID из `TELEGRAM_ADMIN_ID`).
   - Если администратор отвечает на пересланное сообщение (используя reply), бот автоматически пересылает ответ обратно клиенту.
   - Для связи используется `reply_to_message.forward_from` (доступно в Telegram API) для определения исходного отправителя.
   - Дополнительная модель `Message` не требуется (простой механизм пересылки).

6. **Номер телефона при бронировании**:
   - Во время бронирования запрашивать номер телефона (опционально). Если не указан, связь только через Telegram.

7. **Исправить ссылку "Открыть сайт" в админке Django**:
   - Установить `admin.site.site_url = '/admin/'`, чтобы кнопка "Открыть сайт" вела на страницу админки, а не на корень сайта.

8. **Проверка лимита бронирований перед бронированием**:
   - В сервисе `create_booking_request` проверять, не превышает ли пользователь лимит активных бронирований (уже есть MAX_ACTIVE_BOOKINGS_PER_CLIENT). Показывать сообщение в боте.

9. **Выбор даты через aiogram-calendar**:
   - Добавить зависимость `aiogram-calendar` в `pyproject.toml` (версия `~=1.0` или актуальная).
   - Настроить календарь с русской локализацией (если поддерживается).
   - Заменить все выборы даты (бронирование, просмотр расписания) на инлайн-календарь `aiogram-calendar`.
   - Убрать кнопки "сегодня/завтра/послезавтра" и ручной ввод.
   - При выборе даты через календарь показывать свободные слоты только на этот день (использовать `services.get_available_slots`).
   - Обновить FSM сценарий бронирования и просмотра расписания для использования календаря.

10. **Стартовое сообщение с гайдом**:
    - Обновить `/start` с кратким обзором шагов бронирования.

11. **Прочие улучшения**:
    - Обсудить с пользователем дополнительные идеи.

Проверка:
- Все новые функции покрыты тестами.
- Интеграционные тесты для бота.

STOP.

---
## A8) Hardening

### A8.1 [x] Ошибки + логи

**Перед выполнением: перечитать Глобальные правила (пункты 1-10)**

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

---

## A9) Post-MVP fixes

**Перед выполнением: перечитать Глобальные правила (пункты 1-11)**

### A9.1 [x] Восстановить отображение суммы к оплате в боте
Проблема: В сообщении о создании бронирования не отображается сумма к оплате "Сумма к оплате: X руб."

Диагностика:
1. Проверить, что `booking.price_total` правильно рассчитывается в `services.create_booking_request`
2. Проверить, что цена сохраняется в БД (модель Booking, поле price_total - IntegerField)
3. Проверить формирование сообщения в `bot/handlers/booking.py:413-422`
4. Исправить отображение суммы, если проблема найдена

Тесты:
- Создать бронирование через бота → проверить, что сообщение содержит сумму к оплате
- Интеграционный тест: полный flow бронирования с проверкой сообщения

### A9.2 [x] Исправить редактирование статуса в админке
Проблема: Поле `status` в админке недоступно для редактирования (readonly), но должно быть редактируемым, кроме перевода в `payment_reported`.

Исправления:
1. Убрать `'status'` из `readonly_fields` в `BookingAdmin`
2. Добавить валидацию в `BookingAdmin.form` или переопределить `save_model`, чтобы запретить установку статуса `payment_reported` через прямое редактирование
3. Разрешить изменение на другие статусы (`pending`, `approved`, `rejected`, `cancelled`)

Тесты:
- В админке можно изменить статус с `pending` на `approved`
- В админке нельзя изменить статус на `payment_reported` (должна быть ошибка)
- Действие `confirm_payment` по-прежнему работает

### A9.3 [x] Удалить лишнее действие в админке
**Разъяснение:**
- `approve`: переводит бронирование в статус `approved` (подтверждено) - финальное подтверждение бронирования
- `confirm_payment`: переводит бронирование из `pending` в `payment_reported` (оплата сообщена) - промежуточный статус после оплаты

**Решение пользователя:** Удалить `confirm_payment`, оставить только `approve`. Подтверждение оплаты будет через действие `approve`.

**Исправления:**
1. Удалить `'confirm_payment'` из `actions` списка в `BookingAdmin`
2. Удалить метод `confirm_payment` из `BookingAdmin`
3. Обновить тесты админки (убрать тесты для `confirm_payment`)
4. Возможно обновить логику `approve`, если нужно обрабатывать переход из `pending` в `approved`

**Тесты:**
- Действие `approve` должно переводить бронирование в статус `approved`
- Действия `confirm_payment` больше нет в списке

### A9.4 [x] Восстановить функционал максимальных бронирований
**Решение пользователя:** Активными считать только бронирования со статусом `approved`.

**Диагностика:**
1. Проверить функцию `check_booking_limit` в `services.py` - текущая логика считает `['pending', 'payment_reported', 'approved']`
2. Проверить конфигурацию `MAX_ACTIVE_BOOKINGS_PER_CLIENT` в SystemConfig
3. Проверить, что лимит применяется при создании бронирования (вызов в `create_booking_request` и `start_booking`)

**Исправления:**
1. Обновить функцию `check_booking_limit` - считать только бронирования со статусом `approved`
2. Убедиться, что конфиг загружается корректно
3. Добавить явную проверку лимита в UI бота

**Тесты:**
- Создать максимальное количество `approved` бронирований → следующее должно вызывать ошибку
- Бронирования со статусами `pending`, `payment_reported`, `rejected`, `cancelled` не должны учитываться в лимите
- Проверить разные комбинации статусов

### A9.5 [x] Добавить комментарий в отображение таблицы бронирований
Проблема: Поле `comment` не отображается в списке бронирований в админке.

Исправления:
1. Добавить `'comment'` в `list_display` BookingAdmin
2. Возможно добавить усечение длинных комментариев для таблицы
3. Обновить `search_fields` для поиска по комментариям (уже есть)

Тесты:
- Создать бронирование с комментарием → комментарий должен отображаться в списке
- Поиск по комментарию должен работать

### A9.6 [x] Перевести календарь выбора дат на русский язык
Проблема: Календарь aiogram-calendar отображается на английском.

Исправления:
1. Исследовать поддержку локализации в aiogram-calendar
2. Настроить русскую локаль или создать кастомный календарь
3. Обновить `calendar_utils.py` для использования русской локализации

Варианты:
- Использовать `SimpleCalendarRUS` из aiogram-calendar, если доступен
- Создать кастомный календарь с русскими надписями
- Использовать параметр locale в SimpleCalendar

Тесты:
- Календарь должен отображать месяцы и дни недели на русском
- Функциональность выбора даты должна сохраниться

STOP.
