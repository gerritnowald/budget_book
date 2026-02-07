"""
Import new transactions into the database, either from csv or via API (comdirect bank).
Use Machine Learning model to categorize new transactions.
The account balance is also updated."""

import pandas as pd
import yaml

# -----------------------------------------------------------------------------------
# read settings from config file

with open("config.ini", "r") as ymlfile:
    cfg = yaml.safe_load(ymlfile)

clm  = cfg['column names database']
wait = cfg['tan time']

# -----------------------------------------------------------------------------------
# transaction import via CSV
# 'test_import_transactions.ipynb' can be used to develop & test

def transactions_CSV(clm,cfg):

    transactions_new = pd.read_csv( cfg['CSV filenames']['bank export'] + '.csv', encoding = 'ISO-8859-1', sep =';', decimal=',', thousands='.', header=3 )

    transactions_new = transactions_new.dropna(how='all', axis=1)   # removes all empty columns

    transactions_new = transactions_new.drop(['Buchungstag' , ], axis=1)   # insert list of column-names to remove

    transactions_new = transactions_new.rename({
        'Wertstellung (Valuta)' : clm['date']   ,
        'Umsatz in EUR'         : clm['amount'] ,
        'Vorgang'               : clm['type']   ,
        'Buchungstext'          : clm['text']   ,
        } , axis=1)

    transactions_new[clm['date']] = pd.to_datetime( transactions_new[clm['date']] , format='%d.%m.%Y', errors='coerce' )

    transactions_new = transactions_new.dropna(how='any', axis=0)   # removes rows with empty entries

    return transactions_new

# -----------------------------------------------------------------------------
# transaction import via comdirect API
# adapted from https://github.com/phpanhey/comdirect_financialreport

import requests
import uuid
import json
import datetime
import time
import re


def timestamp():
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%d%H%M%S%f")


def callback_tan_push():
    print(f'{wait} seconds to confirm push tan')
    time.sleep(wait)


def authenticate_api():
    # oauth procedure copied from https://github.com/keisentraut/python-comdirect-api
    config = json.loads(open("config_comdirectAPI.json", "r").read())

    # POST /oauth/token
    response = requests.post(
        "https://api.comdirect.de/oauth/token",
        f"client_id={config['client_id']}&"
        f"client_secret={config['client_secret']}&"
        f"username={config['username']}&"
        f"password={config['password']}&"
        f"grant_type=password",
        allow_redirects=False,
        headers={
            "Accept"       : "application/json",
            "Content-Type" : "application/x-www-form-urlencoded",
        },
    )
    if not response.status_code == 200:
        raise RuntimeError(
            f"POST https://api.comdirect.de/oauth/token returned status {response.status_code}"
        )
    tmp = response.json()
    access_token  = tmp["access_token"]
    refresh_token = tmp["refresh_token"]

    # GET /session/clients/user/v1/sessions
    session_id = uuid.uuid4()
    response   = requests.get(
        "https://api.comdirect.de/api/session/clients/user/v1/sessions",
        allow_redirects = False,
        headers = {
            "Accept": "application/json",
            "Authorization": f"Bearer {access_token}",
            "x-http-request-info": f'{{"clientRequestId":{{"sessionId":"{session_id}",'
            f'"requestId":"{timestamp()}"}}}}',
        },
    )
    if not response.status_code == 200:
        raise RuntimeError(
            f"GET https://api.comdirect.de/api/session/clients/user/v1/sessions"
            f"returned status {response.status_code}"
        )
    tmp = response.json()
    session_id = tmp[0]["identifier"]

    # POST /session/clients/user/v1/sessions/{sessionId}/validate
    response = requests.post(
        f"https://api.comdirect.de/api/session/clients/user/v1/sessions/{session_id}/validate",
        allow_redirects=False,
        headers={
            "Accept": "application/json",
            "Authorization": f"Bearer {access_token}",
            "x-http-request-info": f'{{"clientRequestId":{{"sessionId":"{session_id}",'
            f'"requestId":"{timestamp()}"}}}}',
            "Content-Type": "application/json",
        },
        data=f'{{"identifier":"{session_id}","sessionTanActive":true,"activated2FA":true}}',
    )
    if response.status_code != 201:
        raise RuntimeError(
            f"POST /session/clients/user/v1/sessions/.../validate returned status code {response.status_code}"
        )
    tmp = json.loads(response.headers["x-once-authentication-info"])
    challenge_id = tmp["id"]
    tan = callback_tan_push()

    # PATCH /session/clients/user/v1/sessions/{sessionId}
    response = requests.patch(
        f"https://api.comdirect.de/api/session/clients/user/v1/sessions/{session_id}",
        allow_redirects=False,
        headers={
            "Accept": "application/json",
            "Authorization": f"Bearer {access_token}",
            "x-http-request-info": f'{{"clientRequestId":{{"sessionId":"{session_id}",'
            f'"requestId":"{timestamp()}"}}}}',
            "Content-Type": "application/json",
            "x-once-authentication-info": f'{{"id":"{challenge_id}"}}',
            "x-once-authentication": tan,
        },
        data=f'{{"identifier":"{session_id}","sessionTanActive":true,"activated2FA":true}}',
    )
    tmp = response.json()
    if not response.status_code == 200:
        raise RuntimeError(
            f"PATCH https://api.comdirect.de/session/clients/user/v1/sessions/...:"
            f"returned status {response.status_code}"
        )
    session_id = tmp["identifier"]

    # POST https://api.comdirect.de/oauth/token
    response = requests.post(
        "https://api.comdirect.de/oauth/token",
        allow_redirects=False,
        headers={
            "Accept": "application/json",
            "Content-Type": "application/x-www-form-urlencoded",
        },
        data=f"client_id={config['client_id']}&client_secret={config['client_secret']}&"
        f"grant_type=cd_secondary&token={access_token}",
    )
    if not response.status_code == 200:
        raise RuntimeError(
            f"POST https://api.comdirect.de/oauth/token returned status {response.status_code}"
        )
    tmp = response.json()
    access_token  = tmp["access_token"]
    refresh_token = tmp["refresh_token"]
    account_id = get_accountId({"access_token" : access_token,
                                "session_id"   : session_id   })
    return {
        "access_token"  : access_token,
        "session_id"    : session_id,
        "refresh_token" : refresh_token,
        "account_id"    : account_id,
    }


