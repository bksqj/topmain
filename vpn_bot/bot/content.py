"""Data catalog for the setup wizard and FAQ (kept separate from logic)."""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class AppClient:
    key: str
    name: str
    emoji: str
    # HTML link block shown on the "install" step
    links: str
    # instructions shown on the "import key" step
    import_instructions: str


# Device type -> list of clients
SETUP_APPS: dict[str, list[AppClient]] = {
    "phone": [
        AppClient(
            key="v2rayng",
            name="v2rayNG",
            emoji="🟢",
            links=(
                '• <a href="https://play.google.com/store/apps/details?id=com.v2ray.ang">Google Play</a>\n'
                '• <a href="https://github.com/2dust/v2rayNG/releases">APK (GitHub)</a>'
            ),
            import_instructions=(
                "1. Откройте v2rayNG.\n"
                "2. Нажмите «+» → «Импорт из буфера обмена» или по ссылке подписки.\n"
                "3. Вставьте ваш ключ и сохраните.\n"
                "4. Выберите профиль и нажмите кнопку подключения."
            ),
        ),
        AppClient(
            key="happ",
            name="Happ",
            emoji="🟣",
            links=(
                '• <a href="https://apps.apple.com/app/happ-proxy-utility/id6504287215">App Store</a>\n'
                '• <a href="https://apps.apple.com/ru/app/happ-proxy-utility/id6504287215">App Store (РФ)</a>'
            ),
            import_instructions=(
                "1. Откройте Happ.\n"
                "2. Нажмите «Добавить» → «Из буфера обмена».\n"
                "3. Вставьте ключ подписки.\n"
                "4. Включите подключение переключателем."
            ),
        ),
    ],
    "pc": [
        AppClient(
            key="v2rayn",
            name="v2rayN",
            emoji="🟢",
            links=(
                '• <a href="https://github.com/2dust/v2rayN/releases">Windows (GitHub)</a>'
            ),
            import_instructions=(
                "1. Откройте v2rayN.\n"
                "2. Серверы → «Импорт из буфера обмена».\n"
                "3. Вставьте ссылку подписки и обновите.\n"
                "4. Выберите сервер и включите системный прокси."
            ),
        ),
        AppClient(
            key="nekoray",
            name="NekoRay",
            emoji="🟣",
            links=(
                '• <a href="https://github.com/MatsuriDayo/nekoray/releases">Windows / Linux (GitHub)</a>'
            ),
            import_instructions=(
                "1. Откройте NekoRay.\n"
                "2. Program → Add profile from clipboard.\n"
                "3. Вставьте ключ и сохраните.\n"
                "4. Включите режим Tun и запустите профиль."
            ),
        ),
    ],
}

DEVICE_TYPES = {
    "phone": "📱 Телефон",
    "pc": "💻 Компьютер",
}


def get_app(device: str, app_key: str) -> AppClient | None:
    for app in SETUP_APPS.get(device, []):
        if app.key == app_key:
            return app
    return None


# ---- FAQ -----------------------------------------------------------------

@dataclass(frozen=True)
class FaqItem:
    key: str
    title: str
    answer: str


FAQ_ITEMS: list[FaqItem] = [
    FaqItem(
        "app_errors",
        "Ошибки приложения",
        "<b>❓ Ошибки приложения</b>\n\nЕсли приложение не подключается: "
        "обновите подписку, проверьте интернет и попробуйте другую локацию. "
        "Переустановка приложения также помогает.",
    ),
    FaqItem(
        "locations",
        "Локации",
        "<b>❓ Локации</b>\n\nВы можете переключаться между серверами в разделе "
        "«Ключ» → «Локации». Ближайшие серверы обычно быстрее.",
    ),
    FaqItem(
        "subscription",
        "Подписка",
        "<b>❓ Подписка</b>\n\nСтатус, лимит и срок действия видны в разделе "
        "«Личный кабинет» → «Подписка». Там же можно продлить.",
    ),
    FaqItem(
        "traffic",
        "Лимит трафика",
        "<b>❓ Лимит трафика</b>\n\nЛимит указан в вашем тарифе и сбрасывается "
        "ежемесячно. При исчерпании смените тариф или дождитесь сброса.",
    ),
    FaqItem(
        "key",
        "Ключ",
        "<b>❓ Ключ</b>\n\nКлюч — это ссылка подписки. Скопируйте её или "
        "отсканируйте QR-код и импортируйте в приложение.",
    ),
    FaqItem(
        "tariffs",
        "Тарифы",
        "<b>❓ Тарифы</b>\n\nДоступны тарифы на 1, 3, 6 и 12 месяцев. "
        "Чем длиннее срок — тем выгоднее.",
    ),
    FaqItem(
        "referral",
        "Реферальная программа",
        "<b>❓ Реферальная программа</b>\n\nПриглашайте друзей по вашей ссылке "
        "и получайте бонусы, когда они оплачивают подписку.",
    ),
]

FAQ_BY_KEY: dict[str, FaqItem] = {item.key: item for item in FAQ_ITEMS}
