"""
Normalized Last, Book, Candles

Binance, Bitfinex, Bittrex, Coinbase, Kraken, Kucoin, Poloniex

litepresence 2019
"""
# pylint: disable=broad-except, too-many-lines
# pylint: disable=too-many-locals, too-many-statements, too-many-branches


# STANDARD MODULES
import os
import time
from json import dumps as json_dumps
from math import ceil
from multiprocessing import Process, Value
from pprint import pprint

# THIRD PARTY MODULES
import numpy as np
import requests

# CEX MODULES
from utilities import (from_iso_date, json_ipc, symbol_syntax, to_iso_date,
                       trace)

# GLOBAL USER DEFINED CONSTANTS
TIMEOUT = 30
ATTEMPTS = 10
PATH = str(os.path.dirname(os.path.abspath(__file__))) + "/"
DETAIL = False

# READ ME
def read_me():
    """
    MODULE USAGE

    from public_cex import price, klines, depth

    price = get_price(api))
    book = get_book(api, depth))
    candles = get_candles(api, interval, start, end))

    # api contains keys ["pair" and "exchange"]; expanded form:
    # get_price(api={"pair":"BTC:USD", "exchange":"coinbase"})

    ABOUT

    Only supports top ranked exchanges with real volume over $10m daily
    unified API inputs
    normalized return as dict of numpys
    pep8 / pylint
    procedural Python - no class objects
    external requests multiprocess wrapped
    architecture sorted by call type
    human readable interprocess communication via *.txt
    easy to compare exchange parameters

    EXCHANGE RANKINGS

    https://www.sec.gov/comments/sr-nysearca-2019-01/srnysearca201901-5164833-183434.pdf

    https://www.coingecko.com/en/exchanges
    https://www.cryptocompare.com/exchanges
    https://www.bti.live/exchanges/
    https://bitcoinexchangeguide.com/bitcoin-exchanges-in-the-united-states/
    https://coin.market/exchanges
    https://cryptorank.io/exchanges

    https://docs.kucoin.com/

    ADDITIONAL EXCHANGES

    Exchange addition PR's considered on case by case basis.
    $10m minimum daily - legitimate - volume
    """
    print(read_me.__doc__)


def api_docs():
    """
    API DOCS

    https://bittrex.github.io/api/v1-1
    https://github.com/thebotguys/golang-bittrex-api/
        wiki/Bittrex-API-Reference-(Unofficial)

    https://docs.bitfinex.com/reference

    https://docs.pro.coinbase.com/

    https://docs.poloniex.com/#introduction

    https://binance-docs.github.io/apidocs/spot/en/#change-log

    https://www.kraken.com/features/api
    https://github.com/veox/python3-krakenex
    https://support.kraken.com/hc/en-us/categories/360000080686-API
    """
    print(api_docs.__doc__)


# SUBPROCESS REMOTE PROCEDURE CALL
def request(api, signal):
    """
    GET remote procedure call to public exchange API
    """
    urls = {
        "coinbase": "https://api.pro.coinbase.com",
        "bittrex": "https://bittrex.com",
        "bitfinex": "https://api-pub.bitfinex.com",
        "kraken": "https://api.kraken.com",
        "poloniex": "https://www.poloniex.com",
        "binance": "https://api.binance.com",
        "kucoin": "https://api.kucoin.com",
    }

    api["method"] = "GET"
    api["headers"] = {}
    api["data"] = ""
    api["key"] = ""
    api["passphrase"] = ""
    api["secret"] = ""
    api["url"] = urls[api["exchange"]]

    url = api["url"] + api["endpoint"]
    if DETAIL:
        print(api)
        print(url)
    time.sleep(1)
    # /api/v1/market/orderbook/level1?symbol=BTC-USDT

    resp = requests.request(
        method=api["method"],
        url=url,
        data=api["data"],
        params=api["params"],
        headers=api["headers"],
    )
    data = resp.json()

    if DETAIL:
        print(resp)
        print(data)
        if isinstance(data, dict):
            print("dict keys", data.keys())
            if "message" in data.keys():
                print(data)
        elif isinstance(data, list):
            print("list len", len(data))
        else:
            print(data)
        print("len request data", len(data))
    doc = (
        api["exchange"]
        + api["pair"]
        + str(int(10 ** 6 * api["nonce"]))
        + "_{}_private.txt".format(api["exchange"])
    )
    json_ipc(doc, json_dumps(data))
    signal.value = 1


