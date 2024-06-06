#import necessary stuff
from __future__ import (absolute_import,division,print_function,unicode_literals)
import backtrader as bt
import datetime 
import pandas as pd
import matplotlib.pyplot as plt
import os.path
from meanreversion import MeanReversion
from getdata import get_tickers
from secrets1 import address
if __name__ =='__main__':
    #initialize cerebro
    cerebro = bt.Cerebro()
    #get tickers
    tickers = get_tickers()
    #create a list for valid tickers
    valid_tickers = []
    #loop through the tickers
    for i in tickers: #if low on time or resources just use [range_a:range_b] where range are ints between 0-500 and a>b
        datapath = f'{address}/{i}.csv'
        #try to convert the files into dfs
        try:
            df = pd.read_csv(datapath)
            if not df.empty:
                valid_tickers.append(i)
        except FileNotFoundError:
            print(f'CSV file not found for {i}')
    #iterate through valid tickers 
    for i in valid_tickers:
        #print the valid tickers 
        print(i)
        #use the datapaths again
        datapath = f'{address}/{i}.csv'
        #create the dfs again
        df = pd.read_csv(datapath)
        #convert date from string to date
        df['Date'] = pd.to_datetime(df['Date'])
        #get the data
        data = bt.feeds.PandasData(
            dataname=df,
            fromdate=datetime.datetime(2014,1,3),
            todate=datetime.datetime(2020,12,31),
            datetime=0,high=2,low=3,open=1,close=4,volume=5
        )
        #add the data
        cerebro.adddata(data)
    #add sharpe analyzer
    cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name='sharpe')
    ### COMMENTED BELOW IS STRATEGY USED FOR OPTIMIZING WITH EXAMPLATORY PARAMS - WARNING: HIGH COMPUTATIONAL COSTS
    #strats = cerebro.optstrategy(MeanReversion,maperiod=range(10,31,5),entry_threshold=range(1,4,1),exit_threshold=range(1,4,1))
    #add already optimized strategy
    cerebro.addstrategy(MeanReversion)
    #Set cash start
    cerebro.broker.setcash(10000.0)
    #set max size of buy/sell
    cerebro.addsizer(bt.sizers.FixedSize, stake=40)
    #set comission
    cerebro.broker.setcommission(commission=0.001)
    #print out the starting conditions
    print('Starting Portfolio Value: %.2f' % cerebro.broker.getvalue())
    #run over everything
    thestrats = cerebro.run(maxcpus=1)
    #print out the final result
    print('Final Portfolio Value: %.2f' % cerebro.broker.getvalue())
    best_sharpe_ratio = None
    best_strategy = None
    for strat in thestrats:
        #access the Sharpe Ratio analyzer
        sharpe_ratio = strat.analyzers.sharpe.get_analysis()['sharperatio'] #when using optstrat change strat to strat[0]
        #check if the Sharpe Ratio is available
        if sharpe_ratio is not None:
            #update the best Sharpe Ratio and strategy if it's the highest so far
            if best_sharpe_ratio is None or sharpe_ratio > best_sharpe_ratio:
                best_sharpe_ratio = sharpe_ratio
                best_strategy = strat   #when using optstrat change strat to strat[0]
    #show the trading process
    cerebro.plot()
    #print the best Sharpe Ratio found
    if best_strategy is not None:
        print('Best Strategy - Sharpe Ratio:',best_strategy.params.__dict__, best_sharpe_ratio)
    else:
        print('No strategy found with a valid Sharpe Ratio')


