import asyncio
import datetime
import json
import logging
import math
from time import sleep
import numpy as np
import aiohttp
from orjson import orjson
from tabulate import tabulate

from general.DFrame import DFrame
from general.other import func_chunks_generators
from settings import TOKEN, session_auth, ListCouple, FileDataList, user_id, Leverage, Category
from aiogram import types, Router
from aiogram.filters import Text
from aiogram.utils.markdown import text, hpre, hbold
from aiogram.types import Message, BufferedInputFile
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from general.graph_couple import Graph_couple
from keyboard.keyboard_add_order import percent_keyboard, order_keyboard, buy_sell_keyboard, add_order_keyboard
from keyboard.keyboard_coin import coin_keyboard

router = Router()


class Form_add(StatesGroup):
    one_coin = State()
    two_coin = State()
    balance_wallet = State()
    percent = State()
    one_side = State()
    two_side = State()
    One = State()
    Two = State()


@router.message(Text(text='Создать сделку', ignore_case=True))
async def add_couple(message: Message):
    """

    :param message:
    """
    if message.from_user.username == 'Endresk':
        await message.answer("Выбирите первый коин:"
                             "\n", parse_mode="HTML", reply_markup=add_order_keyboard())


@router.callback_query(Text(startswith="one_"))
async def callbacks_one(callback: types.CallbackQuery):
    """

    :param callback:
    """
    one_symbol = callback.data.replace('one_', '')

    await callback.message.edit_text("Выбирите второй коин:"
                                     "\n", parse_mode="HTML", reply_markup=coin_keyboard("long", one_symbol))
    await callback.answer()


@router.callback_query(Text(startswith="long_"))
async def callbacks_long(callback: types.CallbackQuery):
    """

    :param callback:
    """
    coins = callback.data.replace("long_", "")

    one = coins.split("-")[0]
    two = coins.split("-")[1]
    with open(f'json_files/{ListCouple}.json', 'r') as f:
        JsonListSymbolTwo = json.load(f)
        plot_file, _, _, _, _ = Graph_couple(one, two).load(JsonListSymbolTwo)
        await callback.message.edit_text(text(f"Пара", hbold(f"{one} - {two}")), parse_mode="HTML", )
        await callback.message.answer_photo(BufferedInputFile(plot_file.getvalue(), f'{one}_{two}'))

        await callback.message.answer(f'Какой коин в лонг?', reply_markup=buy_sell_keyboard(one, two))


@router.callback_query(Text(startswith="add_"))
async def callbacks_add(callback: types.CallbackQuery, state: FSMContext):
    """

    :param callback:
    :param state:
    """
    with open('json_files/symbols.json', 'r') as f:
        to_json = json.load(f)

    coins = callback.data.replace("add_", "")
    action = coins.split("_")[0]

    if action == 'one':
        One = 'Лонг'
        Two = 'Шорт'
        one_side = 'Buy'
        two_side = 'Sell'
        coin_long = coins.replace("one_", "").split("-")[0]
        coin_short = coins.replace("one_", "").split("-")[1]
    else:
        One = 'Шорт'
        Two = 'Лонг'
        one_side = 'Sell'
        two_side = 'Buy'
        coin_long = coins.replace("two_", "").split("-")[0]
        coin_short = coins.replace("two_", "").split("-")[1]

    if f'{coin_long}USDT' in to_json:
        one_coin = f'{coin_long}USDT'
    else:
        one_coin = '0'
        await callback.answer("Первой монеты нету на BYBIT\n"
                              "Введите существующую монету!")

    if f'{coin_short}USDT' in to_json:
        two_coin = f'{coin_short}USDT'
    else:
        two_coin = '0'
        await callback.answer("Второй монеты нету на BYBIT\n"
                              "Введите существующую монету!")

    if one_coin != '0' and two_coin != '0':

        balance_wallet = float(session_auth.get_wallet_balance(accountType="CONTRACT")
                               ['result']['list'][0]['coin'][0]['availableToWithdraw'])

        percent = {}

        for i in [1, 3, 5, 8, 13, 15, 20, 25]:
            percent[i] = (balance_wallet * int(i)) / 100

        await callback.message.edit_text(
            text(hpre(f"{One}: {one_coin} / {Two}: {two_coin}"
                      f"\nБаланс на фьючерсах: {round(balance_wallet, 3)}\n",
                      tabulate(
                          [
                              [f"1%:", f"{round(percent[1], 3)}", "13%:", f"{round(percent[13], 3)}\n"],
                              [f"3%:", f"{round(percent[3], 3)}", "15%:", f"{round(percent[15], 3)}\n"],
                              [f"5%:", f"{round(percent[5], 3)}", "20%:", f"{round(percent[20], 3)}\n"],
                              [f"8%:", f"{round(percent[8], 3)}", "25%:", f"{round(percent[25], 3)}\n"]
                          ],
                          tablefmt='plain'))),
            parse_mode="HTML")

        await callback.message.answer("Выберите % от вашего баланса USDT на обе пары",
                                      reply_markup=percent_keyboard())

        await state.update_data(One=One)
        await state.update_data(Two=Two)
        await state.update_data(one_side=one_side)
        await state.update_data(two_side=two_side)
        await state.update_data(one_coin=one_coin)
        await state.update_data(two_coin=two_coin)
        await state.update_data(balance_wallet=balance_wallet)
    await callback.answer()


