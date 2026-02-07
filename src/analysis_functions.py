# -*- coding: utf-8 -*-
"""
@author: Gerrit Nowald
"""

import pandas as pd

def get_sum_cat_month(transactions, clm):
    """creates a table of spendings per month and category"""

    # group by month and category
    sum_cat_month = ( transactions
        .groupby([ clm['category'] ,
            pd.Grouper(key=clm['date'], freq='ME') ])[clm['amount']]
        .sum().unstack(level=0, fill_value=0).T )
    
    # prettier column titles
    sum_cat_month.columns = sum_cat_month.columns.strftime('%Y-%m')

    # split categories into a MultiIndex
    sum_cat_month[ [ clm['category'] , clm['cat_fine'] ] ] = sum_cat_month.index.to_series().str.split('/', expand=True).fillna('')
    sum_cat_month = sum_cat_month.set_index([ clm['category'] , clm['cat_fine'] ])
    

    # dataframes for plots
    df_sunburst = sum_cat_month.sum(axis=1)
    df_sunburst.name = clm['sum']
    df_sunburst = df_sunburst[ df_sunburst < 0].abs().reset_index()

    df_plot_rough = sum_cat_month.groupby(level=0).sum().T

    
    # additional rows
    balance = sum_cat_month.sum()
    sum_cat_month.loc[(clm['expenses'  ], ''), :] = sum_cat_month[sum_cat_month < 0].sum()
    sum_cat_month.loc[(clm['sum'       ], ''), :] = balance

    
    # dataframe for plots
    df_plot_fine = sum_cat_month.T


    # additional columns
    sum_cat_month[clm['sum']] = sum_cat_month.sum(axis=1)   # sum per category
    sum_cat_month[clm['mean_month']] = (sum_cat_month.iloc[:,:-2].sum(axis=1)  / 
            ( sum_cat_month.shape[1] - 2 )).round(2)  # mean/month (excluding current month)


    # sum_cat_month = sum_cat_month.sort_index()  # by category
    # sum_cat_month = sum_cat_month.sort_values(clm['sum'], ascending=False)  # by sum
        
    return sum_cat_month, df_plot_fine, df_plot_rough, df_sunburst