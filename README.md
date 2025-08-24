# DE_AN - SAGE (Synergistic Agentic Governance Engine)

SAGE is a comprehensive enterprise-grade system that provides intelligent multi-agent chatbot services, advanced machine learning capabilities, and automated data preprocessing tools with enterprise-level security and role-based access control.

**USE CASE**: **FPT Shop** - A complete customer service and business intelligence solution

## System Overview

SAGE is architected as a modern microservices-based system with the following core capabilities:

- **🤖 Multi-Agent Chatbot System**: Hierarchical intelligent assistants with specialized roles
- **🧠 Advanced ML Operations**: Predictive analytics, sentiment analysis, and customer segmentation
- **📊 Data Intelligence**: Automated PDF and URL processing for knowledge base enrichment
- **🔐 Enterprise Security**: JWT-based authentication with granular role-based access control
- **⚡ High Performance**: Containerized deployment with Nginx API Gateway

## 🏗️ Architecture Overview

```
┌─────────────┐     ┌──────────────────┐
│  Frontend   │────▶│   API Gateway    │
│ (Planned)   │     │    (Nginx)       │
└─────────────┘     │   Port: 8090     │
                    └─────────┬────────┘
                              │
        ┌─────────┬───────────┼───────────┬─────────┐
        │         │           │           │         │
┌───────▼───┐ ┌───▼────┐ ┌────▼────┐ ┌───▼─────┐ ┌─▼────┐
│   AUTH    │ │ ADMIN  │ │  CHAT   │ │  PRE-   │ │  ML  │
│  Service  │ │Service │ │ Service │ │ PROCESS │ │ Serv.│
│ Port:8888 │ │Port:888│ │Port:8090│ │Port:8002│ │Port: │
└───────────┘ └────────┘ └─────────┘ └─────────┘ └──────┘
```

## 🔐 Access Roles & Permissions

SAGE implements a comprehensive hierarchical access control system:

### **👤 Users (Basic Level)**
- Access to chatbot services and personal interactions
- View personal order history and bookings
- Basic customer support through AI assistants

### **👨‍💼 Staff (Intermediate Level)**
- Enhanced access to customer management tools
- ML prediction capabilities for business insights
- Order and booking management functions
- Cannot access data preprocessing or ML training

### **🔧 Administrators (Full Access)**
- Complete system access including ML operations
- Advanced analytics and business intelligence
- System monitoring and configuration management
- Access to all supervisor agents and admin tools
- Full ML training and data preprocessing capabilities

## 🚀 Backend Services

### 🌐 API Gateway (Nginx)

All services are accessible through a **single unified entry point** on port **8090**:

| Service | Endpoint | Description |
|---------|----------|-------------|
| **Auth Service** | `/auth/` | Authentication and user management |
| **Admin Service** | `/admin/` | Administrative tools and supervisor agents |
| **Chatbot Service** | `/chat/` | Multi-agent chatbot system (default route) |
| **Preprocess Service** | `/preprocess/` | PDF and URL processing |
| **ML Service** | `/ml/` | Machine learning operations |

### 🔐 Authentication Service (AUTH)

**Core Security Features:**
- **User Registration & Login** with secure password hashing (bcrypt)
- **JWT Token-based Authentication** for stateless security
- **Role-based Access Control** with granular permissions
- **Password Management** (reset, change, recovery)
- **Session Management** and token validation

### 🤖 Multi-Agent Chatbot System (BE_CHATBOT)

**Advanced Conversational AI Architecture:**

#### **🎯 Primary Assistant (Router)**
- Intelligent request routing and context understanding
- Natural language processing for intent recognition
- Seamless handoff between specialized agents

#### **🛒 Tech Assistant (Shop Agent)**
- **Device Recommendations** based on customer preferences
- **Order Management** (create, modify, track orders)
- **Product Information** and inventory queries
- **Price Comparisons** and promotional offers

#### **🔧 IT Assistant (Technical Support)**
- **Technical Troubleshooting** and maintenance guidance
- **Device Setup** and configuration assistance
- **Warranty Information** and repair services
- **Software Support** and updates

#### **📅 Appointment Assistant (Booking Agent)**
- **Service Booking** management and scheduling
- **Appointment Modifications** and cancellations
- **Reminder Systems** and notifications
- **Resource Allocation** and availability checking

#### **🧠 Advanced AI Capabilities:**
- **RAG (Retrieval Augmented Generation)** for accurate information retrieval
- **URL Scraping & Web Content Analysis** for real-time information
- **Follow-up Question Handling** with context preservation
- **Multi-turn Conversation** management with state persistence

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