# FPT Shop Customer Service Platform - SAGE (Synergistic Agentic Governance Engine)

## 📋 Executive Summary

The FPT Shop Customer Service Platform is a comprehensive, AI-powered e-commerce customer service and analytics system designed to revolutionize customer interactions, streamline operations, and provide data-driven business insights. Built on a modern microservices architecture, the platform integrates advanced AI chatbots, machine learning predictions, document processing, and collaborative admin tools to deliver a seamless customer experience while empowering staff with powerful analytics capabilities.

---

## 🎯 System Overview

**SAGE (Synergistic Agentic Governance Engine)** is an intelligent routing and orchestration system that serves as the core brain of the platform, analyzing customer requests and directing them to specialized AI agents for optimal service delivery. The platform consists of 6 core microservices working in harmony through an API Gateway, providing:

- **Intelligent Customer Service**: AI-powered chatbot with multi-agent collaboration
- **Advanced Analytics**: Machine learning-driven sentiment analysis and churn prediction
- **Document Intelligence**: Automated processing and knowledge base management
- **Team Collaboration**: Multi-agent admin tools for report analysis and decision-making
- **Secure Authentication**: Role-based access control with JWT authentication

---

## 🏗️ High-Level Architecture

### Architecture Pattern: Microservices with API Gateway

```
┌─────────────────────────────────────────────────────────────────┐
│                         FRONTEND                                │
│              React + TypeScript (Port 3000)                    │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    API GATEWAY (NGINX)                          │
│                    Single Entry Point (Port 8090)               │
└─────┬──────┬──────┬──────┬──────┬──────┬────────────────────────┘
      │      │      │      │      │      │
      ▼      ▼      ▼      ▼      ▼      ▼
┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐
│  AUTH  │ │  ADMIN │ │ CHATBOT│ │PREPROC │ │   ML   │ │  DB    │
│ Service│ │ Service│ │ Service│ │Service │ │Service │ │SQLite  │
│ :8888  │ │ :8888  │ │ :8888  │ │ :8888  │ │ :8888  │ │Shared  │
└────────┘ └────────┘ └────────┘ └────────┘ └────────┘ └────────┘
      │      │      │      │      │      │
      └──────┴──────┴──────┴──────┴──────┘
              Internal Network (Docker Bridge)
```

### Key Architectural Components

1. **Frontend Layer** (React + TypeScript)
   - Modern, responsive web application
   - Real-time streaming chat interfaces
   - Role-based UI components
   - Server-Sent Events (SSE) for live updates

2. **API Gateway** (Nginx)
   - Single entry point for all backend services
   - Request routing and load balancing
   - CORS handling and security headers
   - Port: 8090

3. **Microservices** (FastAPI + Python)
   - Each service runs independently on port 8888
   - Containerized with Docker
   - Shared SQLite database for user management
   - Internal communication via Docker network

4. **Data Layer**
   - SQLite database for authentication and user data
   - Vector databases (via Preprocess service) for RAG
   - Redis (for chat history and pub/sub)
   - MLflow for model versioning and tracking

5. **AI/ML Infrastructure**
   - LangGraph for agent orchestration
   - LangChain for tool integration
   - TensorFlow/Keras for sentiment models
   - Scikit-learn for churn prediction
   - Supabase/Vector DB for embeddings

---

## 🚀 Core Services

### 1. 🔐 Authentication Service (AUTH)

**Purpose**: User authentication, authorization, and session management

**Key Features**:
- User registration with comprehensive profile data
- Login with username/email and password
- Password reset and recovery
- JWT token generation and validation
- Role-based access control (user, staff, admin)
- User preference management (brands, price ranges)

**Technology Stack**:
- FastAPI
- SQLite database
- JWT tokens
- Password hashing (bcrypt)

**Endpoints**:
- `POST /auth/v1/auth/register` - User registration
- `POST /auth/v1/auth/login` - User authentication
- `POST /auth/v1/auth/forgot-password` - Password reset

---

### 2. 💬 Chatbot Service (BE_CHATBOT)

**Purpose**: Intelligent customer service chatbot with multi-agent orchestration

