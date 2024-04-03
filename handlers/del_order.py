import logging
import math
import re
from time import sleep

import aiohttp
import emoji
import numpy as np
from aiogram.utils.keyboard import InlineKeyboardBuilder
from orjson import orjson

from settings import TOKEN, session_auth, Category
from aiogram import Router, types
from aiogram.types import Message
from aiogram.filters import Text
from general.other import symbols_list

router = Router()


@router.message(Text(text='Закрыть сделку', ignore_case=True))
async def cancel_couple(message: Message):
    if message.from_user.username == 'Endresk':

        data = []
        data_list = []

        with open('json_files/DataCouples.json', "rb") as read_file:
            DataCouples = orjson.loads(read_file.read())

        list_symbol = await symbols_list()

        for i in DataCouples.values():

            one_couple = i["ONE"]
            two_couple = i["TWO"]

            sideOne = i["ONESide"]
            if sideOne == 'Buy':
                side_one = emoji.emojize(':green_circle:')
            else:
                side_one = emoji.emojize(':red_circle:')
            sideTwo = i["TWOSide"]
            if sideTwo == 'Buy':
                side_two = emoji.emojize(':green_circle:')
            else:
                side_two = emoji.emojize(':red_circle:')

            data.append([f'{side_one}_{one_couple}_{sideOne}', f'{side_two}_{two_couple}_{sideTwo}'])

            data_list.append(f'{one_couple}_{sideOne}')
            data_list.append(f'{two_couple}_{sideTwo}')

        for key, values in list_symbol.items():
            if key not in data_list:

                symbols, side_ = str(key).split('_')
                if side_ == 'Buy':
                    side = emoji.emojize(':green_circle:')
                else:
                    side = emoji.emojize(':red_circle:')
                data.append([f'{side}_{symbols}_{side_}_{values[3]["Size"]}'])

        if len(data) == 0:
            await message.answer('Контрактов открытых нет!')
        else:
            builder = InlineKeyboardBuilder()
            for i in data:

                if len(i) == 2:
                    SmileOne = i[0].split('_')[0]
                    SmileTwo = i[1].split('_')[0]
                    CoinOne = i[0].split('_')[1]
                    CoinTwo = i[1].split('_')[1]
                    SideOne = i[0].split('_')[2]
                    SideTwo = i[1].split('_')[2]

                    builder.add(types.InlineKeyboardButton(
                        text=f"{SmileOne}{CoinOne} / {SmileTwo}{CoinTwo}",
                        callback_data=f"del_{CoinOne}-{SideOne}/{CoinTwo}-{SideTwo}"))
                if len(i) == 1:
                    Smile = i[0].split('_')[0]
                    coin = i[0].split('_')[1]
                    side = i[0].split('_')[2]
                    size = i[0].split('_')[3]
                    builder.add(types.InlineKeyboardButton(
                        text=f"{Smile}{coin}",
                        callback_data=f"del_{coin}-{side}-{size}"))
                builder.adjust(1)
            await message.answer('Выберите контракт который хотите закрыть: ', reply_markup=builder.as_markup())


async def cancel_symbol(symbol, side, qty):
    params = {
        'category': 'linear',
        'symbol': symbol
    }

    async with aiohttp.ClientSession() as session:
        async with session.get(f'https://api.bybit.com/v5/market/instruments-info',
                               params=params) as result:
            result = await result.json()
            try:
                if result["retMsg"] == "OK":
                    result = result['result']['list'][0]['lotSizeFilter']

                    maxTradingQty = int(float(result['maxOrderQty']))

                    if side == 'Buy':
                        sideNew = 'Sell'
                    else:
                        sideNew = 'Buy'

                    PI = 1 if side == 'Buy' else 2

                    if qty > maxTradingQty:
                        sum_symbol = math.floor(qty / maxTradingQty)
                        res = [maxTradingQty for _ in np.arange(0, sum_symbol, 1)]
                        res.append((qty - (sum_symbol * maxTradingQty)))

                        for i in res:
                            session_auth.place_order(
                                category=Category,
                                symbol=symbol,
                                side=sideNew,
                                orderType="Market",
                                qty=i,
                                positionIdx=PI,
                                timeInForce='GTC',
                                reduceOnly=True,
                                closeOnTrigger=False
                            )
                    else:
                        session_auth.place_order(
                            category=Category,
                            symbol=symbol,
                            side=sideNew,
                            orderType="Market",
                            qty=qty,
                            positionIdx=PI,
                            timeInForce='GTC',
                            reduceOnly=True,
                            closeOnTrigger=False
                        )
                else:
                    logging.warning('Не удалось установить связь по запросу получения максимального количества ордера!')
            except:
                logging.warning(f'В bybit символа «{symbol}» нет в стороне «{side}»!')


@router.callback_query(Text(startswith="del_"))
async def callbacks_cancel(callback: types.CallbackQuery):
    """

    :param callback:
    """
    action = callback.data.split("_")[1]

    if re.search(r"/", action):
        OneSymbol, OneSide = action.split('/')[0].split('-')
        TwoSymbol, TwoSide = action.split('/')[1].split('-')

        with open('json_files/DataCouples.json', "rb") as read_file:
            DataCouples = orjson.loads(read_file.read())

        await DeleteOrder(OneSymbol, TwoSymbol, DataCouples)

        await callback.message.edit_text(f"Контракт закрыт! {OneSymbol} / {TwoSymbol}")

    else:
        symbol = action.split('-')[0]
        side = action.split('-')[1]
        size = action.split('-')[2]

        with open('json_files/DataCouples.json', "rb") as read_file:
            DataCouples = orjson.loads(read_file.read())

        Side = None
        for key, values in DataCouples.items():
            if values['ONE'] == symbol:
                if values['ONESide'] == side:
                    Side = values['ONESide']

            if values['TWO'] == symbol:
                if values['TWOSide'] == side:
                    Side = values['TWOSide']

        if Side is None:
            await cancel_symbol(symbol, side, float(size))

        await callback.message.edit_text(f"Контракт закрыт! {symbol}")
    await callback.answer(cache_time=30)


async def DeleteOrder(OneSymbol, TwoSymbol, DataCouples):
    """

    :param TwoSymbol:
    :param OneSymbol:
    :param DataCouples:
    """
    DictValue = DataCouples[f"{OneSymbol}_{TwoSymbol}"]

    QtyOne = DictValue['QtyOne']
    QtyTwo = DictValue['QtyTwo']

    await cancel_symbol(OneSymbol, DictValue['ONESide'], float(QtyOne))

    await cancel_symbol(TwoSymbol, DictValue['TWOSide'], float(QtyTwo))

    del DataCouples[f"{OneSymbol}_{TwoSymbol}"]

    json_data = orjson.dumps(DataCouples)
    with open('json_files/DataCouples.json', 'wb') as f:
        f.write(json_data)
