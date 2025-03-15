#!/usr/bin/env python3
import os
import sys
import platform
import subprocess
import shutil
import tempfile
from pathlib import Path

def print_colored(text, color_code):
    """Print colored text"""
    print(f"\033[{color_code}m{text}\033[0m")

def print_info(text):
    print_colored(text, 94)  # Blue

def print_success(text):
    print_colored(text, 92)  # Green

def print_warning(text):
    print_colored(text, 93)  # Yellow

def print_error(text):
    print_colored(text, 91)  # Red

def run_command(command, check=True, shell=False, env=None):
    """Run a system command and return the result"""
    try:
        if isinstance(command, str) and not shell:
            command = command.split()
        result = subprocess.run(command, check=check, shell=shell, 
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE, 
                               text=True, env=env)
        return result
    except subprocess.CalledProcessError as e:
        print_error(f"Command failed: {e}")
        print_error(f"Error output: {e.stderr}")
        if check:
            sys.exit(1)
        return e

def is_tool_installed(tool_name):
    """Check if a tool is installed and available in PATH"""
    return shutil.which(tool_name) is not None

def install_ffmpeg():
    """Install FFmpeg based on the platform"""
    system = platform.system().lower()
    
    if is_tool_installed("ffmpeg"):
        print_success("FFmpeg is already installed!")
        return
    
    print_info("Installing FFmpeg...")
    
    if system == "windows":
        # On Windows, download the static build
        import urllib.request
        from zipfile import ZipFile
        
        print_info("Downloading FFmpeg for Windows...")
        ffmpeg_url = "https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-win64-gpl.zip"
        temp_dir = tempfile.gettempdir()
        zip_path = os.path.join(temp_dir, "ffmpeg.zip")
        
        try:
            urllib.request.urlretrieve(ffmpeg_url, zip_path)
            
            # Extract the ZIP file
            with ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(temp_dir)
            
            # Find the bin directory with ffmpeg.exe
            ffmpeg_dir = None
            for root, dirs, files in os.walk(temp_dir):
                if "ffmpeg.exe" in files:
                    ffmpeg_dir = root
                    break
            
            if not ffmpeg_dir:
                print_error("FFmpeg executable not found in the downloaded package.")
                print_warning("Please install FFmpeg manually: https://ffmpeg.org/download.html")
                return
            
            # Add to PATH for the current session
            os.environ["PATH"] += os.pathsep + ffmpeg_dir
            
            # Create a directory in the user profile if it doesn't exist
            user_bin_dir = os.path.join(os.path.expanduser("~"), "ffmpeg", "bin")
            os.makedirs(user_bin_dir, exist_ok=True)
            
            # Copy FFmpeg executables
            for file in ["ffmpeg.exe", "ffprobe.exe", "ffplay.exe"]:
                if os.path.exists(os.path.join(ffmpeg_dir, file)):
                    shutil.copy2(os.path.join(ffmpeg_dir, file), os.path.join(user_bin_dir, file))
            
            # Add to PATH permanently
            try:
                import winreg
                with winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment", 0, winreg.KEY_ALL_ACCESS) as key:
                    try:
                        path, _ = winreg.QueryValueEx(key, "Path")
                        if user_bin_dir not in path:
                            winreg.SetValueEx(key, "Path", 0, winreg.REG_EXPAND_SZ, path + os.pathsep + user_bin_dir)
                    except WindowsError:
                        winreg.SetValueEx(key, "Path", 0, winreg.REG_EXPAND_SZ, user_bin_dir)
            except Exception as e:
                print_warning(f"Could not add FFmpeg to PATH permanently: {e}")
                print_warning(f"Please add {user_bin_dir} to your PATH manually.")
            
            print_success("FFmpeg installed successfully!")
            print_info(f"FFmpeg has been installed to: {user_bin_dir}")
            print_info("You may need to restart your terminal or system for the PATH changes to take effect.")
            
        except Exception as e:
            print_error(f"Failed to download or install FFmpeg: {e}")
            print_warning("Please install FFmpeg manually: https://ffmpeg.org/download.html")
    
    elif system == "darwin":  # macOS
        # Check if Homebrew is installed
        if is_tool_installed("brew"):
            print_info("Installing FFmpeg via Homebrew...")
            run_command("brew install ffmpeg")
            print_success("FFmpeg installed successfully!")
        else:
            print_warning("Homebrew is not installed. Installing Homebrew first...")
            homebrew_install_cmd = '/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"'
            try:
                run_command(homebrew_install_cmd, shell=True)
                print_success("Homebrew installed successfully!")
                print_info("Installing FFmpeg via Homebrew...")
                run_command("brew install ffmpeg")
                print_success("FFmpeg installed successfully!")
            except Exception as e:
                print_error(f"Failed to install Homebrew or FFmpeg: {e}")
                print_warning("Please install FFmpeg manually: https://ffmpeg.org/download.html")
    
    elif system == "linux":
        # Try to detect the package manager
        package_manager = None
        if is_tool_installed("apt-get"):  # Debian, Ubuntu, etc.
            package_manager = "apt-get"
            install_cmd = "apt-get update && apt-get install -y ffmpeg"
        elif is_tool_installed("dnf"):  # Fedora
            package_manager = "dnf"
            install_cmd = "dnf install -y ffmpeg"
        elif is_tool_installed("yum"):  # CentOS, RHEL
            package_manager = "yum"
            install_cmd = "yum install -y epel-release && yum install -y ffmpeg"
        elif is_tool_installed("pacman"):  # Arch Linux
            package_manager = "pacman"
            install_cmd = "pacman -Sy ffmpeg --noconfirm"
        elif is_tool_installed("zypper"):  # openSUSE
            package_manager = "zypper"
            install_cmd = "zypper install -y ffmpeg"
        
        if package_manager:
            print_info(f"Installing FFmpeg via {package_manager}...")
            try:
                if os.geteuid() == 0:  # If running as root
                    run_command(install_cmd, shell=True)
                else:
                    # Use sudo if not running as root
                    run_command(f"sudo {install_cmd}", shell=True)
                print_success("FFmpeg installed successfully!")
            except Exception as e:
                print_error(f"Failed to install FFmpeg: {e}")
                print_warning("Please install FFmpeg manually using your package manager.")
        else:
            print_warning("Could not detect package manager.")
            print_warning("Please install FFmpeg manually using your distribution's package manager.")
    
    else:
        print_error(f"Unsupported platform: {system}")
        print_warning("Please install FFmpeg manually: https://ffmpeg.org/download.html")

