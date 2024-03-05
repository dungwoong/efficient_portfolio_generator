import yfinance as yf


def download_data(ticker, symbol, period='max', interval='1mo'):
    """
    downloads data
    :param ticker: the ticker as a yFinance ticker object
    :param symbol: the symbol for the ticker as a str
    :param period: total time to download for
    :param interval: interval
    :return:
    """
    hist = ticker.history(period=period, interval=interval)
    hist.columns = [symbol + '_' + colname for colname in hist.columns]
    return hist


def percent_change(ticker, df):
    """
    Percent change for each period?
    :param ticker: ticker
    :param df: df with keys ticker_Open, ticker_Dividends
    :return: percent change by date
    """
    pc = (df[f'{ticker}_Open'].diff() / df[f'{ticker}_Open'].shift(1)).shift(-1)
    pc += df[f'{ticker}_Dividends'] / df[f'{ticker}_Open']
    return pc
