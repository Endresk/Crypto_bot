import asyncio
import json
import logging
import math
import re

import aiohttp
import numpy as np
from threading import Thread
from aiogram import Bot, Router
from time import time, sleep
from datetime import datetime, timedelta

from statsmodels.tsa.stattools import adfuller, kpss

from CouplePurchases.AutoCrossing import AutoCrossing
from CouplePurchases.FinalCoupleMain import FinalCoupleMain
from CouplePurchases.Counting import Counting
from main import logger
from settings import TOKEN, MainInterval, NoCoupleResult, CoupleResult
from scipy.stats import zscore

bot = Bot(token=TOKEN)
router = Router()


@router.startup()
async def on_startup(*_):
    asyncio.create_task(RUN())


async def RUN():
    while True:
        t0 = time()
        await StationaryCouples()
        t1 = time()
        job_time1 = (t1 - t0)

        t0 = time()
        await Counting()
        t1 = time()
        job_time2 = (t1 - t0)

        t0 = time()
        await FinalCoupleMain()
        t1 = time()
        job_time3 = (t1 - t0)

        t0 = time()
        await AutoCrossing()
        t1 = time()
        job_time4 = (t1 - t0)

        Sec = "{:.2f}".format(job_time1 + job_time2 + job_time3 + job_time3)
        Min = int((job_time1 + job_time2 + job_time3 + job_time3) / 60)
        SecMin = math.ceil(float(Sec) % 60)

        print(f'{datetime.now()} MA - {"{:.2f}".format(job_time1)} '
              f'Counting - {"{:.2f}".format(job_time2)} '
              f'FinalCoupleMain - {"{:.2f}".format(job_time3)}  '
              f'AutoCrossing - {"{:.2f}".format(job_time4)}  '
              f'All Time - {Sec} sec | '
              f'--- {Min} min {SecMin} sec')

        await asyncio.sleep(2)


async def RequestKline(symbol, TimeInterval, start, end, ListQK, session):
    """

    :param symbol:
    :param TimeInterval:
    :param start:
    :param end:
    :param ListQK:
    :param session:
    :return:
    """
    if 1440 == TimeInterval:
        time_interval = 'D'
    elif 10080 == TimeInterval:
        time_interval = 'W'
    elif 43200 == TimeInterval:
        time_interval = 'M'
    else:
        time_interval = TimeInterval

    while True:
        try:
            params = {
                'category': 'linear',
                'symbol': symbol,
                'interval': time_interval,
                'start': f'{start}000',
                'end': f'{end}000'
            }
            async with session.get(f'https://api.bybit.com/v5/market/kline?',
                                   params=params, ssl=False) as result:
                if result.status == 200:
                    result = await result.json()
                    Kline = result['result']['list']
                    break
                else:
                    logger.warning(f"ERROR result.status {result.status}")
        except:
            pass

    for k in reversed(Kline):
        ListQK["time"].append(int(k[0][:-3]))
        ListQK["open"].append(float(k[1]))
        ListQK["close"].append(float(k[4]))
        ListQK["high"].append(float(k[2]))
        ListQK["low"].append(float(k[3]))

    return ListQK, Kline


async def list_symbol(symbol, TimeInterval, TimeLastValue, Bool, session):
    """
    :param symbol:
    :param TimeInterval:
    :param TimeLastValue:
    :param Bool:
    :param session:
    :return:
    """
    next_time = int((str(datetime.timestamp(datetime.now() - timedelta(days=35)))).split('.')[0])

    ListQK = {
        "time": [],
        "open": [],
        "close": [],
        "high": [],
        "low": []
    }
    end = int(datetime.timestamp(datetime.now()))

    if 0 < TimeLastValue <= next_time or Bool:
        timeInterval = int((TimeInterval * 60) * 200)
        EndTime = end + timeInterval

        for NextTime in np.arange(next_time, EndTime, timeInterval):
            ListQK, Kline = await RequestKline(symbol, TimeInterval, NextTime, EndTime, ListQK, session)
    else:
        ListQK, _ = await RequestKline(symbol, TimeInterval, TimeLastValue, end, ListQK, session)

    return ListQK


