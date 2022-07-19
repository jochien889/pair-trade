from datetime import datetime

import pandas as pd
import requests
import json
from enum import Enum
import time
import hashlib
import hmac

class OrderType(Enum):
    """
    Order type
    """
    LIMIT = "LIMIT"
    MARKET = "MARKET"
    STOP = "STOP"
    TAKE_PROFIT = "TAKE_PROFIT"
    STOP_MARKET = "STOP_MARKET"
    TAKE_PROFIT_MARKET = "TAKE_PROFIT_MARKET"
    TRAILING_STOP_MARKET = "TRAILING_STOP_MARKET"


class RequestMethod(Enum):
    """
    Request methods
    """
    GET = 'GET'
    POST = 'POST'
    PUT = 'PUT'
    DELETE = 'DELETE'

class positionside(Enum):
    BOTH = 'BOTH'
    LONG = 'LONG'
    SHORT = 'SHORT'

class TimeInForce(Enum):
    GTC="GTC"
    IOD="IOC"
    FOK="FOK"
    GTX="GTX"

class Interval(Enum):
    """
    Interval for klines
    """
    MINUTE_1 = '1m'
    MINUTE_3 = '3m'
    MINUTE_5 = '5m'
    MINUTE_15 = '15m'
    MINUTE_30 = '30m'
    HOUR_1 = '1h'
    HOUR_2 = '2h'
    HOUR_4 = '4h'
    HOUR_6 = '6h'
    HOUR_8 = '8h'
    HOUR_12 = '12h'
    DAY_1 = '1d'
    DAY_3 = '3d'
    WEEK_1 = '1w'
    MONTH_1 = '1M'


class OrderSide(Enum):
    """
    order side
    """
    BUY = "BUY"
    SELL = "SELL"

class RequestMethod(Enum):
    GET = "get"
    POST = "post"
    DELETE = "delete"
    PUT = "put"

class contractType(Enum):
    PERPETUAL = "PERPETUAL"
    CURRENT_MONTH = "CURRENT_MONTH"
    NEXT_MONTH = "NEXT_MONTH"
    CURRENT_QUARTER = "CURRENT_QUARTER"
    NEXT_QUARTER = "NEXT_QUARTER"

class BinanceHttp(object):

    def __init__(self, marketType='Spot', api_key=None, api_secret=None, timeout=5):
        """Binance Http api config
        Args:
            base_url_type ([str], optional): market type select. Defaults to Spot. (e.g : Spot, USDT-Futures, COIN-Futures, Vanilla.) 
            market_type_config = {
                                    Spot : https://api.binance.com,
                                    Spot1 : https://api1.binance.com, 
                                    Spot2 : https://api2.binance.com, 
                                    Spot3 : https://api3.binance.com, 
                                    USDTFutures : https://fapi.binance.com, 
                                    COINFutures : https://dapi.binance.com, 
                                    Vanilla : https://vapi.binance.com
                                   }
            timeout (int, optional): Defaults to 5.
        """
        self.config = {
                        "Spot" : "https://api.binance.com",
                        "Spot1" : "https://api1.binance.com", 
                        "Spot2" : "https://api2.binance.com", 
                        "Spot3" : "https://api3.binance.com", 
                        "USDTFutures" : "https://fapi.binance.com", 
                        "COINFutures" : "https://dapi.binance.com", 
                        "Vanilla" : "https://vapi.binance.com"
                       }
        self.type = marketType
        self.key = api_key
        self.secret = api_secret
        self.base_url = self.config[self.type]
        self.timeout = timeout

    def build_parameters(self, params:dict):
        '''
        dict convert to url body
        '''
        requery = '&'.join(f"{key}={params[key]}" for key in params.keys())
        return requery

    def request(self, method: RequestMethod, path, params=None, verify=False):
        '''
        request method
        '''
        url = self.base_url + path

        if params:
            url = url + '?' + self.build_parameters(params)

        if verify:
            query_str = self.build_parameters(params)
            signature = hmac.new(self.secret.encode('utf-8'), msg=query_str.encode('utf-8'),
                                 digestmod=hashlib.sha256).hexdigest()
            url += '&signature=' + signature

        headers = {"X-MBX-APIKEY": self.key}
        return requests.request(method.value, url, headers=headers, timeout=self.timeout).json()


    def get_server_time(self):
        '''
        binance server time
        '''
        path = '/fapi/v1/time' if self.type == 'USDTFutures' else '/dapi/v1/time' if self.type == 'COINFutures' else '/vapi/v1/time' if self.type == 'Vanilla' else '/api/v3/time'
        return self.request(RequestMethod.GET, path)
    
    def get_server_status(self):
        path = '/fapi/v1/ping' if self.type == 'USDTFutures' else '/dapi/v1/ping' if self.type == 'COINFutures' else '/vapi/v1/ping' if self.type == 'Vanilla' else '/api/v3/ping'
        return self.request(RequestMethod.GET, path)

    def get_exchange_info(self):
        """
        coin list
        """
        path = '/fapi/v1/exchangeInfo' if self.type == 'USDTFutures' else '/dapi/v1/exchangeInfo' if self.type == 'COINFutures' else '/api/v3/exchangeInfo'        
        return self.request(RequestMethod.GET, path)
    
    def get_kline(self, symbol, interval: Interval, start_time=None, end_time=None, limit=1000):
        path = '/fapi/v1/klines' if self.type == 'USDTFutures' else '/dapi/v1/klines' if self.type == 'COINFutures' else '/api/v3/klines'
        params = {"symbol":symbol,
                  "interval":interval.value,
                  "limit":limit
                  }        
        if start_time:
            params['startTime'] = start_time

        if end_time:
            params['endTime'] = end_time
            
        return self.request(RequestMethod.GET, path, params=params)
    
    def get_continuousKlines(self, pair, interval: Interval, start_time=None, end_time=None, limit=1000):

        '''
            取得U本位合約的K線資料
        :param pair:交易對 ex:BTCUSDT or ETHUSDT ...
        :param contractType:contractType 永續的話就填contractType.PERPETUAL
        :param interval:參照上面的Interval Class 5分K資料的話就填 Interval.MINUTE_5
        :param start_time:可不填
        :param end_time:可不填
        :param limit:預設1000根K棒 可根據自己需要的填入
        '''
        path = '/fapi/v1/continuousKlines' if self.type == 'USDTFutures' else '/dapi/v1/continuousKlines' 
        params = {"pair":pair,
                  "contractType":contractType.value,
                  "interval":interval.value,
                  "limit":limit
                  }

        if start_time:
            params['startTime'] = start_time

        if end_time:
            params['endTime'] = end_time

        return self.request(RequestMethod.GET, path, params=params)

    def get_timestamp(self):
        '''
            取得當前電腦端時間
        '''
        return int(time.time() * 1000)