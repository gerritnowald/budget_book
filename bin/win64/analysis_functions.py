# -*- coding: utf-8 -*-
"""
@author: Gerrit Nowald
"""

import pandas as pd
import numpy as np

# -----------------------------------------------------------------------------
# table operations

def get_sum_cat_month(transactions, clm):
    """creates a table of spendings per month and category"""

    # group by month and category
    sum_cat_month = ( transactions
                        .groupby(clm['category'])
                        .resample('1ME', on=clm['date'])
                        .sum(numeric_only=True)[clm['amount']]
                        .unstack(0) )
    
    # prettier index
    sum_cat_month.index = sum_cat_month.index.map(lambda date : str(date)[:7])

    sum_cat_month = sum_cat_month.transpose()

    # split categories
    sum_cat_month[ [ clm['category'] , clm['cat_fine'] ] ] = sum_cat_month.index.to_series().str.split('/', expand=True)
    sum_cat_month[clm['cat_fine']] = sum_cat_month[clm['cat_fine']].replace(np.nan, '')
    sum_cat_month = sum_cat_month.set_index([ clm['category'] , clm['cat_fine'] ])
    

    # column sum per category
    sum_cat_month[clm['sum']] = sum_cat_month.sum(axis=1)

    # column mean/month (excluding current month)
    sum_cat_month[clm['mean_month']] = sum_cat_month.iloc[:,:-2].sum(axis=1)  / ( sum_cat_month.shape[1] - 2 )

    
    # sum_cat_month = sum_cat_month.sort_index()  # by category
    # sum_cat_month = sum_cat_month.sort_values(clm['sum'], ascending=False)  # by sum
    
    
    # row expenses (sum of negatives)
    expenses = pd.DataFrame( [sum_cat_month[sum_cat_month < 0].sum()] , 
            columns = sum_cat_month.columns , index = [(clm['expenses'], '')] )
    
    # row balance per month
    balance = pd.DataFrame( [sum_cat_month.sum()] , 
            columns = sum_cat_month.columns , index = [(clm['sum'], '')] )

    sum_cat_month = pd.concat([ sum_cat_month, expenses, balance ])


    sum_cat_month.index = sum_cat_month.index.rename([clm['category'],clm['cat_fine']])
    
    return sum_cat_month.round().replace(0, np.nan)



def df_plots(sum_cat_month, clm):
    """reformats the table for plotting"""
    df_plot_fine = sum_cat_month.T.drop([ clm['sum'], clm['mean_month'] ])

    df_plot_rough = df_plot_fine.T.drop([ clm['expenses'], clm['sum'] ], level=0)
    df_plot_rough = df_plot_rough.groupby(clm['category']).sum().T

    df_sunburst = sum_cat_month[[clm['sum']]].drop([ clm['expenses'], clm['sum'] ], level=0).reset_index()
    df_sunburst = df_sunburst[ df_sunburst[clm['sum']] < 0]
    df_sunburst[clm['sum']] = df_sunburst[clm['sum']].abs()

    return df_plot_fine, df_plot_rough, df_sunburst