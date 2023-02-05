from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from core.connect_service import get_vehicle_base_info


# ***** GARAGE MENU ***** #
def garage_menu_keyboard(connection):
    '''

    :param connection:
    :return:
    '''
    keyboard = []

    for count, vehicle in enumerate(connection.vehicles):
        vehicle_info = get_vehicle_base_info(vehicle)
        vehicle_name = f'{vehicle_info["model"]} ' \
                       f'{vehicle_info["manufactured"][0:4]} ' \
                       f'{vehicle_info["engine_capacity"]} ' \
                       f'{vehicle_info["engine_type"]}'
        keyboard.append([InlineKeyboardButton(vehicle_name, callback_data=f'{count + 1}')])

    return InlineKeyboardMarkup(keyboard)


async def garage_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    '''Menu builder to select vehicle'''
    query = update.callback_query
    await query.answer()
    await query.message.reply_text(f'Ти обрав(ла) авто! Тепер набирай /commands і я покажу тобі звідки готував.. упс... Покажу тобі все, що я вмію 😉')
    context.user_data['selected_vehicle'] = int(query.data)

# ***** GARAGE MENU ***** #


# ***** VEHICLE MENU ***** #

def vehicle_menu_keyboard(connection):
    '''
    :param connection:
    :return:
    '''
    keyboard = [[InlineKeyboardButton('Базова інформація', callback_data='base_info')],
                [InlineKeyboardButton('Швидкий звіт по стану авто', callback_data='gen_quick_report')],
                [InlineKeyboardButton('Дані про поїздки', callback_data='trip_report')],
                [InlineKeyboardButton('Сервісні акції', callback_data='service_promo')],
                [InlineKeyboardButton('Запис на сервісне обслуговування', callback_data='service_maintenance')],
                [InlineKeyboardButton('Стан вікон/дверей', callback_data='win_door_state')],
                [InlineKeyboardButton('Запас палива', callback_data='fuel_level')],
                [InlineKeyboardButton('Локація авто', callback_data='location')],
                [InlineKeyboardButton('Віддалені вказівки', callback_data='remote_commands')]]

    return InlineKeyboardMarkup(keyboard)

async def vehicle_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    '''Menu builder to get vehicle data'''
    query = update.callback_query
    await query.answer()
    await query.message.reply_text(f'Обрано команду {query.data}')

# ***** VEHICLE MENU ***** #