def get_authorized(access_credentials, url, extraheaders={}):
    access_token = access_credentials["access_token"]
    session_id   = access_credentials["session_id"]
    headers = {
        "Accept": "application/json",
        "Authorization": f"Bearer {access_token}",
        "x-http-request-info": f'{{"clientRequestId":{{"sessionId":"{session_id}",'
        f'"requestId":"{timestamp()}"}}}}',
    }
    headers.update(extraheaders)
    response = requests.get(url, allow_redirects=False, headers=headers)
    if response.status_code != 200:
        raise RuntimeError(f"{url} returned HTTP status {response.status_code}")
    return response


def get_accountId(access_credentials):
    results = get_authorized(
        access_credentials,
        f"https://api.comdirect.de/api/banking/clients/user/v1/accounts/balances",
    )
    accounts = results.json()["values"]
    for account in accounts:
        if account["account"]["accountType"]["text"] == "Girokonto":
            return account["account"]["accountId"]


def get_transactions(access_credentials, startDate):
    account_id = access_credentials["account_id"]
    end_date   = datetime.datetime.now(datetime.timezone.utc).date()
    start_date = (startDate - datetime.timedelta(days=5)).date()   # to capture possible delayed transactions

    res = []
    i = 0
    for day in ( start_date + datetime.timedelta(n) for n in range((end_date - start_date).days + 1) ):
        res.append( get_authorized( access_credentials,
            f"https://api.comdirect.de/api/banking/v1/accounts/{account_id}/transactions?min-bookingDate={day}&max-bookingDate={day}&transactionState=BOOKED",
            ).json()["values"] )   # loop necessary, since setting different min & max booking dates does not reliably fetch all transactions in this period
        print(f'fetching transactions: {i+1}/{(end_date - start_date).days + 1} days processed', end='\r')
        i += 1
        time.sleep(0.5)   # to avoid too many requests in short time
    
    return [item for sublist in res for item in sublist]


