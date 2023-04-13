# budget book
Managing spendings with Python &amp; Pandas

A finance report is generated as a Jupyter notebook:  
https://github.com/gerritnowald/budget_book/blob/main/analysis.ipynb  
See also this blog post:  
https://gerritnowald.wordpress.com/2023/02/23/managing-spending-with-python-pandas/

Transactions have to be exported from online banking as a csv file.

The account balance over time has to calculated once using *calculate_balance.py* (the final balance has to be given).

Two layers of categories can be used, separated with / (e.g. *living expenses/groceries*).  
A list of all categories which are currently used in the transactions file can be extracted using *get_categories.py*.

As an example for transactions, see  
https://github.com/gerritnowald/budget_book/blob/main/transactions.csv

New transactions can be appended to the database using *import_transactions.ipynb*.  
Also the balance over time is updated.  
New transactions are categorized based on the transaction text using Machine Learning.  
See also this blog post:  
https://gerritnowald.wordpress.com/2023/04/05/categorize-banking-transactions-with-machine-learning/
