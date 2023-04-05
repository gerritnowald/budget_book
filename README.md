# budget book
Managing spendings with Python &amp; Pandas

A finance report is generated as a Jupyter notebook:
https://github.com/gerritnowald/budget_book/blob/main/analysis.ipynb

Transactions have to be exported from online banking as a csv file.

After the first import, the balance over time is calculated using *calculate_balance.py*.
The final balance has to be given (only once).

Two layers of categories can be used, separated with /.
All categories which are currently used in the transactions file can be extracted using *get_categories.py*.

New transactions can be appended to the database using *import_transactions.py*.
Also the balance over time is updated.

New transactions are categorized based on the transaction text and old transactions using machine learning using *categorize_transactions_ML*.

As an example for transactions, see *transactions.csv*.

See also this blog post:
https://gerritnowald.wordpress.com/2023/02/23/managing-spending-with-python-pandas/
