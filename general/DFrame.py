import numpy as np
import pandas as pd
from datetime import datetime, timedelta


def DFrame(ListCoin):

    TitleDayList = np.array([f'{(datetime(1970, 1, 1) + timedelta(seconds=i))}'
                             for i in ListCoin['time']])

    Stock = pd.DataFrame({
        'open': np.array(ListCoin['open']),
        'close': np.array(ListCoin['close']),
        'high': np.array(ListCoin['high']),
        'low': np.array(ListCoin['low'])
    }, index=TitleDayList)

    return Stock, TitleDayList


def TwoCoupleValue(StockOne, StockTwo):

    Couple = pd.DataFrame(np.divide(StockOne.values, StockTwo.values), columns=StockOne.columns,
                          index=StockOne.index)
    return Couple
