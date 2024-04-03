import asyncio
import contextlib
from time import sleep

from aiogram.filters import Text
from orjson import orjson
from tabulate import tabulate

from keyboard.keyboard_update import StatCouple_update_keyboard
from settings import TOKEN, FileDataList, CoupleResult
from general.other import round_up, func_chunks_generators
from aiogram import Router, types
from aiogram.types import Message
from aiogram.utils.markdown import text, hitalic, hpre

router = Router()


async def StatCouple(message, BlockMessage):
    data = []

    with open(CoupleResult, 'rb') as f:
        Result = orjson.loads(f.read())

    with open(FileDataList, 'rb') as f:
        DataList = orjson.loads(f.read())

    Time = Result['time']

    AllCouple = len(Result['result'].keys())

    UP, DOWN = 0, 0

    for key, values in Result['result'].items():
        OneSymbol = key.split("_")[0]
        TwoSymbol = key.split("_")[1]

        while True:
            try:
                ValueCouple = DataList[f'{OneSymbol}_{TwoSymbol}']
                break
            except:
                await asyncio.sleep(5)

        ZScoreYdy = float(ValueCouple["ZScoreYdy"])
        ZScore = float(ValueCouple["ZScore"])
        PValue = float(ValueCouple["PValue"][0])
        ZScoreDBY = float(ValueCouple['ZScoreDBY'])
        BoolBar = float(ValueCouple['BoolBar'])
        CoupleATR = float(ValueCouple['CoupleATR'])

        if BoolBar == 1:
            if CoupleATR > 0:
                if ZScoreDBY > 2 > ZScoreYdy or ZScoreDBY < -2 < ZScoreYdy:
                    data.append([
                        f'{OneSymbol} / {TwoSymbol}',
                        PValue,
                        ZScore,
                        ZScoreYdy
                    ])

                    if ZScoreDBY > 2:
                        UP += 1
                    else:
                        DOWN += 1

    data = sorted(data, key=lambda x: abs(float(x[2])))

    if len(data) > 80:
        for i in list(func_chunks_generators(data, 80)):
            data = tabulate(i,
                            tablefmt='plain',
                            headers=['Couple', 'PValue', 'ZScore', "ZScoreYdy"],
                            colalign=("left", "left", "left", "left")
                            )

            await message.answer(text(f'\n\n{hpre(data)}\n\n'),
                                 parse_mode="HTML")
        await message.answer(f'Всего пар: {AllCouple}'
                             f'\n\nUP: {UP}'
                             f'\nDOWN: {DOWN}'
                             f'\nВремя обновления: {hitalic(Time)} (мск) ',
                             parse_mode="HTML")

    elif len(data) == 0:
        await BlockMessage(text(f'Пар нет'),
                           parse_mode="HTML",
                           reply_markup=StatCouple_update_keyboard())
    else:
        data = tabulate(data,
                        tablefmt='plain',
                        headers=['Couple', 'PValue', 'ZScore', "ZScoreYdy"],
                        colalign=("left", "left", "left", "left")
                        )
        await BlockMessage(text(f'Всего пар: {AllCouple}'
                                f'\n\n{hpre(data)}'
                                f'\n\nUP: {UP}'
                                f'\nDOWN: {DOWN}'
                                f'\n\nВремя обновления: {hitalic(Time)} (мск) '),
                           parse_mode="HTML",
                           reply_markup=StatCouple_update_keyboard())


@router.message(Text(text='Все пары', ignore_case=True))
async def stat_couple(message: Message):
    """

    :param message:
    """
    if message.from_user.username == 'Endresk':
        await StatCouple(message, message.answer)


@router.callback_query(Text(text="StatCoupleUpdate"))
async def callbacks_status(callback: types.CallbackQuery):
    """

    :param callback:
    """
    with contextlib.suppress(Exception):
        await StatCouple(callback, callback.message.edit_text)
    await callback.answer()