async def AllSymbols(SymbolList, symbol, time_interval, session):
    """

    :param SymbolList:
    :param symbol:
    :param time_interval:
    :param session:
    :return:
    """
    AllList = {}
    if SymbolList and symbol in SymbolList.keys():
        value = SymbolList[symbol]
        TimeLastValue = value['time'][-1]

        ListQK = await list_symbol(symbol, time_interval, TimeLastValue, False, session)

        if len(ListQK['time']) == 1:
            if ListQK['time'][0] == TimeLastValue:
                value["close"][-1] = ListQK['close'][0]
                value["high"][-1] = ListQK['high'][0]
                value["low"][-1] = ListQK['low'][0]
        else:
            N = len(ListQK['time']) - 1

            del value["time"][:N]
            del value["open"][:N]
            del value["close"][:N]
            del value["high"][:N]
            del value["low"][:N]

            del value["time"][-1]
            del value["open"][-1]
            del value["close"][-1]
            del value["high"][-1]
            del value["low"][-1]

            value["time"].extend(ListQK['time'])
            value["open"].extend(ListQK['open'])
            value["close"].extend(ListQK['close'])
            value["high"].extend(ListQK['high'])
            value["low"].extend(ListQK['low'])

        AllList[symbol] = value

    else:
        ListQK = await list_symbol(symbol, time_interval, 0, True, session)
        if int(len(np.array(ListQK['close']))) == int(24 / (time_interval / 60) * 35):
            AllList[symbol] = ListQK

    return AllList


async def IMSymbols(SymbolList, symbol, time_interval, session, sem):
    """
    :param SymbolList:
    :param symbol:
    :param time_interval:
    :param session:
    :param sem:
    :return:
    """
    async with sem:
        return await AllSymbols(SymbolList, symbol, time_interval, session)


async def KLines(SSymbols, interval):
    """
    :param SSymbols:
    :param interval:
    :return:
    """
    time_interval = int(interval)

    AllList, DictEstimateStat, Symbols = {}, {}, []

    try:
        with open(f'json_files/SymbolList_{interval}.json', "r") as read_file:
            SymbolList = json.loads(read_file.read())
    except:
        SymbolList = {}

    sem = asyncio.Semaphore(50)

    tasks = []
    async with aiohttp.ClientSession(trust_env=True) as session:
        for symbol in SSymbols:
            tasks.append(asyncio.create_task(
                IMSymbols(SymbolList, symbol, time_interval, session, sem)))
        ListAllSymbols = await asyncio.gather(*tasks)

        for i in ListAllSymbols:
            for k, v in i.items():
                if int(len(np.array(v['close']))) == int(24 / (time_interval / 60) * 35):
                    AllList.update(i)
                    DictEstimateStat[k] = {
                        "time": v["time"],
                        "open": v["open"],
                        "close": v["close"]
                    }
                    Symbols.append(k)

    with open(f'json_files/SymbolsList_{interval}.json', 'w') as write_file:
        json.dump(AllList, write_file)

    return DictEstimateStat, list(filter(None, Symbols))


async def symbols():
    """
    :return:
    """
    while True:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                        f'https://api.bybit.com/derivatives/v3/public/tickers?category=linear',
                        ssl=False) as resp:
                    resp = await resp.json(content_type=None)
                    listSymbols = [i['symbol'] for i in resp['result']['list']
                                   if re.search(r'([^\s]+USDT)', i['symbol']) and
                                   i['symbol'] not in [
                                       'BUSDUSDT', 'USDCUSDT', 'XRPUSDT', 'CROUSDT', 'SUNUSDT', 'BSVUSDT', 'JSTUSDT'
                                   ] and not
                                   re.search(r'(1000[^\s]+USDT)|([^\s]+1000[^\s]+)', i['symbol'])
                                   ]
                    break
        except:
            logger.warning(f"ERROR Symbols")

    with open('json_files/symbols.json', 'w') as f:
        json.dump(listSymbols, f)

    return listSymbols


