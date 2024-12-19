"""
Console user interface to browse & modify transactions:
- change category
- split transaction """

# pip install windows-curses
import curses

import pandas as pd
import numpy as np

import argparse
import yaml
from joblib import load
import re

import functions    # local functions in this repository


def main(stdscr):

    # -----------------------------------------------------------------------------------
    # argparse

    parser = argparse.ArgumentParser(description="modify transactions")
    parser.add_argument("-r", "--row", type=int, default=0, help="start line")
    args = parser.parse_args()

    # -----------------------------------------------------------------------------------
    # load 

    # config file
    with open("config.ini", "r") as ymlfile:
        cfg = yaml.safe_load(ymlfile)
    clm = cfg['column names database']

    # database
    df = pd.read_csv(cfg['CSV filenames']['database']  + '.csv', encoding = "ISO-8859-1")

    # classifier
    Nsuggest = 3    # number of category suggestions
    try:
        vectorizer, classifier = load(cfg['categorizer file'] + '.joblib')
        suggestions = True
    except:
        with open(cfg['CSV filenames']['categories']  + '.csv', 'r') as file:
            categories = file.read().split('\n')[:-1]
        suggestions = False
    
    # -----------------------------------------------------------------------------------
    # settings
    
    # print settings
    curses.curs_set(0)  # Hide the cursor
    curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_WHITE)  # Define color pair
    
    # row & column settings
    y_max, x_max = stdscr.getmaxyx()
    y_header     = 7
    y_entries    = y_max - y_header - 2
    x_category   = 20
    x_float      = 9
    x_text       = x_max - x_category - 2*x_float - 18

    # -----------------------------------------------------------------------------------
    # Print header

    stdscr.addstr(0, 0, '———— categorize & split transactions '.ljust(x_max,'—'))
    stdscr.addstr(1, 0, ' UP / DOWN to navigate')
    stdscr.addstr(2, 0, ' ESC to quit / abort')
    stdscr.addstr(3, 0, ' ENTER to categorize transaction / confirm')
    stdscr.addstr(4, 0, ' s to split transaction')
    stdscr.addstr(5, 0, ' q to quit & save')
    stdscr.addstr(6, 0, ''.ljust(x_max,'—'))
    stdscr.addstr(6, x_text + 14, ' category ')
    stdscr.addstr(6, x_text + x_category + 18, ' amount ')
    stdscr.addstr(6, x_text + x_category + x_float + 18, ' balance ')
    stdscr.addstr(y_max - 2, 0, ''.ljust(x_max,'—'))

    # -----------------------------------------------------------------------------------
    # main loop for transactions
    
    # initialization
    current_row = args.row
    top_row     = max([current_row - y_entries + 1 , 0])
    change      = False   # only save if data changed
    offset      = 0
    
    while True:
        # Print DataFrame rows
        for i, (_, row) in enumerate(df.iloc[top_row : top_row + y_entries].iterrows()):
            # description text
            text = row[clm['text']]
            text = re.sub(r'\s+', ' ', text)    # Replace multiple spaces with a single space
            text = re.sub(r'\d+', '' , text)    # Remove all numbers
            if top_row + i == current_row:
                attr = curses.color_pair(1)
                max_offset = max([len(text) - x_text, 0])   # > 0
                text = text.ljust(x_text)[offset:x_text + offset]
            else:
                attr = curses.A_NORMAL
                text = text.ljust(x_text)[:x_text]
            
            # category
            try:
                category = row[clm['category']].ljust(x_category)[:x_category]
            except:
                category = ''.ljust(x_category)[:x_category]    # nan
            
            stdscr.addstr(i+y_header, 1, f"{row[clm['date']]}  {text}  {category} {- row[clm['amount']]:9.2f} {row[clm['balance']]:9.2f}", attr)
            
        stdscr.refresh()

        # Wait for user input
        key = stdscr.getch()

        # -----------------------------------------------------------------------------------
        # scroll left & right

        if key == curses.KEY_RIGHT:
            if offset < max_offset:
                offset += 1
        elif key == curses.KEY_LEFT:
            if offset > 0:
                offset -= 1

        # -----------------------------------------------------------------------------------
        # navigate main loop

        elif key == curses.KEY_UP:
            offset = 0
            current_row = max(0, current_row - 1)
            if current_row - top_row < 0:
                top_row -= 1
        elif key == curses.KEY_DOWN:
            offset = 0
            current_row = min(len(df) - 1, current_row + 1)
            if current_row - top_row > y_entries - 1:
                top_row += 1

        # -----------------------------------------------------------------------------------
        # split transaction

        elif key == 115:  # ASCII value of s key
            offset = 0
            curses.echo()
            stdscr.addstr(y_entries + y_header + 1, 1, "Enter new amount: ")
            stdscr.refresh()
            new_amount = float(stdscr.getstr().decode())
            stdscr.addstr(y_entries + y_header + 1, 1, "".ljust(25))    # clear line
            curses.noecho()

            # insert new row
            if new_amount < abs(df[clm['amount']].iloc[current_row]):
                change = True
                df = pd.concat([
                    df.iloc[:current_row], 
                    df.iloc[[current_row]], 
                    df.iloc[current_row:]]).reset_index(drop=True)
                df.loc[current_row    , clm['amount'] ]  = - new_amount
                df.loc[current_row + 1, clm['amount'] ] +=   new_amount
                df.loc[current_row + 1, clm['balance']] +=   new_amount
        
        # -----------------------------------------------------------------------------------
        # categorize transaction

        elif key == 10:  # ASCII value of Enter key
            offset = 0
            if suggestions:
                # text pre-processing
                keywords_new = functions.PreProcText(df.loc[current_row:current_row, clm['text']] , minwordlength=4)

                # feature extraction        
                X_new = vectorizer.transform(keywords_new).toarray()
                X_new = np.column_stack(( X_new , df.loc[current_row:current_row, clm['amount']].to_list() ))

                # classification
                prob = classifier.predict_proba(X_new)
                categories  = list(classifier.classes_[np.argsort(-prob[0])[:Nsuggest]])
                categories += [category for category in classifier.classes_ if category not in categories]
            
            # sub loop for categories
            ind = 0
            while True:
                # print current category
                category_str = categories[ind].ljust(x_category)[:x_category]
                stdscr.addstr(current_row - top_row + y_header, x_text + 15, category_str)
                
                # Wait for user input
                key = stdscr.getch()

                # navigate sub loop
                if key == curses.KEY_UP:
                    ind = (ind - 1) % len(categories)
                elif key == curses.KEY_DOWN:
                    ind = (ind + 1) % len(categories)
                                
                # save category
                elif key == 10:  # ASCII value of Enter key
                    change = True
                    df.loc[current_row, clm['category']] = categories[ind]
                    break

                # return without saving
                elif key == 27:  # ASCII value of Escape key
                    break
        
        # -----------------------------------------------------------------------------------
        # quit & save

        elif key == 113:  # ASCII value of q key
            if change:  # save database
                # date and number format are adjusted that they don't conflict with saving the database using Excel.
                df = df.astype(str)
                df = df.replace(to_replace = "\.0+$", value = "", regex = True)     # remove trailing zeros
                # df[clm['type']] = df[clm['type']].replace(to_replace = "nan", value = "", regex = True)
                df.to_csv(cfg['CSV filenames']['database'] + '.csv', encoding = "ISO-8859-1", index=0)
            break
        
        # quit without save
        elif key == 27:  # ASCII value of Escape key
            break


curses.wrapper(main)