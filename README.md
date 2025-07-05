# SAGE (Synergistic Agentic Governance Engine)

SAGE is an integrated enterprise system that provides intelligent chatbot services, machine learning capabilities, and data preprocessing tools with role-based access control.

CASE STUDY: **FPT Shop** 

## System Overview

SAGE is designed with a modular architecture that separates concerns into distinct microservices:

- **Chatbot Interface**: Intelligent assistant for users with routing capabilities
- **ML Processing**: Predictive analytics for churn and sentiment analysis
- **Data Preprocessing**: PDF and URL processing for knowledge base enrichment
- **Authentication**: Secure role-based access control

## Access Roles

SAGE implements a hierarchical access control system:

1. **Users**
   - Access to chatbot services
   - Can interact with SAGE for information retrieval and support

2. **Staff**
   - Access to chatbot services
   - Access to ML prediction capabilities
   - Cannot access data preprocessing or ML training

3. **Administrators**
   - Full system access
   - Access to chatbot services (including admin features)
   - Access to ML (both prediction and training)
   - Access to data preprocessing tools

## Backend Components

### API Gateway

All services are accessible through a single Nginx API gateway running on port 8090:

- **Auth Service**: `/auth/`
- **Admin Service**: `/admin/`
- **Chatbot Service**: `/chat/` (default route)
- **Preprocess Service**: `/preprocess/`
- **ML Service**: `/ml/`

### Authentication (AUTH)

- User registration and login
- JWT token-based authentication
- Role-based access control
- Password management (reset, change)

### Chatbot (BE_CHATBOT)

- Intelligent routing system
- Hierarchical Multi-agentic architecture:
  - Tech Assistant: Device recommendations, order management
  - IT Assistant: Technical support, maintenance guidance
  - Appointment Assistant: Booking management
- RAG (Retrieval Augmented Generation) for accurate information retrieval
- URL-scraping extraction and processing for web content analysis
- Follow-up question handling

### Admin Interface (BE_ADMIN)

- Supervisor chatbot system for administrators: Report analysis agent, SQL Agent, Sale advisor agent with Supervisor architechture
- System monitoring and management
- Access to advanced features and analytics

### Data Preprocessing (BE_PREPROCESS)

- PDF document processing:
  - Text extraction
  - Document chunking
  - Vector store integration
- URL content processing:
  - Web scraping
  - Content extraction
  - Knowledge base integration
- S3 storage integration
- Webhook notifications for process completion

### Machine Learning (ML)

- **Churn Prediction**:
  - Customer behavior analysis
  - Feature engineering
  - Model training and evaluation
  - Prediction API
  - Data drift detection

- **Sentiment Analysis**:
  - Text preprocessing
  - Feature extraction
  - Model training and evaluation
  - Prediction API

- **Time Series Revenue Prediction**:
  - Historical revenue data processing
  - Feature engineering with temporal patterns
  - Seasonality and trend detection
  - Leveraging XGB algorithm
  - Prediction API

- **Customer Segmentation**:
  - Demographic and behavioral clustering using RFM model
  - Unsupervised learning (K-Means, DBSCAN)
  - Feature dimensionality reduction (PCA, t-SNE)
  - Segment-based analytics and targeting
  - Prediction API

- **MLOps Features**:
  - Model versioning
  - Performance monitoring
  - Retraining workflows
  - Metrics tracking with MLflow
  - S3 integration for artifact storage

## Technical Stack

- **Backend**: FastAPI (Python)
- **Database**: SQL databases (via SQLAlchemy)
- **Vector Store**: Qdrant for similarity search
- **Storage**: AWS S3
- **Containerization**: Docker and docker-compose
- **ML Framework**: scikit-learn, MLflow
- **API Gateway**: Nginx
- **Monitoring**: Structured logging

## Deployment

The entire system can be deployed using Docker Compose:

```bash
cd BACKEND
docker-compose up -d
```

## Testing

A test script is provided to verify the API gateway functionality:

```bash
cd BACKEND
chmod +x test_api_gateway.sh
./test_api_gateway.sh
```

## Architecture Diagram

```
┌─────────────┐     ┌──────────────┐
│  Frontend   │────▶│ API Gateway  │
└─────────────┘     │   (Nginx)    │
                    └───────┬──────┘
                            │
        ┌─────────┬─────────┼─────────┬─────────┐
        │         │         │         │         │
┌───────▼───┐ ┌───▼───┐ ┌───▼───┐ ┌───▼────┐ ┌─▼───┐
│   AUTH    │ │ ADMIN │ │ CHAT  │ │  PRE-  │ │ ML  │
│  Service  │ │Service│ │Service│ │PROCESS │ │Serv.│
└───────────┘ └───────┘ └───────┘ └────────┘ └─────┘
```

## Security

- JWT token authentication
- Role-based access control
- Secure password hashing with bcrypt
- API gateway for controlled access

## Future Enhancements

- Frontend integration
- Fine-tuned LLM
- Enhanced analytics dashboard
- Real-time monitoring
