#import necessary libraries
import requests_cache
import requests
import pandas_datareader.data as web
import os
from datetime import date,timedelta
import pandas as pd
import yfinance as yf
from requests import Session
from requests_cache import CacheMixin, SQLiteCache
from requests_ratelimiter import LimiterMixin, MemoryQueueBucket
from pyrate_limiter import Duration, RequestRate, Limiter
import bs4 as bs
from secrets1 import address
#set the time periods for excavation of data
START_DATE_DAILY = 2010
END_DATE_DAILY = '2024-12-31'
#limit the number of requests so that yahoo doesn't get angry
class CachedLimiterSession(CacheMixin, LimiterMixin, Session):
    pass

session = CachedLimiterSession(
    limiter=Limiter(RequestRate(2, Duration.SECOND*5)),  # max 2 requests per 5 seconds
    bucket_class=MemoryQueueBucket,
    backend=SQLiteCache("yfinance.cache"),
)
#get the earliest date of the stock being in s&p500
def get_listing_date(symbol):
    #get ticker
    ticker = yf.Ticker(symbol)
    #try to get the tickers earliest date or return an error
    try:
        hist = ticker.history(period='max')
        if not hist.empty:
            return hist.index.min()
        else:
            return None
    except Exception as e:
        print(f"Error fetching data for {symbol}: {e}")
        return None

#excavate tickers from wikipedia
def get_tickers():
    #get access to wikipedia page
    sp500tb = requests.get('https://en.wikipedia.org/wiki/List_of_S%26P_500_companies')
    #turn it into a soup of text
    soup = bs.BeautifulSoup(sp500tb.text, features='lxml')
    #find a the first table at the top with classes wikitable sortable
    soup = soup.find('table',attrs='wikitable sortable')
    tickers = []
    #for every row except the header
    for row in soup.findAll('tr')[1:]:
        #get the text which is the ticker
        ticker = row.find('td').text
        #take care of tickers that are not available
        if ticker != 'BRK.B\n' and ticker != 'BF.B\n':
            #append the right tickers without '\n'
            tickers.append(ticker[:-1])
    return tickers
    
#get the data with yfinance
def get_data(tickers):
    #initiate a counter
    counter = 0
    #for every ticker
    for i in tickers:
        try:
            #if there is no folder to store it in
            if not os.path.exists(f"{address}"):
                #make one
                os.makedirs(f"{address}") 
            #if the stock is not already in the folder
            if not os.path.exists(f"{address}/{i}.csv"):
                #get the stock from yfinance
                ticker = yf.Ticker(i)
                #import it in a specified timeframe (1day intervals)
                listing_date = get_listing_date(i)
                if listing_date and listing_date.year <= START_DATE_DAILY:
                    stock = ticker.history(period='max')
                    #use tz_localize to make sure that the dates are correct
                    stock.index = stock.index.tz_localize(None)
                    #print a part of the stock to see that everything is fine
                    print(stock)
                    #convert it to csv
                    stock.to_csv(f"{address}/{i}.csv")
                    #update the counter    
                    counter +=1 
        except:
            #if there is an error, assume that symbol is not in db
            print(f'Symbol not in DB {i}')
    #print the number of stocks successfully added
    print(f'{counter} Stocks added')
#used only for the first download of the data
#get_data(get_tickers())