@echo off
echo Script to Subtitles Converter
echo ============================

REM Check for admin privileges
NET SESSION >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo Not running with administrator privileges. Some installations may fail.
    echo.
    echo Options:
    echo 1. Continue without admin rights
    echo 2. Restart with admin rights (recommended for installation)
    echo 3. Exit
    
    set /p choice="Enter your choice (1-3): "
    
    if "%choice%"=="2" (
        echo Restarting with admin rights...
        powershell -Command "Start-Process cmd -ArgumentList '/c cd /d %CD% && %~f0' -Verb RunAs"
        exit /b
    ) else if "%choice%"=="3" (
        exit /b
    )
    echo Continuing without admin rights...
    echo.
)

REM Check if Python dependencies are installed
python -c "import streamlit" 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo Error: Required Python packages are not installed.
    echo Running setup script to install dependencies...
    
    if exist "%CD%\setup.py" (
        python setup.py
        if %ERRORLEVEL% NEQ 0 (
            echo.
            echo Setup failed. Please try one of the following:
            echo 1. Run this script again and choose to restart with admin rights
            echo 2. Manually install Microsoft Visual C++ Build Tools
            echo    Download from: https://visualstudio.microsoft.com/visual-cpp-build-tools/
            echo 3. Try running these commands manually:
            echo    pip install --upgrade pip
            echo    pip install wheel setuptools
            echo    pip install streamlit openai-whisper pysrt pydub nltk numpy pandas plotly --prefer-binary
            echo.
            pause
            exit /b 1
        )
    ) else (
        echo Cannot find setup.py in the current directory.
        echo Please make sure you're running this script from the project root.
        pause
        exit /b 1
    )
)

REM Check if FFmpeg is installed
where ffmpeg >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo Warning: FFmpeg not found in PATH. The application may not work correctly.
    echo Running setup script to install FFmpeg...
    python setup.py
)

echo.
echo Starting Streamlit application...
streamlit run src/app.py
pause 