import os
import re
import requests
import telegram
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ConversationHandler, MessageHandler, filters
from core.connect_service import SkodaConnectService, get_vehicle_base_info


TOKEN = os.getenv('TOKEN')
CLIENT_ID = 'YOUR_CLIENT_ID'
CLIENT_SECRET = 'YOUR_CLIENT_SECRET'
REDIRECT_URI = 'YOUR_REDIRECT_URI'

# Conversation states
EMAIL, PASSWD, CAR_SELECTION, ACTION_SELECTION = range(4)


def vehicle_info_normalization(vehicle):
    vehicle_info = get_vehicle_base_info(vehicle)
    vehicle_name = f'{vehicle_info["model"]} ' \
                   f'{vehicle_info["manufactured"][0:4]} ' \
                   f'{vehicle_info["engine_capacity"]} ' \
                   f'{vehicle_info["engine_type"]}'
    return vehicle_name


def validate_email(email):
    return bool(re.match(r"[^@]+@[^@]+\.[^@]+", email))


async def start(update, context):
    # authorization_url = get_authorization_url()
    user = update.effective_user

    if context.user_data:
        return ConversationHandler.END
    await update.message.reply_html(
        f'Привіт, {user.full_name}! \n'
        f'З моєю допомогою ти можеш керувати своєю автівкою Skoda! \n'
        '\n'
        'Мене лише потрібно синхронізувати із твоїм обліковим записом Skoda Connect, а про все інше я подбаю! 💚\n'
        '\n'
    )
    await update.message.reply_text(
        rf'📧 Відправ мені свою електронну адресу, асоційовану з акаунтом у сервісі Skoda Connect'
    )

    return EMAIL


async def email(update, context) -> int:
    '''Get email from user to authorize in Skoda Connect service.'''
    chat_id = update.message.chat_id
    text = update.message.text

    if not validate_email(text):
        await context.bot.send_message(chat_id=chat_id, text='Напиши будь ласка коректну електронну адресу!')
        return EMAIL

    context.user_data['email'] = text
    await update.message.reply_text(f'🔑 Тепер відправ мені пароль')

    return PASSWD


async def passwd(update, context) -> int:
    '''Get password from user to authorize in Skoda Connect service'''
    text = update.message.text
    context.user_data['password'] = text
    await update.message.reply_text(f'🔄 Авторизуюсь у сервісі Skoda Connect...')
    user_data = context.user_data

    conn_service = SkodaConnectService(user_data.get('email'), user_data.get('password'))
    await conn_service.session_init()
    # connection instance
    connection = conn_service.get_connection_instance()

    if conn_service is not None:
        await update.message.reply_text(f'✅ Авторизація успішна! Отримую дані про твої авто... 🚗 ')
        await conn_service.retrieve_vehicles()

        if len(conn_service.vehicles) < 1:
            await update.message.reply_text(f'Не знайшов жодної автівки у твоєму гаражі 🤷‍♂️')
        else:
            await update.message.reply_text(f'Знайшов {len(connection.vehicles)} авто в твоєму гаражі \n')

            context.user_data['connection'] = connection
    else:
        await update.message.reply_text(f'Упс, щось пішло не так :( Авторизація не успішна, спробуй знову.')
        return ConversationHandler.END

    context.user_data['cars'] = [vehicle_info_normalization(x) for x in connection.vehicles]
    context.user_data['selected_car'] = None
    reply_markup = build_car_selection_keyboard(context.user_data['cars'])
    await update.message.reply_text('Authorization successful. Please select a car:', reply_markup=reply_markup)

    return CAR_SELECTION


async def garage(update, context):
    # Clear the selected car and show the car selection menu again
    context.user_data['selected_car'] = None
    reply_markup = build_car_selection_keyboard(context.user_data['cars'])
    await update.message.reply_text('Please select a car:', reply_markup=reply_markup)
    return CAR_SELECTION


async def car_selection(update, context):
    query = update.callback_query
    selected_car = query.data
    context.user_data['selected_car'] = selected_car
    reply_markup = build_action_selection_keyboard()
    await query.answer()
    await query.message.reply_text(f'Обрано команду {query.data}')
    await query.message.reply_text(text='Please select an action:', reply_markup=reply_markup)
    return ACTION_SELECTION


async def action_selection(update, context):
    query = update.callback_query
    selected_action = query.data
    # Do something with the selected car and action here
    await query.edit_message_text(text=f"You selected {selected_action} for {context.user_data['selected_car']}.")
    # Rebuild the action selection keyboard and send it to the user again
    reply_markup = build_action_selection_keyboard()
    await query.message.reply_text('Please select another action:', reply_markup=reply_markup)
    return ACTION_SELECTION



