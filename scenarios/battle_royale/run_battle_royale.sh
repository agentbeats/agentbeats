#!/bin/bash

# Battle Royale Runner Script
# Starts the complete battle royale system

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
DOCKER_DIR="docker"
AGENTS_DIR="agents"
TESTS_DIR="tests"
LOG_FILE="battle_royale.log"

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

# Function to check if a port is available
check_port() {
    local port=$1
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        return 0  # Port is in use
    else
        return 1  # Port is available
    fi
}

# Function to wait for service to be ready
wait_for_service() {
    local url=$1
    local service_name=$2
    local max_attempts=30
    local attempt=1
    
    print_status "Waiting for $service_name to be ready..."
    
    while [ $attempt -le $max_attempts ]; do
        if curl -s "$url" >/dev/null 2>&1; then
            print_success "$service_name is ready!"
            return 0
        fi
        
        echo -n "."
        sleep 2
        attempt=$((attempt + 1))
    done
    
    print_error "$service_name failed to start within $((max_attempts * 2)) seconds"
    return 1
}

# Function to kill processes on specific ports
kill_port_processes() {
    local ports=("$@")
    
    for port in "${ports[@]}"; do
        if check_port $port; then
            print_warning "Port $port is in use, killing existing process..."
            lsof -ti:$port | xargs kill -9 2>/dev/null || true
            sleep 1
        fi
    done
}

# Function to check prerequisites
check_prerequisites() {
    print_status "Checking prerequisites..."
    
    # Check if Docker is running
    if ! docker info >/dev/null 2>&1; then
        print_error "Docker is not running. Please start Docker and try again."
        exit 1
    fi
    
    # Check if docker-compose is available
    if ! command -v docker-compose >/dev/null 2>&1; then
        print_error "docker-compose is not installed. Please install it and try again."
        exit 1
    fi
    
    # Check if Python is available
    if ! command -v python3 >/dev/null 2>&1; then
        print_error "Python 3 is not installed. Please install it and try again."
        exit 1
    fi
    
    # Check environment variables
    if [ -z "$OPENAI_API_KEY" ]; then
        print_warning "OPENAI_API_KEY is not set. Please set it for OpenRouter access."
    fi
    
    if [ -z "$OPENAI_API_BASE" ]; then
        print_warning "OPENAI_API_BASE is not set. Please set it for OpenRouter access."
    fi
    
    print_success "Prerequisites check completed"
}

# Function to start Docker arena
start_docker_arena() {
    print_status "Starting Docker battle arena..."
    
    cd "$DOCKER_DIR"
    
    # Stop any existing containers
    docker-compose down >/dev/null 2>&1 || true
    
    # Start the arena
    if docker-compose up -d; then
        print_success "Docker arena started successfully"
        cd ..
        
        # Wait for services to be ready
        wait_for_service "http://localhost:9001/health" "Docker Arena API"
        wait_for_service "http://localhost:9002" "Monitoring Dashboard"
        
        return 0
    else
        print_error "Failed to start Docker arena"
        cd ..
        return 1
    fi
}

# Function to start agents
start_agents() {
    print_status "Starting agents..."
    
    cd "$AGENTS_DIR"
    
    # Kill any existing agent processes
    kill_port_processes 8001 8002 8003 8011
    
    # Start green agent in background
    print_status "Starting green agent..."
    python3 agent_launcher.py green_agent >../green_agent.log 2>&1 &
    GREEN_AGENT_PID=$!
    echo $GREEN_AGENT_PID > ../green_agent.pid
    
    # Wait for green agent to start
    wait_for_service "http://localhost:8011/.well-known/agent.json" "Green Agent"
    
    # Start red agents in background with correct ports
    red_agent_ports=(8001 8002 8020)  # Match green agent expectations
    for i in {0..2}; do
        port=${red_agent_ports[$i]}
        print_status "Starting red agent $((i+1)) on port $port..."
        python3 agent_launcher.py red_agent --port $port >../red_agent_$((i+1)).log 2>&1 &
        RED_AGENT_PID=$!
        echo $RED_AGENT_PID > ../red_agent_$((i+1)).pid
        
        # Wait for red agent to start (child port is BASE_PORT + 1)
        child_port=$((port + 1))
        wait_for_service "http://localhost:$child_port/.well-known/agent.json" "Red Agent $((i+1))"
    done
    
    cd ..
    print_success "All agents started successfully"
}

