# -*- coding: utf-8 -*-
"""
@author: Gerrit Nowald
"""

import pandas as pd
import numpy as np
from dateutil import relativedelta

def get_sum_cat_month(transactions, clm, next_months=3):
    """creates a table of spendings per month and category"""

    transactions_cat = transactions.groupby(clm['category'])
    
    sum_cat_month = ( transactions_cat
                        .resample('1M', on=clm['date']).sum(numeric_only=True)[clm['amount']]
                        .unstack(0).replace(0, np.nan) )
    
    sum_cat_month.index = sum_cat_month.index.map(lambda date : str(date)[:7])  # prettier index
    
    sum_cat_month = sum_cat_month.transpose()
    
    
    # columns sum & mean/month per category
    sum_cat_month[clm['sum']] , sum_cat_month[clm['mean_month']] = sum_cat_month.sum(axis=1) , sum_cat_month.mean(axis=1)   # mean not influenced by sum
    
    # column mean/transaction per category
    sum_cat_month[clm['mean_trsct']] = sum_cat_month[clm['sum']] / transactions_cat.count()[clm['amount']]
    
    
    sum_cat_month = sum_cat_month.sort_index()  # by category
    # sum_cat_month = sum_cat_month.sort_values(clm['sum'])
    
    
    # forecast for next months
    forecast = sum_cat_month[clm['sum']] / ( sum_cat_month.shape[1] - 3 )
    
    next_month_lst = [ max(transactions[clm['date']]) ]
    for _ in range(next_months):
        next_month_lst.append( max(next_month_lst) + relativedelta.relativedelta(months=1) )
    next_month_lst = next_month_lst[1:]
    next_month_lst = [ str(month)[:7] for month in next_month_lst ]    # prettier index
    
    NEXT_MONTHS = np.array(forecast)[:,np.newaxis] * np.ones(( sum_cat_month.shape[0] , next_months ))
    NEXT_MONTHS_df = pd.DataFrame( NEXT_MONTHS , columns = next_month_lst , index = sum_cat_month.index  )
    sum_cat_month = pd.concat( [ sum_cat_month , NEXT_MONTHS_df ] , axis=1 )
    
    
    # row sum per month
    sum_cat_month = pd.concat([ sum_cat_month , sum_cat_month.sum().rename(clm['sum']).to_frame().T ])   # after sorting
    
    
    sum_cat_month[clm['mean_month']][clm['sum']] = forecast.sum()
    sum_cat_month[clm['mean_trsct']][clm['sum']] = np.nan
    
    sum_cat_month = sum_cat_month.round()
    
    return sum_cat_month