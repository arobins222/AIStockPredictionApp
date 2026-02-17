@echo off
SETLOCAL ENABLEDELAYEDEXPANSION
chcp 65001 >nul

:: ======================================================
:: AI Trading Terminal Launcher
:: (c) 2026 Drew Robinson
:: ======================================================
echo.
echo  ╔══════════════════════════════════════════╗
echo  ║      AI Trading Terminal Launcher        ║
echo  ║        (c) 2026 Drew Robinson            ║
echo  ╚══════════════════════════════════════════╝
echo.
pause
echo Starting launch process...
echo.

:: ======================================================
:: Log file setup
:: ======================================================
set "LOGFILE=app_out.log"
if exist "!LOGFILE!" del "!LOGFILE!"

:: ======================================================
:: Python check
:: ======================================================
python --version >nul 2>&1
IF ERRORLEVEL 1 (
    echo ERROR: Python not found! Install Python 3.10+ and add to PATH.
    pause
    exit /b
)

:: ======================================================
:: Required Python packages
:: ======================================================
set "PACKAGES=yfinance pandas matplotlib numpy tensorflow scikit-learn tkcalendar"
for %%P in (!PACKAGES!) do (
    python -c "import %%P" 2>nul
    IF ERRORLEVEL 1 (
        echo Installing %%P...
        pip install %%P --progress-bar off >> "!LOGFILE!" 2>&1
        IF ERRORLEVEL 1 (
            echo ERROR: Failed to install %%P! See !LOGFILE!
        ) ELSE (
            echo SUCCESS: %%P installed.
        )
    ) ELSE (
        echo %%P is already installed.
    )
)

:: ======================================================
:: Run Python app quietly (log only)
:: ======================================================
echo Launching AI Trading Terminal...
python -u AnimatedTradingTerminal.py > "!LOGFILE!" 2>&1

:: ======================================================
:: Show critical errors only
:: ======================================================
findstr /i "error exception fail trace" "!LOGFILE!" > temp_errors.log
IF %ERRORLEVEL% EQU 0 (
    echo CRITICAL ERRORS FOUND:
    type temp_errors.log
) ELSE (
    echo No critical errors found.
)
del temp_errors.log

:: ======================================================
:: Prompt to open full log
:: ======================================================
echo.
set /p OPENLOG=Do you want to open the full output log? (Y/N): 
if /I "!OPENLOG!"=="Y" (
    start notepad "!LOGFILE!"
)

echo Done. Exiting launcher...
pause
EXIT