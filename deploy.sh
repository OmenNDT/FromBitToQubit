#!/bin/bash

# Quantum Visualizer 3D - Docker Deployment Script
# This script helps deploy the application using Docker

set -e  # Exit on any error

echo "=============================================="
echo "Quantum Visualizer 3D - Docker Deployment"
echo "=============================================="
echo

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_header() {
    echo -e "${BLUE}=== $1 ===${NC}"
}

# Check if Docker is installed
check_docker() {
    print_header "Checking Prerequisites"
    
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed or not in PATH"
        echo "Please install Docker from: https://docs.docker.com/get-docker/"
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        print_error "Docker Compose is not installed or not in PATH"
        echo "Please install Docker Compose from: https://docs.docker.com/compose/install/"
        exit 1
    fi
    
    print_status "Docker $(docker --version) found"
    print_status "Docker Compose $(docker-compose --version) found"
    
    # Check if Docker daemon is running
    if ! docker info &> /dev/null; then
        print_error "Docker daemon is not running"
        echo "Please start Docker daemon and try again"
        exit 1
    fi
    
    print_status "Docker daemon is running"
}

# Show deployment options
show_options() {
    print_header "Deployment Options"
    echo "1. Simple Version  - Fast build, lightweight (recommended for testing)"
    echo "2. Full Version    - Complete Qiskit integration (production-ready)"
    echo "3. Production      - Full version with Nginx proxy"
    echo "4. Stop Services   - Stop all running containers"
    echo "5. Clean Up        - Remove containers and images"
    echo "6. View Logs       - Show container logs"
    echo "7. Status Check    - Check container status"
    echo
}

# Deploy simple version
deploy_simple() {
    print_header "Deploying Simple Version"
    print_status "Building and starting the simple quantum backend..."
    
    # Stop any existing containers
    docker-compose -f docker-compose.simple.yml down &> /dev/null || true
    
    # Build and start
    docker-compose -f docker-compose.simple.yml up --build -d
    
    print_status "Simple version deployed successfully!"
    print_status "API available at: http://localhost:5000"
    
    # Wait a moment for container to start
    sleep 3
    
    # Test the deployment
    if command -v python3 &> /dev/null; then
        print_status "Running deployment test..."
        python3 test_docker.py || print_warning "Deployment test failed - check container logs"
    else
        print_warning "Python3 not found - skipping automatic test"
        print_status "You can manually test with: curl http://localhost:5000/health"
    fi
}

# Deploy full version
deploy_full() {
    print_header "Deploying Full Version"
    print_warning "This may take 10-15 minutes for first build..."
    print_status "Building and starting the full quantum backend..."
    
    # Stop any existing containers
    docker-compose down &> /dev/null || true
    
    # Build and start
    docker-compose up --build -d
    
    print_status "Full version deployed successfully!"
    print_status "API available at: http://localhost:5000"
    
    # Wait for container to start
    sleep 5
    
    # Test the deployment
    if command -v python3 &> /dev/null; then
        print_status "Running deployment test..."
        python3 test_docker.py || print_warning "Deployment test failed - check container logs"
    else
        print_warning "Python3 not found - skipping automatic test"
        print_status "You can manually test with: curl http://localhost:5000/health"
    fi
}

# Deploy production version
deploy_production() {
    print_header "Deploying Production Version"
    print_warning "This will deploy with Nginx proxy and production settings"
    print_status "Building and starting production deployment..."
    
    # Stop any existing containers
    docker-compose --profile production down &> /dev/null || true
    
    # Build and start with production profile
    docker-compose --profile production up --build -d
    
    print_status "Production version deployed successfully!"
    print_status "API available at: http://localhost:80 (Nginx proxy)"
    print_status "Direct backend: http://localhost:5000"
    
    # Wait for containers to start
    sleep 10
    
    # Test the deployment
    if command -v python3 &> /dev/null; then
        print_status "Testing production deployment..."
        python3 test_docker.py http://localhost:80 || print_warning "Production test failed - check container logs"
    fi
}

# Stop services
stop_services() {
    print_header "Stopping Services"
    
    # Stop all possible configurations
    docker-compose -f docker-compose.simple.yml down &> /dev/null || true
    docker-compose down &> /dev/null || true
    docker-compose --profile production down &> /dev/null || true
    
    print_status "All services stopped"
}

