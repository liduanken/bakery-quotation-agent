#!/bin/bash

# Bakery Quotation System - Google Cloud Run Deployment Script
# Deploys both FastAPI backend and Next.js frontend to Cloud Run

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_ID="${GOOGLE_CLOUD_PROJECT_ID:-ktp-loughborough-university}"
BACKEND_SERVICE="${BACKEND_SERVICE:-bakery-api}"
FRONTEND_SERVICE="${FRONTEND_SERVICE:-bakery-frontend}"
REGION="${GOOGLE_CLOUD_REGION:-europe-west2}"
BACKEND_MEMORY="${BACKEND_MEMORY:-2Gi}"
BACKEND_CPU="${BACKEND_CPU:-2}"
FRONTEND_MEMORY="${FRONTEND_MEMORY:-1Gi}"
FRONTEND_CPU="${FRONTEND_CPU:-1}"
MAX_INSTANCES="${MAX_INSTANCES:-10}"

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

# Function to check if gcloud is installed
check_gcloud() {
    if ! command -v gcloud &> /dev/null; then
        print_error "gcloud CLI is not installed. Please install it first:"
        echo "  curl https://sdk.cloud.google.com | bash"
        echo "  exec -l \$SHELL"
        echo "  gcloud init"
        exit 1
    fi
    print_success "gcloud CLI is installed"
}

# Function to setup project
setup_project() {
    print_status "Setting project to: $PROJECT_ID"
    gcloud config set project $PROJECT_ID
    
    if [ $? -ne 0 ]; then
        print_error "Failed to set project. Please check your project ID."
        exit 1
    fi
    
    print_success "Project set to: $PROJECT_ID"
}

# Function to enable required APIs
enable_apis() {
    print_status "Enabling required Google Cloud APIs..."
    
    apis=(
        "cloudbuild.googleapis.com"
        "run.googleapis.com"
        "containerregistry.googleapis.com"
        "artifactregistry.googleapis.com"
    )
    
    for api in "${apis[@]}"; do
        print_status "Enabling $api..."
        gcloud services enable $api --quiet
        if [ $? -eq 0 ]; then
            print_success "Enabled $api"
        else
            print_error "Failed to enable $api"
            exit 1
        fi
    done
}

# Function to check if billing is enabled
check_billing() {
    print_status "Checking if billing is enabled..."
    
    BILLING_ENABLED=$(gcloud beta billing projects describe $PROJECT_ID --format="value(billingEnabled)" 2>/dev/null || echo "false")
    
    if [ "$BILLING_ENABLED" != "True" ]; then
        print_warning "Billing is not enabled for this project."
        print_warning "Please enable billing in the Google Cloud Console:"
        print_warning "https://console.cloud.google.com/billing/linkedaccount?project=$PROJECT_ID"
        read -p "Press Enter after enabling billing to continue..."
    else
        print_success "Billing is enabled"
    fi
}

# Function to create backend Dockerfile
create_backend_dockerfile() {
    print_status "Creating Dockerfile for backend..."
    
    cat > Dockerfile.backend << 'EOF'
# Use Python 3.10
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create output directory
RUN mkdir -p output

# Expose port
EXPOSE 8001

# Run the application
CMD ["uvicorn", "src.app.main:app", "--host", "0.0.0.0", "--port", "8001"]
EOF

    print_success "Backend Dockerfile created"
}

# Function to create frontend Dockerfile
create_frontend_dockerfile() {
    print_status "Creating Dockerfile for frontend..."
    
    cat > frontend/Dockerfile << 'EOF'
# Use Node.js 18 Alpine
FROM node:18-alpine

# Set working directory
WORKDIR /app

# Install dependencies for node-gyp
RUN apk add --no-cache libc6-compat

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm install

# Copy the application source
COPY . .

# Set environment variables
ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1
ENV PORT=3000

# Build the application
RUN npm run build

# Create non-root user
RUN addgroup -g 1001 -S nodejs
RUN adduser -S nextjs -u 1001

# Change ownership
RUN chown -R nextjs:nodejs /app
USER nextjs

# Expose port
EXPOSE 3000

# Start the application
CMD ["npm", "start"]
EOF

    print_success "Frontend Dockerfile created"
}

