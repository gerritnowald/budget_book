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

import re
from itertools import combinations

from rapidfuzz import fuzz
from rapidfuzz.distance import Levenshtein

import numpy as np
import pandas as pd

from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.utils.validation import check_is_fitted

class CleanTexts(BaseEstimator, TransformerMixin):
    """replace umlauts, remove non-alphabetical characters,
       find word replacements based on similarity """
    def __init__(self, threshold = 85, max_edits = 1):  # no *args or **kwargs!
        self.threshold = threshold  # 0 - 100
        self.max_edits = max_edits  # int

    def Umlaut(self, str):
        """custom text preprocessor necessary for ß --> ss, ä --> ae"""
        str = str.lower()
        str = str.replace('ä','ae')
        str = str.replace('ö','oe')
        str = str.replace('ü','ue')
        str = str.replace('ß','ss')
        str = re.sub(r'[^a-z\s]+', ' ', str)
        return str

    def replace_words(self, text, mapping):
        tokens = text.split()
        new_tokens = [mapping.get(t, t) for t in tokens] # .get(t,t) returns mapping[t] if t is a key, else t
        return " ".join(new_tokens)

    def fit(self, X, y=None):  # y is required even though we don't use it
        vectorizer = CountVectorizer(
            preprocessor  = self.Umlaut,   # overwrites all build in preprocessing (strip_accents, lowercase)
            token_pattern = r"(?u)\b\w{4,}\b" )
        vectorizer.fit(X)
        vocabulary = vectorizer.get_feature_names_out()

        conversions = dict()
        for s1, s2 in combinations(vocabulary, 2):
            score = fuzz.ratio(s1, s2)
            distance = Levenshtein.distance(s1, s2)
            if distance <= self.max_edits and score >= self.threshold:
                if len(s2) > len(s1):
                    conversions[s1] = s2
                else:
                    conversions[s2] = s1

        # apply conversions iteratively to catch multi-step conversions
        for _ in range(2):
            for key, value in conversions.items():
                if value in conversions.keys():
                    conversions[key] = conversions[value]

        # replace words in vocabulary
        for i in range(len(vocabulary)):
            if vocabulary[i] in conversions:
                vocabulary[i] = conversions[vocabulary[i]]
        self.vocabulary_ = list(set(vocabulary))  # remove duplicates

        self.conversions_ = conversions
        self.n_features_in_ = X.shape[0]  # every estimator stores this in fit()
        return self  # always return self!

    def transform(self, X):
        check_is_fitted(self)  # looks for learned attributes (with trailing _)
        
        X = X.apply(self.Umlaut)
        X = X.apply(lambda x: self.replace_words(x, self.conversions_))
        return X
    

class CyclicalEncoder(BaseEstimator, TransformerMixin):
    """encode cyclical features using sine and cosine transformations"""
    def __init__(self, periods):
        self.periods = periods

    def fit(self, X, y=None):
        return self

    def transform(self, X):
        X_new = X.copy()
        for col, period in zip(X_new.columns, self.periods):
            angle = 2 * np.pi * X_new[col] / period
            X_new[col + "_sin"] = np.sin(angle)
            X_new[col + "_cos"] = np.cos(angle)
            X_new.drop(columns=[col], inplace=True)
        return X_new


class DayMonth(BaseEstimator, TransformerMixin):
    """extract day and month from date column"""
    def __init__(self, col, format):
        self.col = col
        self.format = format
        pass

    def fit(self, X, y=None):
        return self

    def transform(self, X):
        X = X.copy()
        X[self.col] = pd.to_datetime( X[self.col] , format = self.format )
        X['day']   = X[self.col].dt.day
        X['month'] = X[self.col].dt.month
        return X