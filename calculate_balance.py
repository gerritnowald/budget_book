# -*- coding: utf-8 -*-
"""
@author: Gerrit Nowald
"""

import pandas as pd

#------------------------------------------------------------------------------
# input

final_balance = 3000

# column names
clm = dict(
    date       = 'date'     ,
    amount     = 'amount'    ,
    balance    = 'balance'
    )

file = 'transactions'

#------------------------------------------------------------------------------
# load data

transactions = pd.read_csv(file + '.csv', sep =";", decimal='.', encoding = "ISO-8859-1")

# transactions[clm['date']] = pd.to_datetime(transactions[clm['date']], format='%d.%m.%Y')

#------------------------------------------------------------------------------
# calculate balance

transactions.sort_values(clm['date'], ascending=False, inplace = True)

transactions[clm['balance']] = transactions.loc[::-1, clm['amount']].cumsum()[::-1]
transactions[clm['balance']] = transactions[clm['balance']] - transactions.iloc[0][clm['balance']] + final_balance

#--------------------------------------------------------------------------
# save

transactions.to_csv(file + '.csv', sep=';', decimal='.', encoding = "ISO-8859-1", index=0)