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

    for vehicle in connection.vehicles:
        vehicle_info = get_vehicle_base_info(vehicle)
        vehicle_name = f'{vehicle_info["model"]} ' \
                       f'{vehicle_info["manufactured"][0:4]} ' \
                       f'{vehicle_info["engine_capacity"]} ' \
                       f'{vehicle_info["engine_type"]}'
        keyboard.append([InlineKeyboardButton(vehicle_name, callback_data='garage_menu')])

    return InlineKeyboardMarkup(keyboard)


async def garage_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    '''Menu builder to select vehicle'''
    connection = context.user_data.get('connection')

    query = update.callback_query
    await query.answer()
    print(query.data)
    # await query.edit_message_text(text='Ось які авто є в твоєму гаражі:', reply_markup=garage_menu_keyboard(connection))

# ***** GARAGE MENU ***** #

    # await query.edit_message_text(text='Ось які авто є в твоєму гаражі:', reply_markup=garage_menu_keyboard(connection))
#     callback_data = update.callback_query.data
#     await update.callback_query.answer()
#     await update.message.reply_text(f'{callback_data}')
#     print(callback_data)