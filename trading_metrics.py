import requests as re
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
pd.set_option('display.max_columns', 10)
pd.set_option('display.width', 200)

def get_daily_data(symbol):
    api_key = 'WE5953TW1O9RI95B'
    api_function = 'TIME_SERIES_DAILY_ADJUSTED'
    url = f'https://www.alphavantage.co/query?function={api_function}&symbol={symbol}'\
          f'&outputsize=compact&apikey={api_key}'
    resp = re.get(url)
    data = resp.json()
    return data

def process_data(json_data):
    header_keys = list(json_data.keys())
    dk = header_keys[-1]
    data = json_data[dk]
    date_keys = data.keys()
    df = pd.DataFrame(data=[data[i] for i in date_keys], index=date_keys)
    df.columns = [" ".join(i.split(' ')[1:]) for i in df.columns]
    df = df.apply(lambda x: x.astype(float))
    df = df.sort_index()
    return df

def prep_data(symbol):
    data = get_daily_data(symbol)
    df = process_data(data)
    return df

tsla = prep_data('TSLA')

n = 9
tsla['adjusted close'].ewm(span=n).mean()


def ema_dema_tema(series, n, t3=False):

    def EMA(series):
        return series.ewm(span=n).mean()

    ema = EMA(series)
    ema_ema = EMA(ema)
    dema = 2 * ema - ema_ema
    tema = 3 * ema - 3 * ema_ema + EMA(ema_ema)
    metrics = pd.concat([ema.rename('EMA'), dema.rename('DEMA'), tema.rename('TEMA')], axis=1)

    if t3:
        vfactor = .7
        gd1 = ema * (1 + vfactor) - ema_ema * vfactor

        def GD(series):
            return EMA(series) * (1 + vfactor) - EMA(EMA(series)) * vfactor

        t3 = GD(GD(gd1))
        metrics = pd.concat([metrics, t3.rename('T3')], axis=1)

    return metrics

ema_dema_tema(tsla['adjusted close'], 9)

trima = tsla['adjusted close'].rolling(n, win_type='triang').mean()
wema = tsla['adjusted close'].rolling(n).apply(lambda x: np.average(x, weights=range(1, n+1)))


def kama(price, n=10, pow1=2, pow2=30):
    ''' kama indicator '''
    ''' accepts pandas dataframe of prices '''

    absDiffx = abs(price - price.shift(1))

    ER_num = abs(price - price.shift(n))
    # ER_den = pd.stats.moments.rolling_sum(absDiffx, n)
    ER_den = absDiffx.rolling(n).sum()
    ER = ER_num / ER_den

    sc = (ER*(2.0/(pow1+1)-2.0/(pow2+1.0))+2/(pow2+1.0)) ** 2.0


    kama = np.zeros(sc.size)
    X = len(kama)
    first_value = True

    for i in range(X):
        if sc[i] != sc[i]:
            kama[i] = np.nan
        else:
            if first_value:
                kama[i] = price[i]
                first_value = False
            else:
                kama[i] = kama[i-1] + sc[i] * (price[i] - kama[i-1])
    return pd.Series(kama)

kama = kama(tsla['adjusted close'])

def macd(fastseries, slowseries, signalperiod=9):
    macd = fastseries - slowseries
    signal = macd.ewm(span=signalperiod).mean()
    delta = macd - signal
    data = pd.concat([macd, signal, delta], axis=1)
    return data

