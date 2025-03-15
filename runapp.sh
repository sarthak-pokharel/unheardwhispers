#!/bin/bash

# Define color codes
BLUE='\033[0;34m'
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo "Script to Subtitles Converter"
echo "============================"
echo

# Set up paths
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export PATH="$SCRIPT_DIR/tools/ffmpeg/bin:$PATH"

# Activate virtual environment
source "$SCRIPT_DIR/venv/bin/activate"

echo -e "${BLUE}[INFO]${NC} Starting Streamlit application..."
echo -e "${BLUE}[INFO]${NC} FFmpeg path: $SCRIPT_DIR/tools/ffmpeg/bin"

# Run the application
streamlit run src/app.py

# Deactivate virtual environment when done
deactivate
