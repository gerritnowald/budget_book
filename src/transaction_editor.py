"""
Console user interface to browse & modify transactions:
- change category
- split transaction """

import curses

import pandas as pd
import numpy as np

import argparse
import yaml
from joblib import load
import re
import os


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

    # classifier pipeline
    Nsuggest = 3    # number of category suggestions
    try:
        classifier = load(cfg['categorizer file'] + '.joblib')
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
    
    # row & column settings: x = characters, y = lines
    y_max, x_max = stdscr.getmaxyx()
    y_header     = 8
    y_entries    = y_max - y_header - 2
    x_category   = 20
    x_float      = 9
    x_text       = x_max - x_category - 2*x_float - 19

    # -----------------------------------------------------------------------------------
    # Print header

    stdscr.addstr(0, 0, '———— categorize & split transactions '.ljust(x_max,'—'))
    stdscr.addstr(1, 0, ' UP / DOWN / LEFT / RIGHT to navigate')
    stdscr.addstr(2, 0, ' ESC to quit / abort')
    stdscr.addstr(3, 0, ' ENTER to categorize transaction / confirm')
    stdscr.addstr(4, 0, ' s to split  transaction')
    stdscr.addstr(5, 0, ' r to remove transaction')
    stdscr.addstr(6, 0, ' q to quit & save')
    stdscr.addstr(7, 0, ''.ljust(x_max,'—'))
    stdscr.addstr(7, x_text + 13, ' category ')
    stdscr.addstr(7, x_text + x_category + 13, ' conf ')
    stdscr.addstr(7, x_text + x_category + 20, ' amount ')
    stdscr.addstr(7, x_text + x_category + x_float + 19, ' balance ')
    stdscr.addstr(y_max - 2, 0, ''.ljust(x_max,'—'))

    # -----------------------------------------------------------------------------------
    # main loop for transactions
    
    # initialization
    last_row     = df.shape[0] - 1      # last row index
    current_row  = last_row - args.row  # highlighted row
    top_row      = min( max( current_row , 0) , last_row + 1 - y_entries )  # first printed row
    
    max_edit_row = last_row  # highest row that was edited
    lines_added  = 0         # sums up added lines due to splits and removed lines due to deletions
    
    change = False   # only save if data changed
    offset = 0       # horizontal offset for text scrolling
    
    while True:

        # -----------------------------------------------------------------------------------
        # Print DataFrame rows

        for i, (_, row) in enumerate(df.iloc[top_row : top_row + y_entries].iterrows()):
            # description text
            text = row[clm['text']]
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

            try:
                confidence = int(row['confidence'])
            except ValueError:
                confidence = 'n/a'

            stdscr.addstr(i+y_header, 1, f"{row[clm['date']]}  {text} {category} {confidence:>3} {row[clm['amount']]:8.2f} {row[clm['balance']]:8.2f}", attr)

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
                top_row -= 1    # scroll up

        elif key == curses.KEY_DOWN:
            offset = 0
            current_row = min(last_row, current_row + 1)
            if current_row - top_row > y_entries - 1:
                top_row += 1    # scroll down

        # -----------------------------------------------------------------------------------
        # split transaction

        elif key == 115:  # ASCII value of s key

            # input new amount
            offset = 0
            curses.echo()
            stdscr.addstr(y_entries + y_header + 1, 1, "Enter new amount: ")
            stdscr.refresh()
            new_amount = float(stdscr.getstr().decode())
            stdscr.addstr(y_entries + y_header + 1, 1, "".ljust(25))    # clear line
            curses.noecho()

            # insert new row
            if abs(new_amount) < abs(df[clm['amount']].iloc[current_row]):

                # update amounts & calculate balance
                df = pd.concat([
                    df.iloc[:current_row], 
                    df.iloc[[current_row]], 
                    df.iloc[current_row:]]).reset_index(drop=True)
                df.loc[current_row + 1, clm['amount'] ]  = new_amount
                df.loc[current_row    , clm['amount'] ] -= new_amount
                df.loc[current_row    , clm['balance']] -= new_amount

                df.loc[current_row:, clm['amount'] ]  = df.loc[current_row:, clm['amount'] ].round(2)
                df.loc[current_row:, clm['balance']]  = df.loc[current_row:, clm['balance']].round(2)

                # update view
                if current_row == last_row: # last row highlighted
                    top_row += 1    # scroll down
                last_row += 1

                # mark change
                change = True
                max_edit_row = min(max_edit_row, current_row)
                lines_added += 1

        # -----------------------------------------------------------------------------------
        # remove transaction

        elif key == 114:  # ASCII value of r key

            # calculate balance
            df.loc[current_row:, clm['balance']] -= df.loc[current_row , clm['amount' ]]
            df.loc[current_row:, clm['balance']]  = df.loc[current_row:, clm['balance']].round(2)

            # remove row
            df = df.drop(current_row).reset_index(drop=True)

            # update view
            if top_row + y_entries > last_row:  # list already scrolled down    
                top_row -= 1    # scroll up
            if current_row == last_row: # last row highlighted
                current_row -= 1
            last_row -= 1

            # mark change
            change = True
            max_edit_row = min(max_edit_row, current_row - 1)
            lines_added -= 1
        
        # -----------------------------------------------------------------------------------
        # categorize transaction

        elif key == 10:  # ASCII value of Enter key
            offset = 0
            if suggestions:
                # classification
                prob = classifier.predict_proba(df.loc[current_row:current_row])
                categories  = list(classifier.classes_[np.argsort(-prob[0])[:Nsuggest]])
                categories += [category for category in classifier.classes_ if category not in categories]
            
            # sub loop for categories
            ind = 0
            while True:
                # print current category
                category_str = categories[ind].ljust(x_category)[:x_category]
                stdscr.addstr(current_row - top_row + y_header, x_text + 14, category_str)
                
                # Wait for user input
                key = stdscr.getch()

                # navigate sub loop
                if key == curses.KEY_UP:
                    ind = (ind - 1) % len(categories)
                elif key == curses.KEY_DOWN:
                    ind = (ind + 1) % len(categories)
                                
                # save category
                elif key == 10:  # ASCII value of Enter key
                    df.loc[current_row, clm['category']] = categories[ind]
                    df.loc[current_row, 'confidence']    = np.nan

                    # mark change
                    change = True
                    max_edit_row = min(max_edit_row, current_row)

                    break

                # return without saving
                elif key == 27:  # ASCII value of Escape key
                    break
        
        # -----------------------------------------------------------------------------------
        # quit & save

        elif key == 113:  # ASCII value of q key
            if change:  # save database
                
                # byte-wise remove last lines from file
                lines_to_remove = last_row - max_edit_row + 1 - lines_added  # added & removed lines are not in file yet
                with open(cfg['CSV filenames']['database'] + '.csv', "rb+") as f:
                    f.seek(0, os.SEEK_END)
                    size = f.tell()

                    f.seek(max(0, size - 4096)) # read last 4KB
                    tail = f.read().splitlines()

                    bytes_to_remove = sum(len(line) + 2 for line in tail[-lines_to_remove:])
                    f.truncate(size - bytes_to_remove)

                # append changed transactions
                transactions_changed = df.iloc[max_edit_row:].copy()
                transactions_changed = transactions_changed.astype(str).replace(to_replace = r"\.0+$", value = "", regex = True)     # remove trailing zeros
                transactions_changed.to_csv(cfg['CSV filenames']['database'] + '.csv', mode='a', header=False, index=False, encoding = "ISO-8859-1")

            break
        
        # quit without save
        elif key == 27:  # ASCII value of Escape key
            break


curses.wrapper(main)