# Function to deploy backend
deploy_backend() {
    print_status "Deploying backend to Cloud Run..."
    
    # Create Dockerfile if it doesn't exist
    if [ ! -f "Dockerfile.backend" ]; then
        create_backend_dockerfile
    fi
    
    # Check for .env file
    if [ ! -f ".env" ]; then
        print_warning ".env file not found. Make sure to set environment variables."
    fi
    
    # Build and deploy
    gcloud run deploy $BACKEND_SERVICE \
        --source . \
        --dockerfile Dockerfile.backend \
        --platform managed \
        --region $REGION \
        --allow-unauthenticated \
        --port 8001 \
        --memory $BACKEND_MEMORY \
        --cpu $BACKEND_CPU \
        --max-instances $MAX_INSTANCES \
        --set-env-vars "OPENAI_API_KEY=${OPENAI_API_KEY:-},BOM_API_URL=http://localhost:8000,DATABASE_PATH=resources/materials.sqlite"
    
    if [ $? -eq 0 ]; then
        BACKEND_URL=$(gcloud run services describe $BACKEND_SERVICE --region $REGION --format="value(status.url)")
        print_success "Backend deployed successfully at: $BACKEND_URL"
        echo $BACKEND_URL > .backend_url
    else
        print_error "Backend deployment failed!"
        exit 1
    fi
}

# Function to deploy frontend
deploy_frontend() {
    print_status "Deploying frontend to Cloud Run..."
    
    # Get backend URL
    if [ -f ".backend_url" ]; then
        BACKEND_URL=$(cat .backend_url)
    else
        print_error "Backend URL not found. Please deploy backend first."
        exit 1
    fi
    
    # Navigate to frontend directory
    if [ ! -d "frontend" ]; then
        print_error "frontend directory not found."
        exit 1
    fi
    
    cd frontend
    
    # Create Dockerfile if it doesn't exist
    if [ ! -f "Dockerfile" ]; then
        create_frontend_dockerfile
    fi
    
    # Update the API URL in the frontend config
    print_status "Configuring frontend to use backend URL: $BACKEND_URL"
    
    # Deploy
    gcloud run deploy $FRONTEND_SERVICE \
        --source . \
        --platform managed \
        --region $REGION \
        --allow-unauthenticated \
        --port 3000 \
        --memory $FRONTEND_MEMORY \
        --cpu $FRONTEND_CPU \
        --max-instances $MAX_INSTANCES \
        --set-env-vars "NEXT_PUBLIC_API_URL=$BACKEND_URL,NODE_ENV=production,NEXT_TELEMETRY_DISABLED=1"
    
    if [ $? -eq 0 ]; then
        FRONTEND_URL=$(gcloud run services describe $FRONTEND_SERVICE --region $REGION --format="value(status.url)")
        print_success "Frontend deployed successfully at: $FRONTEND_URL"
    else
        print_error "Frontend deployment failed!"
        cd ..
        exit 1
    fi
    
    cd ..
}

# Function to show deployment info
show_deployment_info() {
    print_status "Getting deployment information..."
    echo
    echo "=== Deployment Information ==="
    echo
    echo "Backend Service:"
    gcloud run services describe $BACKEND_SERVICE --region $REGION --format="table(
        metadata.name,
        status.url,
        status.conditions[0].status
    )" 2>/dev/null || print_warning "Backend not deployed"
    
    echo
    echo "Frontend Service:"
    gcloud run services describe $FRONTEND_SERVICE --region $REGION --format="table(
        metadata.name,
        status.url,
        status.conditions[0].status
    )" 2>/dev/null || print_warning "Frontend not deployed"
    
    echo
    echo "🔧 Management commands:"
    echo "   View backend logs: gcloud run services logs read $BACKEND_SERVICE --region=$REGION"
    echo "   View frontend logs: gcloud run services logs read $FRONTEND_SERVICE --region=$REGION"
    echo "   Update: Re-run this script"
    echo "   Delete backend: gcloud run services delete $BACKEND_SERVICE --region=$REGION"
    echo "   Delete frontend: gcloud run services delete $FRONTEND_SERVICE --region=$REGION"
}

