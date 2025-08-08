#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_header() {
    echo -e "${BLUE}================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}================================${NC}"
}

print_section() {
    echo -e "${CYAN}--- $1 ---${NC}"
}

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to validate and create required directories and files
validate_and_create() {
    print_section "Validating and Creating Required Structure"
    
    local required_dirs=(
        "backend"
        "backend/models"
        "backend/utils"
        "tests"
    )
    
    # Create directories
    for dir in "${required_dirs[@]}"; do
        if [[ ! -d "$dir" ]]; then
            print_warning "Directory '$dir' not found!"
            print_status "Creating directory '$dir'..."
            mkdir -p "$dir"
            print_status "✓ Directory '$dir' created"
        else
            print_status "✓ Directory '$dir' exists"
        fi
    done
    
    # Check and create required files with basic templates
    local files_to_check=(
        "docker-compose.yml"
        "backend/Dockerfile"
        "backend/requirements.txt"
        "backend/main.py"
        "backend/config.py"
        "backend/chunker.py"
        "backend/summarizer.py"
        "backend/embedder.py"
        "backend/vector_store.py"
        "backend/db.py"
        "backend/ingest.py"
        "backend/models/project.py"
        "backend/models/chunk.py"
        "backend/models/file.py"
        "backend/utils/file_utils.py"
        "backend/Modelfile"
        "tests/test_system.py"
        "tests/run_tests.sh"
        "tests/README.md"
        "README.md"
        ".gitignore"
    )
    
    for file in "${files_to_check[@]}"; do
        if [[ ! -f "$file" ]]; then
            print_warning "File '$file' not found!"
            print_status "This file is required for the system to work properly."
            print_status "Please ensure all project files are present before starting."
            print_error "Missing critical file: $file"
            print_status "Please clone the repository from GitHub or restore missing files."
            return 1
        else
            print_status "✓ File '$file' exists"
        fi
    done
    
    print_status "All required directories and files validated!"
    return 0
}

# Function to check Docker status
check_docker() {
    print_section "Checking Docker Status"
    
    if ! command_exists docker; then
        print_error "Docker is not installed!"
        print_status "Please install Docker first: https://docs.docker.com/get-docker/"
        exit 1
    fi
    
    if ! docker info > /dev/null 2>&1; then
        print_error "Docker is not running!"
        print_status "Please start Docker daemon first"
        exit 1
    fi
    
    if ! command_exists docker; then
        print_error "Docker Compose is not available!"
        print_status "Please install Docker Compose"
        exit 1
    fi
    
    print_status "✓ Docker is running and available"
    print_status "✓ Docker Compose is available"
}

# Function to clean up Docker resources
cleanup_docker() {
    print_section "Cleaning Up Docker Resources"
    
    print_status "Stopping all containers..."
    docker compose down
    
    print_status "Removing unused images..."
    docker image prune -f
    
    print_status "Removing unused volumes..."
    docker volume prune -f
    
    print_status "Cleaning up build cache..."
    docker builder prune -f
    
    print_status "✓ Docker cleanup completed"
}

# Function to download and setup models
setup_models() {
    print_section "Setting Up AI Models"
    
    print_status "Starting Ollama service..."
    docker compose up -d ollama
    
    print_status "Waiting for Ollama to be ready..."
    sleep 10
    
    # Check if model already exists
    if docker compose exec ollama ollama list | grep -q "codellama-q"; then
        print_status "✓ Model 'codellama-q' already exists"
    else
        print_status "Creating optimized model 'codellama-q'..."
        docker compose cp backend/Modelfile ollama:/Modelfile
        docker compose exec ollama ollama create codellama-q -f /Modelfile
        
        if [[ $? -eq 0 ]]; then
            print_status "✓ Model 'codellama-q' created successfully"
        else
            print_error "Failed to create model!"
            return 1
        fi
    fi
    
    print_status "✓ AI models setup completed"
}

