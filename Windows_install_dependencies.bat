call python.exe -m pip install pandas

call python.exe -m pip install pyyaml

@REM analyse.ipynb
call python.exe -m pip install matplotlib

call python.exe -m pip install plotly
call python.exe -m pip install kaleido
call python.exe -m pip install nbformat

@REM transaction_importer.py
call python.exe -m pip install requests

@REM transaction_categorizer.py
call python.exe -m pip install scikit-learn

@REM transaction_editor.py
call python.exe -m pip install windows-curses

pause