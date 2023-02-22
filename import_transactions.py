# -*- coding: utf-8 -*-
"""
@author: Gerrit Nowald
"""

import pandas as pd

#------------------------------------------------------------------------------
# input

file_new = 'bank_export'

file_db  = 'transactions'

# column names in transactions file
clm = dict(
    date       = 'date'     ,
    amount     = 'amount'    ,
    category   = 'category' ,
    balance    = 'balance',
    )

#------------------------------------------------------------------------------
# load

transactions     = pd.read_csv( file_db  + '.csv', encoding = 'ISO-8859-1', sep =';', decimal=',' )
transactions_new = pd.read_csv( file_new + '.csv', encoding = 'ISO-8859-1', sep =';', decimal=',', thousands='.', header=2 )

#------------------------------------------------------------------------------
# clean up transactions

# drop / rename columns
transactions_new = transactions_new.dropna(how='all', axis=1)
transactions_new = transactions_new.drop(['Valuta'] , axis=1)
transactions_new = transactions_new.rename({'day'          : clm['date'],
                                            'amount in EUR': clm['amount']}, axis=1)

# correct dates
transactions[clm['date']]     = pd.to_datetime( transactions[clm['date']]     , format='%d.%m.%Y' )
transactions_new[clm['date']] = pd.to_datetime( transactions_new[clm['date']] , format='%d.%m.%Y', errors='coerce' )

transactions_new = transactions_new.dropna(how='any', axis=0)

#------------------------------------------------------------------------------
# filtering time

max_date = max(transactions[clm["date"]])

transactions_new = transactions_new.query('Datum > @max_date')

#------------------------------------------------------------------------------
# calculate balance

final_balance = transactions.iloc[0][clm['balance']]

transactions_new[clm['balance']] = transactions_new.loc[::-1, clm['amount']].cumsum()[::-1] + final_balance

#------------------------------------------------------------------------------
# concatenate  

transactions = pd.concat( [transactions_new, transactions] ).reset_index(drop=True)

#------------------------------------------------------------------------------
# save

# transactions.to_csv(file_db + '.csv', sep=';', decimal=',', encoding = "ISO-8859-1", index=0)
