# specs/mvp_tasks.md — Bathhouse Booking (подробный план)

> Этот файл — подробный **план разработки MVP**.
>
> Он нужен человеку: чтобы удерживать решения, качество и последовательность.
>
> Для агента отдельный файл: `specs/agent_tasks.md`.

---

## 0) Цель продукта (MVP)

Система бронирования бань для малого бизнеса, где:
- владелец управляет бронированиями через **Django Admin**
- клиент бронирует через **Telegram bot**
- подтверждение брони — через предоплату (ручная проверка)

### MVP должен уметь
- хранить клиентов/бани/бронирования
- показывать занятость владельцу через админку
- показывать свободные интервалы клиенту в Telegram
- создавать заявку на бронь
- “я оплатил” → сигнал владельцу → апрув → подтверждение клиенту

### Не цель MVP
- автоматическая проверка оплат
- сайт/приложение
- роли пользователей кроме admin
- сложные прайсы/скидки
- публичный API

---

## 1) Принятые решения (фиксируем)

### Архитектура
- **Монолит**: Django + Admin + Telegram bot
- Бизнес-ядро в `bookings/services.py`
- Инварианты данных enforced на уровне модели

### БД
- PostgreSQL
- docker compose
- volume `pgdata`

### Конфиги и прайсы
- Таблица `SystemConfig(key уникальный)`:
  - `SLOT_STEP_MINUTES` (например 30)
  - `MIN_BOOKING_MINUTES` (например 120)
  - `OPEN_HOUR`, `CLOSE_HOUR`
  - `QR_TEXT` / `PAYMENT_INSTRUCTIONS`
  - `PRICE_*` (прайсы)

### Пересечения бронирований (важно)
- пересечения запрещены **только** для `approved`
- `pending/payment_reported/rejected/cancelled` могут пересекаться

### Статусы Booking (утверждено)
- `pending`
- `payment_reported`
- `approved`
- `rejected`
- `cancelled`

### Telegram UX
- только кнопки (inline keyboard)
- FSM сценарий (aiogram 3)

### Тесты
- pytest + pytest-django
- TDD для каждой логической части

---

## 2) Структура репозитория (утверждено)

```
bathhouse-booking/
  bathhouse_booking/          # python root
    manage.py
    config/
    bookings/
    bot/

  specs/
    mvp_tasks.md
    agent_tasks.md

  docker-compose.yml
  Dockerfile
  pyproject.toml
  .env.example
  README.md
```

---

## 3) Качество (Definition of Done)

Пункт считается выполненным, если:
- тесты зелёные (`pytest`)
- код не размазан (бизнес-логика в services)
- в Django Admin можно реально работать
- агент остановился (STOP) и ждёт ревью

---

## 4) Milestones

### M1 — Skeleton
- M1.1 repo scaffolding
- M1.2 Django init

### M2 — Docker
- M2.1 docker compose web+db

### M3 — Domain
- M3.1 models
- M3.2 validations/invariants

### M4 — Services
- M4.1 create/report/approve/reject

### M5 — Admin
- M5.1 lists/filters/search
- M5.2 actions

### M6 — Telegram
- M6.1 bot skeleton
- M6.2 FSM booking flow

### M7 — Hardening
- M7.1 logs + errors
- M7.2 edge cases

---

## 5) Дальнейшее расширение (после MVP)

- Calendar view в Admin (custom view)
- API слой (DRF или Django Ninja) поверх services
- Автоматизация оплат
- Сайт/приложение
