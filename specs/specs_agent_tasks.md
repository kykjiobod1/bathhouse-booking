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

---

## A0) Repo scaffolding

### A0.1 Создать структуру репозитория
Создай структуру:
- `bathhouse_booking/` (python root)
- `specs/`
  - `mvp_tasks.md`
  - `agent_tasks.md` (этот файл)
- `README.md`
- `.gitignore`
- `.env.example`

STOP.

---

## A1) Django init

### A1.1 Создать Django проект
Внутри `bathhouse_booking/`:
- Django project `config`
- Django app `bookings`
- подключить Django Admin

Проверка:
- `python manage.py runserver`
- `/admin` открывается

STOP.

---

## A2) Dependencies + pytest

### A2.1 Подключить pytest
Добавить:
- pytest
- pytest-django

Сделать:
- базовую конфигурацию pytest
- тест `tests/test_smoke.py` (простой smoke)

Команды проверки:
- `pytest -q`

STOP.

---

## A3) Docker

### A3.1 Dockerfile + docker compose
Добавь:
- `Dockerfile`
- `docker-compose.yml`

Требования:
- команды использовать как `docker compose ...`
- сервисы:
  - `db` (postgres)
  - `web` (django)
- named volume для postgres (например `pgdata`)
- `.env` подхватывается

Проверка:
- `docker compose up --build`

STOP.

---

## A4) Models + invariants (TDD)

### A4.1 Реализовать модели
Модели:
- `Client`: name, phone, telegram_id?, comment?, created_at
- `Bathhouse`: name, capacity?, is_active
- `Booking`: client(FK), bathhouse(FK), start_datetime, end_datetime, status, price_total?, prepayment_amount?, comment?, created_at
- `SystemConfig`: key(unique), value, description?

Status Booking (choices):
- pending
- payment_reported
- approved
- rejected
- cancelled

STOP.

---

### A4.2 Инварианты в Booking.clean (TDD)
Реализовать в `Booking.clean()`:
- `start_datetime < end_datetime`
- запрет пересечения **только для approved**

Тесты:
- invalid range (start >= end) падает
- approved overlap запрещён
- pending overlap допускается
- payment_reported overlap допускается

Важно:
- это нужно для Django Admin: админ не должен сохранить пересечение

Команды проверки:
- `pytest -q`

STOP.

---

## A5) Services (TDD)

### A5.1 Реализовать services.py
Создать `bookings/services.py`:

Функции:
- `create_booking_request(client, bathhouse, start, end, comment=None)`
  - создаёт Booking(status=pending)
- `report_payment(booking)`
  - переводит в `payment_reported`
- `approve_booking(booking)`
  - переводит в `approved` (должно упасть на overlap)
- `reject_booking(booking, reason=None)`
  - переводит в `rejected`

Правила:
- всегда перед `save()` вызывать `full_clean()`

Тесты:
- create_booking_request создаёт pending
- report_payment меняет статус
- approve_booking запрещает overlap

STOP.

---

## A6) Admin

### A6.1 Настроить Django Admin
Зарегистрировать модели.

BookingAdmin:
- `list_display`: bathhouse, client, start_datetime, end_datetime, status, created_at
- `list_filter`: bathhouse, status
- `search_fields`: client__name, client__phone
- `date_hierarchy`: start_datetime
- `ordering`: -start_datetime

STOP.

---

### A6.2 Admin actions approve/reject
Сделать admin actions:
- approve
- reject

Важно:
- actions должны вызывать **services**, а не менять поля напрямую.

STOP.

---

## A7) Telegram bot (aiogram 3)

### A7.1 Структура бота
Создать `bathhouse_booking/bot/`:
- `main.py` — entrypoint
- `routers.py` — сборка routers
- `handlers/` по фичам
- `states.py` — FSM
- `keyboards.py` — inline кнопки

Требования:
- запуск отдельной командой: `python -m bot.main`
- токен берётся из env
- хендлеры не ходят в ORM
- хендлеры вызывают services

STOP.

---

### A7.2 FSM сценарий бронирования (кнопки)
FSM flow:
- /start
- выбрать баню (кнопки)
- выбрать дату (кнопки)
- выбрать интервал (кнопки)
- создать booking (pending)
- показать QR/инструкцию оплаты
- кнопка «Я оплатил» → report_payment

STOP.

---

## A8) Hardening

### A8.1 Ошибки + логи
Добавить базовую обработку ошибок:
- логировать исключения
- пользователю в Telegram выдавать безопасное сообщение

STOP.

