'''
    RAPHAEL TRADING STRATEGY
    ------------------------  
    This is a basic trend following trading strategy 
    created using the RSI, MACD, and Exponential MA 
    -
    Created by Philson
    https://github.com/AzureKn1ght
    -
'''

class Raphael(QCAlgorithm):

    def Initialize(self):
        
        # Training Period:  2010-2016  
        # Test Period:      2016-Present
        self.SetStartDate(2016, 1, 1)    # Set Start Date
        # self.SetEndDate(2016, 1, 1)    # Set End Date
        
        # Set Strategy Cash
        self.SetCash(1000000)  
        
        # Assets to Trade (See Presentation Document) 
        self.assets = ["MSFT","FB","APPL","GOOGL","AMZN","CRM","JPM","PFE","TLSA","NFLX","IAU","ATVI","MNSO","MDB","CRWD","AMD","DDOG","SE","ZM","MDY","EEM","PYPL","UNH","NVDA","EBAY","MA","TWTR","SQ","CME"]
        
        # STRATEGY PARAMETERS           (use this to optimize)
        RSI_Period = 13                 # Daily RSI Look back period 
        self.RSI_Threshold = 50         # RSI bullish threshold level
        MACD_Fast = 12                  # Hourly MACD fast EMA 
        MACD_Slow = 26                  # Hourly MACD slow EMA
        MACD_Signal = 9                 # Hourly MACD signal length
        EMA_Length = 34                 # Hourly trend baseline EMA
        
        # TRADING PRAMETERS             (portfolio allocation, R/R ratio)
        self.Allocation = 0.1           # Percentage of captital to allocate
        ATR_Period = 13                 # Hourly ATR period for stoploss
        self.SL_Multiple = 2            # Multiple of ATR for stoploss
        self.TP_Multiple = 4            # Multiple of ATR for TP [1 : 2]


        # Warmup period to ensure enough indicator data
        self.SetWarmUp(RSI_Period+1)

        
        # Asset Object (Store the data in Dictionaries)
        self.rsi = {}
        self.macd = {}
        self.ema = {}
        self.atr = {}
        self.prev_macd = {}
        self.prev_macd_signal = {}
        self.entry_price = {}
        self.take_profit = {}
        self.stoploss = {}
        
        # Initialize all the asset variables
        for i in self.assets:
            self.AddEquity(i, Resolution.Hour)
            self.rsi[i] = self.RSI(i, RSI_Period, Resolution.Daily)
            self.macd[i] = self.MACD(i, MACD_Fast, MACD_Slow, MACD_Signal, Resolution.Hour)
            self.ema[i] = self.EMA(i, EMA_Length, Resolution.Hour)
            self.atr[i] = self.ATR(i, ATR_Period, Resolution.Hour)
            self.prev_macd[i] = None
            self.prev_macd_signal[i] = None
            self.entry_price[i] = None
            self.take_profit[i] = None
            self.stoploss[i] = None
            
        self.Debug("RAPHAEL: STRATEGY STARTED")
            
            
    
    # Function to act on every incoming data bar        
    def OnData(self, data):
        # check if indicators ready
        if self.IsWarmingUp: return
        
        # check through all the assets
        for asset in self.assets:
            if data.ContainsKey(asset) and not data[asset] == None:

                # Already invested, check for exit conditions
                if self.Securities[asset].Invested:
                    self.CheckTPandSL(asset, data)
    
                # Not invested, check whether we should enter
                else:
                    self.CheckEntryCondition(asset, data)
                
                # Update prev_macd and prev_macd_signal data
                self.prev_macd[asset] = self.macd[asset].Current.Value
                self.prev_macd_signal[asset] = self.macd[asset].Signal.Current.Value
            
            
            
    # Function to check TP/SL and exit accordingly
    def CheckTPandSL(self, asset, data):
        if self.stoploss[asset] == None or self.take_profit[asset] == None: return
    
        if data[asset].Close <= self.stoploss[asset]:
            self.Liquidate(asset, "stop-loss")
            self.entry_price[asset] = None
            self.take_profit[asset] = None
            self.stoploss[asset] = None
            self.Debug(str(asset) + " stoploss hit: " + str(data[asset].Close))
            
        elif data[asset].High >= self.take_profit[asset]:
            self.Liquidate(asset, "take-profit")
            self.entry_price[asset] = None
            self.take_profit[asset] = None
            self.stoploss[asset] = None
            self.Debug(str(asset) + " profit taken: " + str(data[asset].Close))



    # Function to check for entry conitions and buy
    def CheckEntryCondition(self, asset, data):
        if self.prev_macd[asset] == None or self.rsi[asset] == None: return
    
        # Calculate TP and SL based on ATR
        ATR = self.atr[asset].Current.Value
        TP = data[asset].Close + ATR * self.TP_Multiple
        SL = data[asset].Close - ATR * self.SL_Multiple
    
        # Check for bullish daily RSI
        RSI_Bullish = self.rsi[asset].Current.Value > self.RSI_Threshold
        
        # Check for uptrend in Price
        EMA = self.ema[asset].Current.Value
        Uptrend = (data[asset].Open > EMA) and (data[asset].Close > EMA)
        
        # Check for bullish MACD cross
        MACD_Cross = (self.prev_macd[asset] < self.prev_macd_signal[asset]) \
        and (self.macd[asset].Current.Value > self.macd[asset].Signal.Current.Value)

        
        if RSI_Bullish and Uptrend and MACD_Cross and not self.Securities[asset].Invested:
            self.Debug("--- Buy Signal Triggered ---")
            self.SetHoldings(asset, self.Allocation)
            
            self.entry_price[asset] = data[asset].Close
            self.take_profit[asset] = TP
            self.stoploss[asset] = SL
            
            self.Debug("Bought: " + str(asset) + " at " + str(self.entry_price[asset]))
            self.Debug("Take Profit: " + str(self.take_profit[asset]))
            self.Debug("Stoploss: " + str(self.stoploss[asset]))

  