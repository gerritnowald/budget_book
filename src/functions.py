# -*- coding: utf-8 -*-
"""
@author: Gerrit Nowald
"""

# -----------------------------------------------------------------------------
# table operations

def save_transactions_to_csv(transactions, clm, cfg):
    """date and number format are adjusted that they don't conflict #
    with saving the database using Excel."""
    try:
        transactions[clm['date']] = transactions[clm['date']].dt.strftime(cfg['date format'])
    except:
        pass
    transactions = transactions.astype(str)
    transactions = transactions.replace(to_replace = r"\.0+$", value = "", regex = True)     # remove trailing zeros
    try:
        transactions[clm['type']] = transactions[clm['type']].replace(to_replace = "nan", value = "")
    except:
        pass
    transactions.to_csv(cfg['CSV filenames']['database'] + '.csv', encoding = "ISO-8859-1", index=0)
    print('finished saving transactions to database')

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