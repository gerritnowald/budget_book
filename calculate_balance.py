# -*- coding: utf-8 -*-
"""
@author: Gerrit Nowald
"""

import pandas as pd
import yaml

#------------------------------------------------------------------------------
# read settings from config file

with open("config.ini", "r") as ymlfile:
    cfg = yaml.safe_load(ymlfile)

clm = cfg['column names database']

#------------------------------------------------------------------------------
# load data

transactions = pd.read_csv(cfg['CSV filenames']['database'] + '.csv', encoding = "ISO-8859-1")

# transactions[clm['date']] = pd.to_datetime(transactions[clm['date']], format = cfg['date format'])

#------------------------------------------------------------------------------
# calculate balance

transactions.sort_values(clm['date'], ascending=False, inplace = True)

transactions[clm['balance']] = transactions.loc[::-1, clm['amount']].cumsum()[::-1]
transactions[clm['balance']] = transactions[clm['balance']] - transactions.iloc[0][clm['balance']] + cfg['final balance']
transactions[clm['balance']] = transactions[clm['balance']].round(2)

#--------------------------------------------------------------------------
# save

transactions.to_csv(cfg['CSV filenames']['database'] + '.csv', encoding = "ISO-8859-1", index=0)