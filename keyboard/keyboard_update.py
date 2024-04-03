from aiogram import types


def Status_update_keyboard():
    buttons = [
        [
            types.InlineKeyboardButton(text='Обновить', callback_data="StatusUpdate")
        ]
    ]
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=buttons)
    return keyboard


def StatCouple_update_keyboard():
    buttons = [
        [
            types.InlineKeyboardButton(text='Обновить', callback_data="StatCoupleUpdate")
        ]
    ]
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=buttons)
    return keyboard


def Graph_Update_keyboard():
    buttons = [
        [
            types.InlineKeyboardButton(text='Обновить', callback_data="GraphUpdate")
        ]
    ]
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=buttons)
    return keyboard

