# introduction
Analyzing spendings with Python &amp; Pandas,  
categorizing banking transactions with Machine Learning

![](https://raw.githubusercontent.com/gerritnowald/budget_book/main/sunburst.webp)

Finance report example:  
https://github.com/gerritnowald/budget_book/blob/main/budget_book/analysis.ipynb  

# contents

- [disclaimer](#disclaimer)
- [initial setup](#initial-setup)
  * [transactions database](#transactions-database)
  * [account balance](#account-balance)
  * [categorization](#categorization)
  * [comdirect API](#comdirect-api)
- [how to use](#how-to-use)
  * [managing banking transactions](#managing-banking-transactions)
    + [import](#import)
    + [categorization](#categorization-1)
    + [console user interface](#console-user-interface)
  * [creating a spendings report](#creating-a-spendings-report)
  * [analyzing stock portfolio performance](#analyzing-stock-portfolio-performance)
  * [backup](#backup)
- [dependencies](#dependencies)
- [contributions](#contributions)
- [acknowledgements](#acknowledgements)

<small><i><a href='http://ecotrust-canada.github.io/markdown-toc/'>Table of contents generated with markdown-toc</a></i></small>


# disclaimer

I started this personal project as the German *comdirect bank* abolished their online budget planer *Finanzmanager*. It aims to reproduce this functionality while being as simple and understandable as possible. In principle this project is applicable to every bank, which allows to export transactions as csv files. For the *comdirect bank*, the API access can be used, which I adopted from Philipp Panhey ([acknowledgements](#acknowledgements)).  
I decided to publish this project, since I thought that it might be useful to others. However, this is not a professional and easy to use budget planer and requires some programming knowledge and adaptation to cater to your individual needs.


# initial setup

General settings such as file names & column names have to be set in `budget_book/config.ini`.

## transactions database

Initially, transactions (e.g. from the last year) are exported from online banking as a csv file.  
These form the database, stored locally on your hard drive.  
The minimal required columns are
- date
- amount
- description

As an example for transactions, see  
https://github.com/gerritnowald/budget_book/blob/main/budget_book/transactions.csv  
(only placeholder for description text)

## account balance

The account balance over time has to calculated **once** using
```
python calculate_balance.py FINAL_BALANCE
```

## categorization

The transactions have to be categorized for detailed analysis.  
Two layers of categories can be used, separated with / (e.g. *living expenses/groceries*).  
This has to be done manually in the beginning, e.g. using Excel.  
Later, Machine Learning is used to automatically categorize new transactions.

## comdirect API

For the API import for the German *comdirect bank*, the user has to [register](https://www.comdirect.de/cms/kontakt-zugaenge-api.html) and insert the credentials into `budget_book/config_comdirectAPI.json`.

[back to contents](#contents)


# how to use

## managing banking transactions

New transactions are merged to the database & categorized using three standalone scripts running in batch mode.  
They can be used independently or in sequence, the latter by calling `budget_book/Windows_start_transaction_importer.bat`.

### import

New transactions are appended to the database using
```
python transaction_importer.py
```
which is using the *comdirect bank* API.  
Also the balance over time is updated.  

Alternatively, they can also be read from an exported csv file.  
A code example is provided in `budget_book/test_import_transactions.ipynb`, which can be adapted in the interactive Jupyter environment.  
The final code can then be inserted into the function `def transactions_CSV()` in `budget_book/transaction_importer.py`.

### categorization

```
python transaction_categorizer.py 
```
categorizes the transactions based on their description text using Machine Learning, see also this blog post:  
https://gerritnowald.wordpress.com/2023/04/05/categorize-banking-transactions-with-machine-learning/  
A list of all currently used categories is automatically saved as `budget_book/categories.csv`.  

```
python transaction_categorizer.py -t
```
determines the model prediction accuracy.  

### console user interface

Since the accuracy of the categoriziation is not perfect, wrong categories should be corrected.  
For this, a console user interface is available, which can be run with
```
python transaction_editor.py
```
see also this blog post:  
https://gerritnowald.wordpress.com/2024/02/26/creating-a-command-line-interface-with-python/

It can also be used to split transactions, e.g. for cash withdrawal at the supermarket.

The console user interface is automatically run after `budget_book/transaction_categorizer.py`.  
The pre-selected line highlights the last previously appended transaction.

## spendings report

The spendings report can be updated by running `budget_book/analysis.ipynb`.  
Reports for different time frames can be generated by filtering the database.  
It is recommended to export the notebook (e.g. as html or pdf) regularly (e.g. yearly) for later reference.  
See also this blog post: https://gerritnowald.wordpress.com/2023/02/23/managing-spending-with-python-pandas/

## analyzing stock portfolio performance

Also, scripts to analyze stock portfolio performance are included.  
However, it is not very stable due to yahoo finance and a professional solution such as https://www.portfolio-performance.info/en/ is recommended.

As an example, see:  
https://github.com/gerritnowald/budget_book/blob/main/stocks/calculate_shares.ipynb  
See also this blog post:  
https://gerritnowald.wordpress.com/2024/07/14/tracking-stock-portfolio-value-over-time-with-yfinance-and-pandas/

First, a list of stocks has to be given in `stocks/get_stock_data.ipynb`. The stock short names can be found on https://finance.yahoo.com.  
The currency is retrieved for the given stocks and needs to be translated accordingly.

Then, `stocks/get_stock_transactions.ipynb` is used to extract the stock transactions from the database `budget_book/transactions.csv`.  
They are saved in `stocks/stock_transactions.csv`.  
The list of stock transactions `stocks/stock_transactions.csv` can also be provided directly, e.g. if no full list of transactions is available.

The aquired shares are calculated and the value over time is plotted in `stocks/calculate_shares.ipynb`.


## backup

Git can be used as backup.  
If an online repo is used, it is **strongly** recommended to make it private and to exclude `budget_book/config_comdirectAPI.json`.

[back to contents](#contents)


# dependencies

- Pandas
- plotly (for sunburst diagram)
- sklearn (for categorization)
- curses (for console user interface)
- yfinance (to retrieve stock data)

# contributions

Contributions are welcome, especially regarding APIs for additional banks.

# acknowledgements

thanks to Philipp Panhey for the comdirect API access:  
https://github.com/phpanhey/comdirect_financialreport  

[back to contents](#contents)
