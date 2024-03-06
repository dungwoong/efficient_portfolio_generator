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


class AddFixedRates(PipelineModule):
    """
    Adds fixed rate assets.
    """
    def __init__(self, key, rates_info):
        self.key = key
        # month must be 1-12 I guess?
        self.rates_info = rates_info  # expect label, rate, months tuples

    def run(self, global_state, verbose=False):
        if verbose:
            print(f'Adding {len(self.rates_info)} fixed rate assets...')
        if self.key not in global_state:
            global_state[self.key] = dict()
        for label, rate, period in self.rates_info:
            rate = self.calculate_monthly_rate(rate, period)
            global_state[self.key][label] = rate  # %change you would expect each month

    @staticmethod
    def calculate_monthly_rate(rate, period):
        """
        Calculates the %change you would expect for each month

        so for the outputted rate, we should have
        (rate + 1) ** period = 1 + rate / (12/period)

        eg. for a 4% interest, compounded quarterly, we expect every 3 months you'll gain 1%,
        which equates to a 0.3322% increase per month

        :param rate: annual rate
        :param period: number of months for the compounding period
        :return: %change expected for each month
        """
        rate = rate / (12 / period)  # % appreciation for each compounding period
        rate += 1
        # solve (new_rate^months) = rate
        rate = rate ** (1 / period)
        rate -= 1
        return rate
