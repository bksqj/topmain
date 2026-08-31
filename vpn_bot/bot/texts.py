"""All user-facing message texts, centralised for easy editing.

Only presentation lives here; no business logic. Functions are used where a
text needs runtime values interpolated.
"""
from __future__ import annotations

# ---- Main menu -----------------------------------------------------------

MAIN_MENU = (
    "<b>🛡 VPN-сервис</b>\n\n"
    "Быстрый и надёжный VPN без ограничений скорости.\n"
    "Выберите раздел ниже, чтобы начать."
)

# ---- Personal cabinet ----------------------------------------------------

CABINET = (
    "<b>👤 Личный кабинет</b>\n\n"
    "Здесь ваша подписка и ключ доступа."
)


def subscription_card(
    plan_title: str,
    limit_gb: float,
    used_gb: float,
    days: int,
    hours: int,
    minutes: int,
) -> str:
    return (
        "<b>📶 Ваша подписка:</b>\n"
        f"├ Тариф: {plan_title}\n"
        f"├ Лимит трафика: {_fmt_num(limit_gb)} ГБ в месяц\n"
        f"├ Использованный трафик: {_fmt_num(used_gb)} ГБ\n"
        f"└ До сброса трафика: {days} дн. {hours} ч. {minutes} мин."
    )


def key_card(subscription_url: str) -> str:
    return (
        "<b>🔑 Ваш ключ:</b>\n\n"
        f"<code>{subscription_url}</code>"
    )


NO_KEY_YET = (
    "<b>🔑 Ключ</b>\n\n"
    "У вас ещё нет активного ключа. Оформите подписку, "
    "чтобы получить доступ 🔓"
)

KEY_COPIED = "📋 Ключ скопирован. Нажмите на текст, чтобы выделить."

LOCATIONS_HEADER = "<b>🌍 Локации:</b>\n\nВыберите сервер для подключения."

LOCATION_SWITCHED = "✅ Локация изменена на: {label}"

REISSUE_CONFIRM = (
    "<b>🔄 Перевыпуск ключа</b>\n\n"
    "Старый ключ перестанет работать. Продолжить?"
)

REISSUE_DONE = "✅ Ключ перевыпущен. Обновите подписку в приложении."

# ---- Purchase flow -------------------------------------------------------

CHOOSE_PLAN = (
    "<b>✨ Выбор тарифа</b>\n\n"
    "Чем длиннее срок — тем выгоднее месяц. Выберите подходящий:"
)

CHOOSE_PAYMENT = (
    "<b>💳 Способ оплаты</b>\n\n"
    "Тариф: <b>{plan_title}</b> — {price} ₽\n"
    "Выберите, как удобнее оплатить:"
)


def payment_created(url: str, price: int) -> str:
    return (
        "<b>💳 Счёт создан</b>\n\n"
        f"К оплате: <b>{price} ₽</b>\n"
        "Нажмите кнопку ниже, чтобы перейти к оплате. "
        "После оплаты ключ придёт автоматически 🔑"
    )


PAYMENT_PENDING = (
    "<b>⏳ Ожидаем оплату…</b>\n\n"
    "Как только платёж пройдёт, я пришлю ваш ключ."
)

PAYMENT_SUCCESS = (
    "<b>✅ Оплата прошла!</b>\n\n"
    "Подписка активирована. Ваш ключ доступа:"
)

# ---- Referral ------------------------------------------------------------

REFERRAL_CONDITIONS = (
    "<blockquote>Приглашайте друзей по вашей ссылке. Когда приглашённый "
    "оплачивает подписку, вы получаете бонус к своей. Отслеживайте "
    "статистику ниже.</blockquote>"
)


def referral_stats(invited: int, paid_count: int, paid_amount: float) -> str:
    return (
        "<b>👥 Реферальная программа</b>\n\n"
        "<b>Статистика:</b>\n"
        f"├ Всего рефералов: {invited}\n"
        f"├ Всего оплат: {paid_count}\n"
        f"└ Сумма оплат: {_fmt_num(paid_amount)} ₽\n\n"
        f"{REFERRAL_CONDITIONS}"
    )


