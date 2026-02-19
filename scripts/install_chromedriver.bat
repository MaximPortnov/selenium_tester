@echo off
setlocal

rem Usage: install_chromedriver.bat [version] [destination]
set "VERSION=%~1"
if "%VERSION%"=="" set "VERSION=109.0.5414.74"

set "DEST=%~2"
if "%DEST%"=="" set "DEST=%~dp0..\chromedriver-win64"

set "URL=https://chromedriver.storage.googleapis.com/%VERSION%/chromedriver_win32.zip"
set "ZIP=%TEMP%\chromedriver-win32-%VERSION%-%RANDOM%.zip"

echo Downloading ChromeDriver %VERSION% from %URL% ...
powershell -NoLogo -NoProfile -Command "Invoke-WebRequest -Uri '%URL%' -OutFile '%ZIP%' -UseBasicParsing"
if errorlevel 1 (
    echo Failed to download ChromeDriver %VERSION%.
    exit /b 1
)

echo Extracting to %DEST% ...
powershell -NoLogo -NoProfile -Command "if (-not (Test-Path '%DEST%')) { New-Item -ItemType Directory -Path '%DEST%' -Force | Out-Null }; Expand-Archive -Path '%ZIP%' -DestinationPath '%DEST%' -Force"
if errorlevel 1 (
    echo Failed to extract ChromeDriver.
    exit /b 1
)

if not exist "%DEST%\chromedriver.exe" (
    echo chromedriver.exe not found after extraction: %DEST%\chromedriver.exe
    exit /b 1
)

echo Cleaning up temporary files...
del "%ZIP%" >nul 2>&1
echo ChromeDriver installed to %DEST%\chromedriver.exe
endlocal
