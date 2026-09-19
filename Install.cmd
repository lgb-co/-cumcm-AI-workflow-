@echo off
chcp 65001 >nul
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0install.ps1" %*
set "RC=%ERRORLEVEL%"
if not "%RC%"=="0" echo Installation failed. See the message above.
if "%~1"=="" if not "%CI%"=="1" pause
exit /b %RC%
