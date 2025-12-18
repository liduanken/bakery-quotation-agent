# Bakery Quotation Agent - Just Commands

# Show available commands
default:
    @just --list

# Run CI tests locally (mimics GitHub Actions)
ci: setup test

# Run all tests with coverage
test:
    pytest tests/ -v --cov=src --cov-report=term-missing --cov-report=html

# Run only unit tests
test-unit:
    pytest tests/unit/ -v

# Run only integration tests
test-integration:
    pytest tests/integration/ -v

# Run only e2e tests
test-e2e:
    pytest tests/e2e/ -v

# Run linting checks
lint:
    @echo "Running code quality checks..."
    black --check src/ tests/
    isort --check-only src/ tests/
    flake8 src/ tests/ --max-line-length=100 --extend-ignore=E203,W503

# Auto-fix code formatting
format:
    black src/ tests/
    isort src/ tests/

# Build Docker images
docker-build:
    docker-compose build

# Start Docker services
docker-up:
    docker-compose up -d

# Stop Docker services
docker-down:
    docker-compose down

# View Docker logs
docker-logs:
    docker-compose logs -f

# Run full Docker stack
docker-run: docker-build docker-up

# Clean up generated files
clean:
    rm -rf .pytest_cache .coverage htmlcov/ __pycache__
    find . -type d -name "__pycache__" -exec rm -rf {} +
    find . -type f -name "*.pyc" -delete

# Install pre-commit hooks
install-hooks:
    ./setup-hooks.sh

# Setup development environment
setup:
    @echo "Installing dependencies..."
    pip install -q -r requirements.txt
