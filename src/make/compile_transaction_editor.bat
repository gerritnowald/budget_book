call pyinstaller --noconfirm --onefile ^
    --version-file version_info_transaction_editor.txt ^
    --distpath ../../bin/win64/ ^
    ../transaction_editor.py

pause