def build_car_selection_keyboard(cars):
    keyboard = [[telegram.InlineKeyboardButton(car, callback_data=car)] for car in cars]
    return telegram.InlineKeyboardMarkup(keyboard)


# def build_action_selection_keyboard():
#
#     keyboard = [[telegram.InlineKeyboardButton('Базова інформація', callback_data='base_info')],
#                 [telegram.InlineKeyboardButton('Швидкий звіт по стану авто', callback_data='gen_quick_report')],
#                 [telegram.InlineKeyboardButton('Дані про поїздки', callback_data='trip_report')],
#                 [telegram.InlineKeyboardButton('Сервісні акції', callback_data='service_promo')],
#                 [telegram.InlineKeyboardButton('Запис на сервісне обслуговування', callback_data='service_maintenance')],
#                 [telegram.InlineKeyboardButton('Стан вікон/дверей', callback_data='win_door_state')],
#                 [telegram.InlineKeyboardButton('Запас палива', callback_data='fuel_level')],
#                 [telegram.InlineKeyboardButton('Локація авто', callback_data='location')],
#                 [telegram.InlineKeyboardButton('Віддалені вказівки', callback_data='remote_commands')]]
#
#     return telegram.InlineKeyboardMarkup(keyboard)


def build_action_selection_keyboard():

    keyboard = [['Базова інформація', 'Швидкий звіт по стану авто', 'Дані про поїздки', 'Сервісні акції',
                'Запис на сервісне обслуговування', 'Стан вікон/дверей', 'Запас палива', 'Локація авто', 'Віддалені вказівки']]
    return telegram.ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


def handle_action_selection(message):
    # Retrieve the selected option from the message
    selected_option = message.text

    # Perform an action based on the selected option
    if selected_option == 'Базова інформація':
        reply_text = 'Тут буде повна інформація про авто'
    elif selected_option == 'Швидкий звіт по стану авто':
        reply_text = 'Тут буде швидкий звіт про стан авто'
    elif selected_option == 'Дані про поїздки':
        reply_text = 'Тут будуть дані про поїздки'
    elif selected_option == 'Сервісні акції':
        reply_text = 'Тут будуть сервісні акції'
    elif selected_option == 'Запис на сервісне обслуговування':
        reply_text = 'Тут буде запис на сервісне обслуговування'
    elif selected_option == 'Стан вікон/дверей':
        reply_text = 'Тут буде стан вікон/дверей'
    elif selected_option == 'Запас палива':
        reply_text = 'Тут буде запас палива'
    elif selected_option == 'Локація авто':
        reply_text = 'Тут буде локація авто'
    elif selected_option == 'Віддалені вказівки':
        reply_text = 'Тут будуть віддалені вказівки'
    else:
        reply_text = 'Невідома опція'

    return reply_text


async def handle_message(update, context):
    message = update.message
    reply_text = handle_action_selection(message)
    await message.reply_text(reply_text)


def get_authorization_url():
    url = f'https://oauth3.example.com/authorize?client_id={CLIENT_ID}&redirect_uri={REDIRECT_URI}'
    return url


def get_access_token(authorization_code):
    url = 'https://oauth3.example.com/token'
    payload = {
        'grant_type': 'authorization_code',
        'code': authorization_code,
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
        'redirect_uri': REDIRECT_URI
    }
    response = requests.post(url, data=payload)
    if response.ok:
        return response.json()['access_token']
    else:
        return None


def main():
    # Create an instance of the Updater class
    application = Application.builder().token(TOKEN).build()

    # Add conversation handler for handling the /start command
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, email)],
            PASSWD: [MessageHandler(filters.TEXT & ~filters.COMMAND, passwd)],
            CAR_SELECTION: [CallbackQueryHandler(car_selection)],
            ACTION_SELECTION: [CallbackQueryHandler(action_selection)]
        },
        fallbacks=[CommandHandler('garage', garage)],
        allow_reentry=True
    )
    application.add_handler(conv_handler)
    application.add_handler(telegram.ext.MessageHandler(filters.TEXT, handle_message))

    # Add message handler for handling OAuth3 authorization - future development
    # message_handler = MessageHandler(filters.Regex(r'^https://oauth3.example.com/.*$'), oauth3_callback)
    # application.add_handler(message_handler)

    application.run_polling()
    application.idle()


if __name__ == '__main__':
    main()