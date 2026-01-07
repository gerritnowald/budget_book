# introduction

![](https://raw.githubusercontent.com/gerritnowald/budget_book/main/media/sunburst.webp)

Banking transactions are saved into a csv database and then analyzed for a given timeframe.

Two scripts are used to manage the banking transactions:
- `transaction_importer` downloads new transactions using the *comdirect bank* API and appends them to the database. They are categorized based on their description text using Machine Learning.
- `transaction_editor` is a console user interface to modify transactions, which is faster to use than Excel.  

The transactions are analyzed in a Jupyter notebook, see this example:  
https://github.com/gerritnowald/budget_book/blob/main/src/analysis.ipynb

# disclaimer

This is not a professional and easy to use budget planer and requires some programming knowledge and adaptation to cater to your individual needs.

# contents

- [initial setup](#initial-setup)
  * [transactions database](#transactions-database)
  * [account balance](#account-balance)
  * [categorization](#categorization)
  * [comdirect API](#comdirect-api)
- [how to use](#how-to-use)
  * [managing banking transactions](#managing-banking-transactions)
    + [import & categorization](#import---categorization)
    + [console user interface](#console-user-interface)
  * [spendings report](#spendings-report)
  * [analyzing stock portfolio performance](#analyzing-stock-portfolio-performance)
  * [backup](#backup)
- [dependencies](#dependencies)
- [contributions](#contributions)
- [history](#history)
- [acknowledgements](#acknowledgements)

<small><i><a href='http://ecotrust-canada.github.io/markdown-toc/'>Table of contents generated with markdown-toc</a></i></small>

# initial setup

General settings such as file names & column names have to be set in `config.ini`.

To compile the scripts for Windows, use the batch files in the folder `.\src\make\`.  
They are then placed in `.\bin\win64\`.  
This is optional, all scripts in the folder `.\src\` can be used as is.

## transactions database

Initially, transactions (e.g. from the last year) are exported from online banking as a csv file.  
These form the database, stored locally on your hard drive.  
The minimal required columns are
- date
- amount
- description

As an example for transactions, see  
https://github.com/gerritnowald/budget_book/blob/main/src/transactions.csv  
(only placeholder for description text)

## account balance

The account balance over time has to calculated **once** using
```
calculate_balance FINAL_BALANCE
```
For Windows, the batch script `start_calculate_balance.bat` can be used (the final balance has to be set in the file).

## categorization

The transactions have to be categorized for detailed analysis.  
Two layers of categories can be used, separated with / (e.g. *living expenses/groceries*).  
This has to be done manually in the beginning, e.g. using Excel.  
Later, Machine Learning is used to automatically categorize new transactions.

Use `categorizer_training.ipynb` to train a machine learning model on your transactions with your categories, see also this blog post:  
https://gerritnowald.wordpress.com/2025/12/16/revisiting-categorization-of-banking-transactions/  
A list of all currently used categories is automatically saved as `categories.csv`.  
My current model `categorizer.joblib` is also provided, but it will use my categories.

## comdirect API

For the API import for the German *comdirect bank*, the user has to [register](https://www.comdirect.de/cms/kontakt-zugaenge-api.html) and insert the credentials into `config_comdirectAPI.json`.

[back to contents](#contents)


# how to use

## managing banking transactions

New transactions are merged to the database & categorized using two standalone scripts running in batch mode.  
They can be used independently or in sequence, the latter by calling `start_transaction_importer.bat`.

### import & categorization

New transactions are appended to the database using
```
transaction_importer
```
which is using the *comdirect bank* API.  
New transactions are downloaded based on the last date in the database. Some overlap is considered and removed using a merge to make the import more robust.  
Also the balance over time is updated.  

Alternatively, they can also be read from an exported csv file.  
A code example is provided in `test_import_transactions.ipynb`, which can be adapted in the interactive Jupyter environment.  
The final code can then be inserted into the function `def transactions_CSV()` in `transaction_importer.py`.

The transactions are categorized based on their description text using Machine Learning, see also this blog post:  
https://gerritnowald.wordpress.com/2023/04/05/categorize-banking-transactions-with-machine-learning/  

### console user interface

Since the accuracy of the categoriziation is not perfect, wrong categories should be corrected.  
For this, a console user interface is available, which can be run with
```
transaction_editor
```
see also this blog post:  
https://gerritnowald.wordpress.com/2024/02/26/creating-a-command-line-interface-with-python/

It can also be used to split transactions, e.g. for cash withdrawal at the supermarket.

The console user interface is automatically run after `transaction_importer`.  
The pre-selected line highlights the last previously appended transaction.

## spendings report

The spendings report can be updated by running `analysis.ipynb`.  
Reports for different time frames can be generated by filtering the database.  
It is recommended to export the notebook (e.g. as html or pdf) regularly (e.g. yearly) for later reference.  
See also this blog post: https://gerritnowald.wordpress.com/2023/02/23/managing-spending-with-python-pandas/

## analyzing stock portfolio performance

Also, scripts to analyze stock portfolio performance are included.  
However, it is not very stable due to yahoo finance and a professional solution such as https://www.portfolio-performance.info/en/ is recommended.

As an example, see:  
https://github.com/gerritnowald/budget_book/blob/main/test_stocks/calculate_shares.ipynb  
See also this blog post:  
https://gerritnowald.wordpress.com/2024/07/14/tracking-stock-portfolio-value-over-time-with-yfinance-and-pandas/

First, a list of stocks has to be given in `stocks/get_stock_data.ipynb`. The stock short names can be found on https://finance.yahoo.com.  
The currency is retrieved for the given stocks and needs to be translated accordingly.

Then, `stocks/get_stock_transactions.ipynb` is used to extract the stock transactions from the database `transactions.csv`.  
They are saved in `stocks/stock_transactions.csv`.  
The list of stock transactions `stocks/stock_transactions.csv` can also be provided directly, e.g. if no full list of transactions is available.

The aquired shares are calculated and the value over time is plotted in `stocks/calculate_shares.ipynb`.


## backup

Git can be used as backup.  
If an online repo is used, it is **strongly** recommended to make it private and to exclude `config_comdirectAPI.json`.

[back to contents](#contents)


# dependencies

- Pandas
- plotly (for sunburst diagram)
- sklearn (for categorization)
- curses (for console user interface)
- yfinance (to retrieve stock data)

On Windows, use `src\install_dependencies.bat` to install the required packages.

# contributions

Contributions are welcome, especially regarding APIs for additional banks.

# history

I started this personal project as the German *comdirect bank* abolished their online budget planer *Finanzmanager*. It aims to reproduce this functionality while being as simple and understandable as possible. In principle this project is applicable to every bank, which allows to export transactions as csv files. I decided to publish this project, since I thought that it might be useful to others.

# acknowledgements

thanks to Philipp Panhey for the comdirect API access:  
https://github.com/phpanhey/comdirect_financialreport  

[back to contents](#contents)
