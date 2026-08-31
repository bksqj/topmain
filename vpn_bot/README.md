# VPN Subscription Telegram Bot

Telegram-бот для продажи VPN-подписок на базе **aiogram 3.x**, **Marzban**,
**ЮKassa** и **SQLite (async SQLAlchemy)**. Весь интерфейс построен на
инлайн-клавиатурах и работает как «экран»: каждое действие редактирует
предыдущее сообщение.

## Возможности

- **Главное меню**: Личный кабинет, Реферальная программа, Помощь, О нас
- **Личный кабинет**
  - 📶 Подписка — карточка статуса (тариф, лимит и остаток трафика, время до сброса), покупка/продление
  - 🔑 Ключ — `subscription_url` из Marzban, копирование, QR-код, перевыпуск, выбор локации
  - 🌍 Локации — пагинированный список серверов, переключение нод в Marzban
- **Покупка**: выбор тарифа (1/3/6/12 мес с % экономии) → способ оплаты (ЮKassa/СБП) → счёт → вебхук → автосоздание/продление в Marzban
- **Реферальная программа**: статистика + персональная deep-link `?start=ref_<id>`
- **Помощь**: пошаговый мастер установки (FSM), FAQ (пагинация), техподдержка (пересылка админам)
- **О нас**: правила, условия возврата, локации, тарифы (только просмотр)
- **Админка** (whitelist по ID): статистика, ручная выдача, рассылка
- **Планировщик** (APScheduler): напоминания за 3 и 1 день до истечения подписки

## Структура

```
bot/
├── main.py              # запуск: polling + FastAPI webhook + scheduler
├── config.py            # настройки из окружения (pydantic-settings)
├── plans.py             # каталог тарифов
├── locations.py         # каталог локаций (fallback)
├── texts.py             # все тексты сообщений
├── content.py           # контент мастера установки и FAQ
├── states.py            # FSM StatesGroup
├── callbacks.py         # типизированные CallbackData
├── middlewares.py       # инъекция async-сессии БД
├── utils.py             # edit_screen, форматирование времени
├── db/                  # models, engine, repo
├── keyboards/           # inline-клавиатуры + пагинация
├── services/            # marzban, payments (ЮKassa), qr, provisioning, orders, scheduler
├── handlers/            # start, cabinet, payment, referral, help, about, admin
└── webhook/app.py       # FastAPI /webhook/yookassa
```

## Запуск

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # заполните токены и ключи
python -m bot.main
```

Бот запускает одновременно long-polling, HTTP-сервер вебхуков
(`/webhook/yookassa`, `/health`) и планировщик напоминаний.

## Заметки

- Без настроенных `MARZBAN_*` провижининг работает в demo-режиме (только БД),
  без `YOOKASSA_*` создаётся заглушечный платёж — бот остаётся запускаемым для
  локальной проверки интерфейса.
- Вебхук ЮKassa проверяет источник по официальному списку IP-сетей ЮKassa
  (или по общему секрету `YOOKASSA_WEBHOOK_SECRET` в заголовке
  `X-Webhook-Secret`).
- Тексты вынесены в `texts.py` и `content.py` — редактируются без изменения логики.
