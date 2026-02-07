# -*- coding: utf-8 -*-
"""
@author: Gerrit Nowald
"""

import re
from itertools import combinations

from rapidfuzz import fuzz
from rapidfuzz.distance import Levenshtein

import numpy as np
import pandas as pd

from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.utils.validation import check_is_fitted


def get_sum_cat_month(transactions, clm):
    """creates a table of spendings per month and category"""

    # group by month and category
    sum_cat_month = ( transactions
        .groupby([ clm['category'] ,
            pd.Grouper(key=clm['date'], freq='ME') ])[clm['amount']]
        .sum().unstack(level=0, fill_value=0).T )
    
    # prettier column titles
    sum_cat_month.columns = sum_cat_month.columns.strftime('%Y-%m')

    # split categories into a MultiIndex
    sum_cat_month[ [ clm['category'] , clm['cat_fine'] ] ] = sum_cat_month.index.to_series().str.split('/', expand=True).fillna('')
    sum_cat_month = sum_cat_month.set_index([ clm['category'] , clm['cat_fine'] ])
    

    # dataframes for plots
    df_sunburst = sum_cat_month.sum(axis=1)
    df_sunburst.name = clm['sum']
    df_sunburst = df_sunburst[ df_sunburst < 0].abs().reset_index()

    df_plot_rough = sum_cat_month.groupby(level=0).sum().T

    
    # additional rows
    balance = sum_cat_month.sum()
    sum_cat_month.loc[(clm['expenses'  ], ''), :] = sum_cat_month[sum_cat_month < 0].sum()
    sum_cat_month.loc[(clm['sum'       ], ''), :] = balance

    
    # dataframe for plots
    df_plot_fine = sum_cat_month.T


    # additional columns
    sum_cat_month[clm['sum']] = sum_cat_month.sum(axis=1)   # sum per category
    sum_cat_month[clm['mean_month']] = (sum_cat_month.iloc[:,:-2].sum(axis=1)  / 
            ( sum_cat_month.shape[1] - 2 )).round(2)  # mean/month (excluding current month)


    # sum_cat_month = sum_cat_month.sort_index()  # by category
    # sum_cat_month = sum_cat_month.sort_values(clm['sum'], ascending=False)  # by sum
        
    return sum_cat_month, df_plot_fine, df_plot_rough, df_sunburst


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