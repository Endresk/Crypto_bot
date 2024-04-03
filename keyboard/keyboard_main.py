from aiogram import types

markup_stat = [
    [
        types.KeyboardButton(text='Графики'),
        types.KeyboardButton(text='Статус')
    ],
    [
        types.KeyboardButton(text='Очистить очередь'),
        types.KeyboardButton(text='Все пары')
    ],
    [
        types.KeyboardButton(text='Создать сделку'),
        types.KeyboardButton(text='Закрыть сделку')
    ]
]
markup_adf = types.ReplyKeyboardMarkup(keyboard=markup_stat, resize_keyboard=True)