#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Sep  4 18:09:48 2021

@author: macbookair
"""

#SETUP STRATEGIA 100 candele ALLINEAMENTO

import tickers_dexcalibur as tickers # per selezionare il gruppo di coin tickersBTC_v2
import strategy_moonlight
import matplotlib.pyplot as plt

btc = 0.01
fee = 0.001
slippage = 0.001
n_coins = len(tickers.tickers.keys())

# exit, entry, n_candles, tickers
moonlight = strategy_moonlight.get_data_bot(14,7,90,tickers.tickers,btc,fee,slippage)

adjusted_balance = 0

for SYMBOL in tickers.tickers.keys():
    operations = moonlight[SYMBOL].iloc[-1]['OPERATIONS']
    single_adj_balance = moonlight[SYMBOL].iloc[-1]['BALANCE'] - (btc * fee * operations) - (btc * slippage * operations)
    
    adjusted_balance += round(single_adj_balance, 6)
    
p_l_system_adj = round((adjusted_balance - (btc*n_coins))/(btc*n_coins) * 100, 2)
    
print('\nWALLET: ',round(adjusted_balance,6),'\tP/L:',p_l_system_adj,'% - with FEEs and SLIPPAGE')  

moonlight_master = moonlight[list(moonlight.keys())[0]].copy()
moonlight_master.POSITION = 0
moonlight_master.BALANCE = 0
moonlight_master.OPERATIONS = 0
for coin_dataframe in moonlight:
    moonlight_master += moonlight[coin_dataframe]
    
moonlight_master.BALANCE.plot();plt.legend()
