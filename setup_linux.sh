#!/bin/bash

# Define color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Print functions for consistency
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

echo
echo "========================================"
echo "  Script to Subtitles Converter Setup"
echo "========================================"
echo

# Create project directories
print_info "Creating project directories..."
mkdir -p tools/ffmpeg/bin
mkdir -p temp

# Check Python version
if ! command -v python3 &> /dev/null; then
    print_error "Python 3 is not installed or not in PATH."
    print_info "Please install Python 3.8 or later before continuing."
    exit 1
fi

python_version=$(python3 --version 2>&1 | cut -d' ' -f2)
python_major=$(echo $python_version | cut -d. -f1)
python_minor=$(echo $python_version | cut -d. -f2)

if [ "$python_major" -lt 3 ] || ([ "$python_major" -eq 3 ] && [ "$python_minor" -lt 8 ]); then
    print_error "Python 3.8 or higher is required!"
    print_error "Current version: $python_version"
    exit 1
fi

print_success "Python $python_version detected."

# Install FFmpeg locally (in project directory)
print_info "Installing FFmpeg locally to project directory..."

# Determine OS and architecture
ARCH=$(uname -m)
OS=$(uname -s)
FFMPEG_URL=""
FFMPEG_BIN_PATH="tools/ffmpeg/bin"

# Set download URL based on OS and architecture
if [[ "$OS" == "Linux" ]]; then
    if [[ "$ARCH" == "x86_64" ]]; then
        FFMPEG_URL="https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-linux64-gpl.tar.xz"
    elif [[ "$ARCH" == "aarch64" || "$ARCH" == "arm64" ]]; then
        FFMPEG_URL="https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-arm64-static.tar.xz"
    fi
elif [[ "$OS" == "Darwin" ]]; then  # macOS
    if [[ "$ARCH" == "x86_64" ]]; then
        FFMPEG_URL="https://evermeet.cx/ffmpeg/getrelease/ffmpeg/zip"
    elif [[ "$ARCH" == "arm64" ]]; then
        FFMPEG_URL="https://evermeet.cx/ffmpeg/getrelease/ffmpeg/zip"
    fi
fi

# Download and extract FFmpeg
if [[ -n "$FFMPEG_URL" ]]; then
    print_info "Downloading FFmpeg from $FFMPEG_URL..."
    
    # Create temp directory
    mkdir -p temp
    
    # Download FFmpeg
    if [[ "$OS" == "Darwin" && ("$ARCH" == "x86_64" || "$ARCH" == "arm64") ]]; then
        # macOS uses a zip file
        curl -L "$FFMPEG_URL" -o temp/ffmpeg.zip
        if [ $? -ne 0 ]; then
            print_error "Failed to download FFmpeg"
            exit 1
        fi
        
        # Extract
        unzip -o temp/ffmpeg.zip -d "$FFMPEG_BIN_PATH"
        chmod +x "$FFMPEG_BIN_PATH/ffmpeg"
    else
        # Linux uses tar.xz
        wget -q "$FFMPEG_URL" -O temp/ffmpeg.tar.xz
        if [ $? -ne 0 ]; then
            print_error "Failed to download FFmpeg"
            exit 1
        fi
        
        # Extract
        tar -xf temp/ffmpeg.tar.xz -C temp
        
        # Find and copy FFmpeg binaries
        find temp -name "ffmpeg" -type f -exec cp {} "$FFMPEG_BIN_PATH/ffmpeg" \;
        find temp -name "ffprobe" -type f -exec cp {} "$FFMPEG_BIN_PATH/ffprobe" \;
        find temp -name "ffplay" -type f -exec cp {} "$FFMPEG_BIN_PATH/ffplay" \;
        
        # Make executable
        chmod +x "$FFMPEG_BIN_PATH/ffmpeg" "$FFMPEG_BIN_PATH/ffprobe" 2>/dev/null
    fi
    
    # Verify installation
    if [ -f "$FFMPEG_BIN_PATH/ffmpeg" ]; then
        print_success "FFmpeg installed successfully in project directory"
    else
        print_error "Failed to install FFmpeg locally"
        exit 1
    fi
else
    print_error "Unsupported platform: $OS $ARCH"
    print_error "Please manually download FFmpeg from https://ffmpeg.org/download.html"
    print_error "and place the executables in $FFMPEG_BIN_PATH"
    exit 1
fi

# Clean up
print_info "Cleaning up temporary files..."
rm -rf temp/*

# Create Python virtual environment
print_info "Creating Python virtual environment..."
python3 -m venv venv

# Activate virtual environment
print_info "Activating virtual environment and installing dependencies..."
source venv/bin/activate

# Upgrade pip first
print_info "Upgrading pip, wheel, and setuptools..."
pip install --upgrade pip wheel setuptools

# Check if requirements.txt exists
if [ ! -f "requirements.txt" ]; then
    print_error "requirements.txt not found!"
    print_info "Please ensure you're running this script from the project root directory."
    deactivate
    exit 1
fi

# Install dependencies
print_info "Installing required packages from requirements.txt..."
pip install streamlit
pip install -r requirements.txt

if [ $? -ne 0 ]; then
    print_warning "Some packages may not have installed correctly."
    print_info "Trying to install critical packages individually..."
    
    pip install openai-whisper
    pip install pydub nltk pandas plotly pysrt
fi

# Deactivate virtual environment
deactivate

# Create launcher script
print_info "Creating launcher script..."
cat > runapp.sh << 'EOF'
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
EOF

# Make it executable
chmod +x runapp.sh

echo
echo "============================================"
echo "  Setup Complete! To run the application:"
echo "============================================"
echo
echo "  Run the following command:"
echo "  ./runapp.sh"
echo
echo "============================================" 