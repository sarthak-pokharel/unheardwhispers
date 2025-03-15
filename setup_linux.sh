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

# Check if running with sudo/root on Linux
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    if [ "$EUID" -ne 0 ]; then
        print_warning "Not running as root. Some installations may fail."
        echo "Consider running this script with sudo:"
        echo "sudo $0"
        
        read -p "Continue anyway? [y/N]: " response
        if [[ ! "$response" =~ ^[yY]$ ]]; then
            print_info "Setup aborted. Please run with sudo and try again."
            exit 1
        fi
        
        print_info "Continuing without sudo..."
        echo
    else
        print_success "Running with root privileges."
    fi
fi

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

# Install FFmpeg if not already installed
if ! command -v ffmpeg &> /dev/null; then
    print_info "FFmpeg not found. Installing FFmpeg..."
    
    # Detect the OS
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        print_info "Detected macOS"
        
        # Check if Homebrew is installed
        if command -v brew &> /dev/null; then
            print_info "Installing FFmpeg via Homebrew..."
            brew install ffmpeg
        else
            print_warning "Homebrew is not installed. Installing Homebrew first..."
            /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
            
            if [ $? -eq 0 ]; then
                print_success "Homebrew installed successfully!"
                print_info "Installing FFmpeg via Homebrew..."
                brew install ffmpeg
            else
                print_error "Failed to install Homebrew."
                print_warning "Please install FFmpeg manually: https://ffmpeg.org/download.html"
                exit 1
            fi
        fi
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        # Linux
        print_info "Detected Linux"
        
        # Try to detect the package manager
        if command -v apt-get &> /dev/null; then
            print_info "Installing FFmpeg via apt-get..."
            apt-get update && apt-get install -y ffmpeg
        elif command -v dnf &> /dev/null; then
            print_info "Installing FFmpeg via dnf..."
            dnf install -y ffmpeg
        elif command -v yum &> /dev/null; then
            print_info "Installing FFmpeg via yum..."
            yum install -y epel-release && yum install -y ffmpeg
        elif command -v pacman &> /dev/null; then
            print_info "Installing FFmpeg via pacman..."
            pacman -Sy ffmpeg --noconfirm
        elif command -v zypper &> /dev/null; then
            print_info "Installing FFmpeg via zypper..."
            zypper install -y ffmpeg
        else
            print_warning "Could not detect package manager."
            print_warning "Please install FFmpeg manually using your distribution's package manager."
            exit 1
        fi
    else
        print_error "Unsupported platform: $OSTYPE"
        print_warning "Please install FFmpeg manually: https://ffmpeg.org/download.html"
        exit 1
    fi
    
    # Verify installation
    if command -v ffmpeg &> /dev/null; then
        print_success "FFmpeg installed successfully!"
    else
        print_error "FFmpeg installation failed."
        print_warning "Please install FFmpeg manually and try again."
        exit 1
    fi
else
    print_success "FFmpeg is already installed!"
fi

# Install Python dependencies
echo
print_info "Installing Python dependencies..."
print_info "This process may take several minutes depending on your internet connection."

# Upgrade pip first
print_info "Upgrading pip, wheel, and setuptools..."
python3 -m pip install --upgrade pip wheel setuptools

# Check if requirements.txt exists
if [ ! -f "requirements.txt" ]; then
    print_error "requirements.txt not found!"
    print_info "Please ensure you're running this script from the project root directory."
    exit 1
fi

# Install dependencies
print_info "Installing required packages from requirements.txt..."
python3 -m pip install -r requirements.txt

if [ $? -ne 0 ]; then
    print_warning "Some packages may not have installed correctly."
    print_info "Trying to install critical packages individually..."
    
    python3 -m pip install streamlit
    python3 -m pip install openai-whisper
    python3 -m pip install pydub nltk pandas plotly pysrt
    
    print_warning "If you still experience issues, you may need to install additional system dependencies."
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        print_info "For Ubuntu/Debian, try: sudo apt-get install python3-dev build-essential"
        print_info "For Fedora, try: sudo dnf install python3-devel gcc"
    fi
fi

# Create launcher script
print_info "Creating launcher script..."
cat > runapp.sh << 'EOF'
#!/bin/bash

# Define color codes
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo "Script to Subtitles Converter"
echo "============================"
echo

# Check if Python dependencies are installed
python3 -c "import streamlit" 2>/dev/null
if [ $? -ne 0 ]; then
    echo -e "${RED}[ERROR]${NC} Required Python packages are not installed."
    echo "Please run setup_linux.sh first."
    exit 1
fi

# Check if FFmpeg is installed
if ! command -v ffmpeg &> /dev/null; then
    echo -e "${RED}[WARNING]${NC} FFmpeg not found in PATH. The application may not work correctly."
    echo "Please run setup_linux.sh first."
    exit 1
fi

echo -e "${BLUE}[INFO]${NC} Starting Streamlit application..."
streamlit run src/app.py
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
echo "  Or directly with Streamlit:"
echo "  streamlit run src/app.py"
echo
echo "============================================" 