@router.callback_query(Text(startswith="num_"))
async def callbacks_num(callback: types.CallbackQuery, state: FSMContext):
    """

    :param callback:
    :param state:
    """
    data, balance_one_coin, balance_two_coin = await DataCoin(state)
    action = callback.data.split("_")[1]

    if action == 'one':
        percent = 1
    elif action == 'three':
        percent = 3
    elif action == 'five':
        percent = 5
    elif action == 'eight':
        percent = 8
    elif action == 'thirteen':
        percent = 13
    elif action == 'fifteen':
        percent = 15
    elif action == 'twenty':
        percent = 20
    else:
        percent = 25

    await state.update_data(percent=percent)

    sum_all_coin = (data['balance_wallet'] * percent) / 100

    await callback.message.edit_text(text(hbold(f"{data['One']}: {data['one_coin']} / "
                                                f"{data['Two']}: {data['two_coin']}"),
                                          f'\nВы выбрали {percent}% от дипозита'
                                          f'\nНа общую сумму {round(sum_all_coin, 3)}'
                                          f'\nОткрыть сделку?'),
                                     parse_mode="HTML",
                                     reply_markup=order_keyboard())
    await callback.answer()


async def place(SumHalf, coin, BalanceCoin):
    """

    :param SumHalf:
    :param coin:
    :param BalanceCoin:
    :return:
    """

    try:
        session_auth.switch_position_mode(
            category=Category,
            symbol=coin,
            mode=3
        )
        await asyncio.sleep(1)
    except:
        pass
    try:
        session_auth.switch_margin_mode(
            category=Category,
            symbol=coin,
            tradeMode=0,
            buyLeverage=Leverage,
            sellLeverage=Leverage
        )
        await asyncio.sleep(1)
    except:
        pass

    try:
        session_auth.set_leverage(
            category=Category,
            symbol=coin,
            buyLeverage=Leverage,
            sellLeverage=Leverage
        )
    except :
        pass

    params = {
        'category': Category,
        'symbol': coin
    }
    async with aiohttp.ClientSession() as session:
        async with session.get(f'https://api.bybit.com/v5/market/instruments-info',
                               params=params) as result:
            result = await result.json()

            if result["retMsg"] == "OK":
                result = result['result']['list'][0]['lotSizeFilter']
                maxOrderQty = int(float(result['maxOrderQty']))
                minOrderQty = float(result['minOrderQty'])
                qtyStep = float(result['qtyStep'])

                SumQty = (SumHalf * int(Leverage)) / BalanceCoin

                if SumQty > minOrderQty:

                    if qtyStep < 1:
                        SumPlace = round(float(SumQty), len(str(qtyStep).split(".")[1]))
                    else:
                        SumPlace = int(float(SumQty))

                    return SumPlace, maxOrderQty
                else:
                    return 0, 0
            else:
                logging.warning('Не удалось установить связь по запросу получения максимального количества ордера!')


async def PAO(SumPlace, maxOrderQty, coin, side):
    """

    :param SumPlace:
    :param maxOrderQty:
    :param coin:
    :param side:
    """
    PI = 1 if side == 'Buy' else 2

    if SumPlace > maxOrderQty:

        qty = math.floor(SumPlace / maxOrderQty)

        res = [maxOrderQty for _ in np.arange(0, qty, 1)]
        res.append((float(SumPlace - (qty * maxOrderQty))))

        for i in res:
            session_auth.place_order(
                category=Category,
                symbol=coin,
                side=side,
                orderType="Market",
                qty=i,
                positionIdx=PI,
                timeInForce='GTC',
                reduceOnly=False,
                closeOnTrigger=False
            )
    else:
        session_auth.place_order(
            category=Category,
            symbol=coin,
            side=side,
            orderType="Market",
            qty=SumPlace,
            positionIdx=PI,
            timeInForce='GTC',
            reduceOnly=False,
            closeOnTrigger=False
        )


