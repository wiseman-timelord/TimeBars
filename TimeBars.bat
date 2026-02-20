@echo off
setlocal EnableDelayedExpansion

:: Initialization
mode con cols=80 lines=25
powershell -noprofile -command "& { $w = $Host.UI.RawUI; $b = $w.BufferSize; $b.Height = 6000; $w.BufferSize = $b; }"
cd /d "%~dp0"
color 0F
title TimeBars

:: Main Menu
:menu
cls
echo =============================================================================
echo                   ^_^_^_^_^_ ^_                ^_^_^_^_
echo                  ^|^_   ^_^<^_^>^_^_^_^_^_^_^_^_   ^_^_^_^| ^_^_ ^>  ^_^_^_^_ ^_^_^_^_^_^_^_
echo                    ^| ^| ^| ^|  ^_   ^_ ^\ ^/ ^_ ^\  ^_ ^\ ^/ ^_  ^|  ^_^/ ^_^_^|
echo                    ^| ^| ^| ^| ^| ^| ^| ^| ^|  ^_^_^/ ^|^_^> ^| ^<^_^| ^| ^| ^\^_^_ ^\
echo                    ^|^_^| ^|^_^|^_^| ^|^_^| ^|^_^|^\^_^_^_^|^_^_^_^_^/ ^\^_^_^_^_^|^_^| ^|^_^_^_^/
echo.
echo =============================================================================
echo.
echo.
echo.
echo.
echo     1. Run Program
echo.
echo     2. Run Program (Debug)
echo.
echo     3. Run Installer
echo.
echo.
echo.
echo.
echo =============================================================================
set /p choice=Selection; Menu Options = 1-3, Exit Program = X: 

if "%choice%"=="1" goto runProgram
if "%choice%"=="2" goto runDebug
if "%choice%"=="3" goto runInstaller
if /i "%choice%"=="x" goto end
echo.
echo Invalid choice. Try again.
timeout /t 2 /nobreak >nul
goto menu

:: Run Program (Hidden/Normal Mode)
:runProgram
cls
echo =============================================================================
echo     TimeBars: Launching Program
echo =============================================================================
echo.

:: Check if venv exists (specifically pythonw for hidden mode)
if not exist ".\venv\Scripts\pythonw.exe" (
    echo ERROR: Virtual environment not found!
    echo Please run the installer first ^(Option 3^).
    echo.
    pause
    goto menu
)

:: Check if program.py exists
if not exist ".\program.py" (
    echo ERROR: program.py not found!
    echo.
    pause
    goto menu
)

echo Activating virtual environment...
call ".\venv\Scripts\activate.bat"

echo Starting TimeBars (Hidden Mode)...
echo.

:: FIX: Removed /WAIT to allow batch to close immediately
:: FIX: Used /b to run in background without new window
start "" /b ".\venv\Scripts\pythonw.exe" ".\program.py" 2>>".\Errors-Crash.Log"

:: Wait briefly to ensure launch initiates
timeout /t 2 /nobreak >nul

:: Exit batch script completely (does not return to menu)
:: exit /b ensures we don't close the parent CMD if launched from one
exit /b

:: Run Program with Debug (Visible Console)
:runDebug
cls
echo =============================================================================
echo     TimeBars: Launching Program (Debug Mode)
echo =============================================================================
echo.

:: Check if venv exists
if not exist ".\venv\Scripts\activate.bat" (
    echo ERROR: Virtual environment not found!
    echo Please run the installer first ^(Option 3^).
    echo.
    pause
    goto menu
)

:: Check if program.py exists
if not exist ".\program.py" (
    echo ERROR: program.py not found!
    echo.
    pause
    goto menu
)

echo Activating virtual environment...
call ".\venv\Scripts\activate.bat"

echo Starting TimeBars (Debug Mode)...
echo.

:: Run the program using python.exe (Visible console)
python ".\program.py"

echo.
echo Program exited.
call deactivate 2>nul
echo.
echo Returning to menu...
timeout /t 2 /nobreak >nul
goto menu

:: Run Installer
:runInstaller
cls
echo =============================================================================
echo     TimeBars: Running Installer
echo =============================================================================
echo.

:: Check if Python is available
where python >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo ERROR: Python not found in PATH!
    echo Please install Python 3.10+ and add it to PATH.
    echo.
    pause
    goto menu
)

:: Check Python version
for /f "tokens=2 delims= " %%v in ('python --version 2^>^&1') do set pyver=%%v
echo Detected Python version: %pyver%
echo.

:: Run installer
python ".\installer.py"

if %ERRORLEVEL% neq 0 (
    echo.
    echo Installer encountered an error.
) else (
    echo.
    echo Installation complete!
)

echo.
pause
goto menu

:: End Function
:end
echo.
echo Exiting TimeBars...
timeout /t 1 /nobreak >nul
:: exit /b returns to parent CMD if launched from one, otherwise closes window
exit /b