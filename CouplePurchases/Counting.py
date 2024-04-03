import json
from decimal import Decimal
from time import time, sleep

import numpy as np
from orjson import orjson

from general.ATR import ATR
from general.DFrame import DFrame, TwoCoupleValue
from settings import ListCouple, NoCoupleResult, FileDataList, FileSymbolsATR, CoupleResult


async def CountingATR(JsonListSymbols, Symbol):
    """

    :param JsonListSymbols:
    :param Symbol:
    :return:
    """
    DictSymbols = {}

    Coin, _ = DFrame(JsonListSymbols[f'{Symbol}USDT'])
    AverageTR, CurrentATR = ATR(Coin)

    DictSymbols[Symbol] = {
        "ATR": AverageTR,
        "CurATR": CurrentATR,
    }
    return DictSymbols


async def CountingSymbol(DictCoupleResult, JsonListSymbols):
    """

    :param DictCoupleResult:
    :param JsonListSymbols:
    :return:
    """

    SymbolsList, DictSymbols = [], {}

    for key in DictCoupleResult.keys():
        ONE = key.split("_")[0]
        TWO = key.split("_")[1]

        if ONE not in SymbolsList:
            SymbolsList.append(ONE)
            DictSymbols.update(await CountingATR(JsonListSymbols, ONE))

        if TWO not in SymbolsList:
            SymbolsList.append(TWO)
            DictSymbols.update(await CountingATR(JsonListSymbols, TWO))

    with open(FileSymbolsATR, 'w') as f:
        json.dump(DictSymbols, f)

    return DictSymbols


async def Counting():
    """

    :return:
    """

    with open(CoupleResult, 'rb') as f:
        ResultCouple = orjson.loads(f.read())

    with open(NoCoupleResult, 'rb') as f:
        ResultNoCouple = orjson.loads(f.read())

    DictAutoCrossing, DictCoupleResult, DataList = {}, ResultCouple['result'].copy(), {}

    with open('json_files/DataCouples.json', "rb") as read_file:
        DataCouples = orjson.loads(read_file.read())

    for i in DataCouples.values():
        OneCoinStat = i["ONE"].split("USDT")[0]
        TwoCoinStat = i["TWO"].split("USDT")[0]

        if f'{OneCoinStat}_{TwoCoinStat}' not in ResultCouple['result']:
            DictCoupleResult[f'{OneCoinStat}_{TwoCoinStat}'] = ResultNoCouple['result'][f'{OneCoinStat}_{TwoCoinStat}']

    with open('json_files/DictCoupleResult.json', 'w') as f:
        json.dump(DictCoupleResult, f)

    with open(f'json_files/{ListCouple}.json', 'rb') as f:
        JsonListSymbols = orjson.loads(f.read())

    SymbolsATR = await CountingSymbol(DictCoupleResult, JsonListSymbols)

    # t0 = time()

    for key, values in DictCoupleResult.items():
        OneSymbol = key.split("_")[0]
        TwoSymbol = key.split("_")[1]

        StockOne, _ = DFrame(JsonListSymbols[f'{OneSymbol}USDT'])
        StockTwo, _ = DFrame(JsonListSymbols[f'{TwoSymbol}USDT'])

        Stock_1interval = TwoCoupleValue(StockOne, StockTwo)
        AverageTR, CurrentATR = ATR(Stock_1interval)

        CloseLastOne = StockOne.close[-1]
        CloseLastTwo = StockTwo.close[-1]
        MarkPrice = CloseLastOne / CloseLastTwo

        if f"{OneSymbol}_{TwoSymbol}" in ResultCouple['result'].keys():
            RC = ResultCouple['result'][f"{OneSymbol}_{TwoSymbol}"]
            PValue = ['%.4g' % RC[1], 1]
            ZScore = '%.4g' % RC[2]
            ZScoreYdy = '%.4g' % RC[3]
            ZScoreDBY = '%.4g' % RC[4]
            BoolBar = '%.4g' % RC[5]
        else:
            PValue = ['%.4g' % ResultNoCouple['result'][f'{OneSymbol}_{TwoSymbol}'][1], 0]
            ZScore = '%.4g' % ResultNoCouple['result'][f'{OneSymbol}_{TwoSymbol}'][2]
            ZScoreYdy = '%.4g' % ResultNoCouple['result'][f'{OneSymbol}_{TwoSymbol}'][3]
            ZScoreDBY = '%.4g' % ResultNoCouple['result'][f'{OneSymbol}_{TwoSymbol}'][4]
            BoolBar = '%.4g' % ResultNoCouple['result'][f'{OneSymbol}_{TwoSymbol}'][5]

        DataList[key] = {
            "SOneATR": float('%g' % Decimal(SymbolsATR[OneSymbol]['ATR'])),
            "SOneCurATR": float('%g' % Decimal(SymbolsATR[OneSymbol]['CurATR'])),
            "STwoATR": float('%g' % Decimal(SymbolsATR[TwoSymbol]['ATR'])),
            "STwoCurATR": float('%g' % Decimal(SymbolsATR[TwoSymbol]['CurATR'])),
            "CoupleATR": float('%g' % Decimal(AverageTR)),
            "CoupleCurATR": float('%g' % Decimal(CurrentATR)),
            "MarkPrice": float('%g' % Decimal(MarkPrice)),
            "PValue": PValue,
            "ZScore": float('%g' % Decimal(ZScore)),
            "ZScoreDBY": float('%g' % Decimal(ZScoreDBY)),
            "ZScoreYdy": float('%g' % Decimal(ZScoreYdy)),
            "BoolBar": float('%g' % Decimal(BoolBar))
        }

    # t1 = time()
    # print(t1 - t0)

    with open(FileDataList, 'w') as f:
        json.dump(DataList, f)
