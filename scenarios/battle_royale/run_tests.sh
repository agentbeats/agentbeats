#!/bin/bash

# Battle Royale Test Runner
# This script runs the battle royale tests and provides a simple interface

set -e

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

# Check if we're in the right directory
if [ ! -f "test_battle_royale.py" ]; then
    print_error "Please run this script from the battle_royale directory"
    exit 1
fi

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    print_error "Docker is not installed. Please install Docker first."
    exit 1
fi

# Check if docker-compose is installed
if ! command -v docker-compose &> /dev/null; then
    print_error "docker-compose is not installed. Please install docker-compose first."
    exit 1
fi

# Function to install Python dependencies
install_dependencies() {
    print_status "Installing Python dependencies..."
    if [ -f "requirements.txt" ]; then
        pip install -r requirements.txt
        print_success "Dependencies installed"
    else
        print_warning "No requirements.txt found, skipping dependency installation"
    fi
}

# Function to build and start the container
start_container() {
    print_status "Building and starting battle royale container..."
    cd docker
    docker-compose up --build -d
    cd ..
    print_success "Container started"
}

# Function to stop the container
stop_container() {
    print_status "Stopping battle royale container..."
    cd docker
    docker-compose down
    cd ..
    print_success "Container stopped"
}

# Function to run the tests
run_tests() {
    print_status "Running battle royale tests..."
    python3 test_battle_royale.py
}

# Function to show container status
show_status() {
    print_status "Container status:"
    cd docker
    docker-compose ps
    cd ..
}

# Function to show logs
show_logs() {
    print_status "Container logs:"
    cd docker
    docker-compose logs
    cd ..
}

# Function to show help
show_help() {
    echo "Battle Royale Test Runner"
    echo ""
    echo "Usage: $0 [COMMAND]"
    echo ""
    echo "Commands:"
    echo "  install     Install Python dependencies"
    echo "  start       Build and start the container"
    echo "  stop        Stop the container"
    echo "  test        Run the test suite"
    echo "  status      Show container status"
    echo "  logs        Show container logs"
    echo "  full        Install dependencies, start container, and run tests"
    echo "  help        Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 full     # Complete setup and test"
    echo "  $0 test     # Run tests only (assumes container is running)"
    echo "  $0 stop     # Stop the container"
}

# Main script logic
case "${1:-help}" in
    "install")
        install_dependencies
        ;;
    "start")
        start_container
        ;;
    "stop")
        stop_container
        ;;
    "test")
        run_tests
        ;;
    "status")
        show_status
        ;;
    "logs")
        show_logs
        ;;
    "full")
        print_status "Running full setup and test..."
        install_dependencies
        start_container
        sleep 5  # Wait for container to be ready
        run_tests
        ;;
    "help"|*)
        show_help
        ;;
esac 