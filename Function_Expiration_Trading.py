
# coding: utf-8

# In[ ]:

from IBPY import IB_PY 
import numpy as np
import pandas as pd
import datetime
# A function that gets api information, ticker, date, starting strike and intervals.
# The function calculated the stats in the Augen Book
def expiration_stats(ticker_, date_, strikes_, ib_whatToShow_, threshold_):
    """
    This function calculates the stats in the Augen book. 
    We need these stats to be able to pin down stocks that are good candidate for expiration trading.
    The function spits out a tuple of 1 * 3. 
    
    api_ : an object of api_ type to connect to IB. This should be my own api class
    ticker_ : ticker of the contract. A string object.
    date_ : the date the we are interested in. A datetime object.
    strikes_: an arraye of strikes. Sorted numpy array. 1D.
    ib_whatToShow_: what to query from ib. could be 'LAST' or 'MIDPOINT' or 'IMPLIED_VOL'. Has to be a string
    threshold_: the threshold of closing close to a strike at the close. 
    """
    api_ = IB_PY()
    cont = api_.make_contract(symbol = ticker_, secType = 'STK', currency = 'USD', exchange = 'SMART')
    api_.get_historical_data(cont, barSizeSetting_= '1 min', 
                        durationStr_= '1 D', 
                        whatToShow_= ib_whatToShow_, 
                        endDateTime_= date_, 
                        sameContract_ = True)
    df = api_.hist_data.copy(deep = True)
    start_day_ = date_ - datetime.timedelta(hours = 6.5, minutes = 1)
    df = df[df['date'] >= start_day_]
    
    if df.shape[0] == 391:
        ind = []
        minutes_away_from_strike = [] # our second statistics
        for i in range(df.shape[0]):
            diffed = strikes_ - df.close.iloc[i]
            ind_candidate = np.abs(diffed).argmin()
            if diffed[ind_candidate] <= 0:
                ind_candidate += 1
            ind.append(ind_candidate)
            val = int(np.all(np.abs(diffed) > 1)) # more than a $1 away from strikes
            minutes_away_from_strike.append(val)
        minutes_away_from_strike = np.array(minutes_away_from_strike)
        ind = np.array(ind)

        helper_ind = ind[1:] - ind[:-1]
        times_crossed_strike = int(sum(helper_ind != 0))

        is_close_to_strike_at_expiration = np.min(np.abs(strikes_ - df.close[df.shape[0]-1])) < threshold_ # our third statistic

        length_of_dataframe = df.shape[0] # fourth statistics

        del api_
        return tuple([times_crossed_strike, 
                      np.sum(minutes_away_from_strike), 
                      is_close_to_strike_at_expiration,
                      length_of_dataframe])
    else:
        print 'DataFrame had an unusual size'
        return tuple([np.NaN, np.NaN, np.NaN, np.NaN])

