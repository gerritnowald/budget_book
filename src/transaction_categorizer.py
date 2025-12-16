"""
Train Machine Learning model from description texts & categories of existing transactions.
Use model to categorize new transactions.
Optionally separate data to determine model prediction accuracy."""

import pandas as pd
import numpy as np

import sys
import os
import yaml
from joblib import load

import functions    # local functions in this repository

# -----------------------------------------------------------------------------------
# read settings from config file

with open("config.ini", "r") as ymlfile:
    cfg = yaml.safe_load(ymlfile)

clm = cfg['column names database']

# -----------------------------------------------------------------------------------
# transaction database

# load
transactions = pd.read_csv( cfg['CSV filenames']['database']  + '.csv', encoding = 'ISO-8859-1' )
print('finished loading transaction database')

# find transactions without categories
ind_uncategorized = transactions[transactions[clm['category']].isna()].index

if len(ind_uncategorized) == 0:
    print('no transactions to classify!')
    sys.exit()

# -----------------------------------------------------------------------------------
# load classifier pipeline

classifier = load(cfg['categorizer file'] + '.joblib')

# -----------------------------------------------------------------------------------
# classify new transactions

prob = classifier.predict_proba(transactions.loc[ind_uncategorized])
prob = np.round(prob * 100)
maxindex = np.argmax(prob, axis=1)

transactions.loc[ind_uncategorized, clm['category']] = classifier.classes_[maxindex]
transactions.loc[ind_uncategorized, 'confidence']    = prob[np.arange(prob.shape[0]), maxindex]

print('finished categorizing new transactions')

# -----------------------------------------------------------------------------------
# save transaction database

functions.save_transactions_to_csv(transactions, clm, cfg)

# -----------------------------------------------------------------------------------
# open transaction editor

print('start transaction editor')

if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
    os.system(f"transaction_editor.exe -r {len(ind_uncategorized)}")
elif getattr(sys, 'frozen', True):
    os.system(f"python transaction_editor.py -r {len(ind_uncategorized)}")