def process_request(api):
    """
    Multiprocessing Durability Wrapper for External Requests
    interprocess communication via durable text pipe
    """
    begin = time.time()
    # multiprocessing completion signal
    signal = Value("i", 0)
    # several iterations of external requests until satisfied with response
    i = 0
    while (i < ATTEMPTS) and not signal.value:
        # multiprocessing text file name nonce
        api["nonce"] = time.time()
        i += 1
        if DETAIL:
            print("")
            print(
                "{} {} PUBLIC attempt:".format(api["exchange"], api["pair"]),
                i,
                time.ctime(),
                int(time.time()),
            )
        child = Process(target=request, args=(api, signal))
        child.daemon = False
        child.start()
        child.join(TIMEOUT)
        child.terminate()
        time.sleep(i ** 2)
    # the doc was created by the subprocess; read and destroy it
    doc = (
        api["exchange"]
        + api["pair"]
        + str(int(10 ** 6 * api["nonce"]))
        + "_{}_private.txt".format(api["exchange"])
    )
    data = json_ipc(doc)
    path = PATH + "pipe/"
    if os.path.isfile(path + doc):
        os.remove(path + doc)
    if DETAIL:
        print(
            "{} {} PUBLIC elapsed:".format(api["exchange"], api["pair"]),
            ("%.2f" % (time.time() - begin)),
        )
        print("")
    return data


# METHODS


def get_price(api):
    """
    Last Price as float
    """
    exchange = api["exchange"]
    symbol = symbol_syntax(exchange, api["pair"])
    endpoints = {
        "bittrex": "/api/v1.1/public/getticker",
        "bitfinex": "/v2/ticker/t{}".format(symbol),
        "binance": "/api/v1/ticker/allPrices",
        "poloniex": "/public",
        "coinbase": "/products/{}/ticker".format(symbol),
        "kraken": "/0/public/Ticker",
        "kucoin": "/api/v1/market/orderbook/level1",
    }
    params = {
        "bittrex": {"market": symbol},
        "bitfinex": {"market": symbol},
        "binance": {},
        "poloniex": {"command": "returnTicker"},
        "coinbase": {"market": symbol},
        "kraken": {"pair": [symbol]},
        "kucoin": {"symbol": symbol},
    }
    api["endpoint"] = endpoints[exchange]
    api["params"] = params[exchange]
    while 1:

        try:
            data = process_request(api)
            if exchange == "bittrex":
                last = float(data["result"]["Last"])
            elif exchange == "bitfinex":
                last = float(data[6])
            elif exchange == "binance":
                data = {d["symbol"]: float(d["price"]) for d in data}
                last = data[symbol]
            elif exchange == "poloniex":
                last = float(data[symbol]["last"])
            elif exchange == "coinbase":
                last = float(data["price"])
            elif exchange == "kraken":
                data = data["result"]
                data = data[list(data)[0]]
                last = float(data["c"][0])
            elif exchange == "kucoin":
                last = float(data["data"]["price"])
        except Exception as error:
            print(trace(error), {k: v for k, v in api.items() if k != "secret"})
        break

    return last


