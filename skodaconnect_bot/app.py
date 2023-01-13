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
from core.auth import sc_login

TOKEN = os.getenv('TOKEN')
SETUP, EMAIL, PASSWD = range(3)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Send a welcome message when the command /start is issued"""
    user = update.effective_user
    if context.user_data:
        return ConversationHandler.END

    await update.message.reply_html(
        rf'Привіт {user.full_name}! З моєю допомогою ти можеш отримати багато корисної інфи зі своєї автівки Skoda!' +
        ' Мене лише потрібно синхронізувати із твоїм обліковим записом Skoda Connect, а про все решта я подбаю! 💚' +
        ' Щоб розпочати налаштування, відправ мені команду /setup'
    )

    return ConversationHandler.END


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /help is issued."""
    await update.message.reply_text("От халепа ☹️, мій розробник ще на написав детальну інструкцію з описом всіх команд :( "
                                    "Він вже працює над цим!")


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancels and ends the conversation."""
    await update.message.reply_text(
        "Йолкі-палки! Ти перервав процес налаштування, доведеться починати з початку! 🫣 "
    )

    return ConversationHandler.END


async def setup(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Starting point to setup Skoda Connect account synchronization."""
    if context.user_data:
        await update.message.reply_text(
            rf'Схоже, що твій акаунт вже налаштовано'
        )
        return ConversationHandler.END

    await update.message.reply_text(
        rf'📧 Відправ мені свою електронну адресу, асоційовану з акаунтом у Skoda Connect'
    )
    return EMAIL


async def email(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Get email from user to authorize in Skoda Connect."""
    text = update.message.text
    context.user_data["email"] = text
    await update.message.reply_text(f'🔑 Тепер відправ мені пароль')

    return PASSWD


async def passwd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Get password from user to authorize in Skoda Connect"""
    text = update.message.text
    context.user_data["password"] = text
    await update.message.reply_text(f'🔄 Авторизуюсь у Skoda Connect...')

    # show user data
    user_data = context.user_data

    login_result = await sc_login(user_data.get('email'), user_data.get('password'))
    if login_result:
        await update.message.reply_text(f'✅ Авторизація успішна! Я отримав дані про твій автомобіль 🏎,'
                                        f' тож тепер усе що потрібно, питай у мене 😉')
    else:
        await update.message.reply_text(f'❌ На жаль, щось пішло не так, авторизація не успішна!')

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