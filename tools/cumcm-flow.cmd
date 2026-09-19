@echo off
setlocal EnableExtensions EnableDelayedExpansion
chcp 65001 >nul
set "PYTHONUTF8=1"
set "SCRIPT=%~dp0cumcm_flow.py"
set "PY="
set "PY_LAUNCHER="

rem 环境变量可以指向解释器或虚拟环境目录；每个候选都要实际运行并验证 Python 版本。
if defined CUMCM_CODE_ENV call :try_python "%CUMCM_CODE_ENV%"
if not defined PY if defined CUMCM_PYTHON call :try_python "%CUMCM_PYTHON%"
if not defined PY if defined MODELING_PY call :try_python "%MODELING_PY%"
if not defined PY if exist "%~dp0python.path" (
  set /p CONFIG_PY=<"%~dp0python.path"
  if defined CONFIG_PY call :try_python "!CONFIG_PY!"
)
if not defined PY for %%P in (python.exe) do call :try_python "%%~$PATH:P"
if not defined PY for %%P in (python3.exe) do call :try_python "%%~$PATH:P"
if not defined PY if exist "%LocalAppData%\Programs\Python\Python311\python.exe" call :try_python "%LocalAppData%\Programs\Python\Python311\python.exe"
if not defined PY if exist "%LocalAppData%\Programs\Python\Python312\python.exe" call :try_python "%LocalAppData%\Programs\Python\Python312\python.exe"
if not defined PY if exist "%LocalAppData%\Programs\Python\Python313\python.exe" call :try_python "%LocalAppData%\Programs\Python\Python313\python.exe"
if not defined PY if exist "%ProgramFiles%\Python311\python.exe" call :try_python "%ProgramFiles%\Python311\python.exe"
if not defined PY if exist "%ProgramFiles%\Python312\python.exe" call :try_python "%ProgramFiles%\Python312\python.exe"
if not defined PY if exist "%ProgramFiles%\Python313\python.exe" call :try_python "%ProgramFiles%\Python313\python.exe"
if not defined PY if exist "%SystemRoot%\py.exe" (
  "%SystemRoot%\py.exe" -3 -c "import sys; assert sys.version_info.major > 3 or sys.version_info.minor >= 11" >nul 2>&1
  if not errorlevel 1 (
    set "PY=%SystemRoot%\py.exe"
    set "PY_LAUNCHER=1"
  )
)

if not defined PY (
  echo [cumcm-flow] 找不到 Python 3.11+。请安装 Python，或设置 CUMCM_PYTHON。
  exit /b 9009
)
if defined PY_LAUNCHER (
  "%PY%" -3 "%SCRIPT%" %*
) else (
  "%PY%" "%SCRIPT%" %*
)
exit /b %ERRORLEVEL%

:try_python
set "CAND=%~1"
if not defined CAND exit /b 1
if exist "%CAND%\Scripts\python.exe" set "CAND=%CAND%\Scripts\python.exe"
if exist "%CAND%\python.exe" if not exist "%CAND%\Scripts\python.exe" set "CAND=%CAND%\python.exe"
if not exist "%CAND%" exit /b 1
echo "%CAND%" | findstr /I "WindowsApps" >nul && exit /b 1
"%CAND%" -c "import sys; assert sys.version_info.major > 3 or sys.version_info.minor >= 11" >nul 2>&1
if errorlevel 1 exit /b 1
set "PY=%CAND%"
exit /b 0
