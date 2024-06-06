import backtrader as bt
#create a MeanReversion strat
class MeanReversion(bt.Strategy):
    #create params for moving average, entry and exit
    params = (
        ('maperiod', 20),
        ('entry_threshold', 1),
        ('exit_threshold', 2),
        ('stop_loss',0.02),
        ('take_profit',0.03),
    )
    def log(self,txt,dt=None,doprint=False):
        #if doprint is true
        if doprint:
            #date == date if it was provided or get current date that is provided in datas
            dt = dt or self.datas[0].datetime.date(0)
            #print the date and the text
            print(f"{dt.isoformat()}, {txt}")
    def __init__(self):
        #loop through each data feed and create a dictionary to store order information for each one.
        #the dictionary keys are the data feeds, and the values are initialized to None.
        #keep a reference to the closing price in the data dataseries
        self.dataclose = {data: data.close for data in self.datas}
        #create a var for the order
        self.orders = {data: None for data in self.datas} 
        #create a var for the buyprice
        self.buyprices = {data: None for data in self.datas}
        #create a var for stopprice
        self.stop_prices = {data: None for data in self.datas}
        self.take_profit_prices = {data: None for data in self.datas}
        #create a var for commision
        self.buycomms = {data: None for data in self.datas}
        #calculate the simple moving average
        self.smas = {data: bt.indicators.SimpleMovingAverage(data, period=self.params.maperiod) for data in self.datas}
        #calculate the standard deviation
        self.stddevs = {data: bt.indicators.StandardDeviation(data, period=self.params.maperiod) for data in self.datas}
        #calculate the zscore
        self.zscores = {data :(data.close - self.smas[data]) / self.stddevs[data] for data in self.datas}
        
    def notify_order(self,order):
        data = order.data
        #if order has already been submitted or accepted return
        if order.status in [order.Submitted, order.Accepted]:
            return
        #if order is completed
        if order.status in [order.Completed]:
            #if order is getting bought
            if order.isbuy():
                #log the buy (price cost and commission)
                self.log(f'BUY EXECUTED, Price: {order.executed.price}, Cost: {order.executed.value}, Comm: {order.executed.comm}')
                #set the buying price as the price at which the stock was bought
                self.buyprices[data] = order.executed.price
                #set the commission like that as well
                self.buycomms[data] = order.executed.comm
            #if order is not getting bought
            else:
                #log the sell (price cost and commission)
                self.log(f'SELL EXECUTED, Price: {order.executed.price}, Cost: {order.executed.value}, Comm: {order.executed.comm}')
            #keep track of executed lines
            self.bar_executed = len(self)
        #if order could not go through
        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            #log it
            self.log('Order Canceled/Margin/Rejected')
        #no pending order
        self.orders[data] = None
    #keep track of trades
    def notify_trade(self,trade):
        #if the trade is not closed yet
        if not trade.isclosed:
            return
        #log profit
        self.log(f'OPERATION PROFIT, GROSS {trade.pnl}, NET {trade.pnlcomm}')
    def next(self):
        #log the closing price
        for data in self.datas:
            self.log(f'Close, {self.dataclose[data][0]}',)
            #if order is pending move to the next stock 
            if self.orders[data]:
                continue       

            #if we are not in the market
            if not self.getposition(data):
                #if the zscore is less than the entry threshold and we are not already in the market
                if self.zscores[data][0] < -self.params.entry_threshold and not self.getposition(data):
                    #buy
                    self.orders[data] = self.buy(data=data)
                    self.buyprices[data] = self.dataclose[data][0]
                    self.stop_prices[data] = self.buyprices[data] * (1.0 - self.params.stop_loss)
                    self.take_profit_prices[data] = self.buyprices[data] * (1.0 + self.params.take_profit)
            #if we are in the market
            else:
                #if the price is less than the risk we are willing to take or more than the profit we are willing to lose
                if self.dataclose[data][0] <= self.stop_prices[data] or self.dataclose[data][0] >= self.take_profit_prices[data]:
                    #sell
                    self.orders[data] = self.sell(data=data)
                #if the zscore is more than the exit threshold and we are in the market
                elif self.zscores[data][0] > self.params.exit_threshold and self.getposition(data):
                    #sell
                    self.orders[data] = self.sell(data=data)
    def stop(self):
        self.log(f'Lookback period {self.params.maperiod},, ENTRY {self.params.entry_threshold},, EXIT {self.params.exit_threshold} ENDING VALUE {self.broker.getvalue()} ',doprint=True)
        