def convert2dataframe(transactions, clm):
    df = []
    for transaction in transactions:
        text = ''
        if transaction['remitter'] is not None:
            text += transaction['remitter']['holderName'] + ' ' 
        if transaction['creditor'] is not None:
            text += transaction['creditor']['holderName'] + ' '
        text += transaction['remittanceInfo']
        text.replace(',', '.')  # avoid conflicts with csv reading
        text = re.sub(r'\s+', ' ', text)    # Replace multiple spaces

        df.append([ transaction['valutaDate'], transaction['transactionType']['text'], text, transaction["amount"]["value"] ])
    
    df = pd.DataFrame(df, columns=[clm['date'], clm['type'], clm['text'], clm['amount']])

    df[clm['date']]   = pd.to_datetime( df[clm['date']] , format='%Y-%m-%d', errors='coerce' )
    df[clm['amount']] = df[clm['amount']].astype(float)

    df = df.sort_values(by=[clm['date']], ascending=False)
    return df


def transactions_API_comdirect(clm, startDate):
    access_credentials = authenticate_api()
    print('login successful')
    transactions = get_transactions(access_credentials, startDate)
    df = convert2dataframe(transactions, clm)
    return df


# -----------------------------------------------------------------------------------
# transaction importer

from joblib import load
import sys
import os

import numpy as np

def main():

    # -----------------------------------------------------------------------------------
    # transaction database

    # database
    transactions = pd.read_csv( cfg['CSV filenames']['database'] + '.csv', encoding = 'ISO-8859-1', 
        parse_dates=[clm['date']], date_format=cfg['date format'] )
    print('finished loading transaction database')
    
    # -----------------------------------------------------------------------------------
    # download new transactions

    print('start download new transactions')

    transactions_new = transactions_API_comdirect(clm, startDate = max(transactions[clm["date"]]))
    
    # transactions_new = transactions_CSV(clm,cfg)
    
    print('finished download new transactions')

    # -----------------------------------------------------------------------------------
    # prepare merge

    # removing overlap
    transactions_new = transactions.merge(transactions_new, on=[clm['date'], clm['text']], how='right', suffixes=('_x', None), indicator=True )
    transactions_new = transactions_new.query('_merge == "right_only"').drop(['_merge'], axis=1)    # keep only new transactions, drop indicator column
    transactions_new = transactions_new.drop(columns=[col for col in transactions_new.columns if col.endswith('_x')])

    if len(transactions_new) == 0:
        print('no new transactions since last download!')
        return  # end function

    # sort to prevent negative balance due to same day transactions
    transactions_new.sort_values([clm['date'], clm['amount']], ascending = [True, False], inplace = True)

    # -----------------------------------------------------------------------------------
    # calculate balance

    final_balance = transactions[clm['balance']].iat[-1]
    transactions_new[clm['balance']] = transactions_new[clm['amount']].cumsum() + final_balance
    transactions_new[clm['balance']] = transactions_new[clm['balance']].round(2)

    # -----------------------------------------------------------------------------------
    # load classifier pipeline

    classifier = load(cfg['categorizer file'] + '.joblib')

    # -----------------------------------------------------------------------------------
    # classify new transactions

    prob = classifier.predict_proba(transactions_new)
    prob = np.round(prob * 100)
    maxindex = np.argmax(prob, axis=1)

    transactions_new[clm['category']] = classifier.classes_[maxindex]
    transactions_new['confidence']    = prob[np.arange(prob.shape[0]), maxindex]

    print('finished categorizing new transactions')

    # -----------------------------------------------------------------------------------
    # append to main dataset

    transactions_new = transactions_new[[clm['date'], clm['type'], clm['text'], clm['amount'], clm['category'], clm['balance'], 'confidence']]

    transactions_new[clm['date']] = transactions_new[clm['date']].dt.strftime(cfg['date format'])
    transactions_new = transactions_new.astype(str).replace(to_replace = r"\.0+$", value = "", regex = True)     # remove trailing zeros
    transactions_new.to_csv(cfg['CSV filenames']['database'] + '.csv', mode='a', header=False, index=False, encoding = "ISO-8859-1")

    print(f'new transactions appended to database')

    # -----------------------------------------------------------------------------------
    # open transaction editor

    print('start transaction editor')

    if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
        os.system(f"transaction_editor.exe -r {transactions_new.shape[0] - 1}")
    elif getattr(sys, 'frozen', True):
        os.system(f"python transaction_editor.py -r {transactions_new.shape[0] - 1}")

if __name__ == "__main__":
    main()