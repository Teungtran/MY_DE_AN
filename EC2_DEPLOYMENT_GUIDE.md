# 🚀 DE_AN EC2 Deployment Guide

This guide provides step-by-step instructions to deploy the DE_AN system on an EC2 instance.

## 📋 Prerequisites

- **EC2 Instance**: Ubuntu 20.04 LTS or later (recommended: t3.large or larger)
- **Security Groups**: Open ports 8090 (API Gateway), 22 (SSH)
- **Storage**: At least 20GB EBS volume
- **IAM Role** (optional): For AWS S3 access

## 🔧 Step 1: Initial Server Setup

```bash
# Connect to your EC2 instance
ssh -i your-key.pem ubuntu@your-ec2-ip

# Clone the repository
git clone https://github.com/Teungtran/DE_AN.git
cd DE_AN

# Make setup scripts executable
chmod +x scripts/setup_ec2.sh
chmod +x scripts/setup_env_files.sh
```

## 🏗️ Step 2: Run Setup Scripts

### Run the main setup script:
```bash
./scripts/setup_ec2.sh
```

This script will:
- ✅ Install Docker and Docker Compose
- ✅ Create all required directories
- ✅ Set proper permissions
- ✅ Check for environment files

### Create environment files:
```bash
./scripts/setup_env_files.sh
```

This creates template `.env.docker` files for all services.

## 🔐 Step 3: Configure Environment Variables

Edit each `.env.docker` file with your actual credentials:

### 1. Database Configuration (All Services)
```bash
# Update in all .env.docker files
DB_HOST=your-rds-endpoint.amazonaws.com
DB_PORT=1433
DB_NAME=CUSTOMER_SERVICE
DB_USER=your_db_user
DB_PASSWORD=your_secure_password
```

### 2. JWT Configuration (AUTH Service)
```bash
# Generate a secure JWT secret
openssl rand -hex 32

# Update BACKEND/AUTH/.env.docker
JWT_SECRET_KEY=your_generated_secret_here
```

### 3. OpenAI API Key (Chatbot Service)
```bash
# Update BACKEND/BE_CHATBOT/.env.docker
OPENAI_API_KEY=sk-your-openai-api-key-here
```

### 4. AWS S3 Configuration (ML & Preprocess Services)
```bash
# Update BACKEND/ML/.env.docker and BACKEND/BE_PREPROCESS/.env.docker
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
S3_BUCKET_NAME=your-bucket-name
```

### 5. Vector Database (Qdrant)
```bash
# Update chatbot and preprocess .env.docker files
QDRANT_HOST=your-qdrant-host
QDRANT_API_KEY=your-qdrant-api-key
```

## 🚀 Step 4: Deploy the System

```bash
# Navigate to backend directory
cd BACKEND

# Build and start all services
docker-compose up -d

# Check service status
docker-compose ps

# View logs if needed
docker-compose logs -f [service_name]
```

## 🧪 Step 5: Test the Deployment

```bash
# Make test script executable
chmod +x test_api_gateway.sh

# Run API tests
./test_api_gateway.sh
```

Expected output should show successful responses from all services.

## 🌐 Step 6: Access the System

Once deployed, your services will be available at:

| Service | URL | Description |
|---------|-----|-------------|
| **API Gateway** | `http://your-ec2-ip:8090` | Main entry point |
| **Authentication** | `http://your-ec2-ip:8090/auth/` | User management |
| **Admin Panel** | `http://your-ec2-ip:8090/admin/` | Administrative tools |
| **Chatbot** | `http://your-ec2-ip:8090/chat/` | AI assistant |
| **Data Processing** | `http://your-ec2-ip:8090/preprocess/` | PDF/URL processing |
| **ML Operations** | `http://your-ec2-ip:8090/ml/` | Machine learning |

## 📊 Step 7: Initialize Database

Run the SQL scripts to set up your database:

```bash
# Connect to your SQL Server instance and run:
# 1. SQL_SCRIPTS/TABEL_CUST_SCHEMAS.sql
# 2. SQL_SCRIPTS/input_items_scripts.sql
# 3. SQL_SCRIPTS/add trigger.sql
```

## 🔍 Troubleshooting

### Common Issues:

1. **Port 8090 not accessible**
   - Check EC2 Security Group allows inbound traffic on port 8090
   - Verify nginx service is running: `docker-compose logs nginx`

2. **Database connection errors**
   - Verify database credentials in `.env.docker` files
   - Check database server is accessible from EC2

3. **OpenAI API errors**
   - Verify API key is correct in `BACKEND/BE_CHATBOT/.env.docker`
   - Check API key has sufficient credits

4. **S3 access errors**
   - Verify AWS credentials in ML and preprocess `.env.docker` files
   - Check S3 bucket exists and has proper permissions

### Useful Commands:

```bash
# View all container logs
docker-compose logs

# Restart a specific service
docker-compose restart [service_name]

# Rebuild and restart all services
docker-compose down && docker-compose up -d --build

# Check container resource usage
docker stats

# Access container shell
docker-compose exec [service_name] /bin/bash
```

## 🔄 Updates and Maintenance

To update the system:

```bash
# Pull latest changes
git pull origin main

# Rebuild and restart services
docker-compose down
docker-compose up -d --build

# Clean up unused images
docker system prune -f
```

## 📈 Monitoring

Monitor your deployment:

```bash
# Check service health
curl http://your-ec2-ip:8090/auth/
curl http://your-ec2-ip:8090/ml/

# Monitor logs in real-time
docker-compose logs -f

# Check system resources
htop
df -h
```

## 🆘 Support

If you encounter issues:

1. Check the logs: `docker-compose logs [service_name]`
2. Verify environment variables are correctly set
3. Ensure all required external services (database, S3, etc.) are accessible
4. Check EC2 security groups and network configuration

---

**🎉 Congratulations!** Your DE_AN system should now be running successfully on EC2.
