# -*- coding: utf-8 -*-
"""
@author: Gerrit Nowald
"""

import pandas as pd

import argparse
import yaml

# -----------------------------------------------------------------------------------
# argparse

parser = argparse.ArgumentParser(description="update balance over time")
parser.add_argument("balance", type=float, help="final balance")
args = parser.parse_args()

#------------------------------------------------------------------------------
# read settings from config file

with open("config.ini", "r") as ymlfile:
    cfg = yaml.safe_load(ymlfile)

clm = cfg['column names database']

#------------------------------------------------------------------------------
# load data

transactions = pd.read_csv(cfg['CSV filenames']['database'] + '.csv', encoding = "ISO-8859-1")
transactions[clm['date']] = pd.to_datetime(transactions[clm['date']], format = cfg['date format'])

# ensure necessary columns exist
if clm['type'] not in transactions.columns:
    transactions[clm['type']] = ''
if clm['category'] not in transactions.columns:
    transactions[clm['category']] = ''
if clm['balance'] not in transactions.columns:
    transactions[clm['balance']] = ''
if 'confidence' not in transactions.columns:
    transactions['confidence'] = ''

#------------------------------------------------------------------------------
# calculate balance

# sort to prevent negative balance due to same day transactions
transactions.sort_values([clm['date'], clm['amount']], ascending = [True, False], inplace = True)

transactions[clm['balance']] = transactions[clm['amount']].cumsum()
transactions[clm['balance']] = transactions[clm['balance']] - transactions[clm['balance']].iat[-1] + args.balance
transactions[clm['balance']] = transactions[clm['balance']].round(2)

print('balance over time updated.')

#--------------------------------------------------------------------------
# save transaction database

# reorder columns
transactions = transactions[[clm['date'], clm['type'], clm['text'], clm['amount'], clm['category'], clm['balance'], 'confidence']]

transactions[clm['date']] = transactions[clm['date']].dt.strftime(cfg['date format'])
transactions = transactions.astype(str).replace(to_replace = r"\.0+$", value = "", regex = True)     # remove trailing zeros
transactions.to_csv(cfg['CSV filenames']['database'] + '.csv', encoding = "ISO-8859-1", index=0)