# Clean up
clean_up() {
    print_header "Cleaning Up"
    print_warning "This will remove all containers and images"
    
    read -p "Are you sure? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        # Stop all containers
        stop_services
        
        # Remove images
        docker rmi quantum-visualizer-simple &> /dev/null || true
        docker rmi quantum-visualizer-full &> /dev/null || true
        docker rmi $(docker images -q "vk-5eec-quantum-vi*") &> /dev/null || true
        
        # Clean up unused resources
        docker system prune -f
        
        print_status "Cleanup completed"
    else
        print_status "Cleanup cancelled"
    fi
}

# View logs
view_logs() {
    print_header "Container Logs"
    
    # Check which containers are running
    if docker ps --format "table {{.Names}}" | grep -q "quantum"; then
        echo "Available containers:"
        docker ps --format "table {{.Names}}\t{{.Status}}" | grep quantum || true
        echo
        
        # Show logs for all quantum containers
        for container in $(docker ps --format "{{.Names}}" | grep quantum); do
            print_status "Logs for $container:"
            docker logs --tail 50 "$container"
            echo
        done
    else
        print_warning "No quantum containers are currently running"
        print_status "Use option 1, 2, or 3 to start containers first"
    fi
}

# Check status
check_status() {
    print_header "Container Status"
    
    # Show running containers
    print_status "Running containers:"
    docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | grep -E "(quantum|NAMES)" || echo "No quantum containers running"
    echo
    
    # Show all quantum-related containers (including stopped)
    print_status "All quantum containers:"
    docker ps -a --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | grep -E "(quantum|NAMES)" || echo "No quantum containers found"
    echo
    
    # Test health endpoints if containers are running
    if docker ps --format "{{.Names}}" | grep -q "quantum"; then
        print_status "Testing health endpoints:"
        
        # Test different possible ports
        for port in 5000 80; do
            if curl -s -f "http://localhost:$port/health" &> /dev/null; then
                print_status "✓ Health check passed on port $port"
                curl -s "http://localhost:$port/health" | python3 -m json.tool 2>/dev/null || curl -s "http://localhost:$port/health"
                echo
            else
                print_warning "✗ Health check failed on port $port"
            fi
        done
    fi
}

# Main menu
main_menu() {
    while true; do
        show_options
        read -p "Choose an option (1-7): " choice
        echo
        
        case $choice in
            1)
                deploy_simple
                ;;
            2)
                deploy_full
                ;;
            3)
                deploy_production
                ;;
            4)
                stop_services
                ;;
            5)
                clean_up
                ;;
            6)
                view_logs
                ;;
            7)
                check_status
                ;;
            *)
                print_error "Invalid option. Please choose 1-7."
                ;;
        esac
        
        echo
        read -p "Press Enter to continue or 'q' to quit: " continue
        if [[ $continue == "q" || $continue == "Q" ]]; then
            break
        fi
        echo
    done
}

# Main execution
main() {
    check_docker
    echo
    
    if [[ $# -eq 0 ]]; then
        # Interactive mode
        main_menu
    else
        # Command line mode
        case $1 in
            "simple")
                deploy_simple
                ;;
            "full")
                deploy_full
                ;;
            "production"|"prod")
                deploy_production
                ;;
            "stop")
                stop_services
                ;;
            "clean")
                clean_up
                ;;
            "logs")
                view_logs
                ;;
            "status")
                check_status
                ;;
            "help"|"-h"|"--help")
                echo "Usage: $0 [simple|full|production|stop|clean|logs|status]"
                echo
                echo "Commands:"
                echo "  simple      - Deploy simple version"
                echo "  full        - Deploy full version with Qiskit"
                echo "  production  - Deploy production version with Nginx"
                echo "  stop        - Stop all services"
                echo "  clean       - Clean up containers and images"
                echo "  logs        - View container logs"
                echo "  status      - Check container status"
                echo
                echo "Run without arguments for interactive mode"
                ;;
            *)
                print_error "Unknown command: $1"
                echo "Use '$0 help' for usage information"
                exit 1
                ;;
        esac
    fi
    
    print_status "Deployment script completed"
}

# Run main function
main "$@"