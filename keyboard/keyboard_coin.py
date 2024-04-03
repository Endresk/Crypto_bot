import json

from aiogram import types
from aiogram.utils.keyboard import InlineKeyboardBuilder
from orjson import orjson

from settings import CoupleResult


def coin_keyboard(teg, OneCoin):
    with open(CoupleResult, 'rb') as f:
        ResultTwo = orjson.loads(f.read())

    builder = InlineKeyboardBuilder()
    for key in ResultTwo['result'].keys():

        OneSymbol = key.split("_")[0]
        TwoSymbol = key.split("_")[1]

        if OneCoin == OneSymbol:
            builder.add(types.InlineKeyboardButton(
                text=f'{TwoSymbol}',
                callback_data=f'{teg}_{OneCoin}-{TwoSymbol}'))
        builder.adjust(4)

    return builder.as_markup()
