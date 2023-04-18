# budget book
Managing spendings with Python &amp; Pandas, categorizing with Machine Learning

A finance report is generated as a Jupyter notebook:  
https://github.com/gerritnowald/budget_book/blob/main/analysis.ipynb  
See also this blog post:  
https://gerritnowald.wordpress.com/2023/02/23/managing-spending-with-python-pandas/

Transactions can be exported from online banking as a csv file.

Additionally, an API import is available for the German comdirect bank, thanks to Philipp Panhey:  
https://github.com/phpanhey/comdirect_financialreport  
The user has to register for the API (https://www.comdirect.de/cms/kontakt-zugaenge-api.html) and insert the credentials into `config.json`.

The account balance over time has to calculated **once** using `calculate_balance.py` (the final balance has to be given).

Two layers of categories can be used, separated with / (e.g. *living expenses/groceries*).  

As an example for transactions, see  
https://github.com/gerritnowald/budget_book/blob/main/transactions.csv

New transactions can be appended to the database using `import_transactions.ipynb`.  
They are categorized based on the description text using Machine Learning, see also this blog post:  
https://gerritnowald.wordpress.com/2023/04/05/categorize-banking-transactions-with-machine-learning/  
A list of all currently used categories is saved as `categories.csv`.  
Also the balance over time is updated.