def get_book(api, depth=10):
    """
    Depth of Market format:

    {"bidv": [], "bidp": [], "askp": [], "askv": []}
    """
    exchange = api["exchange"]
    symbol = symbol_syntax(exchange, api["pair"])
    if depth > 50:
        depth = 50

    endpoints = {
        "bittrex": "/api/v1.1/public/getorderbook",
        "bitfinex": "/v2/book/t{}/P0".format(symbol),
        "binance": "/api/v1/depth",
        "poloniex": "/public",
        "coinbase": "/products/{}/book".format(symbol),
        "kraken": "/0/public/Depth",
        "kucoin": "/api/v1/market/orderbook/level2_100",
    }
    params = {
        "bittrex": {"market": symbol, "type": "both"},
        "bitfinex": {"len": 100},
        "binance": {"symbol": symbol},
        "poloniex": {"command": "returnOrderBook", "currencyPair": symbol},
        "coinbase": {"level": 2},
        "kraken": {"pair": symbol, "count": "50"},
        "kucoin": {"symbol": symbol},
    }
    api["endpoint"] = endpoints[exchange]
    api["params"] = params[exchange]

    while 1:
        try:
            data = process_request(api)
            if exchange == "kraken":
                data = data["result"]
                data = data[list(data)[0]]
            if exchange == "bittrex":
                data = data["result"]
            if exchange == "kucoin":
                data = data["data"]

            # convert books to unified format
            book = {"bidv": [], "bidp": [], "askp": [], "askv": []}
            if exchange in ["binance", "poloniex", "coinbase", "kraken", "kucoin"]:
                # {"bids" [[,],[,],[,]], "asks": [[,],[,],[,]]}
                for i in range(len(data["bids"])):
                    book["bidv"].append(float(data["bids"][i][1]))
                    book["bidp"].append(float(data["bids"][i][0]))
                for i in range(len(data["asks"])):
                    book["askv"].append(float(data["asks"][i][1]))
                    book["askp"].append(float(data["asks"][i][0]))
            elif exchange == "bittrex":
                # {"bids": [{Quantity:, "Rate"},...,],
                #  "asks": [{Quantity:, "Rate"},...,]}
                for _, item in enumerate(data["buy"]):
                    book["bidv"].append(float(item["Quantity"]))
                    book["bidp"].append(float(item["Rate"]))
                for _, item in enumerate(data["sell"]):
                    book["askv"].append(float(item["Quantity"]))
                    book["askp"].append(float(item["Rate"]))
            elif exchange == "bitfinex":
                # [[,,],[,,],[,,]] # bids negative volume
                for _, item in enumerate(data):
                    if item[2] > 0:
                        book["bidv"].append(float(item[2]))
                        book["bidp"].append(float(item[0]))
                    else:
                        book["askv"].append(-float(item[2]))
                        book["askp"].append(float(item[0]))
                # book = {k:v[::-1] for k, v in book.items()}

            # normalize lowest ask and highest bid to [0] position
            book["bidv"] = [v for p, v in sorted(zip(book["bidp"], book["bidv"]))]
            book["askv"] = [v for p, v in sorted(zip(book["askp"], book["askv"]))]
            book["bidp"] = sorted(book["bidp"])
            book["askp"] = sorted(book["askp"])
            book["bidv"] = book["bidv"][::-1]
            book["bidp"] = book["bidp"][::-1]
            # standardize book depth
            book["bidv"] = book["bidv"][:depth]
            book["bidp"] = book["bidp"][:depth]
            book["askv"] = book["askv"][:depth]
            book["askp"] = book["askp"][:depth]

            book = {k: np.array(v) for k, v in book.items()}
            if DETAIL:
                print("total bids:", len(book["bidp"]))
                print("total asks:", len(book["askp"]))
        except Exception as error:
            print(trace(error), {k: v for k, v in api.items() if k != "secret"})
        break

    return book


