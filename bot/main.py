"""
AROUND THE MAIN — Interactive Telegram Bot

This bot is intentionally separate from the publication pipeline.
The existing v6 Telegram publisher continues to handle outbound
edition delivery. This service handles inbound user interactions:
- /start
- language selection
- channel link
- subscription verification
- /help
- /language
- /channel

Secrets are supplied through environment variables.
"""

from __future__ import annotations

import logging
import os

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.constants import ChatMemberStatus
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
)

LOG = logging.getLogger("around_the_main_bot")

BOT_TOKEN_ENV = "TELEGRAM_BOT_TOKEN"
CHANNEL_USERNAME_ENV = "AROUND_THE_MAIN_CHANNEL_USERNAME"
CHANNEL_URL_ENV = "AROUND_THE_MAIN_CHANNEL_URL"

CHANNEL_USERNAME = os.getenv(
    CHANNEL_USERNAME_ENV,
    "@aroundthemain",
).strip()

CHANNEL_URL = os.getenv(
    CHANNEL_URL_ENV,
    "https://t.me/aroundthemain",
).strip()

WELCOME_TEXTS = {
    "en": (
        "🌍 <b>AROUND THE MAIN</b>\n\n"
        "Global News | Minimum text | Maximum meaning.\n\n"
        "Three editions every day:\n"
        "07:00 — Morning Briefing\n"
        "13:00 — Midday Update\n"
        "20:00 — Evening Round-up"
    ),
    "ru": (
        "🌍 <b>AROUND THE MAIN</b>\n\n"
        "Мировые новости | Минимум текста | Максимум смысла.\n\n"
        "Три выпуска каждый день:\n"
        "07:00 — Morning Briefing\n"
        "13:00 — Midday Update\n"
        "20:00 — Evening Round-up"
    ),
    "es": (
        "🌍 <b>AROUND THE MAIN</b>\n\n"
        "Noticias globales | Mínimo texto | Máximo significado.\n\n"
        "Tres ediciones cada día:\n"
        "07:00 — Morning Briefing\n"
        "13:00 — Midday Update\n"
        "20:00 — Evening Round-up"
    ),
    "hi": (
        "🌍 <b>AROUND THE MAIN</b>\n\n"
        "वैश्विक समाचार | कम शब्द | अधिक अर्थ।\n\n"
        "हर दिन तीन संस्करण:\n"
        "07:00 — Morning Briefing\n"
        "13:00 — Midday Update\n"
        "20:00 — Evening Round-up"
    ),
    "ar": (
        "🌍 <b>AROUND THE MAIN</b>\n\n"
        "أخبار عالمية | أقل نص | أقصى معنى.\n\n"
        "ثلاثة إصدارات يوميًا:\n"
        "07:00 — Morning Briefing\n"
        "13:00 — Midday Update\n"
        "20:00 — Evening Round-up"
    ),
    "zh": (
        "🌍 <b>AROUND THE MAIN</b>\n\n"
        "全球新闻｜最少文字｜最大信息量。\n\n"
        "每天三个版本：\n"
        "07:00 — Morning Briefing\n"
        "13:00 — Midday Update\n"
        "20:00 — Evening Round-up"
    ),
    "fr": (
        "🌍 <b>AROUND THE MAIN</b>\n\n"
        "Actualités mondiales | Minimum de texte | Maximum de sens.\n\n"
        "Trois éditions chaque jour :\n"
        "07:00 — Morning Briefing\n"
        "13:00 — Midday Update\n"
        "20:00 — Evening Round-up"
    ),
}

SUBSCRIBED_TEXTS = {
    "en": "✅ Subscription confirmed. Welcome to AROUND THE MAIN.",
    "ru": "✅ Подписка подтверждена. Добро пожаловать в AROUND THE MAIN.",
    "es": "✅ Suscripción confirmada. Bienvenido a AROUND THE MAIN.",
    "hi": "✅ सदस्यता की पुष्टि हो गई। AROUND THE MAIN में आपका स्वागत है।",
    "ar": "✅ تم تأكيد الاشتراك. أهلاً بك في AROUND THE MAIN.",
    "zh": "✅ 已确认订阅。欢迎加入 AROUND THE MAIN。",
    "fr": "✅ Abonnement confirmé. Bienvenue sur AROUND THE MAIN.",
}

