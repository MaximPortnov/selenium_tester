@echo off
setlocal

rem Usage: replay_cases_report.bat [target] [venv_path]
set "TARGET=%~1"
set "VENV_PATH=%~2"
if "%VENV_PATH%"=="" set "VENV_PATH=.venv"

set "SCRIPT_DIR=%~dp0"
for %%I in ("%SCRIPT_DIR%..") do set "REPO_ROOT=%%~fI"
set "VENV_PY=%REPO_ROOT%\%VENV_PATH%\Scripts\python.exe"

if exist "%VENV_PY%" (
    set "PYTHON_EXE=%VENV_PY%"
) else (
    set "PYTHON_EXE="
    where python >nul 2>&1
    if not errorlevel 1 (
        set "PYTHON_EXE=python"
    ) else (
        where py >nul 2>&1
        if not errorlevel 1 (
            set "PYTHON_EXE=py"
        )
    )
)

if "%PYTHON_EXE%"=="" (
    echo Python executable not found: "%PYTHON_EXE%"
    echo Run scripts\setup_env.bat to create ".venv" or install Python in PATH.
    exit /b 1
)

if "%TARGET%"=="" (
    "%PYTHON_EXE%" "%REPO_ROOT%\utils\replay_cases_report.py"
) else (
    "%PYTHON_EXE%" "%REPO_ROOT%\utils\replay_cases_report.py" "%TARGET%"
)

set "EXIT_CODE=%ERRORLEVEL%"
if not "%EXIT_CODE%"=="0" (
    exit /b %EXIT_CODE%
)

endlocal
