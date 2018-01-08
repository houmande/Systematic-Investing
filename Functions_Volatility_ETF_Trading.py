
# coding: utf-8

# In[ ]:

from IBPY import IB_PY 
import numpy as np
import pandas as pd
import datetime
import time
# ======================
def get_daily_from_ib(ticker_, whatToShow_, how_many_years_back_):
    """
    This function connects to IB can queries back the daily prices/implied volatility of one ticker. 
    
    ticker_: ticker of the contract. Must be a string.
    whatToShow_: should be 'MIDPOINT' or 'TRADES' or 'OPTION_IMPLIED_VOLATILITY'. A string. 
    how_many_years_back_: how many years should we go back from today for prices. An integer.
    
    returns a dataframe.
    """
    api_ = IB_PY()
    cont = api_.make_contract(symbol = ticker_, secType = 'STK', currency = 'USD', exchange = 'SMART')
    day = datetime.datetime.today()
    for i in range(how_many_years_back_):
        api_.get_historical_data(cont, barSizeSetting_= '1 day', 
                            durationStr_= '1 Y', 
                            whatToShow_= whatToShow_, 
                            endDateTime_= day, 
                            sameContract_ = True)
        day = day - datetime.timedelta(days = 363)
        time.sleep(2)
    df = api_.all_hist_data.values()[0].loc[:,['date', 'close']].copy(deep = True)
    df.drop_duplicates('date', inplace= True)
    df.index = pd.to_datetime(df.date)
    df.drop('date', axis = 1, inplace = True)
    df.sort_index(axis = 0, inplace = True)
    del api_
    
    return df

