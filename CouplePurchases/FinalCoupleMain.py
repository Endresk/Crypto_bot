import emoji
from aiogram import Bot
from aiogram.types import BufferedInputFile
from aiogram.utils.markdown import hbold
from orjson import orjson

from general.other import symbols_list, round_up
from handlers.del_order import DeleteOrder
from settings import TOKEN, user_id, ListCouple, FileDataList, STOPLOSS, TAKEPROFIT
from general.graph_couple import Graph_couple

bot = Bot(token=TOKEN)


async def FinalCoupleMain():

    with open('json_files/DataCouples.json', "rb") as read_file:
        DataCouples = orjson.loads(read_file.read())

    if DataCouples:

        with open(FileDataList, 'rb') as f:
            DataList = orjson.loads(f.read())

        ListSymbol = await symbols_list()

        DataCouplesCopy = DataCouples.copy()

        # Цикл проходим по всем открытым парам
        for i in DataCouplesCopy.values():
            OneCoin = i['ONE'].split("USDT")[0]
            TwoCoin = i['TWO'].split("USDT")[0]
            ZScoreOpen = float(i["ZScoreOpen"])
            ValueCouple = DataList[
                f'{OneCoin}_{TwoCoin}'
            ]

            EntryPrice = float(i["EntryPrice"])
            AverageTR = ValueCouple['CoupleATR']
            MarkPrice = ValueCouple["MarkPrice"]

            if ZScoreOpen < 0:
                sl = EntryPrice + float(AverageTR) * STOPLOSS
                BoolStopLoss = 1 if MarkPrice > sl else 0

                tp = EntryPrice - float(AverageTR) * TAKEPROFIT
                TakeProfit = 1 if MarkPrice < tp else 0
            else:
                sl = EntryPrice - float(AverageTR) * STOPLOSS
                BoolStopLoss = 1 if MarkPrice < sl else 0

                tp = EntryPrice + float(AverageTR) * TAKEPROFIT
                TakeProfit = 1 if MarkPrice > tp else 0

            # STOP LOSS

            if BoolStopLoss == 1:
                color = emoji.emojize(':cross_mark:')
                text = 'достигла двойного значения ATR!'

                with open(f'json_files/{ListCouple}.json', 'rb') as f:
                    JsonListSymbols = orjson.loads(f.read())
                await ClosePosition(i, color, OneCoin, TwoCoin, text, ListSymbol, JsonListSymbols, DataCouples)

            # TAKE PROFIT

            if TakeProfit == 1:
                color = emoji.emojize(':check_mark_button: :partying_face:')
                text = 'достигла Take Profit!'

                with open(f'json_files/{ListCouple}.json', 'rb') as f:
                    JsonListSymbols = orjson.loads(f.read())
                await ClosePosition(i, color, OneCoin, TwoCoin, text, ListSymbol, JsonListSymbols, DataCouples)


async def ClosePosition(i, color, OneCoin, TwoCoin, text, ListSymbol, JsonListSymbols, DataCouples):
    sum_all_pnl = round_up(sum([float(*ListSymbol[f'{i["ONE"]}_{i["ONESide"]}'][-2].values()),
                                float(*ListSymbol[f'{i["TWO"]}_{i["TWOSide"]}'][-2].values())]), 3)
    if text == 'достигла Take Profit!' and sum_all_pnl > 0 or text == 'достигла двойного значения ATR!':
        OneSymbol = i['ONE']
        TwoSymbol = i['TWO']

        await DeleteOrder(OneSymbol, TwoSymbol, DataCouples)

        PlotFile, _, _, _, _ = Graph_couple(OneCoin, TwoCoin).load(JsonListSymbols)

        await bot.send_photo(user_id,
                             BufferedInputFile(PlotFile.getvalue(),
                                               f'{OneCoin}_{TwoCoin}.png'),
                             caption=f'{color} Пара {OneCoin} / {TwoCoin} {text}'
                                     f'\nProfit: {hbold(round(sum_all_pnl, 2))} $',
                             parse_mode="HTML")

        with open('json_files/AutoCrossing.json', "rb") as read_file:
            AutoCrossingJson = orjson.loads(read_file.read())

        try:
            del AutoCrossingJson[f'{OneCoin}_{TwoCoin}']
        except:
            pass