def install_dependencies():
    """Install Python dependencies from requirements.txt
    
    This function performs the following operations:
    1. Displays an informative message about dependency installation
    2. Upgrades pip to the latest version to avoid compatibility issues
    3. Checks for the existence of requirements.txt in the current directory
    4. Installs all dependencies listed in requirements.txt if found
    5. Provides appropriate success or error messages with colored output
    6. Exits with error code 1 if requirements.txt is not found
    """
    print_info("Installing Python dependencies...")
    print_info("This process may take several minutes depending on your internet connection and the packages required.")
    
    # Upgrade pip to the latest version to ensure compatibility with newer packages
    print_info("Step 1/2: Upgrading pip to the latest version...")
    pip_upgrade_result = run_command([sys.executable, "-m", "pip", "install", "--upgrade", "pip"])
    if pip_upgrade_result.returncode == 0:
        print_success("Pip successfully upgraded to the latest version.")
    else:
        print_warning("Pip upgrade encountered issues but continuing with installation.")
    
    # Install all required dependencies from requirements.txt
    print_info("Step 2/2: Installing required packages from requirements.txt...")
    if os.path.exists("requirements.txt"):
        # Read requirements file to show what will be installed
        with open("requirements.txt", "r") as req_file:
            requirements = req_file.read().strip().split("\n")
            print_info(f"Found {len(requirements)} packages to install: {', '.join(requirements[:5])}" + 
                      (f" and {len(requirements)-5} more..." if len(requirements) > 5 else ""))
        
        # Install dependencies with verbose output
        install_result = run_command([sys.executable, "-m", "pip", "install", "-r", "requirements.txt", "-v"])
        if install_result.returncode == 0:
            print_success("All dependencies installed successfully!")
            print_info("Your environment is now ready to run the application.")
        else:
            print_warning("Some dependencies may not have installed correctly.")
            print_info("You may need to install problematic packages manually.")
    else:
        print_error("Critical error: requirements.txt not found in the current directory!")
        print_error("Cannot continue with setup without knowing which packages to install.")
        print_info("Please ensure you're running this script from the project root directory.")
        sys.exit(1)

def create_launcher_script():
    """Create a launcher script for the application"""
    system = platform.system().lower()
    
    print_info("Creating launcher script...")
    
    if system == "windows":
        # Create a .bat file for Windows
        with open("runapp.bat", "w") as f:
            f.write(f"@echo off\n")
            f.write(f"echo Starting Script to Subtitles Converter...\n")
            f.write(f"streamlit run src/app.py\n")
            f.write(f"pause\n")
        
        print_success("Created runapp.bat")
    else:
        # Create a shell script for Unix-like systems
        with open("runapp.sh", "w") as f:
            f.write("#!/bin/bash\n")
            f.write("echo Starting Script to Subtitles Converter...\n")
            f.write("streamlit run src/app.py\n")
        
        # Make it executable
        os.chmod("runapp.sh", 0o755)
        
        print_success("Created runapp.sh")

def main():
    """Main setup function"""
    print_info("""
    ========================================
      Script to Subtitles Converter Setup
    ========================================
    """)
    
    # Check Python version
    python_version = sys.version_info
    if python_version.major < 3 or (python_version.major == 3 and python_version.minor < 8):
        print_error("Python 3.8 or higher is required!")
        sys.exit(1)
    
    print_success(f"Python {python_version.major}.{python_version.minor}.{python_version.micro} detected.")
    
    # Detect operating system
    system = platform.system()
    print_success(f"Operating system: {system}")
    
    # Install FFmpeg
    install_ffmpeg()
    
    # Install dependencies directly
    install_dependencies()
    
    # Create launcher script
    create_launcher_script()
    
    # Finish
    print_info("""
    ============================================
      Setup Complete! To run the application:
    ============================================
    """)
    
    if system == "Windows":
        print_info("  Run the 'runapp.bat' file or execute:")
        print_info("  streamlit run src/app.py")
    else:
        print_info("  Run the 'runapp.sh' file or execute:")
        print_info("  streamlit run src/app.py")
    
    print_info("""
    ============================================
    """)

if __name__ == "__main__":
    main() 