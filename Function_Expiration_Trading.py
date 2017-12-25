
# coding: utf-8

# In[ ]:

from IBPY import IB_PY 
import numpy as np
import pandas as pd
import datetime
# A function that gets api information, ticker, date, starting strike and intervals.
# The function calculated the stats in the Augen Book
def expiration_stats(ticker_, date_, strikes_, ib_whatToShow_):
    """
    This function calculates the stats in the Augen book. 
    We need these stats to be able to pin down stocks that are good candidate for expiration trading.
    The function spits out a tuple of 1 * 3. 
    
    api_ : an object of api_ type to connect to IB. This should be my own api class
    ticker_ : ticker of the contract. A string object.
    date_ : the date the we are interested in. A datetime object.
    strikes_: an arraye of strikes. Sorted numpy array. 1D.
    ib_whatToShow_: what to query from ib. could be 'LAST' or 'MIDPOINT' or 'IMPLIED_VOL'. Has to be a string
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
        minutes_away_from_strike = [] 
        for i in range(df.shape[0]):
            diffed = strikes_ - df.close.iloc[i]
            ind_candidate = np.abs(diffed).argmin()
            if diffed[ind_candidate] <= 0:
                ind_candidate += 1
            ind.append(ind_candidate)
            val = int(np.all(np.abs(diffed) > 1)) # more than a $1 away
            minutes_away_from_strike.append(val)
        minutes_away_from_strike = np.sum(np.array(minutes_away_from_strike))
        ind = np.array(ind)

        helper_ind = ind[1:] - ind[:-1]
        total_times_crossed_strike = int(sum(helper_ind != 0))
        
        # strike crosses over time
        if total_times_crossed_strike != 0:
            first_60_percent = float(sum(helper_ind[:60] != 0))/total_times_crossed_strike
            second_60_percent = float(sum(helper_ind[60:120] != 0))/total_times_crossed_strike
            third_60_percent = float(sum(helper_ind[120:180] != 0))/total_times_crossed_strike
            fourth_60_percent = float(sum(helper_ind[180:240] != 0))/total_times_crossed_strike
            fifth_60_percent = float(sum(helper_ind[240:300] != 0))/total_times_crossed_strike
            sixth_60_percent = float(sum(helper_ind[300:360] != 0))/total_times_crossed_strike
            final_30_percent = float(sum(helper_ind[360:] != 0))/total_times_crossed_strike
        else:
            first_60_percent = 0.0
            second_60_percent = 0.0
            third_60_percent = 0.0
            fourth_60_percent = 0.0
            fifth_60_percent = 0.0
            sixth_60_percent = 0.0
            final_30_percent = 0.0
            
        
        diffed = strikes_ - df.close[df.shape[0]-1]
        argmin = np.abs(diffed).argmin()
        how_close_to_strike_at_expiration = diffed[argmin] 
        
        last_interval = strikes_[ind_candidate] - strikes_[ind_candidate - 1]

        length_of_dataframe = df.shape[0] 
        
        high_low_over_close = (df.high.max() - df.low.min())/df.close[df.shape[0]-1] 
        
        strike_crosses = len(np.unique(ind))-1 
        
        open_price = df.open.iloc[0] 
        close_price = df.close.iloc[df.shape[0]-1] 
        
        del api_
        return tuple([date_,
                      total_times_crossed_strike, 
                      first_60_percent,
                      second_60_percent,
                      third_60_percent,
                      fourth_60_percent,
                      fifth_60_percent,
                      sixth_60_percent,
                      final_30_percent,
                      strike_crosses,
                      minutes_away_from_strike,
                      high_low_over_close,
                      how_close_to_strike_at_expiration,
                      last_interval,
                      open_price,
                      close_price,
                      length_of_dataframe])
    else:
        print 'DataFrame had an unusual size'
        return tuple([np.NaN, np.NaN,
                      np.NaN, np.NaN, np.NaN, np.NaN, np.NaN,
                      np.NaN, np.NaN, np.NaN, np.NaN, np.NaN,
                      np.NaN, np.NaN, np.NaN, np.NaN, np.NaN,])

