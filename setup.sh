#!/bin/bash

"""NOTE: this file was automatically generated using the help of AI, and as thus may contain one or more errors."""

# AgentBeats Setup Script
# This script automatically sets up the AgentBeats environment including:
# - Prerequisites checking
# - Environment variable setup
# - Virtual environment creation
# - Dependency installation
# - Optional service startup

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
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

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to check Python version
check_python_version() {
    if command_exists python3; then
        python_version=$(python3 --version 2>&1 | awk '{print $2}' | cut -d. -f1,2)
        required_version="3.8"
        if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" = "$required_version" ]; then
            print_success "Python $python_version found"
            return 0
        else
            print_error "Python $python_version found, but Python 3.8+ is required"
            return 1
        fi
    else
        print_error "Python 3 not found"
        return 1
    fi
}

# Function to check Node.js version
check_node_version() {
    if command_exists node; then
        node_version=$(node --version | cut -d'v' -f2 | cut -d. -f1,2)
        required_version="18.0"
        if [ "$(printf '%s\n' "$required_version" "$node_version" | sort -V | head -n1)" = "$required_version" ]; then
            print_success "Node.js $node_version found"
            return 0
        else
            print_error "Node.js $node_version found, but Node.js 18+ is required"
            return 1
        fi
    else
        print_error "Node.js not found"
        return 1
    fi
}

# Parse command line arguments
API_KEY=""
API_BASE="https://openrouter.ai/api/v1"
START_SERVICES=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --api-key)
            API_KEY="$2"
            shift 2
            ;;
        --api-base)
            API_BASE="$2"
            shift 2
            ;;
        --start-services)
            START_SERVICES=true
            shift
            ;;
        -h|--help)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --api-key KEY       Set your OpenRouter API key"
            echo "  --api-base URL      Set API base URL (default: https://openrouter.ai/api/v1)"
            echo "  --start-services    Start all services after setup"
            echo "  -h, --help          Show this help message"
            echo ""
            echo "Examples:"
            echo "  $0 --api-key your-key-here"
            echo "  $0 --api-key your-key-here --start-services"
            exit 0
            ;;
        *)
            print_error "Unknown option: $1"
            echo "Use -h or --help for usage information"
            exit 1
            ;;
    esac
done

print_status "Starting AgentBeats setup..."

# Check prerequisites
print_status "Checking prerequisites..."

# Check Python
if ! check_python_version; then
    print_error "Please install Python 3.8+ and try again"
    exit 1
fi

# Check Node.js
if ! check_node_version; then
    print_error "Please install Node.js 18+ and try again"
    exit 1
fi

# Check npm
if ! command_exists npm; then
    print_error "npm not found. Please install Node.js with npm and try again"
    exit 1
fi

# Check Docker
if ! command_exists docker; then
    print_warning "Docker not found. Some features may not work properly"
else
    print_success "Docker found"
fi

# Check Docker Compose
if ! command_exists docker-compose && ! docker compose version >/dev/null 2>&1; then
    print_warning "Docker Compose not found. Some features may not work properly"
else
    print_success "Docker Compose found"
fi

# Check tmux
if ! command_exists tmux; then
    print_warning "tmux not found. Please install tmux for better service management"
else
    print_success "tmux found"
fi

# Check pm2
if ! command_exists pm2; then
    print_warning "pm2 not found. Please install pm2 for process management: npm install -g pm2"
else
    print_success "pm2 found"
fi

# Check nginx
if ! command_exists nginx; then
    print_warning "nginx not found. Please install nginx for web server functionality"
else
    print_success "nginx found"
fi

# Get API key if not provided
if [ -z "$API_KEY" ]; then
    echo ""
    print_status "Please enter your OpenRouter API key:"
    read -s API_KEY
    echo ""
    
    if [ -z "$API_KEY" ]; then
        print_error "API key is required"
        exit 1
    fi
fi

# Set environment variables
print_status "Setting up environment variables..."
export OPENAI_API_KEY="$API_KEY"
export OPENAI_API_BASE="$API_BASE"

# Add to shell profile for persistence
SHELL_PROFILE=""
if [ -f "$HOME/.bashrc" ]; then
    SHELL_PROFILE="$HOME/.bashrc"
elif [ -f "$HOME/.zshrc" ]; then
    SHELL_PROFILE="$HOME/.zshrc"
elif [ -f "$HOME/.profile" ]; then
    SHELL_PROFILE="$HOME/.profile"
fi

if [ -n "$SHELL_PROFILE" ]; then
    # Check if variables are already set
    if ! grep -q "OPENAI_API_KEY" "$SHELL_PROFILE"; then
        echo "" >> "$SHELL_PROFILE"
        echo "# AgentBeats environment variables" >> "$SHELL_PROFILE"
        echo "export OPENAI_API_KEY=\"$API_KEY\"" >> "$SHELL_PROFILE"
        echo "export OPENAI_API_BASE=\"$API_BASE\"" >> "$SHELL_PROFILE"
        print_success "Environment variables added to $SHELL_PROFILE"
    else
        print_warning "Environment variables already exist in $SHELL_PROFILE"
    fi
fi

# Create virtual environment
print_status "Setting up Python virtual environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    print_success "Virtual environment created"
else
    print_warning "Virtual environment already exists"
fi

# Activate virtual environment and install dependencies
print_status "Installing Python dependencies..."
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
print_success "Python dependencies installed"

# Install frontend dependencies
print_status "Installing frontend dependencies..."
cd webapp
npm install
cd ..
print_success "Frontend dependencies installed"

# Create logs directory
print_status "Creating logs directory..."
mkdir -p logs
print_success "Logs directory created"

print_success "Setup completed successfully!"

# Show next steps
echo ""
print_status "Next steps:"
echo "  • Your API key and base URL have been set"
echo "  • Virtual environment is ready at: ./venv"
echo "  • Python dependencies are installed"
echo "  • Frontend dependencies are installed"
echo ""
echo "To start all services, run:"
echo "  ./start-server.sh"
echo ""
echo "Or to start services now, run this script with --start-services flag"

# Start services if requested
if [ "$START_SERVICES" = true ]; then
    echo ""
    print_status "Starting services..."
    if [ -f "start-server.sh" ]; then
        chmod +x start-server.sh
        ./start-server.sh
    else
        print_error "start-server.sh not found"
        exit 1
    fi
fi 