def referral_code(link: str) -> str:
    return (
        "<b>🔗 Ваша реферальная ссылка</b>\n\n"
        f"<code>{link}</code>\n\n"
        "Отправьте её друзьям 👇"
    )


# ---- Help ----------------------------------------------------------------

HELP = (
    "<b>🆘 Помощь</b>\n\n"
    "Инструкции по установке, ответы на вопросы и связь с поддержкой."
)

SETUP_DEVICE = "<b>⚙️ Установка</b>\n\nВыберите Ваш тип устройства:"
SETUP_APP = "<b>⚙️ Установка</b>\n\nВыберите приложение:"


def setup_install(app_name: str, links_block: str) -> str:
    return (
        f"<b>⚙️ Установите приложение «{app_name}»:</b>\n\n"
        f"{links_block}\n\n"
        "Когда установите — нажмите «Далее»."
    )


def setup_import(app_name: str, instructions: str) -> str:
    return (
        f"<b>🔑 Импорт ключа в «{app_name}»</b>\n\n"
        f"{instructions}"
    )


SUPPORT = (
    "<b>💬 Техподдержка</b>\n\n"
    "Есть вопросы или предложения? Напишите сюда: @{support}\n\n"
    "Либо отправьте сообщение прямо здесь — мы передадим его команде."
)

SUPPORT_ASK = (
    "<b>💬 Техподдержка</b>\n\n"
    "Напишите ваше сообщение одним текстом — мы передадим его команде."
)

SUPPORT_SENT = "✅ Сообщение отправлено в поддержку. Мы ответим в ближайшее время."

# ---- About ---------------------------------------------------------------

ABOUT = (
    "<b>ℹ️ О нас</b>\n\n"
    "Мы предоставляем стабильный VPN с широкой географией серверов."
)

RULES = (
    "<b>📄 Правила пользования сервисом</b>\n\n"
    "1. Сервис предназначен для законного использования.\n"
    "2. Запрещено использование для противоправной деятельности.\n"
    "3. Один ключ — для личного использования.\n"
    "4. Администрация вправе ограничить доступ при нарушении правил."
)

REFUND = (
    "<b>📄 Условия возврата</b>\n\n"
    "Возврат средств возможен в течение 3 дней с момента оплаты, "
    "если сервисом фактически не пользовались. Для возврата "
    "обратитесь в техподдержку."
)

TARIFFS_VIEW_HEADER = (
    "<b>🏷️ Тарифы</b>\n\n"
    "Актуальные тарифы сервиса:"
)

# ---- Admin ---------------------------------------------------------------

ADMIN_MENU = "<b>🛠 Админ-панель</b>\n\nВыберите действие:"


def admin_stats(users: int, payments_sum: float) -> str:
    return (
        "<b>📊 Статистика</b>\n\n"
        f"├ Пользователей: {users}\n"
        f"└ Сумма успешных оплат: {_fmt_num(payments_sum)} ₽"
    )


ADMIN_BROADCAST_ASK = (
    "<b>📣 Рассылка</b>\n\nОтправьте текст сообщения для рассылки всем "
    "пользователям."
)


def admin_broadcast_done(sent: int, failed: int) -> str:
    return f"✅ Рассылка завершена. Доставлено: {sent}, ошибок: {failed}."


ADMIN_GRANT_ASK = (
    "<b>🎁 Ручная выдача</b>\n\nОтправьте: <code>telegram_id месяцев</code>\n"
    "Например: <code>123456789 3</code>"
)

ADMIN_GRANT_DONE = "✅ Подписка выдана пользователю {tg_id} на {months} мес."
ADMIN_GRANT_BAD = "❌ Неверный формат. Нужно: telegram_id месяцев"

# ---- Common --------------------------------------------------------------

EXPIRY_REMINDER = (
    "<b>⏰ Напоминание</b>\n\n"
    "Ваша подписка истекает через {days} дн. Продлите, чтобы не "
    "потерять доступ."
)

ERROR_GENERIC = "⚠️ Что-то пошло не так. Попробуйте позже."


def _fmt_num(value: float) -> str:
    """Render a float without a trailing .0 for whole numbers."""
    if value == int(value):
        return str(int(value))
    return f"{value:.2f}".rstrip("0").rstrip(".")
