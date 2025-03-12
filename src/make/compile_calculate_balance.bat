call pyinstaller --noconfirm --onefile ^
    --version-file version_info_calculate_balance.txt ^
    --distpath ../../bin/win64/ ^
    ../calculate_balance.py

pause