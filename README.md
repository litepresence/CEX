# CEX
---------------------------------------------------------------------------
## Centralized Exchange 
### API Authentication 
### and Data Standardization Python Wrapper
### for Algo Trading
----------------------------------------------------------------------------
## SUPPORTED EXCHANGES:

### Binance, Bitfinex, Bittrex, Coinbase, Kraken, Kucoin, Poloniex
----------------------------------------------------------------------------
## SUPPORTED REMOTE PROCEDURES:

### PRIVATE: Authenticate, Buy, Sell, Cancel, Orders, Balances

### PUBLIC: Last, Book, Candles
----------------------------------------------------------------------------

    USER PROVIDES:

    api["key"]          # public key from exchange
    api["secret"]       # private key from exchange
    api["passphrase"]   # some exchanges require passphrase else ""
    api["exchange"]     # name of exchange; ie "binance"
    api["pair"]         # market pair symbol in format BTC:USD

    SCRIPT BUILDS request(api, params) SPECIFIC:

    api["symbol"]       # exchange specific syntax of api["pair"]
    api["nonce"]        # time.time() at beginning of request
    api["url"]          # https://...xyz.com
    api["endpoint"]     # path/to/server/resource
    api["method"]       # GET, POST, or DELETE
    api["params"]       # dict with request specific parameters
    api["data"]         # str with request specific parameters
    api["headers"]      # contains authentication signature


# CEX PRIVATE 

## authenticate(api)

    Confirms api key and signature match by attempting balance call
    Returns <bool> True or False

       
## get_balances(api)

    Normalized external requests for balances in one market
    all values are <float>
    
    {
        "asset_total": 0.0,      
        "asset_free": 0.0,       # available to trade
        "asset_tied": 0.0,       # already on orders
        "currency_total": 0.0, 
        "currency_free": 0.0, 
        "currency_tied": 0.0,
    }

    
## get_orders(api)
    
    Normalized external requests for open orders in one market

    normalized orders (sums in asset terms)
    
    {
        "bids": {}, 
        "asks": {}, 
        "bid_sum": 0.0,     # the sum of user's bids
        "ask_sum": 0.0,
    }

    normalized bid or ask dictionary format (qty in asset terms)
    
    {
        "price": 0.0, 
        "order_id": "", 
        "start_qty": 0.0, 
        "current_qty": 0.0
    }

    
## post_order(edict, api)

    edict = {
        "side": "sell",       # or buy
        "amount": 5531,       
        "price": 0.00003142
    }

    
## cancel(api, order_ids=None)
    
    cancel all orders by api["pair"] (or) by api["pair"] and order_id:
    

# CEX PUBLIC 

## get_price(api)
    
    Last Price as <float>
    
    
## get_book(api, depth=10):
    
    depth of market format is a list of floats
    where bidp[0] is the highest bid and askp[0] is the lowest ask
    
    {
        "bidv": [], 
        "bidp": [], 
        "askp": [], 
        "askv": [],
    }
    
    
## get_candles(api, start=None, end=None, interval=86400):
    
    output normalized requests for candle data
    returns a dict with numpy array values for the following keys
    
    ["high", "low", "open", "close", "volume", "unix"]
    
    where unix is int and the remainder are float
    this is the ideal format for utilizing talib / tulip indicators
    
    
    
WTFPL www.litepresence.com 2019
