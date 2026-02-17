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
echo Press ENTER to start the launcher...
pause >nul
echo.

:: ======================================================
:: Log file setup
:: ======================================================
set "LOGFILE=app_out.log"
if exist "!LOGFILE!" del "!LOGFILE!"

:: ======================================================
:: Python check
:: ======================================================
echo Checking Python installation...
python --version >> "!LOGFILE!" 2>&1
IF ERRORLEVEL 1 (
    echo ERROR: Python not found!
    echo Install Python 3.10+ and ensure it is added to PATH.
    echo.
    echo Press ENTER to exit...
    pause >nul
    exit /b
) ELSE (
    python --version
    echo Python detected successfully.
)

:: ======================================================
:: Upgrade pip quietly (safe)
:: ======================================================
echo Upgrading pip...
python -m pip install --upgrade pip --quiet >> "!LOGFILE!" 2>&1

:: ======================================================
:: Required packages (pip_name import_name)
:: ======================================================
set PACKAGES=yfinance:yfinance pandas:pandas matplotlib:matplotlib numpy:numpy tensorflow:tensorflow scikit-learn:sklearn tkcalendar:tkcalendar

:: Count packages
set COUNT=0
for %%A in (%PACKAGES%) do set /a COUNT+=1
set TOTAL=!COUNT!
set INDEX=0

:: ======================================================
:: Check & Install Dependencies
:: ======================================================
for %%A in (%PACKAGES%) do (
    set /a INDEX+=1
    for /f "tokens=1,2 delims=:" %%B in ("%%A") do (
        set PIPPKG=%%B
        set IMPORTED=%%C
    )

    set /a PERCENT=INDEX*100/TOTAL
    echo ----------------------------------------
    echo Step !INDEX! of !TOTAL! - Checking !PIPPKG!... [!PERCENT!%%]

    python -c "import !IMPORTED!" 2>nul
    if errorlevel 1 (
        echo Installing !PIPPKG!... [!PERCENT!%%]
        python -m pip install !PIPPKG! --progress-bar off >> "!LOGFILE!" 2>&1
        if errorlevel 1 (
            echo ERROR: Failed to install !PIPPKG!. See !LOGFILE!
        ) else (
            echo SUCCESS: !PIPPKG! installed.
        )
    ) else (
        echo !PIPPKG! already installed. [!PERCENT!%%]
    )
)

:: ======================================================
:: Launch Application
:: ======================================================
echo ----------------------------------------
echo Launching AI Trading Terminal...
echo Output log: !LOGFILE!
echo ----------------------------------------

python -u AnimatedTradingTerminal.py >> "!LOGFILE!" 2>&1

:: ======================================================
:: Show Critical Errors Only
:: ======================================================
findstr /i "error exception fail trace" "!LOGFILE!" > temp_errors.log
IF %ERRORLEVEL% EQU 0 (
    echo.
    echo CRITICAL ERRORS FOUND:
    type temp_errors.log
) ELSE (
    echo No critical errors detected.
)
del temp_errors.log

:: ======================================================
:: Prompt to Open Log
:: ======================================================
echo.
set /p OPENLOG=Do you want to open the full output log? (Y/N): 
if /I "!OPENLOG!"=="Y" (
    start notepad "!LOGFILE!"
)

echo.
echo Launcher finished.
echo Press ENTER to exit...
pause >nul
EXIT