from time import sleep, time

import pandas as pd
import numpy as np
import plotly.graph_objects as go
from threading import Thread
from io import BytesIO

from orjson import orjson
from sklearn.linear_model import LinearRegression
from general.DFrame import TwoCoupleValue, DFrame
from settings import DD1, DU1


class Graph_couple(Thread):

    def __init__(self, one, two):
        Thread.__init__(self)

        self.one = one
        self.two = two

    def load(self, JsonListSymbol):
        t0 = time()
        StockOne, TitleDayList = DFrame(JsonListSymbol[f'{self.one}USDT'])
        StockTwo, _ = DFrame(JsonListSymbol[f'{self.two}USDT'])

        stock_ = TwoCoupleValue(StockOne, StockTwo)

        df = pd.DataFrame({'time': TitleDayList,
                           'count': stock_.close})

        df["time"] = pd.to_datetime(df.time)

        model = LinearRegression()
        model.fit(df.time.values.reshape(-1, 1), df['count'])

        y = model.predict(df.time.values.astype(float).reshape(-1, 1))

        df['pred'] = y

        go_candles = go.Candlestick(x=np.array(stock_.index),
                                    open=np.array(stock_.open),
                                    high=np.array(stock_.high),
                                    close=np.array(stock_.close),
                                    low=np.array(stock_.low),
                                    name='Figure'
                                    )

        go_sca = go.Scatter(x=np.array(TitleDayList),
                            y=y,
                            mode='lines',
                            line={'color': 'gold', 'width': 2},
                            name='Regression Line'
                            )

        go_scaUP = go.Scatter(x=np.array(TitleDayList),
                              y=y * DU1,
                              mode='lines',
                              line={'color': 'turquoise', 'width': 2},
                              name='UP'
                              )

        go_scaDOWN = go.Scatter(x=np.array(TitleDayList),
                                y=y * DD1,
                                mode='lines',
                                line={'color': 'turquoise', 'width': 2},
                                name='DOWN'
                                )

        layout = go.Layout(
            autosize=False,
            width=1920,
            height=1200,
            template='plotly_dark'
        )

        try:

            with open('json_files/DataCouples.json', "rb") as read_file:
                DataCouples = orjson.loads(read_file.read())

            StatData = DataCouples[f'{self.one}USDT_{self.two}USDT']
            EntryPrice = StatData['EntryPrice']
            DateTime = StatData['DateTime']

            go_Point = go.Scatter(x=[DateTime],
                                  y=[EntryPrice],
                                  mode='markers',
                                  line={'color': 'white', 'width': 12},
                                  name='Entry Price',
                                  marker=dict(line=dict(color='turquoise', width=6))
                                  )
            fig = go.Figure(
                data=[go_candles, go_sca, go_scaUP, go_scaDOWN, go_Point],
                layout=layout)
        except:

            fig = go.Figure(
                data=[go_candles, go_sca, go_scaUP, go_scaDOWN],
                layout=layout)

        fig.update_layout(xaxis_rangeslider_visible=False, title=f"{self.one} / {self.two}")

        plot_file = BytesIO()

        fig_svg = fig.to_image(format="PNG")
        plot_file.write(fig_svg)
        plot_file.seek(0)

        return plot_file, y, stock_, StockOne, StockTwo
