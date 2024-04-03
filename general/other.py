import asyncio
import logging
import math
import sys
from decimal import Decimal
from time import time

import pandas as pd
from orjson import orjson
from prophet import Prophet
from tabulate import tabulate

from general.DFrame import DFrame, TwoCoupleValue
from general.graph_couple import Graph_couple
from settings import session_auth, ListCouple, MainInterval


def round_up(n, decimals=0):
    """

    :param n:
    :param decimals:
    :return:
    """
    multiplier = 10 ** decimals
    return math.floor(float(n) * multiplier) / multiplier


def func_chunks_generators(lst, n):
    """

    :param lst:
    :param n:
    """
    for i in range(0, len(lst), n):
        yield lst[i: i + n]


async def symbols_list():
    """

    :return:
    """
    list_symbols = {}

    while True:
        try:
            GetPosition = session_auth.get_positions(category="linear", settleCoin="USDT")['result']['list']
            for i in GetPosition:
                liqPrice = i['liqPrice']
                avgPrice = i['avgPrice']
                size = i['size']
                side = i['side']
                symbol = i['symbol']
                unrealisedPnl = i['unrealisedPnl']

                list_symbols[f'{symbol}_{side}'] = [{"ТВХ": round_up(avgPrice, 6)},
                                                    {"Ликвид": liqPrice},
                                                    {"PNL": unrealisedPnl},
                                                    {"Size": size}
                                                    ]

            break

        except Exception as e:
            print("ERROR list_symbols", e)
            await asyncio.sleep(5)

    return list_symbols


def ProphetCoupleCoins(stockOne, stockTwo):
    """

    :param stockOne:
    :param stockTwo:
    :return:
    """
    OverUnderOne, OverUnderTwo = '', ''

    for index, stock in enumerate([stockOne, stockTwo]):

        s = pd.DataFrame()
        s['ds'] = stock.index
        stock.reset_index(inplace=True)
        s['y'] = stock.close
        logging.disable(sys.maxsize)
        mOne = Prophet()
        mOne.fit(s)
        logging.disable(logging.NOTSET)

        future = mOne.make_future_dataframe(periods=0)
        forecast = mOne.predict(future)
        forecast = forecast[['ds', 'yhat', 'yhat_lower', 'yhat_upper']]

        if s.iloc[-1, 1] < forecast.iloc[-1, -2]:
            OverUnder = "Undervalued"
        elif s.iloc[-1, 1] > forecast.iloc[-1, -1]:
            OverUnder = "Overrated"
        else:
            OverUnder = "Usual"

        if index == 0:
            OverUnderOne = OverUnder
        else:
            OverUnderTwo = OverUnder

    return OverUnderOne, OverUnderTwo


def Interval(time):
    """

    :param time:
    :return:
    """
    if 60 <= time < 1400:
        Value = f'{round(time / 60)}h'
    elif 1 < time < 60:
        Value = f'{time}m'
    elif time == 1440:
        Value = 'D'
    elif time == 10080:
        Value = 'W'
    elif time == 43200:
        Value = 'M'
    else:
        Value = 'C'

    return Value


def ListEveryTabulate(OneSymbol, TwoSymbol, ValueCouple):
    """

    :param OneSymbol:
    :param TwoSymbol:
    :param ValueCouple:
    :return:
    """
    interval = Interval(MainInterval)
    t0 = time()

    with open(f'json_files/{ListCouple}.json', 'rb') as f:
        JsonListSymbols = orjson.loads(f.read())
    plot_file, y, Stock, stockOne, stockTwo = Graph_couple(OneSymbol, TwoSymbol).load(JsonListSymbols)

    # OverUnderOne, OverUnderTwo = ProphetCoupleCoins(stockOne, stockTwo)

    ListEvery = tabulate(
                    [
                        ['__Coin__', OneSymbol, TwoSymbol],
                        # ['Prophet', OverUnderOne, OverUnderTwo],
                        [f'ATR {interval}',
                         float('%g' % Decimal(ValueCouple['SOneATR'])),
                         float('%g' % Decimal(ValueCouple['STwoATR']))],
                        [f'CurATR {interval}',
                         float('%g' % Decimal(ValueCouple['SOneCurATR'])),
                         float('%g' % Decimal(ValueCouple['STwoCurATR']))],
                        ['__Couple__', interval],
                        ['PValue', float('%g' % Decimal(ValueCouple["PValue"][0]))],
                        ['ZScore', ValueCouple["ZScore"]],
                        ['ZScoreYdy', ValueCouple["ZScoreYdy"], ""],
                        ['ATR', ValueCouple["CoupleATR"]],
                        ['CurATR', ValueCouple["CoupleCurATR"]]
                    ],
                    tablefmt='simple',
                    showindex=False,
                    colalign=("right", "left", "left")
    )

    return ListEvery, plot_file, y, Stock
