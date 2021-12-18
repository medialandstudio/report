#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Sep  4 18:09:48 2021

@author: macbookair
"""

#SETUP STRATEGIA 100 candele ALLINEAMENTO

from datetime import datetime
import myBINANCE as bnc
import pandas as pd
import tickersBTC_v2 as tickers # per selezionare il gruppo di coin tickersBTC_v2

btc = 0.01 
fee = 0.001
slippage = 0.001
n_coins = len(tickers.tickers.keys())


def get_data_bot(en, ex, backtest_length):
    global btc, fee, slippage, n_coins
    
    candles = {}
    ledger_pl = {}
    
    total_balance = 0
    
    print('SYMBOL | BALANCE | POSITION |  P/L %  |')
    
    for SYMBOL in tickers.tickers.keys():
        candles[SYMBOL] = bnc.getCandles('1d', SYMBOL) 
        
        ledger_pl[SYMBOL] = pd.DataFrame(columns=['POSITION','BALANCE','OPERATIONS'])
        
        position = 0
        entry_price = 0
        p_l = 0
        operations = 0
        
        for i in range(-backtest_length, 0):
        
            date = datetime.utcfromtimestamp(candles[SYMBOL].iloc[i].MTS)
            close = candles[SYMBOL].iloc[i-1].CLOSE if i == -1 else candles[SYMBOL].iloc[i].CLOSE
            #high = candles[SYMBOL].iloc[i].HIGH
            #low = candles[SYMBOL].iloc[i].LOW
            #print(SYMBOL, date, 'POSITION', '___' if position == 0 else '///', 'CLOSE', close)
            if i == -backtest_length:
                ledger_pl[SYMBOL].loc[date.strftime('%m/%d/%Y'), 'BALANCE'] = btc
            
            else:    
                if position == 0:
                    highest = candles[SYMBOL].iloc[-en+i:i].CLOSE.max()
                    
                    if close > highest:
                        position = 1
                        entry_price = close
                        operations += 1
                        
                    ledger_pl[SYMBOL].loc[date.strftime('%m/%d/%Y'), 'BALANCE'] = ledger_pl[SYMBOL].iloc[-1]['BALANCE']
                    ledger_pl[SYMBOL].loc[date.strftime('%m/%d/%Y'), 'OPERATIONS'] = operations

                else:
                    lowest = candles[SYMBOL].iloc[-ex+i:i].CLOSE.min()
    
                    if close < lowest:
                        position = 0
                        operations += 1
                        p_l = round(((close - entry_price)/entry_price) * btc, 4)
                        
                        ledger_pl[SYMBOL].loc[date.strftime('%m/%d/%Y'), 'BALANCE'] = round(ledger_pl[SYMBOL].iloc[-2]['BALANCE']+p_l, 4)
                        
                        #print('P/L:', p_l, datetime.utcfromtimestamp(candles[SYMBOL].iloc[i].MTS))
                    else:
                        if len(ledger_pl[SYMBOL]) > 1:
                            last_balance = ledger_pl[SYMBOL].iloc[-2]['BALANCE']
                        else:
                            last_balance = ledger_pl[SYMBOL].iloc[-1]['BALANCE']
                            
                        ledger_pl[SYMBOL].loc[date.strftime('%m/%d/%Y'), 'BALANCE'] = last_balance
                    
                    ledger_pl[SYMBOL].loc[date.strftime('%m/%d/%Y'), 'OPERATIONS'] = operations
                    
            ledger_pl[SYMBOL].loc[date.strftime('%m/%d/%Y'), 'POSITION'] = position
        
        final_balance = ledger_pl[SYMBOL].iloc[-1]['BALANCE']
        total_balance += final_balance
        last_position = ledger_pl[SYMBOL].iloc[-1]['POSITION']
        p_l_coin = round((final_balance - btc)/btc * 100, 2)
        
        print(SYMBOL,'  ',final_balance,'\t\t',last_position,'\t',p_l_coin,'%')
     
    p_l_system = round((total_balance - (btc*n_coins))/(btc*n_coins) * 100, 6)  
    
    print('\nWALLET: ',round(total_balance,8),'\tP/L:',p_l_system,'%')   
    
    return ledger_pl


moonlight = get_data_bot(14,7,90)

adjusted_balance = 0

for SYMBOL in tickers.tickers.keys():
    operations = moonlight[SYMBOL].iloc[-1]['OPERATIONS']
    single_adj_balance = moonlight[SYMBOL].iloc[-1]['BALANCE'] - (btc * fee * operations) - (btc * slippage * operations)
    
    adjusted_balance += round(single_adj_balance, 6)
    
p_l_system_adj = round((adjusted_balance - (btc*n_coins))/(btc*n_coins) * 100, 2)
    
print('\nWALLET: ',round(adjusted_balance,6),'\tP/L:',p_l_system_adj,'% - with FEEs and SLIPPAGE')  

moonlight_master = moonlight[list(moonlight.keys())[0]]
moonlight_master.POSITION = 0
moonlight_master.BALANCE = 0
moonlight_master.OPERATIONS = 0
for coin_dataframe in moonlight:
    moonlight_master += moonlight[coin_dataframe]
    
moonlight_master.BALANCE.plot()