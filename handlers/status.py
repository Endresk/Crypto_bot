import contextlib
import datetime
import itertools
from decimal import Decimal
from time import time, sleep

import emoji
from orjson import orjson
from tabulate import tabulate
from itertools import chain

from keyboard.keyboard_update import Status_update_keyboard
from general.other import round_up, symbols_list, Interval
from settings import TOKEN, session_auth, MainInterval, FileDataList, STOPLOSS, TAKEPROFIT
from aiogram import types, Router
from aiogram.filters import Text
from aiogram.utils.markdown import hpre, hbold, text
from aiogram.types import Message

router = Router()

url = "https://api.bybit.com"


async def status_symbol():
    """

    :param message:
    :return:
    """
    ListSymbol = await symbols_list()
    balance = session_auth.get_wallet_balance(accountType="CONTRACT")

    Base = list([
        hbold("Capital:"),
        f"{hbold(round(float(balance['result']['list'][0]['coin'][0]['equity']), 3))} $",
        hbold("\nAvailable balance:"),
        f"{hbold(round(float(balance['result']['list'][0]['coin'][0]['availableToWithdraw']), 3))} $\n"
    ])

    CurrentPrice = {}

    for Coin in session_auth.get_tickers(category="linear")['result']['list']:
        if Coin['symbol'] in [h.split('_')[0] for h in list(ListSymbol.keys())]:
            CurrentPrice[Coin['symbol']] = Coin['bid1Price']

    ListNoCouple = ListSymbol.copy()

    with open(FileDataList, 'rb') as f:
        DataList = orjson.loads(f.read())

    with open('json_files/DataCouples.json', "rb") as read_file:
        DataCouples = orjson.loads(read_file.read())

    DataCouplesDel = DataCouples.copy()

    StatCouple = []
    NotStatCouple = []

    OneInterval = Interval(MainInterval)

    # Цикл выводит все пары
    for couple in DataCouples.values():
        # Проверяем присутствуют ли наша пара в словаре ByBit

        if f'{couple["ONE"]}_{couple["ONESide"]}' in ListSymbol.keys() \
                and f'{couple["TWO"]}_{couple["TWOSide"]}' in ListSymbol.keys():
            One = couple["ONE"].split("USDT")[0]
            Two = couple["TWO"].split("USDT")[0]

            # DateOpen = datetime.datetime.strptime(f'{couple[2]}', "%Y-%m-%d %H:%M:%S")
            NumDay = datetime.datetime.today() - \
                     datetime.datetime.strptime(f'{couple["DateTime"]}', "%Y-%m-%d %H:%M:%S")
            SymbolUSDTOne = couple["ONE"].split("_")[0]
            SymbolUSDTTwo = couple["TWO"].split("_")[0]

            if couple["ONESide"] == 'Buy':
                emoji_one = emoji.emojize(':green_circle:')
            else:
                emoji_one = emoji.emojize(':red_circle:')

            if couple["TWOSide"] == 'Buy':
                emoji_two = emoji.emojize(':green_circle:')
            else:
                emoji_two = emoji.emojize(':red_circle:')

            priceMarkOne = CurrentPrice[SymbolUSDTOne] if SymbolUSDTOne in CurrentPrice.keys() else 0
            priceMarkTwo = CurrentPrice[SymbolUSDTTwo] if SymbolUSDTTwo in CurrentPrice.keys() else 0

            one_value = ListSymbol[f'{couple["ONE"]}_{couple["ONESide"]}'].copy()
            two_value = ListSymbol[f'{couple["TWO"]}_{couple["TWOSide"]}'].copy()

            sum_all_pnl = round_up(sum([float(*one_value[-2].values()), float(*two_value[-2].values())]), 3)
            # Первая строка
            Symbols = ["_Symbol_", f'{emoji_one}{SymbolUSDTOne.replace("USDT", "")}',
                       f'{emoji_two}{SymbolUSDTTwo.replace("USDT", "")}']
            # Вторая строка
            SymbolEP = ['EntryPr', *one_value[0].values(), *two_value[0].values()]
            # Третья строка
            SymbolMP = ['MarkPr', priceMarkOne, priceMarkTwo]
            # Четвертая строка
            LiqPrice = ['LiqPr', *one_value[1].values(), *two_value[1].values()]
            # Пятая строка
            Qty = ['Qty', couple["QtyOne"], couple["QtyTwo"]]
            # Шестая строка
            Couple = ['_Couple_', f"Current {OneInterval}", f"Open {OneInterval}"]
            # Седьмая строка
            PValue = [
                "PValue",
                '%g' % Decimal(DataList[f'{One}_{Two}']['PValue'][0])
            ]
            # Восьмая строка
            ATR = [
                "ATR",
                '%g' % Decimal(DataList[f'{One}_{Two}']['CoupleATR'])
            ]

            # Девятая строка
            ZScore = [
                "ZScore",
                '%g' % Decimal(DataList[f'{One}_{Two}']['ZScore']),
                '%g' % Decimal(couple["ZScoreOpen"])
            ]
            # Десятая строка
            Price = [
                'Price',
                '%g' % Decimal(DataList[f'{One}_{Two}']['MarkPrice']),
                '%g' % Decimal(couple["EntryPrice"])
            ]
            # Одиннадцатая строка
            TakeProfit = [
                'TP', round(
                    float('%g' % Decimal(float(couple["EntryPrice"]) +
                                         float(DataList[f'{One}_{Two}']['CoupleATR']) * TAKEPROFIT
                                         if float('%g' % Decimal(couple["ZScoreOpen"])) > 0
                                         else
                                         float(couple["EntryPrice"]) - float(
                                             DataList[f'{One}_{Two}']['CoupleATR']) * TAKEPROFIT)), 8),
                ''
            ]

            # Двенадцатая строка
            StopLoss = [
                'SL', round(
                    float('%g' % Decimal(float(couple["EntryPrice"]) +
                                         float(DataList[f'{One}_{Two}']['CoupleATR']) * STOPLOSS
                                         if float('%g' % Decimal(couple["ZScoreOpen"])) < 0
                                         else
                                         float(couple["EntryPrice"]) - float(
                                             DataList[f'{One}_{Two}']['CoupleATR']) * STOPLOSS)), 8),
                ''
            ]
            # Последние две строки
            Other = f'Profit: {hbold(round(sum_all_pnl, 2))} $' \
                    f'\nTime Open: <i>{datetime.timedelta(NumDay.days, NumDay.seconds)} </i>\n'

            # Цикл: Если да, то стационарные иначе не стационарные пары
            if DataList[f'{One}_{Two}']['PValue'][1] == 1:
                data_couple = tabulate(
                    [
                        Symbols, SymbolEP, SymbolMP, LiqPrice, Qty, Couple,
                        PValue, ATR, ZScore, Price, TakeProfit, StopLoss
                    ],
                    tablefmt='simple',
                    showindex=False,
                    colalign=("right", "left", "left"))
                StatCouple.append(f'\n{hpre(data_couple)}'
                                  f'\n{Other}')
            else:
                data_couple = tabulate(
                    [
                        Symbols, SymbolEP, SymbolMP, LiqPrice, Qty, Couple,
                        PValue, ATR, ZScore, Price, TakeProfit, StopLoss
                    ],
                    tablefmt='simple',
                    showindex=False,
                    colalign=("right", "left", "left"))

                NotStatCouple.append(f'\n{hpre(data_couple)}'
                                     f'\n{Other}')
            # Удаляем из словаря пары, для работы с ним в следующим цикле (Цикл с символами)
            try:
                del ListNoCouple[f'{couple["ONE"]}_{couple["ONESide"]}']
            except:
                pass
            try:
                del ListNoCouple[f'{couple["TWO"]}_{couple["TWOSide"]}']
            except:
                pass
        else:
            del DataCouplesDel[f'{couple["ONE"]}_{couple["TWO"]}']

            json_data = orjson.dumps(DataCouplesDel)
            with open('json_files/DataCouples.json', 'wb') as f:
                f.write(json_data)

    Symbols = []

    # Цикл выводит все символы если они есть
    for key, values in ListNoCouple.items():

        values[0] = values[0]['ТВХ']
        values[1] = values[1]['Ликвид']
        values[2] = values[2]['PNL']
        values[3] = values[3]['Size']

        symbol = list(itertools.chain([key.split('_')[0]], list(map(str, chain.from_iterable([values])))))
        symbol_sum_pnl = symbol[-2]
        priceMark = CurrentPrice[f'{symbol[0]}'] if f'{symbol[0]}' in CurrentPrice.keys() else 0

        if key.split('_')[1] == 'Buy':
            emoji_one = emoji.emojize(':green_circle:')
        else:
            emoji_one = emoji.emojize(':red_circle:')
        symbol.pop(-2)
        symbol[0] = f'{emoji_one}{key.split("_")[0].replace("USDT", "")}'

        data_coins = tabulate([['Coin', symbol[0]],
                               ['EntryPr', symbol[1]],
                               ['MarkPr', priceMark],
                               ['LiqPr', symbol[2]],
                               ['Qty', symbol[3]]],
                              tablefmt='simple',
                              showindex=False,
                              colalign=("right", "left"))

        Symbols.append(f'{hpre(data_coins)}\nProfit: {hbold(symbol_sum_pnl)} $\n')

    if StatCouple:
        Base.append(f'\n - {hbold("Stationary")} -\n')
        Base += StatCouple
    else:
        Base.append(f'\n - {hbold("Stationary None")} -\n')

    if NotStatCouple:
        Base.append(f'\n - {hbold("Not Stationary")} -\n')
        Base += NotStatCouple
    else:
        Base.append(f'\n - {hbold("Not Stationary None")} -\n')

    if Symbols:
        Base.append(f'\n - {hbold("Symbols")} -\n')
        Base += Symbols
    else:
        Base.append(f'\n - {hbold("Symbols None")} -\n')

    return Base


@router.message(Text(text='Статус', ignore_case=True))
async def status(message: Message):
    """

    :param message:
    """
    if message.from_user.username == 'Endresk':
        data = await status_symbol()
        await message.answer(text(*data),
                             parse_mode="HTML",
                             reply_markup=Status_update_keyboard())


@router.callback_query(Text(text="StatusUpdate"))
async def callbacks_status(callback: types.CallbackQuery):
    """

    :param callback:
    """
    with contextlib.suppress(Exception):
        data = await status_symbol()
        await callback.message.edit_text(text(*data),
                                         parse_mode="HTML",
                                         reply_markup=Status_update_keyboard())
    await callback.answer()
