import itertools
import time

import numpy as np

from settings import DAY


def ATR(df):
    DictATRTrue, DictATRFalse, Num, ListATR = {}, {}, 7, []

    LenBars = (np.max(df, axis=1).to_numpy() - np.min(df, axis=1).to_numpy()).tolist()

    while True:
        for i, j in itertools.product(range(2, Num), range(2, Num)):
            if i != j:
                jj = (LenBars[-j] / 2 - LenBars[-i]) / LenBars[-i] * 100

                if -7.5 > jj > -69.5:
                    DictATRTrue[i] = DictATRTrue.get(i, []) + [LenBars[-j]]
                else:
                    DictATRFalse[i] = DictATRFalse.get(i, []) + [LenBars[-j]]

        for keyI, valueI in DictATRTrue.items():
            if keyI in DictATRFalse:
                if len(valueI) >= len(DictATRFalse[keyI]):
                    ListATR.append(LenBars[-keyI])
            else:
                ListATR.append(LenBars[-keyI])
            if len(ListATR) == 5:
                break

        if len(ListATR) == 5:
            break
        else:
            ListATR, DictATRTrue, DictATRFalse = [], {}, {}
            Num += 1

        if Num == DAY:
            ListATR = [-1]
            break

    AverageTR = '{:.9f}'.format(sum(ListATR) / len(ListATR))
    CurrentATR = '{:.9f}'.format(np.abs(df.iloc[-2].close - df.iloc[-1].close))

    return AverageTR, CurrentATR
