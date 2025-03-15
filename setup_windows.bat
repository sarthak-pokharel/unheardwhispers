@echo off
setlocal enabledelayedexpansion

echo.
echo ========================================
echo   Script to Subtitles Converter Setup
echo ========================================
echo.

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

REM Install FFmpeg if not already installed
where ffmpeg >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [INFO] FFmpeg not found. Installing FFmpeg...
    
    REM Create a directory for FFmpeg
    set ffmpeg_dir=%USERPROFILE%\ffmpeg\bin
    mkdir "%ffmpeg_dir%" 2>nul
    
    echo [INFO] Downloading FFmpeg for Windows...
    powershell -Command "(New-Object System.Net.WebClient).DownloadFile('https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-win64-gpl.zip', '%TEMP%\ffmpeg.zip')"
    
    if %ERRORLEVEL% NEQ 0 (
        echo [ERROR] Failed to download FFmpeg.
        echo Please install FFmpeg manually: https://ffmpeg.org/download.html
        pause
        exit /b 1
    )
    
    echo [INFO] Extracting FFmpeg...
    powershell -Command "Expand-Archive -Path '%TEMP%\ffmpeg.zip' -DestinationPath '%TEMP%\ffmpeg' -Force"
    
    REM Find the bin directory with ffmpeg.exe
    for /r "%TEMP%\ffmpeg" %%G in (ffmpeg.exe) do (
        copy "%%G" "%ffmpeg_dir%\ffmpeg.exe" >nul
        echo [INFO] Copied ffmpeg.exe to %ffmpeg_dir%
    )
    
    for /r "%TEMP%\ffmpeg" %%G in (ffprobe.exe) do (
        copy "%%G" "%ffmpeg_dir%\ffprobe.exe" >nul
        echo [INFO] Copied ffprobe.exe to %ffmpeg_dir%
    )
    
    for /r "%TEMP%\ffmpeg" %%G in (ffplay.exe) do (
        copy "%%G" "%ffmpeg_dir%\ffplay.exe" >nul
        echo [INFO] Copied ffplay.exe to %ffmpeg_dir%
    )
    
    REM Add to PATH for current session
    set "PATH=%PATH%;%ffmpeg_dir%"
    
    REM Add to PATH permanently
    setx PATH "%PATH%;%ffmpeg_dir%" >nul
    
    echo [SUCCESS] FFmpeg installed successfully!
    echo [INFO] Added to PATH: %ffmpeg_dir%
    echo [INFO] You may need to restart your command prompt for PATH changes to take effect.
) else (
    echo [SUCCESS] FFmpeg is already installed!
)

REM Install Python dependencies
echo.
echo [INFO] Installing Python dependencies...
echo This process may take several minutes depending on your internet connection.

REM Install pip, wheel and setuptools first
echo [INFO] Upgrading pip, wheel and setuptools...
python -m pip install --upgrade pip wheel setuptools

REM Check if requirements.txt exists
if not exist "requirements.txt" (
    echo [ERROR] requirements.txt not found!
    echo Please ensure you're running this script from the project root directory.
    pause
    exit /b 1
)

REM Try to install packages with --prefer-binary first
echo [INFO] Installing required packages from requirements.txt...
python -m pip install streamlit --user
if %ERRORLEVEL% NEQ 0 (
    echo [WARNING] Failed to install streamlit. This is a critical dependency.
    echo Please try installing it manually: pip install streamlit --user
)

python -m pip install -r requirements.txt --prefer-binary
if %ERRORLEVEL% NEQ 0 (
    echo [WARNING] Some packages may not have installed correctly.
    echo Trying alternative installation with --user flag...
    
    python -m pip install -r requirements.txt --prefer-binary --user
    if %ERRORLEVEL% NEQ 0 (
        echo [WARNING] Installation with --user flag also encountered issues.
        echo.
        echo [INFO] Trying to install packages individually...
        
        python -m pip install openai-whisper --prefer-binary --user
        python -m pip install pydub nltk pandas plotly pysrt --user
        
        echo.
        echo [WARNING] If you still experience issues, you may need to:
        echo 1. Install Microsoft Visual C++ Build Tools
        echo    Download from: https://visualstudio.microsoft.com/visual-cpp-build-tools/
        echo    Select "Desktop development with C++" during installation
    )
)

REM Create launcher script
echo [INFO] Creating launcher script...
(
echo @echo off
echo echo Script to Subtitles Converter
echo echo ============================
echo.
echo REM Check if Python dependencies are installed
echo python -c "import streamlit" 2^>nul
echo if %%ERRORLEVEL%% NEQ 0 ^(
echo     echo Error: Required Python packages are not installed.
echo     echo Please run setup_windows.bat first.
echo     pause
echo     exit /b 1
echo ^)
echo.
echo REM Check if FFmpeg is installed
echo where ffmpeg ^>nul 2^>nul
echo if %%ERRORLEVEL%% NEQ 0 ^(
echo     echo Warning: FFmpeg not found in PATH. The application may not work correctly.
echo     echo Please run setup_windows.bat first.
echo     pause
echo     exit /b 1
echo ^)
echo.
echo echo.
echo echo Starting Streamlit application...
echo streamlit run src/app.py
echo pause
) > runapp.bat

echo.
echo ============================================
echo   Setup Complete! To run the application:
echo ============================================
echo.
echo   Run the 'runapp.bat' file or execute:
echo   streamlit run src/app.py
echo.
echo ============================================

pause 