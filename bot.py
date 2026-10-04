import os
import tempfile
import yt_dlp

from dotenv import load_dotenv
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)

load_dotenv()

TOKEN = os.getenv("BOT_TOKEN")

# Majburiy obuna kanali
CHANNEL = "@Sobrallyv"


async def check_subscription(user_id, context):
    try:
        member = await context.bot.get_chat_member(
            chat_id=CHANNEL,
            user_id=user_id
        )

        return member.status in ["member", "administrator", "creator"]

    except Exception as e:
        print("OBUNA TEKSHIRISH XATOSI:", e)
        return False


def subscription_keyboard():
    keyboard = [
        [
            InlineKeyboardButton(
               InlineKeyboardButton(
    "📢 Kanalga obuna bo‘lish",
    url="https://t.me/Sobrallyv"
)
            )
        ],
        [
            InlineKeyboardButton(
                "✅ Obunani tekshirish",
                callback_data="check_subscription"
            )
        ]
    ]

    return InlineKeyboardMarkup(keyboard)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.effective_user.id

    subscribed = await check_subscription(
        user_id,
        context
    )

    if not subscribed:
        await update.message.reply_text(
            "🔒 Botdan foydalanish uchun avval kanalimizga obuna bo‘ling!\n\n"
            "1️⃣ Kanalga obuna bo‘ling\n"
            "2️⃣ «✅ Obunani tekshirish» tugmasini bosing",
            reply_markup=subscription_keyboard()
        )
        return

    await update.message.reply_text(
        "👋 Salom!\n\n"
        "✅ Obuna tasdiqlandi.\n\n"
        "📸 Instagram linkini yuboring."
    )


async def subscription_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query

    await query.answer()

    user_id = query.from_user.id

    subscribed = await check_subscription(
        user_id,
        context
    )

    if subscribed:
        await query.edit_message_text(
            "✅ Obuna tasdiqlandi!\n\n"
            "📸 Endi Instagram linkini yuborishingiz mumkin."
        )
    else:
        await query.answer(
            "❌ Siz hali kanalga obuna bo‘lmagansiz!",
            show_alert=True
        )


async def handle_message(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    user_id = update.effective_user.id

    # Har bir linkdan oldin obunani tekshirish
    subscribed = await check_subscription(
        user_id,
        context
    )

    if not subscribed:
        await update.message.reply_text(
            "🔒 Avval kanalga obuna bo‘ling!",
            reply_markup=subscription_keyboard()
        )
        return

    url = update.message.text.strip()

    if "instagram.com" not in url:
        await update.message.reply_text(
            "❗ Instagram link yuboring."
        )
        return

    msg = await update.message.reply_text(
        "⏳ Media olinmoqda..."
    )

    try:
        with tempfile.TemporaryDirectory() as folder:

            output = os.path.join(
                folder,
                "media.%(ext)s"
            )

            options = {
                "outtmpl": output,
                "noplaylist": True,
                "quiet": True,
            }

            with yt_dlp.YoutubeDL(options) as ydl:
                info = ydl.extract_info(
                    url,
                    download=True
                )

                filename = ydl.prepare_filename(info)

            await msg.edit_text(
                "📤 Telegram'ga yuborilmoqda..."
            )

            ext = os.path.splitext(
                filename
            )[1].lower()

            if ext in [
                ".jpg",
                ".jpeg",
                ".png",
                ".webp"
            ]:

                with open(filename, "rb") as photo:

                    await update.message.reply_photo(
                        photo=photo,
                        caption="🖼️ Rasm tayyor!"
                    )

            else:

                with open(filename, "rb") as video:

                    await update.message.reply_video(
                        video=video,
                        caption="🎬 Video tayyor!"
                    )

            await msg.delete()

    except Exception as e:

        print("XATO:", e)

        await msg.edit_text(
            "❌ Media olishda xatolik yuz berdi.\n"
            "Boshqa Instagram link bilan sinab ko‘ring."
        )


def main():

    if not TOKEN:
        print("❌ BOT_TOKEN topilmadi!")
        return

    app = Application.builder().token(TOKEN).build()

    app.add_handler(
        CommandHandler(
            "start",
            start
        )
    )

    app.add_handler(
        CallbackQueryHandler(
            subscription_callback,
            pattern="^check_subscription$"
        )
    )

    app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            handle_message
        )
    )

    print("🤖 Bot ishga tushdi!")

    app.run_polling()


if __name__ == "__main__":
    main()