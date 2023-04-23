# budget book
Analyzing spendings with Python &amp; Pandas,  
categorizing banking transactions with Machine Learning

![](https://github.com/gerritnowald/budget_book/tree/main/examples_blog/sunburst.png?raw=true)

A finance report is generated as a Jupyter notebook:  
https://github.com/gerritnowald/budget_book/blob/main/analysis.ipynb  
See also this blog post:  
https://gerritnowald.wordpress.com/2023/02/23/managing-spending-with-python-pandas/

## initial setup

Initially, transactions are exported from online banking as a csv file.  
These form the database.  
The minimal required columns are
- date
- description
- amount

The account balance over time has to calculated **once** using `calculate_balance.py` (the final balance has to be given).

For analysis, the transactions should be categorized.  
Two layers of categories can be used, separated with / (e.g. *living expenses/groceries*).  
In the beginning, this has to be done manually, e.g. using Excel.  
Later, Machine Learning is used to automatically categorize new transactions.

As an example for transactions, see  
https://github.com/gerritnowald/budget_book/blob/main/transactions.csv  
(without description text)

For the API import for the German *comdirect bank*, the user has to register (https://www.comdirect.de/cms/kontakt-zugaenge-api.html) and insert the credentials into `config.json`.

## how to use

New transactions are be appended to the database using `import_transactions.ipynb`.  
Those can also be imported from a csv file.  
Additionally, an API import is available for the German *comdirect bank*.

The transactions are categorized based on their description text using Machine Learning, see also this blog post:  
https://gerritnowald.wordpress.com/2023/04/05/categorize-banking-transactions-with-machine-learning/  
Since the accuracy of the categoriziation is not perfect, wrong categories should be corrected, e.g. using Excel.  
A list of all currently used categories is automatically saved as `categories.csv`.  

Also the balance over time is updated.

Then, the finance report can be updated by running `analysis.ipynb`.  
Reports for different time frames can be generated by filtering the database.  
It is recommended to export the notebook to e.g. save a yearly report for later reference.

Git can be used as backup.  
If an online repo is used, it is recommended to make it private and to exclude `config.json`.

## dependencies

- Pandas
- plotly (for sunburst diagram)

## contributions

Contributions are welcome, especially regarding additional import functions for different banks.

## Aknowledgements

thanks to Philipp Panhey for the comdirect API access:  
https://github.com/phpanhey/comdirect_financialreport  
