call pyinstaller --noconfirm --onefile ^
    --version-file version_info_transaction_importer.txt ^
    --distpath ../../bin/win64/ ^
    ../transaction_importer.py

pause