# Function to check if images need to be rebuilt
check_images() {
    print_section "Checking Docker Images"
    
    # Check if backend image exists
    if ! docker images | grep -q "new-backend"; then
        print_warning "Backend image not found!"
        print_status "Building backend service..."
        docker compose build --no-cache backend
        if [[ $? -ne 0 ]]; then
            print_error "Failed to build backend image!"
            return 1
        fi
    else
        print_status "✓ Backend image exists"
    fi
    
    # Check if other service images exist
    local services=("postgres" "qdrant" "ollama")
    for service in "${services[@]}"; do
        if ! docker images | grep -q "$service"; then
            print_warning "$service image not found, pulling..."
            docker compose pull "$service"
        else
            print_status "✓ $service image exists"
        fi
    done
}

# Function to start all services
start_services() {
    print_section "Starting All Services"
    
    # Check and build images if needed
    check_images
    
    print_status "Starting PostgreSQL and Qdrant..."
    docker compose up -d postgres qdrant
    
    print_status "Waiting for databases to initialize..."
    sleep 15
    
    print_status "Starting backend service..."
    docker compose up -d backend
    
    print_status "Waiting for backend to be ready..."
    sleep 10
}

# Function to check service health
check_health() {
    print_section "Checking Service Health"
    
    local max_attempts=30
    local attempt=1
    
    while [[ $attempt -le $max_attempts ]]; do
        print_status "Checking health endpoint... (attempt $attempt/$max_attempts)"
        
        if curl -s http://localhost:8000/health > /dev/null 2>&1; then
            print_status "✓ All services are healthy!"
            return 0
        fi
        
        if [[ $attempt -eq $max_attempts ]]; then
            print_error "Services failed to start properly after $max_attempts attempts"
            print_status "Checking service logs..."
            docker compose logs --tail 50
            return 1
        fi
        
        print_warning "Services not ready yet, waiting 10 seconds..."
        sleep 10
        ((attempt++))
    done
}

# Function to show system status
show_status() {
    print_section "System Status"
    
    print_status "Container Status:"
    docker compose ps
    
    echo ""
    print_status "Service Health:"
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        print_status "✓ Backend API is responding"
    else
        print_error "✗ Backend API is not responding"
    fi
    
    echo ""
    print_status "Model Status:"
    docker compose exec ollama ollama list 2>/dev/null || print_error "Cannot check model status"
    
    echo ""
    print_status "Database Status:"
    if docker compose exec postgres pg_isready -U user -d codebase_db > /dev/null 2>&1; then
        print_status "✓ PostgreSQL is ready"
    else
        print_error "✗ PostgreSQL is not ready"
    fi
    
    if curl -s http://localhost:6333/collections > /dev/null 2>&1; then
        print_status "✓ Qdrant is ready"
    else
        print_error "✗ Qdrant is not ready"
    fi
}

# Function to show logs
show_logs() {
    print_section "Service Logs"
    
    local service=${1:-"all"}
    
    case $service in
        "backend")
            docker compose logs -f backend
            ;;
        "ollama")
            docker compose logs -f ollama
            ;;
        "postgres")
            docker compose logs -f postgres
            ;;
        "qdrant")
            docker compose logs -f qdrant
            ;;
        "all"|*)
            docker compose logs -f
            ;;
    esac
}

# Function to run tests
run_tests() {
    print_section "Running System Tests"
    
    if [[ ! -f "tests/test_system.py" ]]; then
        print_error "Test file not found!"
        return 1
    fi
    
    print_status "Running system tests..."
    python3 tests/test_system.py
    
    if [[ $? -eq 0 ]]; then
        print_status "✓ All tests passed!"
    else
        print_error "✗ Some tests failed!"
        return 1
    fi
}

# Function to stop services
stop_services() {
    print_section "Stopping Services"
    
    print_status "Stopping all containers..."
    docker compose down
    
    print_status "✓ All services stopped"
}