NOT_SUBSCRIBED_TEXTS = {
    "en": "You are not subscribed yet. Join the channel and then press the check button.",
    "ru": "Вы ещё не подписаны. Подпишитесь на канал, затем нажмите кнопку проверки.",
    "es": "Aún no estás suscrito. Únete al canal y pulsa el botón de verificación.",
    "hi": "आपने अभी सदस्यता नहीं ली है। चैनल से जुड़ें और फिर जाँच बटन दबाएँ।",
    "ar": "لم تشترك بعد. انضم إلى القناة ثم اضغط زر التحقق.",
    "zh": "您尚未订阅。请先加入频道，然后点击检查按钮。",
    "fr": "Vous n’êtes pas encore abonné. Rejoignez le canal puis appuyez sur le bouton de vérification.",
}

LANGUAGE_NAMES = {
    "en": "🇬🇧 English",
    "ru": "🇷🇺 Русский",
    "es": "🇪🇸 Español",
    "hi": "🇮🇳 हिन्दी",
    "ar": "🇸🇦 العربية",
    "zh": "🇨🇳 中文",
    "fr": "🇫🇷 Français",
}


def language_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("🇬🇧 English", callback_data="lang_en"),
                InlineKeyboardButton("🇷🇺 Русский", callback_data="lang_ru"),
            ],
            [
                InlineKeyboardButton("🇪🇸 Español", callback_data="lang_es"),
                InlineKeyboardButton("🇮🇳 हिन्दी", callback_data="lang_hi"),
            ],
            [
                InlineKeyboardButton("🇸🇦 العربية", callback_data="lang_ar"),
                InlineKeyboardButton("🇨🇳 中文", callback_data="lang_zh"),
            ],
            [
                InlineKeyboardButton("🇫🇷 Français", callback_data="lang_fr"),
            ],
        ]
    )


