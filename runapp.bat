@echo off
echo Starting Script to Subtitles Converter...

REM Check if Python dependencies are installed
python -c "import streamlit" 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo Error: Required Python packages are not installed.
    echo Running setup script to install dependencies...
    python setup.py
    if %ERRORLEVEL% NEQ 0 (
        echo Setup failed. Please see the error messages above.
        echo You may need to install Microsoft Visual C++ Build Tools.
        echo Download from: https://visualstudio.microsoft.com/visual-cpp-build-tools/
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

streamlit run src/app.py
pause 