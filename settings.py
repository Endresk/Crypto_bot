import os

from pybit.unified_trading import HTTP
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())

TOKEN = os.getenv('TOKEN')

session_auth = HTTP(
    testnet=True,
    api_key=os.getenv('ApiKey'),
    api_secret=os.getenv('ApiSecret'),
)

user_id = os.getenv('USERID')

MainInterval = 1440

ListCouple = f'SymbolsList_{MainInterval}'

DU1 = 1.035
DD1 = 0.965

CoupleResult = 'json_files/CoupleResult.json'
NoCoupleResult = 'json_files/NoCoupleResult.json'

FileDataList = 'json_files/DataList.json'
FileSymbolsATR = 'json_files/SymbolsATR.json'

PointsMovement = 1

DAY = 30

STOPLOSS = 1.8
TAKEPROFIT = 3.6

Category = "linear"
Leverage = "12"