def get_candles(api, start=None, end=None, interval=86400):
    """
    input and output normalized requests for candle data
    returns a dict with numpy array values for the following keys
    ["high", "low", "open", "close", "volume", "unix"]
    where unix is int and the remainder are float
    this is the ideal format for utilizing talib / tulip indicators
    """

    def paginate_candles(api, start, end, interval):
        """
        paginate requests per maximum request size per exchange
        collate responses crudely with overlap

        # USE FOR EDGE MATCHING DEV
        max_candles = {
            "bittrex": 100,
            "bitfinex": 100,
            "binance": 100,
            "poloniex": 100,
            "coinbase": 100,
            "kraken": 100,
            "kucoin": 100,
        }
        """
        max_candles = {
            "bittrex": 1000,  # 1000
            "bitfinex": 10000,  # 10000
            "binance": 500,  # 1000
            "poloniex": 2000,
            "coinbase": 300,  # 300
            "kraken": 200,  # 200
            "kucoin": 1500,  # 1500
        }
        overlap = 2
        # fetch the max candles at this exchange
        max_candles = max_candles[exchange] - (2 * overlap + 1)
        # define the maximum exchange window in seconds
        window = int(max_candles * interval)
        # determine number of candles we require
        depth = int(ceil((end - deep_begin) / float(interval)))
        # determine number of calls required to get those candles
        calls = int(max(ceil(depth / float(max_candles)), 1))
        # pagination and crude collation
        stop = end
        if calls > 1:
            data = []
            for call in range(calls, 0, -1):
                # overlap on each end
                end = stop - ((call - 1) * window) + (overlap * interval)
                start = stop - (call * window) - (overlap * interval)
                print("call", call, "/", calls, start, end)
                datum = candles(api, start, end, interval)
                time.sleep(1)
                data += datum
        # single request
        else:
            data = candles(api, deep_begin, end, interval)

        return data

    def remove_null(data):
        """
        Ensure all data in list are dicts with a "unix" key
        """
        data = [i for i in data if isinstance(i, dict)]
        data = [i for i in data if "unix" in i]

        return data

    def no_duplicates(data):
        """
        ensure no duplicates due to pagination overlap at edges
        """
        dup_free = []
        timestamps = []
        for _, item in enumerate(data):
            if item["unix"] not in timestamps:
                timestamps.append(item["unix"])
                dup_free.append(item)

        return dup_free

    def sort_by_unix(data):
        """
        pagination may still be backwards and segmented; resort by timestamp
        """
        data = sorted(data, key=lambda k: k["unix"])

        return data

    def interpolate_previous(data, start, end, interval):
        """
        candles may be missing; fill them in with previous close
        """
        start = int(start)
        end = int(end)
        interval = int(interval)
        ip_unix = [*range(min(data["unix"]), max(data["unix"]), interval)]
        out = {
            "high": [],
            "low": [],
            "open": [],
            "close": [],
            "volume": [],
            "unix": ip_unix,
        }
        for _, candle in enumerate(ip_unix):
            for idx, _ in enumerate(data["unix"]):

                match = False
                diff = candle - data["unix"][idx]

                if 0 <= diff < interval:
                    match = True
                    out["volume"].append(data["volume"][idx])
                    out["high"].append(data["high"][idx])
                    out["low"].append(data["low"][idx])
                    out["open"].append(data["open"][idx])
                    out["close"].append(data["close"][idx])
                    break

            if not match:
                if candle == start:
                    close = data["close"][0]
                else:
                    close = out["close"][-1]
                out["volume"].append(0)
                out["high"].append(close)
                out["low"].append(close)
                out["open"].append(close)
                out["close"].append(close)

        if DETAIL:
            for key, val in out.items():
                print(len(val), key)

        return out

    def window_data(data, start, end):
        """
        Ensure we do not return any data outside requested window

        # use this instead if still in list of dict form
        # d2 = []
        # for index, item in enumerate(data):
        #     if start < item["unix"] < end:
        #        d2.append(item)
        """
        out = {"high": [], "low": [], "open": [], "close": [], "volume": [], "unix": []}

        for idx, item in enumerate(data["unix"]):
            if start < item <= end:
                out["high"].append(data["high"][idx])
                out["low"].append(data["low"][idx])
                out["open"].append(data["open"][idx])
                out["close"].append(data["close"][idx])
                out["volume"].append(data["volume"][idx])
                out["unix"].append(data["unix"][idx])

        return out

    def left_strip(data):
        """
        Remove no volume candles in beginning of dataset
        """
        out = {"high": [], "low": [], "open": [], "close": [], "volume": [], "unix": []}
        begin = False

        for idx, item in enumerate(data["volume"]):
            if item or begin:
                begin = True
                out["high"].append(data["high"][idx])
                out["low"].append(data["low"][idx])
                out["open"].append(data["open"][idx])
                out["close"].append(data["close"][idx])
                out["volume"].append(data["volume"][idx])
                out["unix"].append(data["unix"][idx])

        return out

    def reformat(data):
        """
        switch from list-of-dicts to dict-of-lists
        """
        list_format = {}
        list_format["unix"] = []
        list_format["high"] = []
        list_format["low"] = []
        list_format["open"] = []
        list_format["close"] = []
        list_format["volume"] = []
        for _, item in enumerate(data):
            list_format["unix"].append(item["unix"])
            list_format["high"].append(item["high"])
            list_format["low"].append(item["low"])
            list_format["open"].append(item["open"])
            list_format["close"].append(item["close"])
            list_format["volume"].append(item["volume"])

        return list_format

    def normalize(data):
        """
        ensure high is high and low is low
        filter extreme candatales at 0.5X to 2X the candatale average
        ensure open and close are within high and low
        """

        for i, _ in enumerate(data["close"]):

            data["high"][i] = max(
                data["high"][i], data["low"][i], data["open"][i], data["close"][i]
            )
            data["low"][i] = min(
                data["high"][i], data["low"][i], data["open"][i], data["close"][i]
            )
            ocl = (data["open"][i] + data["close"][i] + data["low"][i]) / 3
            och = (data["open"][i] + data["close"][i] + data["high"][i]) / 3
            data["high"][i] = min(data["high"][i], 2 * ocl)
            data["low"][i] = max(data["low"][i], och / 2)
            data["open"][i] = min(data["open"][i], data["high"][i])
            data["open"][i] = max(data["open"][i], data["low"][i])
            data["close"][i] = min(data["close"][i], data["high"][i])
            data["close"][i] = max(data["close"][i], data["low"][i])

        return data

    exchange = api["exchange"]
    if end is None:
        # to current
        end = int(time.time())
    if start is None:
        # default 10 candles
        start = end - 10 * interval
    # allow for timestamp up to one interval and one minute in future.
    end = end + interval + 60
    # request 3 candles deeper than needed
    deep_begin = start - 3 * interval

    print("\nstart:", to_iso_date(start), "end:", to_iso_date(end))
    while True:
        try:
            # collect external data in pages if need be
            data = paginate_candles(api, deep_begin, end, interval)
            if DETAIL:
                print(len(data), "paginated with overlap and collated")
            data = remove_null(data)
            if DETAIL:
                print(len(data), "null data removed")
            data = no_duplicates(data)
            if DETAIL:
                print(len(data), "edge match - no duplicates by unix")
            data = sort_by_unix(data)
            if DETAIL:
                print(len(data), "edge match - sort by unix")
            data = reformat(data)
            if DETAIL:
                print(len(data["unix"]), "rotation; reformated to dict of lists")
            data = interpolate_previous(data, deep_begin, end, interval)
            if DETAIL:
                print(
                    len(data["unix"]),
                    len(data["close"]),
                    "missing buckets to candles interpolated as previous close",
                )
            data = window_data(data, start, end)
            if DETAIL:
                print(len(data["unix"]), "windowed to intial start / end request")
            data = left_strip(data)
            if DETAIL:
                print(len(data["unix"]), "stripped of empty pre market candles")
            data = normalize(data)
            if DETAIL:
                print({k: len(v) for k, v in data.items()})
            if DETAIL:
                print("normalized as valid: high is highest, no extremes, etc.")
            data = {k: np.array(v) for k, v in data.items()}
            if DETAIL:
                print("final conversion to dict of numpy arrays:\n")
            print(
                "total items",
                len(data),
                "/",
                len(data["unix"]),
                "keys",
                data.keys(),
                "type",
                type(data["unix"]),
            )
            print("\n\nRETURNING", exchange.upper(), api["pair"], "CANDLE DATA\n\n")

            return data

        except Exception as error:
            msg = trace(error)
            print(msg, data, {k: v for k, v in api.items() if k != "secret"})
            continue


