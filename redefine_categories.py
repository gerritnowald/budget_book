# -*- coding: utf-8 -*-
"""
@author: Gerrit Nowald
"""

import pandas as pd

#------------------------------------------------------------------------------
# load

transactions = pd.read_csv('transactions.csv', sep =';', decimal='.', encoding = 'ISO-8859-1')

categories   = pd.read_csv('category_replacement.csv', sep =';', index_col=0)

#------------------------------------------------------------------------------
# functions

def get_category(description, categories):
    """set category based on keyword in description"""
    for key in categories:
        if key in description:
            return categories.get(key)
    return None

#------------------------------------------------------------------------------
# categorize

mapping = categories.squeeze('columns').to_dict()

transactions['category'] = transactions['category'].apply(get_category, args=((mapping,)) )

#--------------------------------------------------------------------------
# save

# transactions.to_csv('transactions.csv', sep=';', decimal='.', encoding = 'ISO-8859-1', index=0)