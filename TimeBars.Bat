REM Script: TimeLoop-Ps.Bat

@echo off

:: Initialization
mode con cols=46 lines=17
echo.
echo =================( TimeBars )=================
echo.
cd /d "%~dp0"
color 80
title TimeBars
timeout /t 1 /nobreak >nul
echo Launcher Initialized...
echo.
timeout /t 1 /nobreak >nul

:: Main Menu
:menu
cls
echo   ^_^_^_^_^_ ^_                ^_^_^_^_
echo  ^|^_   ^_^<^_^>^_^_^_^_^_^_^_^_   ^_^_^_^| ^_^_ ^>  ^_^_^_^_ ^_^_^_^_^_^_^_
echo    ^| ^| ^| ^|  ^_   ^_ ^\ ^/ ^_ ^\  ^_ ^\ ^/ ^_  ^|  ^_^/ ^_^_^|
echo    ^| ^| ^| ^| ^| ^| ^| ^| ^|  ^_^_^/ ^|^_^> ^| ^<^_^| ^| ^| ^\^_^_ ^\
echo    ^|^_^| ^|^_^|^_^| ^|^_^| ^|^_^|^\^_^_^_^|^_^_^_^_^/ ^\^_^_^_^_^|^_^| ^|^_^_^_^/
echo.
echo =================( TimeBars )=================
echo.
echo.
echo              1. Run TimeBars
echo              2. Check Integrity
echo.
echo.
echo ----------------------------------------------

:: Variables
set /p choice=Select; Options=1-2, Exit=X: 
if "%choice%"=="1" goto executeMain
if "%choice%"=="2" goto checkScript
if "%choice%"=="x" goto end
echo Invalid choice. Try again.
timeout /t 2 /nobreak >nul
goto menu

:: Execute main.py
:executeMain
cls
echo.
echo =================( TimeBars )=================
echo.
timeout /t 1 /nobreak >nul
echo Maintenenace Started..
if exist ".\Errors-Crash.Log" (
    echo Deleted: Errors-Crash.Log
    del ".\Errors-Crash.Log"
)
echo ..Maintenance Done.
echo.
timeout /t 1 /nobreak >nul
echo Launching Script...
echo.
timeout /t 1 /nobreak >nul
where pwsh >nul 2>&1
if %ERRORLEVEL% equ 0 (
    pwsh.exe -NoProfile -ExecutionPolicy Bypass -File ".\main.ps1" 2>>".\Errors-Crash.Log"
	echo ...Psc Process Exited.
) else (
    powershell.exe -NoProfile -ExecutionPolicy Bypass -File ".\main.ps1" 2>>".\Errors-Crash.Log"
	echo ...Ps Process Exited.
)
echo.
color 80
echo Returning to menu..
timeout /t 2 /nobreak >nul
goto menu

:: Check File Structure
:checkScript
cls
echo.
echo =================( TimeBars )=================
echo.
echo Checking Script Files..
set missing=0
timeout /t 1 /nobreak >nul
if not exist ".\main.ps1" set missing=1
if not exist ".\scripts\display.ps1" set missing=1
if %missing%==1 (
    echo ..Failure, Re-Install Program!
) else (
    echo ..Program Files Correct.
)
echo.
timeout /t 1 /nobreak >nul
echo Returning to menu..
echo.
timeout /t 2 /nobreak >nul
goto menu

:: End Function
:end
echo ...Exit Process Initiated.
timeout /t 2 /nobreak >nul