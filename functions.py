# -*- coding: utf-8 -*-
"""
@author: Gerrit Nowald
"""

import pandas as pd
import numpy as np
from dateutil import relativedelta

# -----------------------------------------------------------------------------
# table operations

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
    
    NEXT_MONTHS    = np.array(forecast)[:,np.newaxis] * np.ones(( sum_cat_month.shape[0] , next_months ))
    NEXT_MONTHS_df = pd.DataFrame( NEXT_MONTHS , columns = next_month_lst , index = sum_cat_month.index  )
    sum_cat_month  = pd.concat( [ sum_cat_month , NEXT_MONTHS_df ] , axis=1 )
    
    
    # row sum per month
    sum_cat_month = pd.concat([ sum_cat_month , sum_cat_month.sum().rename(clm['sum']).to_frame().T ])   # after sorting
    
    
    sum_cat_month[clm['mean_month']][clm['sum']] = forecast.sum()
    sum_cat_month[clm['mean_trsct']][clm['sum']] = np.nan
    
    sum_cat_month = sum_cat_month.round()
    
    return sum_cat_month

# -----------------------------------------------------------------------------
# text processing

def PreProcText(texts , minwordlength=3):
    """extracts individual words from transaction text
    input & output: pandas series"""
    texts = texts.str.lower()
    texts = texts.str.replace('ä','ae')
    texts = texts.str.replace('ö','oe')
    texts = texts.str.replace('ü','ue')
    texts = texts.str.replace('ß','ss')
    texts = texts.str.replace('[^a-z ]', ' ', regex=True)     # removes all non-alphabetical characters
    texts = texts.str.split()
    texts = texts.apply(lambda keywords: { word for word in keywords if len(word) >= minwordlength } )    # every word only once
    texts = texts.str.join(' ')
    return texts

# -----------------------------------------------------------------------------
# comdirect API transaction import
# adapted from https://github.com/phpanhey/comdirect_financialreport

import requests
import uuid
import json
import datetime
import time


def timestamp():
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%d%H%M%S%f")


def callback_tan_push():
    wait = 20
    print(f'{wait} seconds to confirm push tan')
    time.sleep(wait)


def authenticate_api():
    # oauth procedure copied from https://github.com/keisentraut/python-comdirect-api
    config = json.loads(open("config.json", "r").read())

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


def get_transactions(access_credentials, pastDays = 30):
    account_id = access_credentials["account_id"]
    end_date   = datetime.datetime.now(datetime.timezone.utc).date()
    start_date = end_date - datetime.timedelta(days=pastDays)

    res = []
    for day in ( start_date + datetime.timedelta(n) for n in range((end_date - start_date).days + 1) ):
        res.append( get_authorized( access_credentials,
            f"https://api.comdirect.de/api/banking/v1/accounts/{account_id}/transactions?min-bookingDate={day}&max-bookingDate={day}&transactionState=BOOKED",
            ).json()["values"] )   # loop necessary, since setting different min & max booking dates does not reliably fetch all transactions in this period
    
    return [item for sublist in res for item in sublist]


def convert2dataframe(transactions, clm):
    df = []
    for transaction in transactions:
        text = ''
        if transaction['remitter'] is not None:
            text += transaction['remitter']['holderName'] + ' ' 
        if transaction['creditor'] is not None:
            text += transaction['creditor']['holderName'] + ' '
        text += transaction['remittanceInfo'] + ' '

        df.append([ transaction['bookingDate'], transaction['transactionType']['text'], text, transaction["amount"]["value"] ])
    
    df = pd.DataFrame(df, columns=[clm['date'], clm['type'], clm['text'], clm['amount']])

    df[clm['date']]   = pd.to_datetime( df[clm['date']] , format='%Y-%m-%d', errors='coerce' )
    df[clm['amount']] = df[clm['amount']].astype(float)

    df = df.sort_values(by=[clm['date']], ascending=False)
    return df


def transactions_API_comdirect(clm, pastDays = 30):
    access_credentials = authenticate_api()
    transactions = get_transactions(access_credentials, pastDays)
    df = convert2dataframe(transactions, clm)
    return df

# -----------------------------------------------------------------------------
# csv transaction import

def transactions_csv(file, clm, header=2):
    df = pd.read_csv( file + '.csv', encoding = 'ISO-8859-1', sep =';', decimal=',', thousands='.', header=header )
    df = df.dropna(how='all', axis=1)
    df = df.drop(['Valuta'], axis=1)
    df = df.rename({'day'          : clm['date'],
                    'amount in EUR': clm['amount']}, axis=1)
    df[clm['date']] = pd.to_datetime( df[clm['date']] , format='%d.%m.%Y', errors='coerce' )
    df = df.dropna(how='any', axis=0)
    return df