
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
    df = df[pd.to_datetime(df['date']) >= start_day_]
    
    if df.shape[0] == 391:
        ind = []
        minutes_away_from_strike = [] 
        for i in range(df.shape[0]):
            diffed = strikes_ - df.close.iloc[i]
            diffed_high = strikes_ - df.high.iloc[i] # only if high of the minute
            diffed_low = strikes_ - df.low.iloc[i] # and the low of the minute is more than a $1 away
            ind_candidate = np.abs(diffed).argmin()
            if diffed[ind_candidate] <= 0:
                ind_candidate += 1
            ind.append(ind_candidate)
            val = int((np.all(np.abs(diffed_low) > 1)) & (np.all(np.abs(diffed_high) > 1))) # more than a $1 away
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
        
        high_low_over_close_percent = (df.high.max() - df.low.min())/df.close[df.shape[0]-1] * 100
        
        strike_crosses = len(np.unique(ind))-1 
        strike_crosses_first_60 = len(np.unique(ind[:60]))-1 
        strike_crosses_second_60 = len(np.unique(ind[60:120]))-1 
        strike_crosses_third_60 = len(np.unique(ind[120:180]))-1 
        strike_crosses_fourth_60 = len(np.unique(ind[180:240]))-1 
        strike_crosses_fifth_60 = len(np.unique(ind[240:300]))-1 
        strike_crosses_sixth_60 = len(np.unique(ind[300:360]))-1 
        strike_crosses_final_30 = len(np.unique(ind[360:]))-1 
        
        open_price = df.open.iloc[0] 
        close_price = df.close.iloc[df.shape[0]-1] 
        # Variance of return by hours
        annual_var_first_60 = np.var(np.log(np.array(df.close.iloc[1:60])/np.array(df.close.iloc[:59]))) * 252 * 6.5 
        annual_var_second_60 = np.var(np.log(np.array(df.close.iloc[61:120])/np.array(df.close.iloc[60:119]))) * 252 * 6.5 
        annual_var_third_60 = np.var(np.log(np.array(df.close.iloc[121:180])/np.array(df.close.iloc[120:179]))) * 252 * 6.5 
        annual_var_fourth_60 = np.var(np.log(np.array(df.close.iloc[181:240])/np.array(df.close.iloc[180:239]))) * 252 * 6.5 
        annual_var_fifth_60 = np.var(np.log(np.array(df.close.iloc[241:300])/np.array(df.close.iloc[240:299]))) * 252 * 6.5 
        annual_var_sixth_60 = np.var(np.log(np.array(df.close.iloc[301:360])/np.array(df.close.iloc[300:359]))) * 252 * 6.5 
        annual_var_final_30 = np.var(np.log(np.array(df.close.iloc[361:390])/np.array(df.close.iloc[360:389]))) * 252 * 6.5 * 2 
        
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
                      strike_crosses_first_60,
                      strike_crosses_second_60,
                      strike_crosses_third_60,
                      strike_crosses_fourth_60,
                      strike_crosses_fifth_60,
                      strike_crosses_sixth_60,
                      strike_crosses_final_30,
                      minutes_away_from_strike,
                      high_low_over_close_percent,
                      how_close_to_strike_at_expiration,
                      last_interval,
                      open_price,
                      close_price,
                      annual_var_first_60,
                      annual_var_second_60,
                      annual_var_third_60,
                      annual_var_fourth_60,
                      annual_var_fifth_60,
                      annual_var_sixth_60,
                      annual_var_final_30,
                      length_of_dataframe])
    else:
        print 'DataFrame had an unusual size'
        return tuple(np.repeat(np.NaN, 31))
    
    
# A function to get the implied vol every minute
def get_ivol_minutebar_from_ib(ticker_, date_, how_many_weeks_):
    """
    The function returns a dictionary of specified dates as keys and a dataframe of minutes and clsing implied vol as 
    values. There is a few things to notice here. 
    1) IB calculated the implied vol. This is tricky. 
    2) We can go far back as many weeks as we want.
    
    -----
    ticker_: A ticker for the stock we are considering. Has to be a string.
    date_: the last friday which we want to consider. A datetime object.
    how_many_weeks_: how many weeks we want to go back. An integer
    
    """
    api_ = IB_PY()
    cont = api_.make_contract(symbol = ticker_, secType = 'STK', currency = 'USD', exchange = 'SMART')
    out = dict()
    for i in range(how_many_weeks_):
        api_.get_historical_data(cont, barSizeSetting_= '1 min', 
                            durationStr_= '1 D', 
                            whatToShow_= 'OPTION_IMPLIED_VOLATILITY', 
                            endDateTime_= date_, 
                            sameContract_ = True)
        df = api_.hist_data.copy(deep = True)
        start_day_ = date_ - datetime.timedelta(hours = 6.5, minutes = 1)
        df = df[df['date'] >= start_day_]
        out_df = pd.DataFrame(columns = ['close'])
        out_df['close'] = df.loc[:,'close'].copy(deep = True)
        out_df.index = df.date.apply(lambda x: str(x)[11:16])
        out_df.index.names = ['time']
        out[date_] = out_df
        date_ = date_ - datetime.timedelta(days = 7)
        
    return out
# A function to get the price every minute
def get_prices_minutebar_from_ib(ticker_, date_, how_many_weeks_, whatToShow_):
    """
    The function returns a dictionary of specified dates as keys and a dataframe of minutes and specified prices as 
    values. There is a few things to notice here.     
    -----
    ticker_: A ticker for the stock we are considering. Has to be a string.
    date_: the last friday which we want to consider. A datetime object.
    how_many_weeks_: how many weeks we want to go back. An integer
    whatToShow_: should be 'MIDPOINT'/'BID'/'ASK'/'TRADES'/'BID_ASK'. A string. 
    
    """
    api_ = IB_PY()
    cont = api_.make_contract(symbol = ticker_, secType = 'STK', currency = 'USD', exchange = 'SMART')
    out = dict()
    for i in range(how_many_weeks_):
        api_.get_historical_data(cont, barSizeSetting_= '1 min', 
                            durationStr_= '1 D', 
                            whatToShow_= whatToShow_, 
                            endDateTime_= date_, 
                            sameContract_ = True)
        df = api_.hist_data.copy(deep = True)
        start_day_ = date_ - datetime.timedelta(hours = 6.5, minutes = 1)
        df = df[df['date'] >= start_day_]
        out_df = pd.DataFrame(columns = ['close'])
        out_df['close'] = df.loc[:,'close'].copy(deep = True)
        out_df.index = df.date.apply(lambda x: str(x)[11:16])
        out_df.index.names = ['time']
        out[date_] = out_df
        date_ = date_ - datetime.timedelta(days = 7)
        
    return out    