# Function to run tests
run_tests() {
    print_status "Running system tests..."
    
    cd "$TESTS_DIR"
    
    if python3 test_battle_royale_comprehensive.py; then
        print_success "All tests passed!"
        cd ..
        return 0
    else
        print_warning "Some tests failed. Check test_results.json for details."
        cd ..
        return 1
    fi
}

# Function to start battle
start_battle() {
    print_status "Starting battle royale simulation..."
    
    if python3 battle_orchestrator.py; then
        print_success "Battle royale simulation completed successfully!"
        return 0
    else
        print_error "Battle royale simulation failed. Check logs for details."
        return 1
    fi
}

# Function to show status
show_status() {
    print_status "System Status:"
    echo
    
    # Check Docker services
    echo "🐳 Docker Services:"
    if docker-compose -f "$DOCKER_DIR/docker-compose.yml" ps | grep -q "Up"; then
        print_success "Docker arena is running"
    else
        print_error "Docker arena is not running"
    fi
    
    # Check agents
    echo
    echo "🤖 Agents:"
    for port in 8011 8001 8002 8003; do
        if check_port $port; then
            print_success "Agent on port $port is running"
        else
            print_error "Agent on port $port is not running"
        fi
    done
    
    # Check services
    echo
    echo "🌐 Services:"
    if curl -s "http://localhost:9001/health" >/dev/null 2>&1; then
        print_success "Docker arena API is accessible"
    else
        print_error "Docker arena API is not accessible"
    fi
    
    if curl -s "http://localhost:9002" >/dev/null 2>&1; then
        print_success "Monitoring dashboard is accessible"
    else
        print_error "Monitoring dashboard is not accessible"
    fi
}

# Function to cleanup
cleanup() {
    print_status "Cleaning up..."
    
    # Kill agent processes
    for pid_file in green_agent.pid red_agent_*.pid; do
        if [ -f "$pid_file" ]; then
            pid=$(cat "$pid_file")
            kill $pid 2>/dev/null || true
            rm -f "$pid_file"
        fi
    done
    
    # Stop Docker services
    cd "$DOCKER_DIR"
    docker-compose down >/dev/null 2>&1 || true
    cd ..
    
    print_success "Cleanup completed"
}

# Function to show help
show_help() {
    echo "Battle Royale Runner Script"
    echo
    echo "Usage: $0 [COMMAND]"
    echo
    echo "Commands:"
    echo "  start     Start the complete battle royale system"
    echo "  stop      Stop all services and cleanup"
    echo "  status    Show current system status"
    echo "  test      Run system tests"
    echo "  battle    Start the battle simulation"
    echo "  help      Show this help message"
    echo
    echo "Examples:"
    echo "  $0 start    # Start everything"
    echo "  $0 status   # Check what's running"
    echo "  $0 stop     # Stop everything"
}

# Main script logic
case "${1:-start}" in
    "start")
        print_status "Starting Battle Royale System..."
        check_prerequisites
        start_docker_arena
        start_agents
        run_tests
        print_success "Battle Royale system is ready!"
        print_status "Access monitoring dashboard at: http://localhost:9002"
        print_status "Run '$0 battle' to start the simulation"
        ;;
    "stop")
        cleanup
        ;;
    "status")
        show_status
        ;;
    "test")
        run_tests
        ;;
    "battle")
        start_battle
        ;;
    "help"|"-h"|"--help")
        show_help
        ;;
    *)
        print_error "Unknown command: $1"
        show_help
        exit 1
        ;;
esac 