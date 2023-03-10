import os

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    ConversationHandler,
    CallbackQueryHandler,
    filters
)
from core.connect_service import SkodaConnectService
from menu import (
    garage_menu, vehicle_menu, garage_menu_keyboard, vehicle_menu_keyboard
)

TOKEN = os.getenv('TOKEN')
SETUP, EMAIL, PASSWD = range(3)
VEHICLE_SELECTION = range(1)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    '''Send a welcome message when the command /start is issued'''
    user = update.effective_user
    if context.user_data:
        return ConversationHandler.END

    await update.message.reply_html(
        f'Привіт, {user.full_name}! \n'
        f'З моєю допомогою ти можеш керувати своєю автівкою Skoda! \n'
        '\n'
        'Мене лише потрібно синхронізувати із твоїм обліковим записом Skoda Connect, а про все інше я подбаю! 💚\n'
        '\n'
        'Щоб розпочати налаштування, відправ мені команду /setup'
    )

    return ConversationHandler.END


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    '''Send a message when the command /help is issued.'''
    await update.message.reply_text('От халепа ☹️, мій розробник ще на написав детальну інструкцію з описом всіх команд :( '
                                    'Він вже працює над цим!')


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    '''Cancels and ends the conversation.'''
    await update.message.reply_text(
        'Йолкі-палки! Ти перервав процес налаштування, доведеться починати з початку! 🫣 '
    )

    return ConversationHandler.END


async def garage(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    '''Select vehicle to manage'''
    connection = context.user_data.get('connection', None)

    if connection is None:
        await update.message.reply_text(
            'От хулєра! Твій гараж пустий, можливо ти не авторизувався, або у тебе немає жодного авто ☹️'
        )
    else:
        await update.message.reply_text('Ось які авто є в твоєму гаражі:', reply_markup=garage_menu_keyboard(connection))


async def vehicle(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    '''Select vehicle to manage'''
    connection = context.user_data.get('connection', None)
    selected_vehicle = context.user_data.get('selected_vehicle', None)

    if not all([connection, selected_vehicle]):
        await update.message.reply_text(
            'Агов, не так швидко! Спочатку обери автівку в гаражі 🏠'
        )
        return ConversationHandler.END

    await update.message.reply_text('Обирай команду для свого авто:', reply_markup=vehicle_menu_keyboard(connection))


async def setup(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    '''Starting point to setup Skoda Connect account synchronization.'''
    if context.user_data:
        await update.message.reply_text(
            rf'Схоже, що твій акаунт вже налаштовано'
        )
        return ConversationHandler.END

    await update.message.reply_text(
        rf'📧 Відправ мені свою електронну адресу, асоційовану з акаунтом у сервісі Skoda Connect'
    )
    return EMAIL


async def email(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    '''Get email from user to authorize in Skoda Connect service.'''
    text = update.message.text
    context.user_data['email'] = text
    await update.message.reply_text(f'🔑 Тепер відправ мені пароль')

    return PASSWD


async def passwd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    '''Get password from user to authorize in Skoda Connect service'''
    text = update.message.text
    context.user_data['password'] = text
    await update.message.reply_text(f'🔄 Авторизуюсь у сервісі Skoda Connect...')

    # show user data
    user_data = context.user_data

    conn_service = SkodaConnectService(user_data.get('email'), user_data.get('password'))
    await conn_service.session_init()
    # connection instance
    connection = conn_service.get_connection_instance()

    if connection is not None:
        await update.message.reply_text(f'✅ Авторизація успішна! Отримую дані про твої авто... 🚗 ')
        await conn_service.retrieve_vehicles()

        if len(connection.vehicles) < 1:
            await update.message.reply_text(f'Не знайшов жодної автівки у твоєму гаражі 🤷‍♂️')
        else:
            await update.message.reply_text(f'Знайшов {len(connection.vehicles)} авто в твоєму гаражі \n'
                                            f'Відправ /garage щоб перейти у гараж і обрати авто')

            context.user_data['connection'] = conn_service
            return ConversationHandler.END
    else:
        await update.message.reply_text(f'❌ На жаль, щось пішло не так, авторизація не успішна!')

    return ConversationHandler.END


if __name__ == '__main__':
    application = Application.builder().token(TOKEN).build()
    application.add_handler(CommandHandler('start', start))

    credentials_handler = ConversationHandler(
        entry_points=[CommandHandler('setup', setup)],
        states={
            EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, email)],
            PASSWD: [MessageHandler(filters.TEXT & ~filters.COMMAND, passwd)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )
    application.add_handler(CommandHandler('help', help_command))
    application.add_handler(CommandHandler('garage', garage))
    application.add_handler(CallbackQueryHandler(garage_menu))
    application.add_handler(CommandHandler('commands', vehicle))
    application.add_handler(CallbackQueryHandler(vehicle_menu))
    application.add_handler(credentials_handler)
    application.run_polling()