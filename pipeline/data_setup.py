import pandas as pd
import yfinance as yf
from pipeline.base_classes import PipelineModule
import utils.download_data as dd


class DownloadTickerHistorical(PipelineModule):
    """
    Downloads data as dataframe, saves ticker objects and dataframe of percent change
    """

    def __init__(self, df_key, ticker_obj_key, tickers, period, interval, dropna=True):
        self.df_key = df_key
        self.ticker_obj_key = ticker_obj_key
        self.tickers = tickers
        self.period = period
        self.interval = interval
        self.dropna = dropna

    def run(self, global_state, verbose=False):
        tickers_dict = {t: yf.Ticker(t) for t in self.tickers}
        global_state[self.ticker_obj_key] = tickers_dict
        ret = dict()
        for t in tickers_dict:
            if verbose:
                print(f'Fetching {t}')
            ret[t] = dd.percent_change(t,
                                       dd.download_data(tickers_dict[t],
                                                        t,
                                                        self.period,
                                                        self.interval))
        df = pd.DataFrame(ret)
        if self.dropna:
            global_state[self.df_key] = df.dropna()
        else:
            global_state[self.df_key] = df.fillna(df.median())


class GetCovExpected(PipelineModule):
    """
    Adds cov and exp to global state
    """

    def __init__(self, df_key, cov_key, exp_key):
        self.df_key = df_key
        self.cov_key, self.exp_key = cov_key, exp_key

    def run(self, global_state, verbose=False):
        df = global_state[self.df_key]
        global_state[self.cov_key] = df.cov()
        global_state[self.exp_key] = df.mean()