# Main deployment function
main() {
    echo "================================================================"
    echo "   Bakery Quotation System - Google Cloud Run Deployment"
    echo "================================================================"
    echo
    
    # Parse command line arguments
    DEPLOY_BACKEND=true
    DEPLOY_FRONTEND=true
    
    while [[ $# -gt 0 ]]; do
        case $1 in
            --backend-only)
                DEPLOY_FRONTEND=false
                shift
                ;;
            --frontend-only)
                DEPLOY_BACKEND=false
                shift
                ;;
            --project)
                PROJECT_ID="$2"
                shift 2
                ;;
            --region)
                REGION="$2"
                shift 2
                ;;
            --help)
                echo "Usage: $0 [options]"
                echo ""
                echo "Options:"
                echo "  --project PROJECT_ID      Google Cloud Project ID (default: ktp-loughborough-university)"
                echo "  --region REGION           Deployment region (default: europe-west2)"
                echo "  --backend-only            Deploy only the backend service"
                echo "  --frontend-only           Deploy only the frontend service"
                echo "  --help                    Show this help message"
                echo ""
                echo "Environment variables:"
                echo "  OPENAI_API_KEY            OpenAI API key (required)"
                echo ""
                exit 0
                ;;
            *)
                print_error "Unknown option: $1. Use --help for usage information."
                exit 1
                ;;
        esac
    done
    
    # Check for OpenAI API key
    if [ -z "$OPENAI_API_KEY" ]; then
        print_warning "OPENAI_API_KEY environment variable not set."
        print_warning "The backend will not function without it."
        read -p "Enter your OpenAI API key: " OPENAI_API_KEY
        export OPENAI_API_KEY
    fi
    
    # Pre-flight checks
    print_status "Starting deployment process..."
    check_gcloud
    setup_project
    check_billing
    enable_apis
    
    echo
    print_status "Pre-flight checks completed successfully!"
    echo
    
    # Confirm deployment
    echo "Deployment Configuration:"
    echo "• Project: $PROJECT_ID"
    echo "• Region: $REGION"
    echo "• Backend Service: $BACKEND_SERVICE (Memory: $BACKEND_MEMORY, CPU: $BACKEND_CPU)"
    echo "• Frontend Service: $FRONTEND_SERVICE (Memory: $FRONTEND_MEMORY, CPU: $FRONTEND_CPU)"
    echo "• Deploy Backend: $DEPLOY_BACKEND"
    echo "• Deploy Frontend: $DEPLOY_FRONTEND"
    echo
    
    read -p "Proceed with deployment? (y/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_warning "Deployment cancelled by user"
        exit 0
    fi
    
    # Deploy
    if [ "$DEPLOY_BACKEND" = true ]; then
        deploy_backend
    fi
    
    if [ "$DEPLOY_FRONTEND" = true ]; then
        deploy_frontend
    fi
    
    # Post-deployment
    show_deployment_info
    
    echo
    print_success "🎉 Bakery Quotation System deployment completed successfully!"
    
    if [ -f ".backend_url" ]; then
        BACKEND_URL=$(cat .backend_url)
        echo
        echo "📍 Backend API: $BACKEND_URL"
    fi
    
    if [ "$DEPLOY_FRONTEND" = true ]; then
        FRONTEND_URL=$(gcloud run services describe $FRONTEND_SERVICE --region $REGION --format="value(status.url)" 2>/dev/null)
        echo "🌐 Frontend: $FRONTEND_URL"
    fi
    
    echo
    print_status "Next steps:"
    echo "1. Test the application thoroughly"
    echo "2. Make sure the BOM pricing tool is accessible"
    echo "3. Monitor costs and performance"
    echo
}

# Handle script interruption
trap 'print_error "Deployment interrupted"' INT TERM

# Run main function
main "$@"
