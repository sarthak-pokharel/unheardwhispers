@echo off
setlocal enabledelayedexpansion

echo.
echo ========================================
echo   Script to Subtitles Converter Setup
echo ========================================
echo.

REM Create project directories
mkdir "tools" 2>nul
mkdir "tools\ffmpeg" 2>nul
mkdir "temp" 2>nul

REM Check Python version
python --version > nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Python is not installed or not in PATH.
    echo Please install Python 3.8 or later from https://www.python.org/downloads/
    pause
    exit /b 1
)

for /f "tokens=2" %%I in ('python --version 2^>^&1') do set pyver=%%I
for /f "tokens=1,2 delims=." %%a in ("%pyver%") do (
    set pymajor=%%a
    set pyminor=%%b
)

if %pymajor% LSS 3 (
    echo [ERROR] Python 3.8 or higher is required!
    echo Current version: %pyver%
    pause
    exit /b 1
) else if %pymajor% EQU 3 (
    if %pyminor% LSS 8 (
        echo [ERROR] Python 3.8 or higher is required!
        echo Current version: %pyver%
        pause
        exit /b 1
    )
)

echo [SUCCESS] Python %pyver% detected.

REM Install FFmpeg locally
echo [INFO] Installing FFmpeg locally...

REM Create a directory for FFmpeg
set ffmpeg_dir=%CD%\tools\ffmpeg\bin
mkdir "%ffmpeg_dir%" 2>nul

echo [INFO] Downloading FFmpeg for Windows...
powershell -Command "(New-Object System.Net.WebClient).DownloadFile('https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-win64-gpl.zip', 'temp\ffmpeg.zip')"

if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Failed to download FFmpeg.
    echo Please check your internet connection and try again.
    pause
    exit /b 1
)

echo [INFO] Extracting FFmpeg...
powershell -Command "Expand-Archive -Path 'temp\ffmpeg.zip' -DestinationPath 'temp\ffmpeg' -Force"

REM Find the bin directory with ffmpeg.exe and copy files
for /r "temp\ffmpeg" %%G in (ffmpeg.exe) do (
    copy "%%G" "%ffmpeg_dir%\ffmpeg.exe" >nul
    echo [INFO] Copied ffmpeg.exe to %ffmpeg_dir%
)

for /r "temp\ffmpeg" %%G in (ffprobe.exe) do (
    copy "%%G" "%ffmpeg_dir%\ffprobe.exe" >nul
    echo [INFO] Copied ffprobe.exe to %ffmpeg_dir%
)

for /r "temp\ffmpeg" %%G in (ffplay.exe) do (
    copy "%%G" "%ffmpeg_dir%\ffplay.exe" >nul
    echo [INFO] Copied ffplay.exe to %ffmpeg_dir%
)

echo [SUCCESS] FFmpeg installed locally to %ffmpeg_dir%

REM Clean up temp files
echo [INFO] Cleaning up temporary files...
if exist "temp\ffmpeg.zip" del /Q "temp\ffmpeg.zip"
if exist "temp\ffmpeg" rmdir /S /Q "temp\ffmpeg"

REM Create Python virtual environment
echo [INFO] Creating Python virtual environment...
python -m venv venv

REM Activate virtual environment and install dependencies
echo [INFO] Installing Python dependencies in virtual environment...
call venv\Scripts\activate.bat

REM Install pip, wheel and setuptools first
echo [INFO] Upgrading pip, wheel and setuptools...
python -m pip install --upgrade pip wheel setuptools

REM Check if requirements.txt exists
if not exist "requirements.txt" (
    echo [ERROR] requirements.txt not found!
    echo Please ensure you're running this script from the project root directory.
    deactivate
    pause
    exit /b 1
)

REM Install required packages
echo [INFO] Installing required packages from requirements.txt...
python -m pip install streamlit
python -m pip install -r requirements.txt --prefer-binary

if %ERRORLEVEL% NEQ 0 (
    echo [WARNING] Some packages may not have installed correctly.
    echo Trying alternative installation...
    
    python -m pip install openai-whisper --prefer-binary
    python -m pip install pydub nltk pandas plotly pysrt
)

REM Deactivate virtual environment
deactivate

REM Create launcher script with proper paths
echo [INFO] Creating launcher script...
(
echo @echo off
echo setlocal
echo.
echo echo Script to Subtitles Converter
echo echo ============================
echo echo.
echo.
echo REM Set up paths
echo set "SCRIPT_DIR=%%~dp0"
echo set "PATH=%%SCRIPT_DIR%%tools\ffmpeg\bin;%%PATH%%"
echo.
echo REM Activate virtual environment
echo call "%%SCRIPT_DIR%%venv\Scripts\activate.bat"
echo.
echo echo [INFO] Starting Streamlit application...
echo echo [INFO] FFmpeg path: %%SCRIPT_DIR%%tools\ffmpeg\bin
echo.
echo REM Run the application
echo streamlit run src/app.py
echo.
echo REM Deactivate virtual environment when done
echo deactivate
echo.
echo pause
) > runapp.bat

echo.
echo ============================================
echo   Setup Complete! To run the application:
echo ============================================
echo.
echo   Run the 'runapp.bat' file from this directory
echo.
echo ============================================

pause 