def channel_keyboard(language: str) -> InlineKeyboardMarkup:
    join_label = {
        "en": "🌍 Join AROUND THE MAIN",
        "ru": "🌍 Подписаться на AROUND THE MAIN",
        "es": "🌍 Unirse a AROUND THE MAIN",
        "hi": "🌍 AROUND THE MAIN से जुड़ें",
        "ar": "🌍 انضم إلى AROUND THE MAIN",
        "zh": "🌍 加入 AROUND THE MAIN",
        "fr": "🌍 Rejoindre AROUND THE MAIN",
    }.get(language, "🌍 Join AROUND THE MAIN")

    check_label = {
        "en": "✅ Check subscription",
        "ru": "✅ Проверить подписку",
        "es": "✅ Comprobar suscripción",
        "hi": "✅ सदस्यता जाँचें",
        "ar": "✅ التحقق من الاشتراك",
        "zh": "✅ 检查订阅",
        "fr": "✅ Vérifier l’abonnement",
    }.get(language, "✅ Check subscription")

    language_label = {
        "en": "🌐 Language",
        "ru": "🌐 Язык",
        "es": "🌐 Idioma",
        "hi": "🌐 भाषा",
        "ar": "🌐 اللغة",
        "zh": "🌐 语言",
        "fr": "🌐 Langue",
    }.get(language, "🌐 Language")

    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton(join_label, url=CHANNEL_URL)],
            [InlineKeyboardButton(check_label, callback_data="check_subscription")],
            [InlineKeyboardButton(language_label, callback_data="choose_language")],
        ]
    )


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /start and show the language selector immediately."""
    if update.message is None:
        return

    # Keep this ready for future referral links such as /start ref_ABC123.
    context.user_data["start_parameter"] = (
        context.args[0] if context.args else None
    )

    await update.message.reply_text(
        "🌍 <b>AROUND THE MAIN</b>\n\n"
        "<b>Choose your language / Выберите язык:</b>",
        reply_markup=language_keyboard(),
        parse_mode="HTML",
    )


async def language_selected(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """Save the selected language and show channel actions."""
    query = update.callback_query
    if query is None:
        return

    await query.answer()

    language = query.data.removeprefix("lang_")
    if language not in WELCOME_TEXTS:
        language = "en"

    context.user_data["language"] = language

    await query.edit_message_text(
        WELCOME_TEXTS[language],
        reply_markup=channel_keyboard(language),
        parse_mode="HTML",
    )


async def choose_language(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """Return to the language selector."""
    query = update.callback_query
    if query is None:
        return

    await query.answer()
    await query.edit_message_text(
        "🌍 <b>AROUND THE MAIN</b>\n\n"
        "<b>Choose your language / Выберите язык:</b>",
        reply_markup=language_keyboard(),
        parse_mode="HTML",
    )


async def check_subscription(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """Verify whether the user is a member of the public channel."""
    query = update.callback_query
    if query is None:
        return

    await query.answer()

    language = context.user_data.get("language", "en")
    user_id = query.from_user.id

    try:
        member = await context.bot.get_chat_member(
            chat_id=CHANNEL_USERNAME,
            user_id=user_id,
        )

        subscribed = member.status in {
            ChatMemberStatus.MEMBER,
            ChatMemberStatus.ADMINISTRATOR,
            ChatMemberStatus.OWNER,
        }

        # A restricted member can still be a channel member.
        if member.status == ChatMemberStatus.RESTRICTED:
            subscribed = bool(getattr(member, "is_member", False))

        if subscribed:
            await query.edit_message_text(
                SUBSCRIBED_TEXTS.get(language, SUBSCRIBED_TEXTS["en"]),
                reply_markup=channel_keyboard(language),
            )
            return

        await query.edit_message_text(
            NOT_SUBSCRIBED_TEXTS.get(
                language,
                NOT_SUBSCRIBED_TEXTS["en"],
            ),
            reply_markup=channel_keyboard(language),
        )

    except Exception:
        LOG.exception("Subscription check failed for user %s", user_id)
        await query.answer(
            "⚠️ Unable to verify subscription right now.",
            show_alert=True,
        )


async def help_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    language = context.user_data.get("language", "en")

    texts = {
        "en": (
            "ℹ️ <b>AROUND THE MAIN</b>\n\n"
            "/start — start the bot\n"
            "/language — change language\n"
            "/channel — open the channel\n"
            "/help — show this help"
        ),
        "ru": (
            "ℹ️ <b>AROUND THE MAIN</b>\n\n"
            "/start — запустить бота\n"
            "/language — изменить язык\n"
            "/channel — открыть канал\n"
            "/help — эта справка"
        ),
    }

    text = texts.get(language, texts["en"])
    await update.message.reply_text(
        text,
        reply_markup=channel_keyboard(language),
        parse_mode="HTML",
    )


async def language_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    await update.message.reply_text(
        "🌐 <b>Choose your language / Выберите язык:</b>",
        reply_markup=language_keyboard(),
        parse_mode="HTML",
    )


async def channel_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    await update.message.reply_text(
        f"🌍 <b>AROUND THE MAIN</b>\n{CHANNEL_URL}",
        parse_mode="HTML",
    )


async def error_handler(
    update: object,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    LOG.exception(
        "Unhandled Telegram update error",
        exc_info=context.error,
    )


def main() -> None:
    token = os.getenv(BOT_TOKEN_ENV, "").strip()

    if not token:
        raise RuntimeError(
            f"{BOT_TOKEN_ENV} is not set"
        )

    logging.basicConfig(
        level=os.getenv("LOG_LEVEL", "INFO").upper(),
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )

    app = Application.builder().token(token).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("language", language_command))
    app.add_handler(CommandHandler("channel", channel_command))

    app.add_handler(
        CallbackQueryHandler(
            language_selected,
            pattern=r"^lang_[a-z]{2}$",
        )
    )
    app.add_handler(
        CallbackQueryHandler(
            choose_language,
            pattern=r"^choose_language$",
        )
    )
    app.add_handler(
        CallbackQueryHandler(
            check_subscription,
            pattern=r"^check_subscription$",
        )
    )

    app.add_error_handler(error_handler)

    LOG.info(
        "AROUND THE MAIN bot started; channel=%s",
        CHANNEL_USERNAME,
    )

    app.run_polling(
        allowed_updates=Update.ALL_TYPES,
    )


if __name__ == "__main__":
    main()