def candles(api, start, end, interval):
    """
    single page of candle data
    """
    exchange = api["exchange"]
    symbol = symbol_syntax(exchange, api["pair"])
    limit = int(float(end - start) / interval) + 1
    intervals = {
        "bittrex": {
            60: "oneMin",
            300: "fiveMin",
            1800: "thirtyMin",
            3600: "hour",
            86400: "day",
        },
        "bitfinex": {
            60: "1m",
            300: "5m",
            900: "15m",
            1800: "30m",
            3600: "1h",
            10800: "3h",
            21600: "6h",
            43200: "12h",
            86400: "1D",
            604800: "7D",
            1209600: "14D",
            2419200: "1M",
        },
        "binance": {
            60: "1m",
            180: "3m",
            300: "5m",
            900: "15m",
            1800: "30m",
            3600: "1h",
            14400: "4h",
            21600: "6h",
            28800: "8h",
            43200: "12h",
            86400: "1d",
            604800: "1w",
            2419200: "1M",
        },
        "poloniex": {
            300: 300,
            900: 900,
            1800: 1800,
            7200: 7200,
            14400: 14000,
            86400: 86400,
        },
        "coinbase": {
            60: 60,
            300: 300,
            900: 900,
            3600: 3600,
            21600: 21600,
            86400: 86400,
        },
        "kraken": {
            60: 1,
            300: 5,
            900: 15,
            1800: 30,
            3600: 60,
            14400: 240,
            86400: 1440,
            604800: 10080,
            2419200: 21600,
        },
        "kucoin": {
            60: "1min",
            180: "3min",
            300: "5min",
            900: "15min",
            1800: "30min",
            3600: "1hour",
            7200: "2hour",
            14400: "4hour",
            21600: "6hour",
            28800: "8hour",
            43200: "12hour",
            86400: "1day",
            604800: "1week",
        },
    }

    try:
        bitfinex_hist = "".join(
            [i for i in intervals["bitfinex"][interval] if not i.isdigit()]
        )
        interval_raw = interval
        interval = intervals[exchange][interval]
    except Exception as error:
        trace(error)
        print("Invalid interval for this exchange")
        print(exchange, symbol, interval)
        pprint(intervals)

    endpoints = {
        "bittrex": "/api/v2.0/pub/market/GetTicks",
        "bitfinex": "/v2/candles/trade:1{}:t{}/hist".format(bitfinex_hist, symbol),
        "binance": "/api/v1/klines",
        "poloniex": "/public",
        "coinbase": "/products/{}/candles".format(symbol),
        "kraken": "/0/public/OHLC",
        "kucoin": "/api/v1/market/candles",
    }
    params = {
        "bittrex": {"marketName": symbol, "tickInterval": interval},
        "bitfinex": {"granularity": interval, "limit": limit},
        "binance": {"symbol": symbol, "interval": interval},
        "poloniex": {
            "command": "returnChartData",
            "currencyPair": symbol,
            "period": interval,
        },
        "coinbase": {"granularity": interval},
        "kraken": {"pair": symbol, "interval": interval},
        "kucoin": {"symbol": symbol, "type": interval},
    }
    windows = {
        "bittrex": {},  # {"_": ???}, # FIXME NO DOCS BETA
        "bitfinex": {"start": 1000 * start, "end": 1000 * end},
        "binance": {"startTime": 1000 * start, "endTime": 1000 * end},
        "poloniex": {"start": start, "end": end},
        "coinbase": {"start": to_iso_date(start), "end": to_iso_date(end)},
        "kraken": {"since": start},
        "kucoin": {"startAt": int(start), "endAt": int(end)},  # unix
    }
    if exchange == "bitfinex" and int(time.time()) - end < interval_raw:
        windows["bitfinex"].pop("end")

    api["endpoint"] = endpoints[exchange]
    api["params"] = params[exchange]
    api["params"].update(windows[exchange])

    try:
        data = process_request(api)
        if exchange == "bittrex":
            data = data["result"]
            data = [
                {
                    "open": float(d["O"]),
                    "high": float(d["H"]),
                    "low": float(d["L"]),
                    "close": float(d["C"]),
                    "volume": float(d["V"]),
                    "unix": from_iso_date(d["T"]),
                }
                for d in data
                if start < from_iso_date(d["T"]) <= end
            ]

        elif exchange == "bitfinex":
            data = [
                {
                    "unix": int(float(d[0]) / 1000.0),
                    "open": float(d[1]),
                    "close": float(d[2]),
                    "high": float(d[3]),
                    "low": float(d[4]),
                    "volume": float(d[5]),
                }
                for d in data
                if start <= int(float(d[0]) / 1000.0) <= end
            ]
        elif exchange == "binance":
            data = [
                {
                    "open": float(d[1]),
                    "high": float(d[2]),
                    "low": float(d[3]),
                    "close": float(d[4]),
                    "volume": float(d[5]),
                    "unix": int(int(d[6]) / 1000.0),
                }
                for d in data
            ]
        elif exchange == "poloniex":
            data = [
                {
                    "open": float(d["open"]),
                    "high": float(d["high"]),
                    "low": float(d["low"]),
                    "close": float(d["close"]),
                    "volume": float(d["quoteVolume"]),
                    "unix": int(d["date"]),
                }
                for d in data
            ]
        elif exchange == "coinbase":
            data = [
                {
                    "unix": int(d[0]),
                    "low": float(d[1]),
                    "high": float(d[2]),
                    "open": float(d[3]),
                    "close": float(d[4]),
                    "volume": float(d[5]),
                }
                for d in data
            ]
        elif exchange == "kraken":
            data = data["result"]
            data = data[list(data)[0]]
            data = [
                {
                    "unix": int(d[0]),
                    "open": float(d[1]),
                    "high": float(d[2]),
                    "low": float(d[3]),
                    "close": float(d[4]),
                    # vwap d[5]
                    "volume": float(d[6]),
                }
                for d in data
            ]
        elif exchange == "kucoin":
            data = data["data"]
            data = [
                {
                    "unix": int(d[0]),
                    "open": float(d[1]),
                    "close": float(d[2]),
                    "high": float(d[3]),
                    "low": float(d[4]),
                    "volume": float(d[5]),
                }
                for d in data
            ]
    except Exception as error:
        print(trace(error), {k: v for k, v in api.items() if k != "secret"})
        data = []

    return data


