#!/bin/bash

# DE_AN Environment Files Setup Script
# This script creates template .env.docker files for all services

set -e

echo "🔧 Setting up environment files for DE_AN services..."

# Function to create env file
create_env_file() {
    local file_path=$1
    shift
    local content=$1
    
    echo "📝 Creating $file_path..."
    
    # Use cat with a heredoc to write the content to the file
    cat > "$file_path" << EOF
$content
EOF
}

# Common Content for all services
COMMON_CONTENT=$(cat <<'EOF'
# QDRANT
BASE_URL=https://fptshop.com.vn
QDRANT_URL=<your_qdrant_url>
QDRANT_API_KEY=<your_qdrant_api_key>
STORAGE=FPT_SHOP
POLICY=FPT_Policy
EXPERT=EXPERT_STORE
DOCINTEL_ENDPOINT=<document_intelligence_endpoint>

# CHATBOT
OPENAI_API_KEY=<your_openai_api_key>
TAVILY_API_KEY=<your_tavily_api_key>

# MongoDB
MONGO_URL=<your_mongo_url>
MONGO_AGENT_COLLECTION_NAME=chat_history
MONGO_MEMORY_COLLECTION_NAME=agent_memmory
MONGO_DB_NAME=Store_agent_memory

# AWS
AWS_ACCESS_KEY_ID=<your_aws_access_key_id>
AWS_SECRET_ACCESS_KEY=<your_aws_secret_access_key>
AWS_REGION=<your_aws_region>
TABLE_NAME=CHAT_HISTORY
PREPROCESS_BUCKET_NAME=dataversion0204
ML_BUCKET_NAME=ml-dataversion-1

# redis
REDIS_PASS=<your_redis_password>
REDIS_HOST=<your_redis_host>

# AUTH
SECRET_KEY=<your_jwt_secret_key>
ALGORITHM=HS256

# EMAIL
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
EMAIL_USER=<your_email_user>
EMAIL_PASSWORD=<your_email_password>

# DB
SQL_SERVER=<your_sql_server>
SQL_DATABASE=CUSTOMER_SERVICE

# TF
TF_ENABLE_ONEDNN_OPTS=0
EOF
)

# Create .env.docker files for all services
create_env_file "BACKEND/AUTH/.env.docker" "$COMMON_CONTENT"
create_env_file "BACKEND/BE_ADMIN/.env.docker" "$COMMON_CONTENT"
create_env_file "BACKEND/BE_CHATBOT/.env.docker" "$COMMON_CONTENT"
create_env_file "BACKEND/BE_PREPROCESS/.env.docker" "$COMMON_CONTENT"
create_env_file "BACKEND/ML/.env.docker" "$COMMON_CONTENT"


echo "✅ Environment files created successfully!"
echo ""
echo "⚠️  IMPORTANT: Please update the placeholder values in each .env.docker file."
echo ""
echo "📋 Files created:"
for file in BACKEND/AUTH/.env.docker BACKEND/BE_ADMIN/.env.docker BACKEND/BE_CHATBOT/.env.docker BACKEND/BE_PREPROCESS/.env.docker BACKEND/ML/.env.docker; do
    echo "   - $file"
done