async def DataCoin(state):
    """

    :param state:
    :return:
    """
    data = await state.get_data()

    BalanceOneCoin, BalanceTwoCoin = 0, 0

    for Coin in session_auth.get_tickers(category="linear")['result']['list']:

        if data['one_coin'] == Coin['symbol']:
            BalanceOneCoin = float(Coin['lastPrice'])

        if data['two_coin'] == Coin['symbol']:
            BalanceTwoCoin = float(Coin['lastPrice'])

    return data, BalanceOneCoin, BalanceTwoCoin


@router.callback_query(Text(startswith="order_"))
async def callbacks_order(callback: types.CallbackQuery, state: FSMContext):
    """

    :param callback:
    :param state:
    """
    Data, BalanceOneCoin, BalanceTwoCoin = await DataCoin(state)
    action = callback.data.split("_")[1]

    DataCouples = {}

    try:
        with open('json_files/DataCouples.json', "rb") as read_file:
            DataCouples = orjson.loads(read_file.read())
    except:
        with open('json_files/DataCouples.json', 'w')  as WriteFile:
            json.dump({}, WriteFile)

    if action == 'yes':
        SumHalf = ((Data['balance_wallet'] * Data['percent']) / 100) / 2

        ONE = Data['one_coin']
        TWO = Data['two_coin']

        ONESide = Data['one_side']
        TWOSide = Data['two_side']

        sumPlaceOne, maxOrderQtyOne = await place(SumHalf, ONE, BalanceOneCoin)

        if sumPlaceOne != 0:

            sumPlaceTwo, maxOrderQtyTwo = await place(SumHalf, TWO, BalanceTwoCoin)

            if sumPlaceTwo != 0:

                try:
                    with open(FileDataList, 'rb') as f:
                        DataList = orjson.loads(f.read())
                    ZScoreOpen = DataList[f'{ONE.split("USDT")[0]}_{TWO.split("USDT")[0]}']['ZScore']
                    num = 1
                except:
                    ZScoreOpen = 0
                    num = 0

                if num == 1:
                    await PAO(sumPlaceOne, maxOrderQtyOne, ONE, ONESide)
                    await PAO(sumPlaceTwo, maxOrderQtyTwo, TWO, TWOSide)

                    with open(f'json_files/{ListCouple}.json', 'rb') as f:
                        JsonListSymbols = orjson.loads(f.read())

                    StockOne, _ = DFrame(JsonListSymbols[ONE])
                    StockTwo, _ = DFrame(JsonListSymbols[TWO])
                    CloseLastOne = StockOne.close[-1]
                    CloseLastTwo = StockTwo.close[-1]
                    TVXOpen = CloseLastOne / CloseLastTwo

                    if f'{ONE}_{TWO}' not in DataCouples:
                        DateTime = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                        DataCouples[f'{ONE}_{TWO}'] = {
                                 "user_id": user_id,
                                 "ONE": ONE,
                                 "ONESide": ONESide,
                                 "TWO": TWO,
                                 "TWOSide": TWOSide,
                                 "QtyOne": sumPlaceOne,
                                 "QtyTwo": sumPlaceTwo,
                                 "ZScoreOpen": ZScoreOpen,
                                 "EntryPrice": TVXOpen,
                                 "DateTime": DateTime
                        }
                    else:
                        DictValue = DataCouples[f"{ONE}_{TWO}"]

                        sumPlaceOne += float(DictValue["QtyOne"]) \
                            if float(DictValue["QtyOne"]) < 1 \
                            else int(DictValue["QtyOne"])
                        sumPlaceTwo += float(DictValue["QtyTwo"]) \
                            if float(DictValue["QtyTwo"]) < 1 \
                            else int(float(DictValue["QtyTwo"]))

                        DictValue |= {"QtyOne": sumPlaceOne, "QtyTwo": sumPlaceTwo}
                        DataCouples |= {f'{ONE}_{TWO}': DictValue}

                    with open(f'json_files/DataCouples.json', "w") as WriteFile:
                        json.dump(DataCouples, WriteFile)

                    await callback.message.edit_text("Контракты открыты!\n"
                                                     f"Количество для {ONE} - {sumPlaceOne}\n"
                                                     f"Количество для {TWO} - {sumPlaceTwo}\n")

                    await state.clear()
                    await callback.answer(cache_time=30)
                else:
                    await callback.message.edit_text(f"Пара {ONE} - {TWO} больше не стационарна!")

            else:
                await callback.message.edit_text(
                    f"Процент для коина {TWO} меньше допустимого количества на заказ"
                    f"\nВыберите процент больше",
                    reply_markup=percent_keyboard())
                await callback.answer()

        else:
            await callback.message.edit_text(
                f"Процент для коина {ONE} меньше допустимого количества на заказ"
                f"\nВыберите процент больше",
                reply_markup=percent_keyboard())
            await callback.answer()
    else:
        await callback.message.edit_text("Сделка отклонена!")
        await state.clear()
        await callback.answer()