**Key Features**:
- **SAGE Router**: Intelligent request routing to specialized agents
- **Shop Assistant**: Product recommendations, device details, order management
- **IT Assistant**: Technical support, troubleshooting, ticket management
- **Appointment Assistant**: Service appointment booking and management
- **RAG Agent**: Policy and information retrieval from knowledge base
- **URL Extraction**: Content analysis from web URLs
- Real-time streaming responses (Server-Sent Events)
- Conversation history management
- Multi-language support (responds in user's language)

**Technology Stack**:
- LangGraph for agent orchestration
- LangChain for tool integration
- Redis for conversation state
- DynamoDB for checkpointing (optional)
- Vector databases for RAG
- Hybrid search (semantic + keyword)

**Endpoints**:
- `POST /chat/v1/chat/streaming-answer` - Streaming chat responses
- `GET /chat/{conversation_id}/messages` - Chat history retrieval
- `GET /chat/{conversation_id}/subscribe` - Real-time updates (SSE)

**Agent Capabilities**:
1. **ToShopAssistant**: 
   - Personalized product recommendations using hybrid search
   - Device specifications and pricing
   - Order placement, tracking, and cancellation
   - Price comparisons and availability checks

2. **ToITAssistant**:
   - Technical troubleshooting guidance
   - Device setup and configuration help
   - IT support ticket creation and tracking
   - Maintenance tips and best practices

3. **ToAppointmentAssistant**:
   - Service appointment scheduling
   - Appointment tracking and management
   - Cancellation and rescheduling

4. **RAG_Agent Tool**:
   - FPT Shop policies and regulations
   - Warranty and return information
   - Store locations and hours
   - Company procedures

5. **URL Tools**:
   - Extract and analyze content from URLs
   - Compare information across multiple sources
   - Follow-up questions on previously viewed URLs

---

### 3. 👨‍💼 Admin Service (BE_ADMIN)

**Purpose**: Team collaboration tools and business report analysis

**Key Features**:
- **Team Chat**: Multi-agent collaboration for complex problem-solving
- **Report Analysis**: Upload and analyze CSV/Excel business reports
- **File Management**: Track and manage uploaded reports
- **AI-Powered Insights**: Automated analysis and visualization suggestions
- Real-time streaming responses for team discussions

**Technology Stack**:
- LangGraph for multi-agent workflows
- Pandas for data processing
- AI agents for report analysis

**Endpoints**:
- `POST /admin/v1/chat/team/chat/stream` - Streaming team chat
- `POST /admin/v1/chat/team/chat` - Non-streaming team chat
- `POST /admin/v1/chat/report/upload-and-analyze` - Report upload and analysis
- `GET /admin/v1/chat/report/files` - List uploaded reports

**Access Control**: Requires `staff` or `admin` role

---

### 4. ⚙️ Preprocessing Service (BE_PREPROCESS)

**Purpose**: Document processing and knowledge base management

**Key Features**:
- **URL Processing**: Extract and process content from web URLs
- **PDF Processing**: Parse and extract text from PDF documents
- **Vector Storage**: Store processed documents in vector databases for RAG
- **Document Types**: Support for RAG, Expert Knowledge, and Recommendation data
- **Metadata Management**: Track document sources, types, and update timestamps

**Technology Stack**:
- Web scraping and content extraction
- PDF parsing libraries
- Vector database integration (Supabase/Chroma)
- Embedding generation

**Endpoints**:
- `POST /preprocess/internal/v1/urls-rag/` - Process URLs for RAG
- `POST /preprocess/internal/v1/pdf-rag/` - Process PDFs for RAG
- `POST /preprocess/internal/v1/urls-expert/` - Process URLs for expert knowledge
- `POST /preprocess/internal/v1/pdf-expert/` - Process PDFs for expert knowledge
- `POST /preprocess/internal/v1/recommend-data/` - Process recommendation data

**Access Control**: Requires `admin` role

---

### 5. 🤖 Machine Learning Service (ML)

**Purpose**: Predictive analytics and model management

**Key Features**:

#### Sentiment Analysis
- **Model**: CNN-based deep learning model (TensorFlow/Keras)
- **Input**: CSV files with text data
- **Output**: Sentiment classification (positive/negative/neutral) with confidence scores
- **Features**: 
  - Text preprocessing and tokenization
  - Embedding generation
  - Model versioning with MLflow
  - Batch prediction support

#### Churn Prediction
- **Model**: Random Forest classifier (Scikit-learn)
- **Input**: Customer data (demographics, behavior, transaction history)
- **Output**: Churn probability and risk level (low/medium/high)
- **Features**:
  - Feature engineering pipeline
  - Model versioning and tracking
  - Risk stratification

#### Model Training & Management
- **Training Pipelines**: Automated data ingestion, preprocessing, training, and evaluation
- **MLflow Integration**: Experiment tracking and model versioning
- **Cloud Storage**: Model artifact storage (S3-compatible)
- **DVC Integration**: Data version control for reproducibility

**Technology Stack**:
- TensorFlow/Keras for sentiment models
- Scikit-learn for churn models
- MLflow for experiment tracking
- DVC for data versioning
- Pandas for data processing

**Endpoints**:
- `POST /ml/v1/sentiment/predict/` - Sentiment prediction
- `POST /ml/v1/churn/predict/` - Churn prediction
- `POST /ml/v1/sentiment/train/` - Retrain sentiment model (admin only)
- `POST /ml/v1/churn/train/` - Retrain churn model (admin only)
- `GET /ml/v1/sentiment/train/status` - Training status
- `GET /ml/v1/churn/train/status` - Training status

**Access Control**:
- Predictions: `staff` or `admin` role
- Training: `admin` role only

---

### 6. 🌐 Frontend Service

**Purpose**: User interface and user experience

**Key Features**:
- **Landing Page**: Platform introduction and feature highlights
- **Authentication Pages**: Login, registration, password reset
- **Customer Dashboard**: Profile management, chat history, preferences
- **AI Chat Interface**: Real-time streaming chat with SAGE
- **Admin Dashboard**: Team chat, report analysis, file management
- **ML Analytics**: Sentiment and churn prediction interfaces
- **Responsive Design**: Works on desktop and mobile devices

**Technology Stack**:
- React 18
- TypeScript
- Vite for build tooling
- Tailwind CSS + shadcn/ui components
- Server-Sent Events for real-time updates
- Axios for API communication

**Key Pages**:
- `/` - Landing page
- `/login` - Login page
- `/register` - Registration page
- `/chat` - Customer chatbot interface
- `/admin/team-chat` - Admin team collaboration
- `/admin/reports` - Report analysis dashboard
- `/ml/sentiment` - Sentiment analysis interface
- `/ml/churn` - Churn prediction interface

---

## ✨ Complete Feature List

### Customer-Facing Features

1. **User Authentication & Management**
   - Secure registration with email and phone validation
   - Login with username/email
   - Password reset functionality
   - User profile management
   - Preference settings (brands, price ranges)

2. **AI Customer Service Chat**
   - Real-time streaming conversations
   - Product recommendations based on preferences
   - Device specifications and pricing
   - Order management (place, track, cancel)
   - Technical support and troubleshooting
   - Appointment booking
   - Policy and warranty information
   - URL content analysis
   - Multi-language support
   - Conversation history

3. **Customer Dashboard**
   - Personal profile view and edit
   - Chat history access
   - Order tracking
   - Preference management

### Staff/Admin Features

4. **Team Collaboration**
   - Multi-agent team chat
   - Complex problem-solving workflows
   - Real-time streaming responses
   - Session management

5. **Report Analysis**
   - CSV/Excel file upload
   - Automated data analysis
   - AI-powered insights generation
   - Visualization suggestions
   - File management and tracking

6. **Machine Learning Analytics**
   - **Sentiment Analysis**:
     - Batch text sentiment prediction
     - Confidence scores
     - Results visualization
     - Model version selection
   
   - **Churn Prediction**:
     - Customer churn risk assessment
     - Risk level classification
     - Probability scores
     - High-risk customer alerts

7. **Model Management** (Admin Only)
   - Model retraining workflows
   - Training status monitoring
   - Model version management
   - Performance metrics tracking

8. **Document Processing** (Admin Only)
   - URL processing for knowledge base
   - PDF upload and processing
   - Vector database management
   - Document type classification
   - Knowledge base updates

### System Features

9. **Security & Access Control**
   - JWT-based authentication
   - Role-based access control (user, staff, admin)
   - Secure password hashing
   - API endpoint protection
   - CORS configuration

10. **Real-Time Capabilities**
    - Server-Sent Events (SSE) for streaming
    - Redis pub/sub for live updates
    - WebSocket-ready architecture

11. **Scalability & Performance**
    - Microservices architecture
    - Containerized deployment (Docker)
    - Horizontal scaling capability
    - API Gateway for load distribution

12. **Observability**
    - Structured logging (Structlog)
    - Request tracing
    - Health check endpoints
    - Error handling and reporting

---

## 📊 Use Cases

### Use Case 1: Customer Product Inquiry
**Actor**: Customer  
**Scenario**: A customer wants to buy a laptop for gaming under 20 million VND

**Flow**:
1. Customer logs into the platform
2. Opens chat interface and asks: "I need a gaming laptop under 20 million VND"
3. SAGE router analyzes the request and routes to Shop Assistant
4. Shop Assistant uses hybrid search to find matching products
5. System retrieves user preferences (if available) and enhances search
6. Returns top 3-5 recommendations with specifications, prices, and availability
7. Customer can ask follow-up questions about specific models
8. Customer can place order directly through chat

**Value**: Personalized recommendations, instant responses, seamless purchase flow

---

### Use Case 2: Technical Support Request
**Actor**: Customer  
**Scenario**: Customer's laptop is running slowly and needs help

**Flow**:
1. Customer describes the problem in chat
2. SAGE routes to IT Assistant
3. IT Assistant asks diagnostic questions
4. Provides step-by-step troubleshooting guidance
5. If issue persists, creates IT support ticket
6. Customer receives ticket number and tracking information

**Value**: Immediate support, reduced support ticket volume, customer satisfaction

---

### Use Case 3: Business Report Analysis
**Actor**: Business Analyst (Staff/Admin)  
**Scenario**: Upload monthly sales report and get insights

**Flow**:
1. Analyst logs into admin dashboard
2. Navigates to Report Analysis page
3. Uploads CSV file with sales data
4. System processes and analyzes the data
5. AI agents generate insights, trends, and recommendations
6. System suggests visualizations
7. Analyst can ask follow-up questions about the data
8. Results are saved for future reference

**Value**: Time-saving analysis, data-driven insights, informed decision-making

---

### Use Case 4: Customer Sentiment Monitoring
**Actor**: Marketing Manager (Staff/Admin)  
**Scenario**: Analyze customer reviews to understand sentiment

**Flow**:
1. Manager uploads CSV file with customer reviews
2. ML service processes the data through sentiment model
3. System returns sentiment classifications (positive/negative/neutral)
4. Confidence scores for each prediction
5. Visualizations showing sentiment distribution
6. Manager can identify trends and areas for improvement

**Value**: Real-time sentiment tracking, proactive issue identification, brand reputation management

---

### Use Case 5: Churn Risk Assessment
**Actor**: Customer Success Manager (Staff/Admin)  
**Scenario**: Identify customers at risk of churning

**Flow**:
1. Manager uploads customer data file
2. ML service runs churn prediction model
3. System returns churn probabilities and risk levels
4. High-risk customers are flagged
5. Manager can prioritize outreach efforts
6. System tracks prediction accuracy over time

**Value**: Proactive customer retention, reduced churn rate, improved customer lifetime value

---

### Use Case 6: Knowledge Base Update
**Actor**: Admin  
**Scenario**: Add new product information to knowledge base

**Flow**:
1. Admin logs into document processing interface
2. Provides URLs or uploads PDFs with product information
3. Preprocess service extracts and processes content
4. Content is embedded and stored in vector database
5. System becomes aware of new information immediately
6. Chatbot can now answer questions about new products

**Value**: Always up-to-date information, improved chatbot accuracy, reduced manual updates

---

### Use Case 7: Team Problem Solving
**Actor**: Support Team (Staff/Admin)  
**Scenario**: Complex customer issue requiring multiple perspectives

**Flow**:
1. Team member opens team chat interface
2. Describes the complex problem
3. Multiple AI agents collaborate to analyze the issue
4. Each agent provides specialized insights
5. System synthesizes recommendations
6. Team can discuss and refine solutions
7. Solution is documented for future reference

**Value**: Enhanced problem-solving, knowledge sharing, consistent service quality

---

### Use Case 8: Model Retraining
**Actor**: Data Scientist (Admin)  
**Scenario**: Improve model accuracy with new data

**Flow**:
1. Admin uploads new training data
2. Initiates model retraining workflow
3. System processes data, trains model, and evaluates performance
4. Training progress is tracked in real-time
5. New model version is created if performance improves
6. Model is deployed automatically
7. Predictions now use the updated model

**Value**: Continuously improving accuracy, adapting to new patterns, maintaining model relevance

---

## 🔐 Role-Based Access Control

### User Roles

1. **User** (Customer)
   - Access to customer chatbot
   - View own profile and chat history
   - Manage preferences
   - Place and track orders

2. **Staff**
   - All user permissions
   - Access to admin team chat
   - Report analysis capabilities
   - ML prediction access (sentiment, churn)
   - Cannot retrain models or process documents

3. **Admin**
   - All staff permissions
   - Model retraining capabilities
   - Document processing and knowledge base management
   - Full system access

### Access Matrix

| Feature | User | Staff | Admin |
|---------|------|-------|-------|
| Customer Chat | ✅ | ✅ | ✅ |
| Profile Management | ✅ | ✅ | ✅ |
| Team Chat | ❌ | ✅ | ✅ |
| Report Analysis | ❌ | ✅ | ✅ |
| ML Predictions | ❌ | ✅ | ✅ |
| Model Training | ❌ | ❌ | ✅ |
| Document Processing | ❌ | ❌ | ✅ |

---

## 🛠️ Technology Stack

### Backend
- **Framework**: FastAPI (Python)
- **AI/ML**: LangGraph, LangChain, TensorFlow, Scikit-learn
- **Database**: SQLite (user data), Vector DB (embeddings), Redis (caching/pub-sub)
- **Containerization**: Docker, Docker Compose
- **API Gateway**: Nginx
- **MLOps**: MLflow, DVC
- **Authentication**: JWT, bcrypt

### Frontend
- **Framework**: React 18 with TypeScript
- **Build Tool**: Vite
- **Styling**: Tailwind CSS, shadcn/ui
- **State Management**: React Hooks
- **HTTP Client**: Axios
- **Real-time**: Server-Sent Events (SSE)

### Infrastructure
- **Container Orchestration**: Docker Compose
- **Networking**: Docker Bridge Network
- **Logging**: Structlog
- **Monitoring**: Health check endpoints

---

## 🚀 Quick Start

### Prerequisites
- Docker and Docker Compose
- Git

### Installation

```bash
# Clone the repository
git clone <repository-url>
cd DE_AN

# Start all services
docker-compose up --build

# Services will be available at:
# Frontend: http://localhost:3000
# API Gateway: http://localhost:8090
```

### Service URLs
- **Frontend**: `http://localhost:3000`
- **API Gateway**: `http://localhost:8090`
- **Auth Service**: `http://localhost:8090/auth/`
- **Chatbot Service**: `http://localhost:8090/chat/`
- **Admin Service**: `http://localhost:8090/admin/`
- **ML Service**: `http://localhost:8090/ml/`
- **Preprocess Service**: `http://localhost:8090/preprocess/`

---

## 📈 Business Value

### For Customers
- **24/7 Availability**: Instant support anytime
- **Personalized Experience**: Recommendations based on preferences
- **Multi-language Support**: Service in customer's preferred language
- **Fast Response Times**: Real-time streaming responses
- **Comprehensive Support**: Product info, orders, technical help, appointments

### For Business
- **Reduced Support Costs**: AI handles routine inquiries
- **Data-Driven Insights**: ML predictions inform strategy
- **Improved Efficiency**: Automated report analysis
- **Customer Retention**: Churn prediction enables proactive action
- **Scalability**: Microservices architecture supports growth
- **Knowledge Management**: Centralized, always-updated knowledge base

### For Staff
- **Enhanced Productivity**: AI-powered tools for analysis
- **Better Decision-Making**: Data insights and visualizations
- **Collaboration Tools**: Team chat for complex problems
- **Time Savings**: Automated report processing

---
---

## 📞 Support & Documentation

- **Backend API Documentation**: Available at `/docs` endpoint for each service
- **Frontend Documentation**: See `FRONTEND/README.md`
- **Backend Details**: See `BACKEND/README.md`

---

## 📄 License

See LICENSE file for details.

---

**Built with ❤️ for FPT Shop**

