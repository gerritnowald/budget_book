# -*- coding: utf-8 -*-
"""
@author: Gerrit Nowald
"""

import pandas as pd

#------------------------------------------------------------------------------
# load

transactions = pd.read_csv('transactions.csv', sep =";", encoding = "ISO-8859-1")

#------------------------------------------------------------------------------
# find unique categories

categories = pd.DataFrame( transactions['category'].unique() ).sort_values(0)

#------------------------------------------------------------------------------
# save

categories.to_csv('categories.csv', encoding = "ISO-8859-1", index=0, header=0)