async def CoupleResults(symbolOne, symbolsTwo, DictEstimateStat):
    """
    :param symbolOne:
    :param symbolsTwo:
    :param DictEstimateStat:
    :return:
    """
    Couple, NoCouple = {}, {}

    # if Interval == MainInterval:
    func = symbolsTwo[symbolsTwo.index(symbolOne) + 1:]
    Num = 8
    # else:
    #     func = [symbolsTwo]
    #     Num = 120

    for symbolTwo in func:

        if len(DictEstimateStat[symbolOne]['close']) == len(DictEstimateStat[symbolTwo]['close']):

            DivideOpen = np.divide(DictEstimateStat[symbolOne]['open'], DictEstimateStat[symbolTwo]['open'])
            DivideClose = np.divide(DictEstimateStat[symbolOne]['close'], DictEstimateStat[symbolTwo]['close'])

            DBYOpen = DivideOpen[-3]
            DBYClose = DivideClose[-3]
            YdyClose = DivideClose[-2]

            if DBYOpen < DBYClose:
                BoolBar = 1 if YdyClose > DBYClose - (DBYClose - DBYOpen) / 2 else 0
            else:
                BoolBar = 1 if YdyClose < DBYClose + (DBYOpen - DBYClose) / 2 else 0

            ADFResult = adfuller(DivideClose, maxlag=1, autolag='AIC')
            # KPssResult = kpss(DivideClose, regression="c", nlags="auto")

            ZScore = list(zscore(DivideClose[-Num:]))[-1]
            ZScoreDBY = list(zscore(DivideClose[-Num - 2:-2]))[-1]
            ZScoreYdy = list(zscore(DivideClose[-Num - 1:-1]))[-1]

            if ADFResult[0] < ADFResult[4]['5%'] and ADFResult[1] < 0.05:
                Couple[f'{symbolOne.replace("USDT", "")}_{symbolTwo.replace("USDT", "")}'] = [
                    ADFResult[0], ADFResult[1], ZScore, ZScoreYdy, ZScoreDBY, BoolBar
                ]

            else:
                NoCouple[f'{symbolOne.replace("USDT", "")}_{symbolTwo.replace("USDT", "")}'] = [
                    ADFResult[0], ADFResult[1], ZScore, ZScoreYdy, ZScoreDBY, BoolBar
                ]

    return Couple, NoCouple


async def ResultTwo(couples):
    """

    :param couples:
    :return:
    """
    Couples, NoCouples = {}, {}

    for j in list(filter(None, [i[0] for i in couples])):
        Couples.update(j)

    for j in list(filter(None, [i[1] for i in couples])):
        NoCouples.update(j)

    return Couples, NoCouples


async def Estimate(Symbols, Interval):
    """

    :param Symbols:
    :param Interval:
    :return:
    """
    DictEstimateStat, SSymbols = await KLines(Symbols, Interval)

    couples = [await CoupleResults(symbolOne, SSymbols, DictEstimateStat) for symbolOne in SSymbols]

    Couples, NoCouples = await ResultTwo(couples)

    return Couples, NoCouples


async def StationaryCouples():

    Symbols = await symbols()
    CouplesResult, NoCouplesResult = await Estimate(Symbols, MainInterval)
    for count, _ in enumerate([0, 1]):
        if count == 0:
            file = CoupleResult
            result = CouplesResult

        else:
            file = NoCoupleResult
            result = NoCouplesResult

        JsonResultCouple = {"time": f"{datetime.now().strftime('%d-%m-%Y')} "
                                    f"{str(((datetime.now()) - timedelta(hours=1)).time()).split('.')[0]}",
                            "result": result}

        with open(file, 'w') as f:
            json.dump(JsonResultCouple, f)

