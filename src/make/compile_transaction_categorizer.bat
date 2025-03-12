call pyinstaller --noconfirm --onefile ^
    --version-file version_info_transaction_categorizer.txt ^
    --distpath ../../bin/win64/ ^
    ../transaction_categorizer.py

pause