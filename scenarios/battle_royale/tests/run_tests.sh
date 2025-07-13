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
if [ ! -f "test_battle_royale_infrastructure.py" ]; then
    print_error "Please run this script from the tests directory"
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
    if [ -f "../requirements.txt" ]; then
        pip install -r ../requirements.txt
        print_success "Dependencies installed"
    else
        print_warning "No requirements.txt found, skipping dependency installation"
    fi
}

# Function to build and start the container
start_container() {
    print_status "Building and starting battle royale container..."
    cd ../docker
    docker-compose up --build -d
    cd ../tests
    print_success "Container started"
}

# Function to stop the container
stop_container() {
    print_status "Stopping battle royale container..."
    cd ../docker
    docker-compose down
    cd ../tests
    print_success "Container stopped"
}

# Function to run the tests
run_tests() {
    local test_type="${1:-all}"
    
    case "$test_type" in
        "all")
            print_status "Running all battle royale tests..."
            echo ""
            print_status "1. Running agent structure tests..."
            python3 test_agent_basics.py
            echo ""
            print_status "2. Running battle royale infrastructure tests..."
            python3 test_battle_royale_infrastructure.py
            echo ""
            print_status "3. Running agent interaction tests..."
            python3 test_battle_royale_agents.py
            ;;
        "basics")
            print_status "Running agent structure tests..."
            python3 test_agent_basics.py
            ;;
        "infrastructure")
            print_status "Running battle royale infrastructure tests..."
            python3 test_battle_royale_infrastructure.py
            ;;
        "agents")
            print_status "Running agent interaction tests..."
            python3 test_battle_royale_agents.py
            ;;
        *)
            print_error "Unknown test type: $test_type"
            print_status "Available test types: all, basics, infrastructure, agents"
            exit 1
            ;;
    esac
}

# Function to show container status
show_status() {
    print_status "Container status:"
    cd ../docker
    docker-compose ps
    cd ../tests
}

# Function to show logs
show_logs() {
    print_status "Container logs:"
    cd ../docker
    docker-compose logs
    cd ../tests
}

# Function to show help
show_help() {
    echo "Battle Royale Test Runner"
    echo ""
    echo "Usage: $0 [COMMAND] [OPTIONS]"
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
    echo "Test Types (for 'test' command):"
    echo "  all         Run all tests (default)"
    echo "  basics      Run only agent structure tests"
    echo "  infrastructure  Run only battle royale infrastructure tests"
    echo "  agents      Run only agent interaction tests"
    echo ""
    echo "Examples:"
    echo "  $0 full                    # Complete setup and all tests"
    echo "  $0 test                    # Run all tests (assumes container is running)"
    echo "  $0 test basics             # Run only agent structure tests"
    echo "  $0 test infrastructure     # Run only infrastructure tests"
    echo "  $0 test agents             # Run only agent interaction tests"
    echo "  $0 stop                    # Stop the container"
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
        run_tests "$2"
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
        run_tests "all"
        ;;
    "help"|*)
        show_help
        ;;
esac 