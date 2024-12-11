# -*- coding: utf-8 -*-
"""
@author: Gerrit Nowald
"""

import pandas as pd

import argparse
import yaml


def main():

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

    #------------------------------------------------------------------------------
    # calculate balance

    # sort to prevent negative balance due to same day transactions
    transactions.sort_values([clm['date'], clm['amount']], ascending = [False, True], inplace = True)

    transactions[clm['balance']] = transactions.loc[::-1, clm['amount']].cumsum()[::-1]
    transactions[clm['balance']] = transactions[clm['balance']] - transactions.loc[0,clm['balance']] + args.balance
    transactions[clm['balance']] = transactions[clm['balance']].round(2)

    #--------------------------------------------------------------------------
    # save
    # The date and number format are adjusted that they don't conflict with saving the database using Excel.

    transactions[clm['date']] = transactions[clm['date']].dt.strftime(cfg['date format'])
    transactions = transactions.astype(str)
    transactions = transactions.replace(to_replace = "\.0+$", value = "", regex = True)     # remove trailing zeros
    # transactions[clm['type']] = transactions[clm['type']].replace(to_replace = "nan", value = "", regex = True)
    transactions.to_csv(cfg['CSV filenames']['database'] + '.csv', encoding = "ISO-8859-1", index=0)


if __name__ == "__main__":
    main()