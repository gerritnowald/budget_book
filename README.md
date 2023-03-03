# budget book
Managing spendings with Python &amp; Pandas

A finance report is generated as a Jupyter notebook:
https://github.com/gerritnowald/budget_book/blob/main/analysis.ipynb

Transactions have to be exported from online banking as a csv file.

After the first import, the balance over time is calculated using calculate_balance.py.
The final balance has to be given (only once).

Currently, categories have to be defined manually.
Two layers of categories can be used, separated with /.
All categories which are currently used in the transactions file can be extracted using get_categories.py.
All categories can be redefined at once using redefine_categories.py. A mapping of old to new categories has to be provided as a csv file (1st column old categories, 2nd column new categories).

New transactions can be appended to the database using import_transactions.py.
Also the balance over time is updated.
New transactions have to be categorized manually. For this, Excel can be used.

As an example for transactions, see transactions.csv.

See also this blog post:
https://gerritnowald.wordpress.com/2023/02/23/managing-spending-with-python-pandas/