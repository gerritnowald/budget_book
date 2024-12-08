import pandas as pd
import numpy as np

from sklearn.feature_extraction.text import CountVectorizer
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score

import os
import argparse
import yaml
import random
from joblib import dump
from datetime import datetime as dt

import functions


def main():

    # -----------------------------------------------------------------------------------
    # argparse
    
    parser = argparse.ArgumentParser(description="download & classify transactions")
    parser.add_argument("-t", "--test", action="store_true", help="Test classifier?")
    args = parser.parse_args()
    
    # -----------------------------------------------------------------------------------
    # read settings from config file

    with open("config.yml", "r") as ymlfile:
        cfg = yaml.safe_load(ymlfile)

    clm = cfg['column names database']

    # -----------------------------------------------------------------------------------
    # transaction database

    # database
    transactions = pd.read_csv( cfg['CSV filenames']['database']  + '.csv', encoding = 'ISO-8859-1' )
    transactions[clm['date']] = pd.to_datetime( transactions[clm['date']] , format = cfg['date format'] )
    print('finished loading transaction database')

    # filtering training data
    transactions_train = transactions[ ~transactions[clm['type']].isna() ]

    # -----------------------------------------------------------------------------------
    # train classifier

    # text pre-processing
    keywords_train = functions.PreProcText(transactions_train[clm['text']] , minwordlength=4)

    if args.test:
        # split data
        N = transactions_train.shape[0]
        ind_test  = random.sample(range(N), k=int(N*0.2))        # part of data for testing
        ind_train = [i for i in range(N) if i not in ind_test]   # remaining data
        transactions_test  = transactions_train.iloc[ind_test]
        transactions_train = transactions_train.iloc[ind_train]  # overwritten
        keywords_test  = keywords_train.iloc[ind_test]
        keywords_train = keywords_train.iloc[ind_train]          # overwritten

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

        return  # end function
    
    # -----------------------------------------------------------------------------------
    # download new transactions

    print('start download new transactions')
    transactions_new = functions.transactions_API_comdirect(clm, pastDays = 30)
    print('finished download new transactions')

    # -----------------------------------------------------------------------------------
    # prepare merge

    # filtering time
    max_date = max(transactions[clm["date"]])
    transactions_new = transactions_new[transactions_new[clm['date']] >= max_date]

    # removing overlap
    # transactions_new = transactions.merge(transactions_new, on=[clm['type'], clm['date'], clm['text'], clm['amount']], how='right', indicator=True )
    transactions_new = transactions.merge(transactions_new, on=[clm['date'], clm['text'], clm['amount']], how='right', indicator=True )
    transactions_new = transactions_new.query('_merge == "right_only"').drop(['_merge'], axis=1)

    if len(transactions_new) == 0:
        print('no new transactions since last download!')
        return  # end function

    # sort to prevent negative balance due to same day transactions
    transactions_new.sort_values([clm['date'], clm['amount']], ascending = [False, True], inplace = True)

    # -----------------------------------------------------------------------------------
    # classify new transactions

    # text pre-processing
    keywords_new = functions.PreProcText(transactions_new[clm['text']] , minwordlength=4)

    # feature extraction
    X_new = vectorizer.transform(keywords_new).toarray()
    X_new = np.column_stack(( X_new , transactions_new[clm['amount']].to_list() ))

    # classification
    transactions_new[clm['category']] = classifier.predict(X_new)
    print('finished categorizing new transactions')
    
    # -----------------------------------------------------------------------------------
    # calculate balance

    final_balance = transactions.loc[0, clm['balance']]
    transactions_new[clm['balance']] = transactions_new.loc[::-1, clm['amount']].cumsum()[::-1] + final_balance
    transactions_new[clm['balance']] = transactions_new[clm['balance']].round(2)

    # -----------------------------------------------------------------------------------
    # save

    # merge & save transactions
    transactions = pd.concat( [transactions_new, transactions] ).reset_index(drop=True)

    transactions[clm['date']] = transactions[clm['date']].dt.strftime(cfg['date format'])
    transactions = transactions.astype(str)
    transactions = transactions.replace(to_replace = "\.0+$", value = "", regex = True)     # remove trailing zeros
    # transactions[clm['type']] = transactions[clm['type']].replace(to_replace = "nan", value = "")
    transactions.to_csv(cfg['CSV filenames']['database'] + '.csv', encoding = "ISO-8859-1", index=0)
    print('finished saving transactions to database')

    # save classifier
    dump([vectorizer,classifier], cfg['categorizer file'] + '.joblib')

    # save categories
    transactionsLY = transactions[( transactions[clm['date']] >= dt(dt.today().year - 1 , dt.today().month , 1) )]
    categories = pd.DataFrame( transactionsLY[clm['category']].unique() ).sort_values(0)
    categories.to_csv( cfg['CSV filenames']['categories'] + '.csv', encoding = "ISO-8859-1", index=0, header=0 )

    # -----------------------------------------------------------------------------------
    # open transaction editor

    print('start transaction editor')
    os.system(f"python transaction_editor.py -r {len(transactions_new)}")



if __name__ == "__main__":
    main()