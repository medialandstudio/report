#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun May 10 17:52:28 2020

@author: ministudio
"""

from binance.client import Client
import pandas as pd
import sys
from datetime import datetime
import smtplib
import time
from decimal import Decimal as D, ROUND_DOWN

client = Client()

def execOrder(user, user_name, multi, sym, Ncrt, maxValue, ticker, side, mailingList, strategyName, attempts = 1):
    '''user, multi, symbol, Ncrt, maxValue, ticker, side, mailingList, strategyName, attempts'''
                   
    amount = Ncrt
    
    filled = False
    
    try:
        if side == 'buy':
            order = user.order_market_buy(symbol=sym,quantity=amount)
            
        if side == 'sell':
            order = user.order_market_sell(symbol=sym,quantity=amount)
        
        if order['status'] == 'FILLED':
            
            print(f'{datetime.now()} FILLED {amount} @{ticker} {sym} for {user_name}')
            #logging.info(f'{datetime.now()} {side} @ {ticker} for {user}')
            
            filled = True
    
        return filled
    
    except:
        
        error = sys.exc_info()[1]
        
        if error.code == -2010:
            print('insufficient balance... buy/sell-ing as much as possible')
            
            try:
                if side == 'buy':
                    toBuy = round(float(user.get_asset_balance(sym[3:])['free']),6)
                    newQnty = round(Ncrt/(maxValue/toBuy),6)
                    order = user.order_market_buy(symbol=sym,quantity=newQnty)

                if side == 'sell':
                    free = float(user.get_asset_balance(sym[:3])['free'])
                    newQnty = float(D(free).quantize(D('0.000001'), rounding=ROUND_DOWN))# - 0.000001
                    print(free, newQnty)
                    order = user.order_market_sell(symbol=sym,quantity=newQnty)

                amount = newQnty

                print('STATUS ->',order['status'],'at',order['executedQty'])
                filled = True

                return filled
            
            except:
                
                print(error)

                return False
        
        else:
            print(datetime.now(),error.message)
            
    finally:
        
        if filled:
            thBNB = 0.1
            
            if feeBNB(user,thBNB):
                print(user_name,f'W A R N I N G - - - BNB < {thBNB}')
                #mail di avviso
                #mailReport(mailingList,f'{strategyName}',f'{user_name} -- BNB < di {thBNB}') 
            
            return filled
            
        else:
            if attempts < 2:
                time.sleep(0.1)
                execOrder(user, user_name, multi, sym, Ncrt, maxValue, ticker, side, mailingList, strategyName, attempts+1)
            else:
                #mailReport(mailingList,f'{strategyName}',f'{user_name} -- impossibile effettuare ordine {sym}') 
                return False

def getCandles(timeframe, sym, length = 1, reverse= True, exchange='binance'):
    ''' restituisce il DATAFRAME relativo alle candele richieste '''
    
    dataCandles = [ 'MTS', 'OPEN', 'HIGH', 'LOW', 'CLOSE', 'VOLUME', 'CLOSETIME', 
                   'QUOTE_ASSET_VOLUME', 'N_TRADES', 'TAKER_BUY_BASE', 'TAKER_BUY_QUOTE', 'TO_IGNORE']
    
    timeframeStandard = ['1m','5m','15m','30m','1h','2h','4h','6h','8h','12h','1d','1M']
    
    if timeframe in timeframeStandard:
        
        candlesBIN = client.get_klines(symbol=sym, interval=timeframe)   
        candles = pd.DataFrame(candlesBIN, columns = dataCandles)
        candles.MTS = pd.to_numeric(candles.MTS/1000,downcast='integer')
        candles.HIGH = pd.to_numeric(candles.HIGH)
        candles.LOW = pd.to_numeric(candles.LOW)
        candles.OPEN = pd.to_numeric(candles.OPEN)
        candles.CLOSE = pd.to_numeric(candles.CLOSE)     
        
        return candles
    
    elif 'd' in timeframe:
        number = int(timeframe[:-1])
        #offset = datetime.utcnow().isoweekday()
        candlesBIN = client.get_klines(symbol=sym, interval=Client.KLINE_INTERVAL_1DAY, limit=500)
        
        indexStart = 0
        indexEnd = len(candlesBIN)
        
        return pd.DataFrame(merge(candlesBIN,indexStart,indexEnd,number,dataCandles), columns = dataCandles)


def merge(candlesRAW,indexStart,indexEnd,offset, dataCandles):
    
    adjRAW = []
    for x in range(indexStart,indexEnd):
        if datetime.utcfromtimestamp(candlesRAW[x][0]/1000).isoweekday() == 7:
            indexStart = x
            break
           
    for x in range(indexStart,indexEnd,offset):
            
        mergingRAWS = []
        
        if x+offset > indexEnd-1:
            break
              
        for y in range (x, x+offset):
            mergingRAWS.append(candlesRAW[y])
            
        merged = pd.DataFrame(mergingRAWS, columns = dataCandles)
                         
        adjRAW.append([merged.MTS[0],merged.OPEN[0],max(pd.to_numeric(merged.HIGH)),
                       min(pd.to_numeric(merged.LOW)), merged.CLOSE[offset-1],
                       sum(pd.to_numeric(merged.VOLUME)),merged.CLOSETIME[offset-1],
                       merged.QUOTE_ASSET_VOLUME[0],sum(merged.N_TRADES),merged.TAKER_BUY_BASE[0],
                       merged.TAKER_BUY_QUOTE[0],merged.TO_IGNORE[0]])                 
                      
    return adjRAW


def feeBNB(client, treshold):
    try:
        if float(client.get_asset_balance('BNB')['free']) < treshold:
            return True
        else:
            return False
    except:
        print('impossibile prelevare dati su portafoglio BNB')
        return False
    

def mailReport(mailingList, subject, message):
    
    try:
        subject = f'Subject: {subject}\n\n'
        content = message

        for to in mailingList:
            email = smtplib.SMTP('m-ra.th.seeweb.it', 587)

            email.ehlo()
            email.starttls()
            email.login('medialand.it','p14n0f0rt3')

            email.sendmail('francescosilipo@medialand.it',to, subject + content)
        
        email.quit()
    except:
        pass


def precisionCoin(stepSize):
    precision = 0
    floatStepSize = float(stepSize)
    
    for i in range(0, len(stepSize)):
        if floatStepSize == 1:
            return int(precision)
        else:
            precision += 1
            floatStepSize *= 10
# def process_message(msg):
#     print("message type: {}".format(msg['e']))
#     print(msg)
#     # do something

# bm = BinanceSocketManager(client)
# # start any sockets here, i.e a trade socket
# #conn_key = bm.start_trade_socket('BTCUSDT', process_message)
# conn_key = bm.start_symbol_ticker_socket('BNBBTC', process_message)
# # then start the socket manager
# bm.start()
