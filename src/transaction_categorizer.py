"""
Train Machine Learning model from description texts & categories of existing transactions.
Use model to categorize new transactions.
Optionally separate data to determine model prediction accuracy."""

import pandas as pd
import numpy as np

# pip install -U scikit-learn
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score

import sys
import os
import argparse
import yaml
import random
from joblib import dump
from datetime import datetime as dt

import functions    # local functions in this repository


# -----------------------------------------------------------------------------------
# argparse

parser = argparse.ArgumentParser(description="categorize transactions")
parser.add_argument("-t", "--test", action="store_true", help="test categorizer")
args = parser.parse_args()

# -----------------------------------------------------------------------------------
# read settings from config file

with open("config.ini", "r") as ymlfile:
    cfg = yaml.safe_load(ymlfile)

clm = cfg['column names database']

# -----------------------------------------------------------------------------------
# transaction database

# load
transactions = pd.read_csv( cfg['CSV filenames']['database']  + '.csv', encoding = 'ISO-8859-1' )
transactions[clm['date']] = pd.to_datetime( transactions[clm['date']] , format = cfg['date format'] )
print('finished loading transaction database')

# filtering out training data without detailed description text (Finanzmanager export)
try:
    transactions_train = transactions[ ~transactions[clm['type']].isna() ]
except:
    transactions_train = transactions.copy()

# find transactions without categories
# transactions_train[clm['category']] = transactions_train[clm['category']].replace(to_replace = "", value = "nan")
ind_uncategorized = transactions_train[transactions_train[clm['category']].isna()].index

if len(ind_uncategorized) == 0 and not args.test:
    print('no transactions to classify!')
    sys.exit()

transactions_train = transactions_train.drop(index = ind_uncategorized)

# -----------------------------------------------------------------------------------
# train classifier

# text pre-processing
keywords_train = functions.PreProcText(transactions_train[clm['text']] , minwordlength=4)

if args.test:
    # split data
    indices = list(transactions_train.index)
    ind_test  = random.sample(indices, k=int(len(indices)*0.2)) # part of data for testing
    ind_train = [i for i in indices if i not in ind_test]       # remaining data

    transactions_test  = transactions_train.loc[ind_test ]
    transactions_train = transactions_train.loc[ind_train]  # overwritten
    keywords_test      =     keywords_train.loc[ind_test ]
    keywords_train     =     keywords_train.loc[ind_train]  # overwritten

# feature extraction
vectorizer = CountVectorizer(ngram_range=(1,1), max_features = 500)
y_train = transactions_train[clm['category']]
X_train = vectorizer.fit_transform(keywords_train).toarray()
X_train = np.column_stack(( X_train , transactions_train[clm['amount']].to_list() ))    # add amount

# model training
classifier = RandomForestClassifier(100)
classifier.fit(X_train, y_train)
print('finished training classifier')

# -----------------------------------------------------------------------------------
# test classifier

if args.test:
    # feature extraction
    y_test = transactions_test[clm['category']]
    X_test = vectorizer.transform(keywords_test).toarray()
    X_test = np.column_stack(( X_test , transactions_test[clm['amount']].to_list() ))   # add amount

    # classification
    y_pred = classifier.predict(X_test)

    # compare prediction & real data
    print(f'accuracy of prediction: {int(100*accuracy_score(y_test, y_pred))} %')

    sys.exit()

# -----------------------------------------------------------------------------------
# classify new transactions

# text pre-processing
keywords_new = functions.PreProcText(transactions.loc[ind_uncategorized, clm['text']] , minwordlength=4)

# feature extraction
X_new = vectorizer.transform(keywords_new).toarray()
X_new = np.column_stack(( X_new , transactions.loc[ind_uncategorized, clm['amount']].to_list() ))

# classification
transactions.loc[ind_uncategorized, clm['category']] = classifier.predict(X_new)
print('finished categorizing new transactions')

# -----------------------------------------------------------------------------------
# save

# save classifier
dump([vectorizer, classifier], cfg['categorizer file'] + '.joblib')

# save categories
transactionsLY = transactions[( transactions[clm['date']] >= dt(dt.today().year - 1 , dt.today().month , 1) )]
categories = pd.DataFrame( transactionsLY[clm['category']].unique() ).sort_values(0)
categories.to_csv( cfg['CSV filenames']['categories'] + '.csv', encoding = "ISO-8859-1", index=0, header=0 )

# save transaction database
functions.save_transactions_to_csv(transactions, clm, cfg)

# -----------------------------------------------------------------------------------
# open transaction editor

print('start transaction editor')

if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
    os.system(f"transaction_editor.exe -r {len(ind_uncategorized)}")
elif getattr(sys, 'frozen', True):
    os.system(f"python transaction_editor.py -r {len(ind_uncategorized)}")