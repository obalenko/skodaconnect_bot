import os
from typing import Dict

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    ConversationHandler,
    filters
)

TOKEN = os.getenv('TOKEN')
SETUP, EMAIL, PASSWD = range(3)


def data_to_str(user_data: Dict[str, str]) -> str:
    """Helper function for formatting the gathered user info."""
    data = [f"{key} - {value}" for key, value in user_data.items()]
    return "\n".join(data).join(["\n", "\n"])


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Send a welcome message when the command /start is issued"""
    user = update.effective_user
    if context.user_data:
        return ConversationHandler.END

    await update.message.reply_html(
        rf'Привіт {user.full_name}! Я знаю все про твій автомобіль Skoda!' +
        ' Просто обери, про що б ти хотів(ла) дізнатись, а я про все подбаю!' +
        ' Щоб я міг спілкуватись з тобою і твоїм авто, потрібно налаштувати твій існуючий акаунт SkodaConnect' +
        ' Для цього надішли мені команду /setup'
    )

    return ConversationHandler.END


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /help is issued."""
    await update.message.reply_text("От халепа ☹️, мій розробник ще на написав детальну інструкцію з описом всіх команд :( "
                                    "Обіцяю виправити це якнайшвидше ")


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancels and ends the conversation."""
    await update.message.reply_text(
        "Бувай!👋 Буду радий поспілкуватись ще у будь-який час!"
    )

    return ConversationHandler.END


async def setup(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Starting point to setup Skoda Connect account synchronization."""
    if context.user_data:
        await update.message.reply_text(
            rf'Схоже, твій акаунт вже налаштовано.'
        )
        return ConversationHandler.END

    await update.message.reply_text(
        rf'Давай налаштуємо твій акаунт. Спочатку відправ мені свою електронну адресу, на яку ти зареєстрований у SkodaConnect'
    )
    return EMAIL


async def email(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Get email from user to authorize in SkodaConnect."""
    text = update.message.text
    context.user_data["email"] = text
    await update.message.reply_text(f'Тепер відправ мені пароль')

    return PASSWD


async def passwd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Get password from user to authorize in SkodaConnect"""
    text = update.message.text
    context.user_data["password"] = text
    await update.message.reply_text(f'Чудово, налаштування завершено. Я отримав дані про твій автомобіль 🏎,'
                                    f' тож тепер усе що потрібно, питай у мене 😉')

    # show user data
    user_data = context.user_data
    await update.message.reply_text(data_to_str(user_data))

    return ConversationHandler.END


if __name__ == '__main__':
    application = Application.builder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))

    credentials_handler = ConversationHandler(
        entry_points=[CommandHandler("setup", setup)],
        states={
            EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, email)],
            PASSWD: [MessageHandler(filters.TEXT & ~filters.COMMAND, passwd)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(credentials_handler)
    application.run_polling()