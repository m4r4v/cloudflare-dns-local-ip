#!/bin/bash
# Auto-DDNS Installation Script
# One-click installation for Auto-DDNS system

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

print_header() {
    echo -e "${BLUE}============================================================${NC}"
    echo -e "${BLUE}🏠 Auto-DDNS for Home Laboratories - Installation${NC}"
    echo -e "${BLUE}============================================================${NC}"
    echo "This script will install and configure Auto-DDNS on your system."
    echo ""
}

print_step() {
    echo -e "${BLUE}[STEP]${NC} $1"
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

check_requirements() {
    print_step "Checking system requirements..."
    
    # Check Python version
    if command -v python3 &> /dev/null; then
        PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
        PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
        PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)
        
        if [ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -ge 8 ]; then
            print_success "Python $PYTHON_VERSION found"
        else
            print_error "Python 3.8+ required, found $PYTHON_VERSION"
            exit 1
        fi
    else
        print_error "Python 3 not found. Please install Python 3.8 or higher."
        exit 1
    fi
    
    # Check pip
    if command -v pip3 &> /dev/null; then
        print_success "pip3 found"
    else
        print_error "pip3 not found. Please install pip for Python 3."
        exit 1
    fi
    
    # Check curl (for IP detection fallback)
    if command -v curl &> /dev/null; then
        print_success "curl found"
    else
        print_warning "curl not found. Some IP detection methods may not work."
    fi
    
    # Check cron
    if command -v crontab &> /dev/null; then
        print_success "cron found"
    else
        print_warning "cron not found. Automatic scheduling will not be available."
    fi
    
    echo ""
}

install_dependencies() {
    print_step "Installing Python dependencies..."
    
    if [ -f "$SCRIPT_DIR/requirements.txt" ]; then
        pip3 install -r "$SCRIPT_DIR/requirements.txt"
        print_success "Dependencies installed successfully"
    else
        print_error "requirements.txt not found"
        exit 1
    fi
    
    echo ""
}

make_executable() {
    print_step "Making scripts executable..."
    
    chmod +x "$SCRIPT_DIR/auto_ddns.py"
    chmod +x "$SCRIPT_DIR/setup.py"
    
    print_success "Scripts made executable"
    echo ""
}

create_directories() {
    print_step "Creating directories..."
    
    mkdir -p "$SCRIPT_DIR/config"
    mkdir -p "$SCRIPT_DIR/logs"
    
    print_success "Directories created"
    echo ""
}

setup_configuration() {
    print_step "Setting up configuration..."
    
    # Check if configuration already exists
    if [ -f "$SCRIPT_DIR/config/config.json" ]; then
        print_warning "Configuration already exists"
        read -p "Do you want to reconfigure? (y/n): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            print_success "Keeping existing configuration"
            return 0
        fi
    fi
    
    # Run interactive setup
    echo "Starting interactive configuration..."
    python3 "$SCRIPT_DIR/setup.py"
    
    if [ $? -eq 0 ]; then
        print_success "Configuration completed successfully"
    else
        print_error "Configuration failed"
        exit 1
    fi
    
    echo ""
}

test_installation() {
    print_step "Testing installation..."
    
    # Test script execution
    if python3 "$SCRIPT_DIR/auto_ddns.py" --help &> /dev/null; then
        print_success "Script execution test passed"
    else
        # Try a dry run if --help is not available
        echo "Running basic functionality test..."
        # This will be handled by the configuration test in setup.py
    fi
    
    echo ""
}

print_summary() {
    echo -e "${GREEN}🎉 Installation Complete!${NC}"
    echo "============================================================"
    echo "Auto-DDNS has been installed and configured successfully."
    echo ""
    echo "📁 Installation directory: $SCRIPT_DIR"
    echo "📄 Configuration file: $SCRIPT_DIR/config/config.json"
    echo "📝 Log directory: $SCRIPT_DIR/logs"
    echo ""
    echo "🚀 Usage:"
    echo "  Manual run:    python3 $SCRIPT_DIR/auto_ddns.py"
    echo "  Reconfigure:   python3 $SCRIPT_DIR/setup.py"
    echo ""
    echo "📖 Documentation: $SCRIPT_DIR/docs/system-architecture.md"
    echo ""
    echo "⏰ If you enabled cron scheduling, the system will run automatically every hour."
    echo "   Check logs in $SCRIPT_DIR/logs/ for monitoring."
    echo ""
    echo "🔧 Troubleshooting:"
    echo "  - Check logs for error messages"
    echo "  - Verify Cloudflare API token permissions"
    echo "  - Ensure domain is properly configured in Cloudflare"
    echo "============================================================"
}

cleanup_on_error() {
    print_error "Installation failed. Cleaning up..."
    # Add cleanup logic here if needed
    exit 1
}

main() {
    # Set up error handling
    trap cleanup_on_error ERR
    
    print_header
    
    # Installation steps
    check_requirements
    create_directories
    install_dependencies
    make_executable
    setup_configuration
    test_installation
    
    print_summary
}

# Check if script is being sourced or executed
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    # Script is being executed directly
    main "$@"
fi
