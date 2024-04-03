from datetime import timedelta, date, datetime
from time import sleep, time

import numpy as np
from aiogram import Bot
from aiogram.types import BufferedInputFile
from aiogram.utils.markdown import hpre
from orjson import orjson

from general.DFrame import TwoCoupleValue
from general.other import ListEveryTabulate
from settings import user_id, TOKEN, FileDataList, DU1, DD1

bot = Bot(token=TOKEN)


async def AutoCrossing():
    with open('json_files/DataCouples.json', "rb") as read_file:
        DataCouples = orjson.loads(read_file.read())

    with open(FileDataList, 'rb') as f:
        DataList = orjson.loads(f.read())

    DictAutoCrossing = {}

    try:
        with open('json_files/AutoCrossing.json', "rb") as read_file:
            AutoCrossingJson = orjson.loads(read_file.read())

            for key, value in AutoCrossingJson.copy().items():
                if datetime.today() > datetime.strptime(value[1], '%Y-%m-%d') + timedelta(days=1):
                    del AutoCrossingJson[key]
        DictAutoCrossing = AutoCrossingJson
    except:
        with open('json_files/AutoCrossing.json', 'w'):
            pass

    with open('json_files/DictCoupleResult.json', 'rb') as f:
        DictCoupleResult = orjson.loads(f.read())

    for key, values in DictCoupleResult.items():
        OneSymbol = key.split("_")[0]
        TwoSymbol = key.split("_")[1]

        Couple = [Couple for Couple in DataCouples.keys()
                  if f'{OneSymbol}USDT' == Couple.split("_")[0] and f'{TwoSymbol}USDT' == Couple.split("_")[1]]

        Coin = [Couple for Couple in DataCouples.keys()
                if f'{OneSymbol}USDT' == Couple.split("_")[0] or
                f'{TwoSymbol}USDT' == Couple.split("_")[0] or
                f'{OneSymbol}USDT' == Couple.split("_")[1] or
                f'{TwoSymbol}USDT' == Couple.split("_")[1]
                ]

        if not Coin and not Couple:

            ValueCouple = DataList[f'{OneSymbol}_{TwoSymbol}']
            ZScore = float(ValueCouple['ZScore'])
            ZScoreYdy = float(ValueCouple['ZScoreYdy'])
            BoolBar = float(ValueCouple['BoolBar'])
            CoupleATR = float(ValueCouple['CoupleATR'])
            CoupleCurATR = float(ValueCouple['CoupleCurATR'])
            PValue = float(ValueCouple['PValue'][0])

            if PValue < 0.009:
                if CoupleATR * 25 / 100 > CoupleCurATR:
                    if BoolBar == 1:
                        if ZScoreYdy > 2 or ZScoreYdy < -2:
                            if f'{OneSymbol}_{TwoSymbol}' not in DictAutoCrossing:

                                ListEvery, plot_file, y, Stock = ListEveryTabulate(OneSymbol, TwoSymbol, ValueCouple)
                                StockClose = Stock['close'][-1]

                                if StockClose > np.array(y)[-1] * DU1 and ZScoreYdy > 2 or \
                                        StockClose < np.array(y)[-1] * DD1 and ZScoreYdy < -2:

                                    DictAutoCrossing[f'{OneSymbol}_{TwoSymbol}'] = [
                                        float(ZScore), f'{date.today()}'
                                    ]

                                    await bot.send_photo(
                                        user_id,
                                        BufferedInputFile(plot_file.getvalue(),
                                                          f'{OneSymbol}_{TwoSymbol}.png'),
                                        caption=f'<u>NEW</u> {OneSymbol} / {TwoSymbol}'
                                                f'\n{hpre(ListEvery)} ',
                                        parse_mode="HTML")

    json_data = orjson.dumps(DictAutoCrossing)
    with open('json_files/AutoCrossing.json', 'wb') as f:
        f.write(json_data)