# DEMONSTRATION


def demo(api):
    """
    Print demo of last price, orderbook, and candles
    Formatted to extinctionEVENT standards
    """
    exchange = api["exchange"]

    print("\n***", exchange.upper(), "PRICE ***")
    pprint(get_price(api))
    print("\n***", exchange.upper(), "BOOK ***")
    depth = 50
    pprint(get_book(api, depth))
    # kline request parameters
    interval = 86400
    # None / None will return latest ten candles
    start = None  # or unix epoch seconds
    end = None  # or unix epoch seconds
    print("\n***", exchange.upper(), "CANDLES ***")
    now = int(time.time())
    depth = 100
    start = now - interval * depth
    end = now
    pprint(get_candles(api, start, end, interval))


def main():
    """
    Primary Demonstration Events
    """
    print("\033c", __doc__)
    read_me()
    api_docs()
    api = {}
    api["pair"] = "LTC:BTC"
    exchanges = [
        "bitfinex",
        "bittrex",
        "binance",
        "poloniex",
        "coinbase",
        "kraken",
        "kucoin",
    ]
    exchanges = ["kucoin"]
    print("\n", api["pair"], "\n")
    print("fetching PRICE, BOOK, and CANDLES from:\n\n", exchanges)
    for exchange in exchanges:
        print("\n==================\n", exchange.upper(), "API\n==================")
        api["exchange"] = exchange
        demo(api)


if __name__ == "__main__":
    main()
