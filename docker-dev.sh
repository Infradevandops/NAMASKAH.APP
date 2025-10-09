#!/bin/bash

# namaskah Docker Development Helper Script

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

# Check if .env file exists
check_env_file() {
    if [ ! -f .env ]; then
        print_warning ".env file not found. Creating from .env.example..."
        if [ -f .env.example ]; then
            cp .env.example .env
            print_success "Created .env file from .env.example"
            print_warning "Please update the API keys in .env file before running the application"
        else
            print_error ".env.example file not found. Please create .env file manually."
            exit 1
        fi
    fi
}

# Build Docker images
build() {
    print_status "Building Docker images..."
    docker-compose build --no-cache
    print_success "Docker images built successfully"
}

# Start services
start() {
    print_status "Starting namaskah services..."
    docker-compose up -d
    print_success "Services started successfully"
    
    print_status "Waiting for services to be ready..."
    sleep 10
    
    # Check health
    health_check
}

# Stop services
stop() {
    print_status "Stopping namaskah services..."
    docker-compose down
    print_success "Services stopped successfully"
}

# Restart services
restart() {
    print_status "Restarting namaskah services..."
    docker-compose restart
    print_success "Services restarted successfully"
}

# View logs
logs() {
    if [ -z "$1" ]; then
        print_status "Showing logs for all services..."
        docker-compose logs -f
    else
        print_status "Showing logs for service: $1"
        docker-compose logs -f "$1"
    fi
}

# Health check
health_check() {
    print_status "Checking service health..."
    
    # Check app health
    if curl -f http://localhost:8000/health > /dev/null 2>&1; then
        print_success "✓ Application is healthy"
    else
        print_error "✗ Application health check failed"
    fi
    
    # Check database
    if docker-compose exec -T db pg_isready -U postgres -d Namaskah.App_db > /dev/null 2>&1; then
        print_success "✓ Database is ready"
    else
        print_error "✗ Database is not ready"
    fi
    
    # Check Redis
    if docker-compose exec -T redis redis-cli ping > /dev/null 2>&1; then
        print_success "✓ Redis is ready"
    else
        print_error "✗ Redis is not ready"
    fi
}

# Clean up everything
clean() {
    print_warning "This will remove all containers, volumes, and images. Are you sure? (y/N)"
    read -r response
    if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
        print_status "Cleaning up Docker resources..."
        docker-compose down -v --rmi all --remove-orphans
        docker system prune -f
        print_success "Cleanup completed"
    else
        print_status "Cleanup cancelled"
    fi
}

# Development mode (with hot reload)
dev() {
    print_status "Starting development mode with hot reload..."
    check_env_file
    docker-compose -f docker-compose.yml -f docker-compose.dev.yml up --build
}

# Production mode
prod() {
    print_status "Starting production mode..."
    check_env_file
    docker-compose --profile production up -d --build
    print_success "Production services started"
    health_check
}

# Show service status
status() {
    print_status "Service status:"
    docker-compose ps
    echo ""
    health_check
}

# Execute command in app container
exec_app() {
    if [ -z "$1" ]; then
        print_status "Opening shell in app container..."
        docker-compose exec app bash
    else
        print_status "Executing command in app container: $*"
        docker-compose exec app "$@"
    fi
}

# Database operations
db_shell() {
    print_status "Opening database shell..."
    docker-compose exec db psql -U postgres -d Namaskah.App_db
}

db_backup() {
    backup_file="backup_$(date +%Y%m%d_%H%M%S).sql"
    print_status "Creating database backup: $backup_file"
    docker-compose exec -T db pg_dump -U postgres Namaskah.App_db > "$backup_file"
    print_success "Database backup created: $backup_file"
}

# Show help
show_help() {
    echo "namaskah Docker Development Helper"
    echo ""
    echo "Usage: $0 [COMMAND]"
    echo ""
    echo "Commands:"
    echo "  build       Build Docker images"
    echo "  start       Start all services"
    echo "  stop        Stop all services"
    echo "  restart     Restart all services"
    echo "  logs [svc]  Show logs (optionally for specific service)"
    echo "  health      Check service health"
    echo "  status      Show service status"
    echo "  clean       Clean up all Docker resources"
    echo "  dev         Start in development mode"
    echo "  prod        Start in production mode"
    echo "  shell       Open shell in app container"
    echo "  exec [cmd]  Execute command in app container"
    echo "  db-shell    Open database shell"
    echo "  db-backup   Create database backup"
    echo "  help        Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 start                 # Start all services"
    echo "  $0 logs app             # Show app logs"
    echo "  $0 exec python --version # Check Python version"
    echo "  $0 dev                  # Start development mode"
}

# Main script logic
case "$1" in
    build)
        check_env_file
        build
        ;;
    start)
        check_env_file
        start
        ;;
    stop)
        stop
        ;;
    restart)
        restart
        ;;
    logs)
        logs "$2"
        ;;
    health)
        health_check
        ;;
    status)
        status
        ;;
    clean)
        clean
        ;;
    dev)
        dev
        ;;
    prod)
        prod
        ;;
    shell)
        exec_app
        ;;
    exec)
        shift
        exec_app "$@"
        ;;
    db-shell)
        db_shell
        ;;
    db-backup)
        db_backup
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        if [ -z "$1" ]; then
            show_help
        else
            print_error "Unknown command: $1"
            echo ""
            show_help
            exit 1
        fi
        ;;
esac