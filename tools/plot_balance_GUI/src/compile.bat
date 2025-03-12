call pyinstaller --noconfirm --onefile ^
    --version-file version_info.txt ^
    --noconsole ^
    --distpath ../ ^
    plot_balance_GUI.py

pause