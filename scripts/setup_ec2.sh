#!/bin/bash

# DE_AN EC2 Setup Script
# This script sets up the complete directory structure and environment for the DE_AN system

set -e  # Exit on any error

echo "🚀 Starting DE_AN EC2 Setup..."

# Update system packages
echo "📦 Updating system packages..."
sudo apt-get update -y

# Install Docker and Docker Compose if not present
if ! command -v docker &> /dev/null; then
    echo "🐳 Installing Docker..."
    sudo apt-get install -y docker.io
    sudo systemctl start docker
    sudo systemctl enable docker
    sudo usermod -aG docker $USER
fi

if ! command -v docker-compose &> /dev/null; then
    echo "🐳 Installing Docker Compose..."
    sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
fi

# Create all required directories
echo "📁 Creating directory structure..."

# ML Service Directories
echo "  Creating ML artifacts directories..."
mkdir -p BACKEND/ML/artifacts/churn/{data_ingestion,data_version,model_version,evaluation}
mkdir -p BACKEND/ML/artifacts/sentiment/{data_ingestion,data_version,model_version,evaluation}
mkdir -p BACKEND/ML/artifacts/timeseries/{data_ingestion,data_version,model_version,evaluation}
mkdir -p BACKEND/ML/artifacts/segmentation/{data_ingestion,data_version,model_version,evaluation}

# ML Plots directories (separate from artifacts as per docker-compose.yml)
mkdir -p BACKEND/ML/plots/{churn,sentiment,timeseries,segmentation}

# Logs directories for all services
echo "  Creating logs directories..."
mkdir -p BACKEND/AUTH/logs
mkdir -p BACKEND/BE_ADMIN/logs
mkdir -p BACKEND/BE_CHATBOT/logs
mkdir -p BACKEND/BE_PREPROCESS/logs
mkdir -p BACKEND/ML/logs



# Frontend directory (for future use)
mkdir -p FRONTEND

echo "✅ Directory structure created successfully"

# Set proper permissions
echo "🔐 Setting proper permissions..."
chmod -R 755 BACKEND/
chmod -R 777 BACKEND/*/logs/  # Logs need write permissions
chmod -R 777 BACKEND/ML/artifacts/
chmod -R 777 BACKEND/ML/plots/

# Environment setup
echo "🌍 Setting up environment..."

# Check for environment files
ENV_FILES=(
    "BACKEND/AUTH/.env.docker"
    "BACKEND/BE_ADMIN/.env.docker"
    "BACKEND/BE_CHATBOT/.env.docker"
    "BACKEND/BE_PREPROCESS/.env.docker"
    "BACKEND/ML/.env.docker"
)

missing_env_files=()
for env_file in "${ENV_FILES[@]}"; do
    if [ ! -f "$env_file" ]; then
        missing_env_files+=("$env_file")
    fi
done

if [ ${#missing_env_files[@]} -gt 0 ]; then
    echo "⚠️  WARNING: Missing environment files:"
    for file in "${missing_env_files[@]}"; do
        echo "    - $file"
    done
    echo "   Please create these files before running docker-compose"
fi

# Load main environment variables if available
if [ -f ".env" ]; then
    echo "📋 Loading main environment variables from .env"
    set -a
    source .env
    set +a
else
    echo "⚠️  No main .env file found in root directory"
fi

echo "🎯 EC2 setup completed successfully!"
echo ""
echo "📋 Next steps:"
echo "   1. Ensure all .env.docker files are properly configured"
echo "   2. Run: cd BACKEND && docker-compose up -d"
echo "   3. Test the API gateway: ./test_api_gateway.sh"
echo ""
echo "🌐 Services will be available at:"
echo "   - API Gateway: http://localhost:8090"
echo "   - Auth: http://localhost:8090/auth/"
echo "   - Admin: http://localhost:8090/admin/"
echo "   - Chat: http://localhost:8090/chat/"
echo "   - Preprocess: http://localhost:8090/preprocess/"
echo "   - ML: http://localhost:8090/ml/"