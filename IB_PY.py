
# coding: utf-8

# In[ ]:

# Version 19 of the IB Data Downloader
# ========================================
from ib.opt import ibConnection, message, Connection
from time import sleep
from ib.ext.Contract import Contract
from ib.ext.ContractDetails import ContractDetails
from ib.ext.ExecutionFilter import ExecutionFilter
from ib.ext.Execution import Execution
from ib.ext.CommissionReport import CommissionReport
from ib.ext.Order import Order
import pandas as pd
import numpy as np
import datetime

# Plotting essentials
# ===================
import matplotlib.pyplot as plt
get_ipython().magic(u'matplotlib inline')

# A Helper Class For Dictionary with Contract as key
class my_contract:
    def __init__(self, contract_, ident_):
        self.con = contract_
        self.ident = ident_
        
    def __hash__(self):
        return hash(self.ident)
    
    def __eq__(self, other):
        return self.con == other.con
    
    def __ne__(self, other):
        return not(self.con == other.con)
    # Printing Capabilities
    def __repr__(self):
        return " | ".join(["%s = %s" % (a, b) for a, b in vars(self.con).items()])
    def __str__(self):
        return " | ".join(["%s = %s" % (a, b) for a, b in vars(self.con).items()])

# The class
# ====================
class IB_PY():
    def __init__(self):
        # Initializing the dictionary
        # self.val
        
        # For Querying Market Data
        self.mkt_data = pd.DataFrame([{'Bid Size': None, 'Bid': None, 'Ask': None, 'Ask Size': None, 
                      'Last': None, 'Last Size': None, 'High' : None, 'Low': None, 'Volume': None,
                      'Close': None}])
        
        # For Querying Historical Data
        self.hist_data = pd.DataFrame(columns = ['date', 'open', 'high', 'low', 'close']) # For the very recently queried contract
        self.all_hist_data = {} # All the contracts, they are stored by contract instances as keys
        
        # Account Information
        self.account_info = pd.DataFrame()
        # Account Summary
        self.account_summary = pd.DataFrame()
        # Fundamental Data
        self.fundamental_data = None
        # Option Data
        self.option_data = pd.DataFrame()
        self._interim_option_data_dict = {}
        # Account Information
        self.account_info_dict = {}
        # Contract Details
        self.summary_contract = pd.DataFrame()
        self._summary_contract_dict = {}
        self.detail_contract = pd.DataFrame()
        self._detail_contract_dict = {}
        # Executions Over The Past 24hrs
        self.all_executions = {} # A dictionary with contracts as key
        self.this_execution = pd.DataFrame()
        self.all_commissions = pd.DataFrame() # Commmission are not identified by contract 
        self.this_commission = pd.DataFrame()
        # Market Depth
        self.market_depth = pd.DataFrame()
        self.market_depthL2 = pd.DataFrame()
        self.all_market_depth = pd.DataFrame()
        self.all_market_depthL2 = pd.DataFrame()
        # Positions of The Account
        self.all_positions = {} # A dictionary keyed by the contract
        # Orders
        self.order_status = pd.DataFrame()
        self.order_state = pd.DataFrame()
        self.all_contract_orders = {} # A dictionary keyed by contracts, value is a list, [0] is order object [1] is order_status
        self.all_contract_open_orders = {} # A dictionary keyed by contracts, value is a list, [0] is order object [1] is order_status
        # Miscellaneous
        self.counter_conId = 0
        
        #------ Ends
        self.end_contract_details = False
        
    def my_acct_handler(self, msg):
        """
        This handler would help us to see the updated account values (? Add details here)
        """
        #print msg.key, type(msg.key), msg.value
        #self.account_info[str(msg.key)] = msg.value
        self.account_info_dict['DateTime'] = datetime.datetime.now()
        if self.account_info_dict.has_key(msg.key):
            #print "in the keys"
            self.account_info_dict[msg.key] = msg.value
        else:
            #print "not in the keys"
            self.account_info_dict[msg.key] = msg.value        
    
    # Summary Handler
    def my_acct_summary_handler(self, msg):
        """
        This handler would help us to see the updated account values (? Add details here)
        """
        #print "in accountSummary"
        #print msg.tag, msg.value
        if hasattr(msg, 'account'):
            self.account_info_dict['account'] = msg.account
        if hasattr(msg, 'tag') and hasattr(msg, 'value') and hasattr(msg, 'currency'):
            if msg.value == None:
                self.account_info_dict[msg.tag] = ' ' + msg.currency
            elif msg.currency == None:
                self.account_info_dict[msg.tag] = msg.value + ' '
            else:
                self.account_info_dict[msg.tag] = msg.value + ' ' + msg.currency
                
        self.account_info_dict['DateTime'] = datetime.datetime.now()


    # Summary Handler End
    def my_acct_summary_end(self, msg):
        print "in accountSummaryEnd"
        print msg
        
    # Tick Handler
    def my_tick_handler(self, msg):
        """
        This handler would help us to assign tick size and tick value (? Add details here)
        """
    # Based on what the IB document lays out
        field_dict = {0: 'Bid Size', 1: 'Bid', 2: 'Ask', 3: 'Ask Size', 
                      4: 'Last', 5: 'Last Size', 6: 'High', 7: 'Low', 8: 'Volume',
                      9: 'Close'}
    
        if hasattr(msg, 'price'):
            value = msg.price
        elif hasattr(msg, 'size'):
            value = msg.size
    
        #print('TickerId: ', msg.tickerId, ' Field: ', field_dict[msg.field], ' Value: ', value)
        #print 'Assigning To Self'
        #self.attr.append(field_dict[msg.field]) 
        #self.val.append(value)
        #print 'Done' 
        if msg.field in field_dict.keys():
            #print field_dict[msg.field] This is to prevent KeyError 14 which is for dictionaries in python
            self.mkt_data[[field_dict[msg.field]]] = value
    
    # Account Handler
    def my_hist_data_handler(self, msg):
        #print msg.date, msg.open, msg.high, msg.low, msg.close
        #print msg
        print ' - In Historical Data Handler - '
        if msg.close != -1:
            interim_df = pd.DataFrame([[msg.date, msg.open, msg.high, msg.low, msg.close, msg.volume, msg.count, msg.WAP, msg.hasGaps]],
                                               columns = ['date', 'open', 'high', 'low', 'close', 'volume', 'count', 'WAP', 'hasGaps'])
            self.hist_data = self.hist_data.append(interim_df, ignore_index = True)
            #print interim_df
        #elif msg.close == -1:
            # print 'done'
            
    def my_hist_option_eod_handler(self, msg):
        #print msg.date[11:15]
        if msg.date[10:15] == '15:57': 
            print ' - In Historical Data Handler - '
            if msg.close != -1:
                interim_df = pd.DataFrame([[msg.date[0:8], msg.open, msg.high, msg.low, msg.close, msg.volume, msg.count, msg.WAP, msg.hasGaps]],
                                                   columns = ['date', 'open', 'high', 'low', 'close', 'volume', 'count', 'WAP', 'hasGaps'])
                self.hist_data = self.hist_data.append(interim_df, ignore_index = True)
    
    def my_hist_option_bod_handler(self, msg):
        #print msg.date[11:15]
        if msg.date[10:15] == '09:30': 
            print ' - In Historical Data Handler - '
            if msg.close != -1:
                interim_df = pd.DataFrame([[msg.date[0:8], msg.open, msg.high, msg.low, msg.close, msg.volume, msg.count, msg.WAP, msg.hasGaps]],
                                                   columns = ['date', 'open', 'high', 'low', 'close', 'volume', 'count', 'WAP', 'hasGaps'])
                self.hist_data = self.hist_data.append(interim_df, ignore_index = True)
    
        
    # Time handler
    def my_acct_time(self, msg):
        print "The time is:"
        print msg.timeStamp
    
    # Position Handler
    def my_position_handler(self, msg):
        """
        This handler gets called as a callback to reqPositions
        """
        print 'In the position handler'
        #print msg.account, msg.contract.m_symbol, msg.pos
        m_contract = my_contract(msg.contract, msg.contract.m_conId)
        self.all_positions[m_contract] = msg.pos
    
    # Position Handler End
    def my_position_end(self, msg):
        print ' - End of Querying Positions - '
    
    def my_fundamental_handler(self, msg):
        print ' - In The Fundamental Data - '
        self.fundamental_data = msg.data
    
    # Option Handler
    def my_option_handler(self, msg):
        """
        handling tickOptionComputation
        """
        # print msg.impliedVol, msg.delta
        self._interim_option_data_dict['Implied Volatility'] = msg.impliedVol
        self._interim_option_data_dict['Delta'] = msg.delta
        self._interim_option_data_dict['Option Price'] = msg.optPrice
        self._interim_option_data_dict['Present Value Dividend'] = msg.pvDividend
        self._interim_option_data_dict['Gamma'] = msg.gamma
        self._interim_option_data_dict['Vega'] = msg.vega
        self._interim_option_data_dict['Theta'] = msg.theta
        self._interim_option_data_dict['Underlying Price'] = msg.undPrice
        self._interim_option_data_dict['DateTime'] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    # Contract Handler
    def my_contract_handler(self, msg):
        print ' - Getting the Contract Details - '
        self._detail_contract_dict = vars(msg.contractDetails)
        #for a, b in specs.items():
        #    if a not in ['m_summary']:
        #        print a, b
        # print " - printing the contract - "
        self._summary_contract_dict = vars(msg.contractDetails.m_summary)
        #print self._summary_contract_dict
        self.store_contract_detail_summary(self._detail_contract_dict, self._summary_contract_dict)
        
    # End of contract handler
    def my_contract_end(self, msg):
        self.end_contract_details = True
        print ' - End of Contract Details - '
    
    # Execution handler
    def my_execution_handler(self, msg):
        print ' - In Execution Handler - '
        print ' - Execution - '
        self.this_execution = pd.DataFrame([vars(msg.execution)])
        self.store_executions(msg.contract, msg.contract.m_conId)
        
    # Commission handler
    def my_commission_handler(self, msg):
        print ' - In Commission Handler - '
        #print pd.DataFrame(vars(msg.commissionReport))
        self.this_commission = pd.DataFrame([vars(msg.commissionReport)])
        self.all_commissions = pd.concat([self.this_commission, self.all_commissions], axis = 0, join = 'outer',
                                         ignore_index = True, copy = True)
        
    # Execution End
    def my_execution_end(self, msg):
        print ' - End of Execution Handler - '
        
    # Market Depth Handler
    def my_market_depth_handler(self, msg):
        print ' - Market Depth - '
        operation_dict = {0: 'insert', 1:'update', 2:'delete'}
        side_dict = {0:'ask', 1:'bid'}
        #print msg.price, msg.size
        self.market_depth = pd.DataFrame([[msg.position, operation_dict[msg.operation], side_dict[msg.side], msg.price, msg.size]],
                                               columns = ['position', 'operation', 'side', 'price', 'size'])
        self.all_market_depth = pd.concat([self.market_depth, self.all_market_depth], axis = 0, join = 'outer', ignore_index = True,
                                          copy = True)
        
    # Market Depth Level 2 Handler
    # def my_market_depthL2_handler(self, msg):
    #    """
    #    THIS IS NOT TESTED
    #    """
    #    print ' - Level II Market Depth - '
    #    self.market_depthL2 = pd.DataFrame([vars(msg)])
    #    self.all_market_depthL2 = pd.concat([self.market_depthL2, self.all_market_depthL2], axis = 0, join = 'outer', 
    #                                        ignore_index = True, copy = True)
        
    # Open orders
    def my_order_status_handler(self, msg):
        print ' - Order Status Handler - '
        #print msg.orderId, msg.status, msg.filled, msg.remaining, msg.remaining
        #print vars(msg)
        interim = pd.DataFrame([[msg.orderId, msg.status, msg.filled, msg.remaining, msg.avgFillPrice, msg.permId, msg.parentId,
                            msg.lastFillPrice, msg.clientId, msg.whyHeld]], 
                          columns = ['orderId', 'status', 'filled', 'remaining', 'avgFillPrice', 'permId', 'parentId', 
                                     'lastFillPrice', 'cliendId', 'whyHeld'])
        self.order_status = pd.concat([self.order_status, interim], axis = 0, join = 'outer', copy = True, ignore_index = True)
        
    # Open order handler
    def my_open_order_handler(self, msg):
        print ' - Open Orders Handler - '
        #print vars(msg.orderState)
        self.order_state = pd.DataFrame([vars(msg.orderState)])
        m_contract = my_contract(msg.contract, msg.contract.m_conId)
        self.all_contract_open_orders[m_contract] = [msg.order, self.order_state]
        
    # Open orders End
    def my_open_order_end(self, msg):
        print ' - End of Open Orders - '
        
    # The general handler - WATCHER!!    
    def watcher(self, msg):
        print msg
    
    # ======================= Intermediary Methods
    # =============================================
    
    def make_contract(self, **kwargs):
        """
        A contract needs items below
        
        m_conId: unique identifier
        m_currency: 'USD'
        m_exchange: 'SMART'
        m_expiry: '20170120'
        m_multiplier: '100'
        m_right: 'PUT, CALL, P, C'
        m_secType: 'STK, OPT, FUT, IND, CASH, FOP, BAG, NEWS'
        m_strike: '100.00'
        m_symbol: 'AAPL'
        
        """
        cont = Contract()
        cont.m_exchange = 'SMART'
        cont.m_currency = 'USD'
        for name, value in kwargs.items():
            if not isinstance(name, basestring) or not isinstance(value, basestring):
                raise('Contract keywords are not set right! It should start with m_. They should both be strings as well.')
            setattr(cont, 'm_' + name, value)
        return cont
        
    # Make an order 
    def make_order(self, **kwargs):
        """
        This method helps to build an order object
        
        * m_orderId = The id for the order
        m_clientId the id of the client
        m_permid unique TWS id for orders, remains the same as long as TWS is connected
        -----
        * m_action: BUY, SELL
        m_auxPrice: 
        * m_lmtPrice: Limit price for limit orders
        * m_orderType: order types that are supported, STP STP LMT, LMT, MKT, ...
        * m_totalQuantity: order quantity
        ------
        * m_ocaGroup: The OneCancelsAll group
        * m_ocaType: 1 = calcel all remaining orders
        m_outsideRth: true, false - trading outside regular tradinhg hours
        * m_tif : DAY, GTC, IOC, GTD. time in force
        
        * The necessary fields
        """
        order = Order()
        for name, value in kwargs.items():
            if not isinstance(name, basestring) or not isinstance(value, basestring):
                raise('Contract keywords are not set right! They should both be strings.')
            setattr(order, 'm_' + name, value)
        return order
    
    # ExecutionFilter maker
    def make_exec_filter(self, **kwargs):
        """
        This function helps us to filter a executio based on its attributes
        
        m_acctCode - String
        m_exchange - String
        m_secType - String
        m_side - String
        m_symbol - String
        m_time - String 'yyyymmdd-hh:mm:ss'
        m_clientId - int
        
        """
        ex_filter = ExecutionFilter()
        for name, value in kwargs.items():
            if not isinstance(name, basestring) or not isinstance(value, basestring):
                raise('Contract keywords are not set right! It should start with m_. They should both be strings as well.')
            setattr(ex_filter, 'm_' + name, value)
        return ex_filter
    
    # Storing the historical data
    def store_historical_data(self, contract_, local_id_):
        """
        This method helps to store the results into a dictionary with keys as cumstom classes
        Remember that the identifier is NOT the conId from the IB
        """
        if not self.hist_data.empty:
            keys = self.all_hist_data.keys()
            m_contract = my_contract(contract_, ident_ = local_id_)
            if m_contract in keys:
                interim_df = pd.concat([self.all_hist_data[m_contract], self.hist_data], 
                                                          axis = 0, join = 'outer', ignore_index = True, copy = True)
                self.all_hist_data[m_contract] = None
                self.all_hist_data[m_contract] = interim_df

                # Unique on dates
                # ...
            else:
                self.all_hist_data[m_contract] = self.hist_data.copy()

            print ' - Stored The Results - '
        else:
            print ' - Nothing Stored, Query came back empty - '

    def store_executions(self, contract_, local_id_):
        """
        This method helps to store the execution details of the contracts
        """
        keys = self.all_executions.keys()
        m_contract = my_contract(contract_, ident_ = local_id_)
        if m_contract in keys:
            interim_df = pd.concat([self.all_executions[m_contract], self.this_execution], 
                                                      axis = 0, join = 'outer', ignore_index = True, copy = True)
            self.all_executions[m_contract] = None
            self.all_executions[m_contract] = interim_df
            
            # Unique on dates
            # ...
        else:
            self.all_executions[m_contract] = self.this_execution.copy()
        
        print ' - Stored The Results - '
    
    # Storing the contract details
    def store_contract_detail_summary(self, detail_dict, summary_dict):
        # Let us store it now that the callback function is finished
        self.summary_contract = pd.concat([self.summary_contract, pd.DataFrame([summary_dict])],
                                          ignore_index = True, axis = 0, copy = True)
        self.detail_contract = pd.concat([self.detail_contract, pd.DataFrame([detail_dict])],
                                         ignore_index = True, axis = 0, copy = True)
        print ' - Stored Contract Summary & Details - '
    
    
    def get_conId(self, sameContract = False):
        """
        Generates the conId for IB. It has purposes for a dictionary of Contract-type keys. sameContract is a control over generating conId's.
        """
        if sameContract:
            return self.counter_conId
        else:
            self.counter_conId += 1
            return self.counter_conId
        
    # ======================= Getter Methods
    # ======================================
    def get_updates(self):
        """
        This method helps us to get the historical data. It is not written in the most optimal way yet.
        """
        # First step is to define a dictionary whill will be populated by IB API
        con = ibConnection(port=4001, clientId=998)
        con.register(self.my_acct_handler, 'UpdateAccountValue')
        con.register(self.my_tick_handler, message.tickPrice, message.tickSize)
        con.register(self.my_hist_data_handler, message.historicalData)
        # Setting up the connection
        con.connect()

        # Defining the contract
        aapl = Contract()
        aapl.m_symbol = 'AAPL'
        aapl.m_secType = 'STK'
        aapl.m_exchange = 'SMART'

        # con.reqMktData(1, aapl, '', False)
        # con.reqHistoricalData(tickerId=1, 
        #                      contract=aapl, 
        #                      endDateTime=datetime.datetime.today().strftime("%Y%m%d %H:%M:%S %Z"), 
        #                      durationStr='1 Y', 
        #                      barSizeSetting='1 day', 
        #                      whatToShow='MIDPOINT', 
        #                      useRTH=0, 
        #                      formatDate=1)

        
        # Sleep
        sleep(5)

        # Disconnecting
        print('Disconnected', con.disconnect())
        
    def get_account_updates(self):
        # Connection object
        con = ibConnection(port=4001, clientId=998)
        # registering the handler
        con.register(self.my_acct_handler, 'UpdateAccountValue')
        con.register(self.my_acct_time, 'UpdateAccountTime')
        # Connect to IB! 
        con.connect()
        # Request updates
        con.reqAccountUpdates(1, '')
        # Sleep
        sleep(5)
        # Disconnecting
        print('Disconnected', con.disconnect())
        
        self.account_info = self.account_info.append(pd.DataFrame([self.account_info_dict]), ignore_index=True)
        
    def get_account_summary(self, items = 'AccountType'):
        # Connection object
        con = ibConnection(port=4001, clientId=998)
        # registering the handler
        #con.register(self.my_acct_summary_handler, 'accountSummary')
        #con.register(self.my_acct_summary_end, 'accountSummaryEnd')
        #con.registerAll(self.watcher)
        #con.registerAll(self.my_acct_summary_handler)
        con.register(self.my_acct_summary_handler, message.accountSummary)
        con.register(self.my_acct_summary_end, message.accountSummaryEnd)
        # Connect to IB! 
        con.connect()
        # Request updates
        con.reqAccountSummary(1, 'All', items)
        # Sleep
        sleep(2)
        # Canceling the request
        con.cancelAccountSummary(1)
        # Disconnecting
        print('Disconnected', con.disconnect())
        
        self.account_summary = self.account_summary.append(pd.DataFrame([self.account_info_dict]), ignore_index=True)
        
    def get_positions(self):
        # Connection object
        con = ibConnection(port=4001, clientId=998)
        # Registering Handlers
        #con.registerAll(self.watcher)
        con.register(self.my_position_handler, message.position)
        con.register(self.my_position_end, message.positionEnd)
        # Connect to IB! 
        con.connect()
        # Request updates
        con.reqPositions()
        # Sleep
        sleep(2)
        # Canceling the request
        con.cancelPositions()
        # Disconnecting
        print('Disconnected', con.disconnect())
        
    def get_fundamentals(self):
        # First step is to define a dictionary whill will be populated by IB API
        con = ibConnection(port=4001, clientId=999)
        # Registering Handlers
        #con.registerAll(self.watcher)
        con.register(self.my_fundamental_handler, message.fundamentalData)
        # Setting up the connection
        con.connect()

        # Defining the contract
        aapl = Contract()
        aapl.m_symbol = 'AAPL'
        aapl.m_secType = 'STK'
        aapl.m_exchange = 'SMART'
        aapl.m_currency = 'USD'
        
        con.reqFundamentalData(1, aapl, 'ReportSnapshot')
        sleep(10)
        con.cancelFundamentalData(1)
        
        # Disconnecting from the server
        print('Disconnected', con.disconnect())
        
    def get_implied_vol(self):
        """
        calculates the implied vol for a given contract, underlying price and the option price
        """
        # First step is to define a dictionary whill will be populated by IB API
        con = ibConnection(port=4001, clientId=999)
        # Registering Handlers
        # con.registerAll(self.watcher)
        con.register(self.my_option_handler, message.tickOptionComputation)
        # Setting up the connection
        con.connect()

        # Defining the contract
        asset = Contract()
        asset.m_symbol = 'GS'
        asset.m_secType = 'OPT'
        asset.m_exchange = 'SMART'
        asset.m_currency = 'USD'
        asset.m_strike = str(245.00)
        asset.m_right = 'CALL'
        asset.m_expiry = '20161230'
        asset.m_multiplier = '100'
        
        
        con.calculateImpliedVolatility(1, asset, 0.92, 240.12)
        sleep(2)
        con.cancelCalculateImpliedVolatility(1)
        
        # Assigning The Contract Characteristics To The interim_data
        attrs_contract = vars(asset)
        for a, b in attrs_contract.items():
            self._interim_option_data_dict[str(a)] = b
        self._interim_option_data_dict['CalcImpVol'] = 'True'
        # Attaching to the permanent DataFrame
        self.option_data = self.option_data.append(pd.DataFrame([self._interim_option_data_dict]), ignore_index = True)
        # Disconnecting from the server
        print('Disconnected', con.disconnect())
        
    def get_option_price(self):
        """
        Calculates the option price for a given implied volatility, and option contract
        """
        # First step is to define a dictionary whill will be populated by IB API
        con = ibConnection(port=4001, clientId=999)
        # Registering Handlers
        #con.registerAll(self.watcher)
        con.register(self.my_option_handler, message.tickOptionComputation)
        # Setting up the connection
        con.connect()

        # Defining the contract
        asset = Contract()
        asset.m_symbol = 'GS'
        asset.m_secType = 'OPT'
        asset.m_exchange = 'SMART'
        asset.m_currency = 'USD'
        asset.m_strike = str(245.00)
        asset.m_right = 'CALL'
        asset.m_expiry = '20161230'
        asset.m_multiplier = '100'
        
        
        con.calculateOptionPrice(1, asset, 0.18, 241.25)
        sleep(2)
        con.cancelCalculateOptionPrice(1)
        
        # Assigning The Contract Characteristics To The interim_data
        attrs_contract = vars(asset)
        for a, b in attrs_contract.items():
            self._interim_option_data_dict[str(a)] = b
        self._interim_option_data_dict['CalcImpVol'] = 'False'
        # Attaching to the permanent DataFrame
        self.option_data = self.option_data.append(pd.DataFrame([self._interim_option_data_dict]), ignore_index = True)
        # Disconnecting from the server
        print('Disconnected', con.disconnect())
        
    def get_contract_details(self, contract_ = Contract()):
        """
        Calculates the option price for a given implied volatility, and option contract
        """
        # First step is to define a dictionary will will be populated by IB API
        con = ibConnection(port=4001, clientId=999)
        # Registering Handlers
        #con.registerAll(self.watcher)
        con.register(self.my_contract_handler, message.contractDetails)
        con.register(self.my_contract_end, 'ContractDetailsEnd')
        # Setting up the connection
        con.connect()

        # This is an asynchronous callback method I am building to make sure the call to a method is finished
        con.reqContractDetails(1, contract_)
        ticker = 0
        while not self.end_contract_details and ticker < 100:
            sleep(1)
            ticker += 1
        
        # Disconnecting
        print('Disconnected', con.disconnect())
        
    def get_execution(self, executionFilter_ = ExecutionFilter()):
        """
        Getting the details of the execution within the past 24 hours. Commission reports as well
        
        An executionFilter needs to be passed in
        """
        # First step is to define a dictionary will will be populated by IB API
        con = ibConnection(port=4001, clientId=999)
        
        # Registering Handlers
        #con.registerAll(self.watcher)
        con.register(self.my_execution_handler, message.execDetails)
        con.register(self.my_commission_handler, message.commissionReport)
        con.register(self.my_execution_end, message.execDetailsEnd)
        
        # Setting up the connection
        con.connect()
        
        # Cleaning up the this_execution first
        if not self.this_execution.empty:
            self.this_execution.drop(range(self.this_execution.shape[0]), inplace=True)
        # Cleaning up the this_execution first
        if not self.this_commission.empty:
            self.this_commission.drop(range(self.this_commission.shape[0]), inplace=True)
            
        # Asking the execution details
        #filter_in = self.make_exec_filter(secType = 'BAG')
        con.reqExecutions(1, executionFilter_)
        sleep(5)
        # Disconnecting
        print('Disconnected', con.disconnect())
        
    def get_historical_data(self, 
                            contract_ = Contract(),
                            endDateTime_ = datetime.datetime.now(),
                            durationStr_ = '1 Y',
                            barSizeSetting_ = '1 day',
                            whatToShow_ = 'MIDPOINT',
                            useRTH_ = 0,
                            formatDate_ = 1,
                            sameContract_ = False):
        """
        This function helps to get the historical data for one single contract 
        This method helps us to get the historical data. It is not written in the most optimal way yet.
        """
        # First step is to define a dictionary whill will be populated by IB API
        con = ibConnection(port=4001, clientId=998)
        #con.registerAll(self.watcher)
        con.register(self.my_hist_data_handler, message.historicalData)
        # Setting up the connection
        con.connect()
        
        # Building the contract
        #aapl = self.make_contract(secType = 'STK', symbol = 'AAPL')
        
        # First we should clean up the temporary dataframe of ours
        if not self.hist_data.empty:
            self.hist_data.drop(range(self.hist_data.shape[0]), inplace=True)
        
        # Putting the request in
        con.reqHistoricalData(tickerId = 1, 
                              contract = contract_, 
                              endDateTime = endDateTime_.strftime("%Y%m%d %H:%M:%S %Z"), 
                              durationStr = durationStr_, 
                              barSizeSetting = barSizeSetting_, 
                              whatToShow = whatToShow_, 
                              useRTH = useRTH_, 
                              formatDate = formatDate_)

        
        # Sleep
        sleep(5)
        # Canceling the request
        con.cancelHistoricalData(tickerId = 1)
        # Adding One Thing Before Storing The Contract
        self.hist_data['whatToShow'] = whatToShow_
        self.hist_data['Ticker'] = contract_.m_symbol
        self.hist_data.date = pd.to_datetime(self.hist_data.date)
        # Storing The Data
        conId = self.get_conId(sameContract = sameContract_)
        self.store_historical_data(contract_, conId)
        # Disconnecting
        print('Disconnected', con.disconnect())
        
        
    def get_historical_data_years(self, 
                            contract_ = Contract(),
                            endDateTime_ = datetime.datetime.now(),
                            durationStr_ = '1 Y',
                            barSizeSetting_ = '1 day',
                            whatToShow_ = 'MIDPOINT',
                            useRTH_ = 0,
                            formatDate_ = 1,
                            numOfYears_ = 2):
        """
        This function helps to get the historical data for one single contract 
        This method helps us to get the historical data. It is not written in the most optimal way yet.
        This function calls the previous function to get multiple years of data
        """
        
        # First call
        self.get_historical_data(contract_, endDateTime_, durationStr_, barSizeSetting_, whatToShow_, useRTH_, formatDate_, False)
        endDateTime_ = endDateTime_ - datetime.timedelta(days = 365)
        # The rest
        for i in xrange(1, numOfYears_):
            self.get_historical_data(contract_, endDateTime_, durationStr_, barSizeSetting_, whatToShow_, useRTH_, formatDate_, True)
            endDateTime_ = endDateTime_ - datetime.timedelta(days = 365)
            
        print('Done')
            
    

    def get_market_depth(self, contract_ = Contract(), numRows_ = 5):
        """
        This mathod helps to get the depth of the market before placing an order
        
        """
        # First step is to define a dictionary whill will be populated by IB API
        con = ibConnection(port=4001, clientId=998)
        #con.registerAll(self.watcher)
        con.register(self.my_market_depth_handler, 'UpdateMktDepth')
        # Setting up the connection
        con.connect()
        # Cleaning up the market depth
        self.market_depth.drop(range(self.market_depth.shape[0]), inplace=True)
        self.market_depthL2.drop(range(self.market_depthL2.shape[0]), inplace=True)
        self.all_market_depth.drop(range(self.all_market_depth.shape[0]), inplace=True)
        self.all_market_depthL2.drop(range(self.all_market_depthL2.shape[0]), inplace=True)
        # Requesting the market depth
        con.reqMktDepth(1, contract_, numRows_)
        # Sleep
        sleep(1)
        # Canceling the request
        con.cancelMktDepth(tickerId = 1)
        # Storing The Data
        # ...
        # Disconnecting
        print('Disconnected', con.disconnect())
        
    def put_order(self, contract_ = Contract(), order_ = Order()):
        """
        This function places an order to the exchange
        """
        # First step is to define a dictionary whill will be populated by IB API
        con = ibConnection(port=4001, clientId=998)
        con.registerAll(self.watcher)
        # Setting up the connection
        con.connect()
        con.placeOrder(order_.m_orderId, contract_, order_)
        # Sleep
        sleep(5)
        # Disconnecting
        print('Disconnected', con.disconnect())
        # Storing the orders based on contracts
        m_contract = my_contract(contract_, contract_.m_conId)
        self.all_contract_orders[m_contract] = order_
        
    def cancel_order(self, orderId_ = 1):
        """
        This method is called is to cancel open orders
        """
        # First step is to define a dictionary whill will be populated by IB API
        con = ibConnection(port=4001, clientId=998)
        con.registerAll(self.watcher)
        # Setting up the connection
        con.connect()
        con.cancelOrder(orderId_)
        # Sleep
        sleep(5)
        # Disconnecting
        print('Disconnected', con.disconnect())
    
    def get_open_orders(self):
        """
        This method helps us to get all open orders
        """
        # First step is to define a dictionary whill will be populated by IB API
        con = ibConnection(port=4001, clientId=998)
        #con.registerAll(self.watcher)
        con.register(self.my_order_status_handler, message.orderStatus)
        con.register(self.my_open_order_handler, message.openOrder)
        con.register(self.my_open_order_end, message.openOrderEnd)
        # Setting up the connection
        con.connect()
        con.reqAllOpenOrders()
        # Sleep
        sleep(5)
        # Disconnecting
        print('Disconnected', con.disconnect())
        
    def cancel_all_open_orders(self):
        """
        This method cancels all open orders
        """
        # First step is to define a dictionary whill will be populated by IB API
        con = ibConnection(port=4001, clientId=998)
        con.registerAll(self.watcher)
        # Setting up the connection
        con.connect()
        con.reqGlobalCancel()
        # Sleep
        sleep(2)
        # Disconnecting
        print('Disconnected', con.disconnect())
        
    def get_eod_options(self, 
                        contract_ = Contract(), 
                        eod_or_bod = True, # EOD or BOD options? 
                        whatToShow_ = 'MIDPOINT',
                        endDateTime_ = datetime.datetime.now(),
                        numOfWeeks_ = 1,
                        sameContract_ = False):
        """
        The method returns EOD (3 min before close) and BOD data for options. It uses a different handler
        
        Contract: Specifies the contract we are querying. ib.ext.Contract 
        eod_or_bod: end of the day or beginning of the day. Boolean
        whatToShow: TRADE, MIDPOINT, BID, ASK, BID_ASK. From IB, string.
        endDateTime_: The last datetime that you would like to be queried. string in the right format
        numOfWeeks_: number of weekes we are iterating over. int
        sameContract_: For storage purposes, if it is indeed the same contract then get_conId would return the same id
        """
        # First step is to define a dictionary whill will be populated by IB API
        con = ibConnection(port=4001, clientId=998)
        #con.registerAll(self.watcher)
        #con.register(self.my_hist_data_handler, message.historicalData)
        #con.register(self.my_hist_option_eod_handler, message.historicalData)
        if eod_or_bod:
            con.register(self.my_hist_option_eod_handler, message.historicalData)
        else:
            con.register(self.my_hist_option_bod_handler, message.historicalData)
        # Setting up the connection
        con.connect()
        
        # First we should clean up the temporary dataframe of ours
        if not self.hist_data.empty:
            self.hist_data.drop(range(self.hist_data.shape[0]), inplace=True)
        
        # Putting the request in
        weekEnd = endDateTime_
        for i in xrange(numOfWeeks_):
            con.reqHistoricalData(tickerId = i, 
                                  contract = contract_, 
                                  endDateTime = weekEnd.strftime("%Y%m%d %H:%M:%S %Z"), 
                                  durationStr = '1 W', 
                                  barSizeSetting = '3 mins', 
                                  whatToShow = whatToShow_, 
                                  useRTH = 0, 
                                  formatDate = 1)
            sleep(2)
            print ' - Iteration %s Completed - ' % i
            weekEnd = weekEnd - datetime.timedelta(days = 7)
 
        # Sleep
        sleep(1)
        # Canceling the request
        con.cancelHistoricalData(tickerId = 1)
        # Adding One Thing Before Storing The Contract
        self.hist_data['whatToShow'] = whatToShow_
        self.hist_data['Ticker'] = contract_.m_symbol
        self.hist_data.date = pd.to_datetime(self.hist_data.date)
        # Storing The Data
        conId = self.get_conId(sameContract = sameContract_)
        self.store_historical_data(contract_, conId)
        # Disconnecting
        print('Disconnected', con.disconnect())

