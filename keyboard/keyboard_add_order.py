import json

from aiogram import types
from aiogram.utils.keyboard import InlineKeyboardBuilder
from orjson import orjson

from settings import CoupleResult


def percent_keyboard():
    buttons = [
        [
            types.InlineKeyboardButton(text="1", callback_data="num_one"),
            types.InlineKeyboardButton(text="3", callback_data="num_three"),
            types.InlineKeyboardButton(text="5", callback_data="num_five"),
            types.InlineKeyboardButton(text="8", callback_data="num_eight")
        ],
        [
            types.InlineKeyboardButton(text="13", callback_data="num_thirteen"),
            types.InlineKeyboardButton(text="15", callback_data="num_fifteen"),
            types.InlineKeyboardButton(text="20", callback_data="num_twenty"),
            types.InlineKeyboardButton(text="25", callback_data="num_twenty-five")
        ]
    ]
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=buttons)
    return keyboard


def order_keyboard():
    buttons = [
        [
            types.InlineKeyboardButton(text="Подтверждаю", callback_data="order_yes"),
            types.InlineKeyboardButton(text="Откланяю", callback_data="order_no")
        ]
    ]
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=buttons)
    return keyboard


def buy_sell_keyboard(one, two):
    buttons = [
        [
            types.InlineKeyboardButton(text=one, callback_data=f"add_one_{one}-{two}"),
            types.InlineKeyboardButton(text=two, callback_data=f"add_two_{one}-{two}")
        ]
    ]
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=buttons)
    return keyboard


def add_order_keyboard():
    with open('json_files/AutoCrossing.json', "rb") as read_file:
        AutoCrossingJson = orjson.loads(read_file.read())

    with open(CoupleResult, 'rb') as f:
        ResultTwo = orjson.loads(f.read())

    list_ = []

    one_add = InlineKeyboardBuilder()
    for key, _ in sorted(AutoCrossingJson.items()):

        if key in ResultTwo['result']:
            OneCoin = key.split("_")[0]
            if OneCoin not in list_:
                list_.append(OneCoin)
                one_add.add(types.InlineKeyboardButton(
                    text=f'{OneCoin}',
                    callback_data=f'one_{OneCoin}'))
    one_add.adjust(4)

    return one_add.as_markup()