# Function to build services with no-cache
build_services() {
    print_section "Building Services (No Cache)"
    
    print_status "Building backend service with no-cache..."
    docker compose build --no-cache backend
    
    if [[ $? -eq 0 ]]; then
        print_status "✓ Backend service built successfully"
    else
        print_error "✗ Failed to build backend service"
        return 1
    fi
    
    print_status "✓ All services built successfully"
}

# Function to rebuild all services
rebuild_services() {
    print_section "Rebuilding All Services (No Cache)"
    
    print_status "Stopping all services..."
    docker compose down
    
    print_status "Removing all images..."
    docker compose down --rmi all
    
    print_status "Building all services with no-cache..."
    docker compose build --no-cache
    
    if [[ $? -eq 0 ]]; then
        print_status "✓ All services rebuilt successfully"
    else
        print_error "✗ Failed to rebuild services"
        return 1
    fi
}

# Function to restart services
restart_services() {
    print_section "Restarting Services"
    
    stop_services
    sleep 5
    start_services
    check_health
}

# Function to show help
show_help() {
    print_header "CodebaseAI Management Script"
    echo ""
    echo "Usage: $0 [COMMAND]"
    echo ""
    echo "Commands:"
    echo "  start       - Start all services (default)"
    echo "  stop        - Stop all services"
    echo "  restart     - Restart all services"
    echo "  build       - Build services with no-cache"
    echo "  rebuild     - Rebuild all services with no-cache"
    echo "  status      - Show system status"
    echo "  logs        - Show service logs"
    echo "  logs [SERVICE] - Show logs for specific service (backend|ollama|postgres|qdrant)"
    echo "  test        - Run system tests"
    echo "  cleanup     - Clean up Docker resources"
    echo "  models      - Setup AI models only"
    echo "  validate    - Validate directories and files"
    echo "  help        - Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 start          # Start all services"
    echo "  $0 build          # Build services with no-cache"
    echo "  $0 rebuild        # Rebuild all services with no-cache"
    echo "  $0 logs backend   # Show backend logs"
    echo "  $0 status         # Check system status"
    echo "  $0 test           # Run tests"
    echo ""
}

# Main script logic
main() {
    local command=${1:-"start"}
    
    case $command in
        "start")
            print_header "Starting CodebaseAI System"
            validate_and_create
            if [[ $? -ne 0 ]]; then
                print_error "Validation failed! Please ensure all required files are present."
                exit 1
            fi
            check_docker
            setup_models
            start_services
            check_health
            if [[ $? -eq 0 ]]; then
                print_header "System Started Successfully!"
                echo ""
                echo -e "${GREEN}🎉 CodebaseAI is ready!${NC}"
                echo ""
                echo "🌐 API: http://localhost:8000"
                echo "📚 Docs: http://localhost:8000/docs"
                echo "🔍 Health: http://localhost:8000/health"
                echo ""
                echo "📋 Quick Commands:"
                echo "  $0 status    # Check system status"
                echo "  $0 logs      # View logs"
                echo "  $0 test      # Run tests"
                echo "  $0 stop      # Stop services"
                echo ""
            else
                print_error "Failed to start system properly!"
                exit 1
            fi
            ;;
        "stop")
            stop_services
            ;;
        "restart")
            restart_services
            ;;
        "build")
            check_docker
            build_services
            ;;
        "rebuild")
            check_docker
            rebuild_services
            ;;
        "status")
            show_status
            ;;
        "logs")
            show_logs "$2"
            ;;
        "test")
            run_tests
            ;;
        "cleanup")
            cleanup_docker
            ;;
        "models")
            check_docker
            setup_models
            ;;
        "validate")
            validate_and_create
            ;;
        "help"|"-h"|"--help")
            show_help
            ;;
        *)
            print_error "Unknown command: $command"
            show_help
            exit 1
            ;;
    esac
}

# Run main function with all arguments
main "$@"
