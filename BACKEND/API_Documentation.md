# Backend Microservices API Documentation

## Overview

This backend consists of 5 microservices running behind an Nginx reverse proxy. After running `docker-compose up -d`, all services are accessible through port **8090**.

### Service Architecture
- **AUTH** (container: `de_an_auth`) → `/auth/` → User authentication and authorization
- **ML** (container: `de_an_ml`) → `/ml/` → Machine learning models for sentiment analysis and churn prediction  
- **BE_PREPROCESS** (container: `de_an_preprocess`) → `/preprocess/` → Document processing (URLs and PDFs)
- **BE_CHATBOT** (container: `de_an_chatbot`) → `/chat/` → Real-time chat functionality
- **BE_ADMIN** (container: `de_an_admin`) → `/admin/` → Team collaboration and report analysis

### Getting Started
```bash
docker-compose up -d
```

**Frontend Base URL**: `http://localhost:8090` (Nginx proxy port)

### Docker Architecture Explanation

**Internal Container Communication** (docker-compose.yml):
```
nginx:8090 → auth:8888 (container: de_an_auth)
nginx:8090 → ml:8888 (container: de_an_ml) 
nginx:8090 → be_admin:8888 (container: de_an_admin)
nginx:8090 → be_chatbot:8888 (container: de_an_chatbot)
nginx:8090 → be_preprocess:8888 (container: de_an_preprocess)
```

**Frontend Access** (what you should use):
- ✅ `http://localhost:8090/auth/` → AUTH service
- ✅ `http://localhost:8090/ml/` → ML service  
- ✅ `http://localhost:8090/admin/` → Admin service
- ✅ `http://localhost:8090/chat/` → Chatbot service
- ✅ `http://localhost:8090/preprocess/` → Preprocessing service

**❌ DO NOT use direct container ports:**
- ❌ `http://localhost:8888` (individual service ports)
- ❌ Container names like `de_an_auth`, `be_admin` (only for internal Docker communication)

---

## Authentication Service (`/auth/`)

### Register User
**POST** `/auth/v1/auth/register`

**Request Body:**
```json
{
  "customer_name": "john_doe",
  "address": "123 Main St",
  "age": 25,
  "customer_phone": "+1234567890",
  "password": "SecurePass123!",
  "email": "john@example.com",
  "role": "user",
}
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user_id": "USER_abc123def",
  "email": "john@example.com",
  "role": "user"
}
```

### Login
**POST** `/auth/v1/auth/login`

**Request Body:**
```json
{
  "customer_name_or_email": "john@example.com",
  "password": "SecurePass123!"
}
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user_id": "USER_abc123def",
  "email": "john@example.com",
  "role": "user"
}
```

### Forgot Password
**POST** `/auth/v1/auth/forgot-password`

**Request Body:**
```json
{
  "customer_name": "john_doe",
  "email": "john@example.com"
}
```

**Response:**
```json
{
  "message": "A new temp password has been sent to your email."
}
```

### Change Password
**POST** `/auth/v1/auth/change-password`

**Request Body:**
```json
{
  "customer_name": "john_doe",
  "email": "john@example.com",
  "new_password": "NewSecurePass123!"
}
```

**Response:**
```json
{
  "message": "Password updated successfully"
}
```

---

## ML Service (`/ml/`) - Requires staff/admin role

### Sentiment Analysis Prediction
**POST** `/ml/v1/sentiment/predict/`

**Headers:**
```
Authorization: Bearer <access_token>
Content-Type: multipart/form-data
```

**Request Body (Form Data):**
```
file: <CSV file containing text data>
model_version: "1" (optional)
tokenizer_version: "tokenizer/tokenizer_version_20250701T105905.pkl" (optional)
run_id: "a523ba441ea0465085716dcebb916294" (optional)
```

**Response:**
```json
{
  "payload": {
    "message": "📊Rating Analysis Complete:\n• Average Rating: 3.75/5.0\n• Total Records Processed: 150\n• Rating Distribution: {1.0: 10, 2.0: 15, 3.0: 45, 4.0: 50, 5.0: 30}\n• Prediction Confidence: 87.50%\n✅ Prediction confidence meets quality threshold",
    "s3_url": "https://dataversion0205.s3.us-east-1.amazonaws.com/sentiment_data_store/prediction/prediction__sentiment_20250925T143025.csv",
    "s3_results_data": [
      {
        "review": "This product is amazing",
        "predicted_sentiment": 4.5,
        "rating": 4.5
      }
    ],
    "summary": {
      "total_records": 150,
      "average_rating": 3.75,
      "rating_distribution": {
        "1.0": 10,
        "2.0": 15,
        "3.0": 45,
        "4.0": 50,
        "5.0": 30
      }
    },
    "timestamp": "2025-09-25 14:30:25"
  },
  "mlflow_url": "https://dagshub.com/Teungtran/MY_DE_AN.mlflow"
}
```

### Churn Prediction  
**POST** `/ml/v1/churn/predict/`

**Headers:**
```
Authorization: Bearer <access_token>
Content-Type: multipart/form-data
```

**Request Body (Form Data):**
```
file: <CSV file containing customer data>
model_version: "1" (optional)
scaler_version: "scaler_churn_version_20250701T105905.pkl" (optional)
run_id: "b523ba441ea0465085716dcebb916294" (optional)
```

**Response:**
```json
{
  "payload": {
    "message": "✅ Average prediction confidence (89.50%) is above the threshold of 85.00%. No further action required.",
    "s3_url": "https://dataversion0205.s3.us-east-1.amazonaws.com/churn_data_store/prediction/prediction_churn_20250925T143045.csv",
    "s3_results_data": [
      {
        "customer_id": "CUST_001",
        "Customer_Name": "John Doe",
        "Frequency": 15,
        "TotalSpent": 2500.75,
        "Recency": 30,
        "Churn_RATE": 0.23,
        "LastPurchaseDate": "2025-08-25"
      }
    ],
    "summary": {
      "total_records": 500,
      "churn_count": 75,
      "not_churn_count": 425,
      "average_confidence": 0.895
    },
    "timestamp": "2025-09-25 14:30:45"
  },
  "mlflow_url": "https://dagshub.com/Teungtran/MY_DE_AN.mlflow"
}
```

### Sentiment Model Training (Admin only)
**POST** `/ml/v1/sentiment/train/`

**Headers:**
```
Authorization: Bearer <access_token>
Content-Type: multipart/form-data
```

**Request Body (Form Data):**
```
file: <CSV/Excel file for training data> (optional)
```

**Response:**
```json
{
  "status": "success",
  "message": "Model training workflow completed successfully",
  "mlflow_url": "https://dagshub.com/Teungtran/MY_DE_AN.mlflow"

  }

```

### Churn Model Training (Admin only)
**POST** `/ml/v1/churn/train/`

**Headers:**
```
Authorization: Bearer <access_token>
Content-Type: multipart/form-data
```

**Request Body (Form Data):**
```
file: <CSV/Excel file for training data> (optional)
```

**Response:**
```json
{
  "status": "success",
  "message": "Model training workflow completed successfully",
  "mlflow_url": "https://dagshub.com/Teungtran/MY_DE_AN.mlflow",
}
```


## Preprocessing Service (`/preprocess/`)

### RAG URL Processing
**POST** `/preprocess/internal/v1/url/urls-rag/`

**Request Body:**
```json
{
  "urls": [
    {
      "source": "https://example.com/article",
      "description": "Technology article",
      "type": "RAG",
      "is_active": true
    }
  ]
}
```

**Response:**
```json
{
  "message": "Successfully processed URLs: https://example.com/article"
}
```

### Expert Knowledge URL Processing
**POST** `/preprocess/internal/v1/url/urls-expert/`

**Request Body:**
```json
{
  "urls": [
    {
      "source": "https://expertsite.com/knowledge",
      "description": "Expert knowledge base",
      "type": "EXPERT_KNOWLEDGE",
      "is_active": true
    }
  ]
}
```

**Response:**
```json
{
  "message": "Successfully processed URLs: https://expertsite.com/knowledge"
}
```

### Recommendation Data Processing
**POST** `/preprocess/internal/v1/url/recommend/`

**Request Body:**
```json
{
  "urls": [
    {
      "source": "https://products.com/catalog",
      "description": "Product catalog",
      "type": "RECOMMEND",
      "is_active": true
    }
  ]
}
```

**Response:**
```json
{
  "message": "Successfully processed URLs: https://products.com/catalog"
}
```

### RAG PDF Processing
**POST** `/preprocess/internal/v1/pdf/pdf-rag/`

**Headers:**
```
Content-Type: multipart/form-data
```

**Request Body (Form Data):**
```
files: <PDF files array>
```

**Response:**
```json
{
  "message": "Successfully processed PDF files: document1.pdf, document2.pdf"
}
```

### Expert Knowledge PDF Processing
**POST** `/preprocess/internal/v1/pdf/pdf-expert/`

**Headers:**
```
Content-Type: multipart/form-data
```

**Request Body (Form Data):**
```
files: <PDF files array>
```

**Response:**
```json
{
  "message": "Successfully processed PDF files: expert_doc.pdf"
}
```


## Chatbot Service (`/chat/`) - Requires user role

### Real-time Chat: Send Message & Get AI Response
**POST** `/chat/v1/chat/streaming-answer`

**Purpose**: Send a message to the AI and receive streaming response chunks in real-time.

**Headers:**
```
Authorization: Bearer <access_token>
Content-Type: application/json
```

**Request Body:**
```json
{
  "conversation_id": uuid_auto generated,
  "message": "Hello, how can you help me?"
}
```

**Response (Server-Sent Events):**
```
Content-Type: text/event-stream

data: {"response": "Hello! I'm", "tools": null, "prompt_token": 10, "completion_token": 2, "title": "Greeting", "conversation_id": "conv_123456"}

data: {"response": " here to help", "tools": null, "prompt_token": 10, "completion_token": 5, "title": "Greeting", "conversation_id": "conv_123456"}

data: {"response": " you today.", "tools": null, "prompt_token": 10, "completion_token": 8, "title": "Greeting", "conversation_id": "conv_123456"}
```
**NOTE**: store in side bar the title ( and conversation_id for track chat history later)
**Frontend Implementation:**
```javascript
// Use this when user sends a message
const sendMessage = async (conversationId, message) => {
  const response = await fetch(`${API_BASE_URL}/chat/v1/chat/streaming-answer`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${getAuthToken()}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      conversation_id: conversationId,
      message: message
    })
  });

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  
  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    
    const chunk = decoder.decode(value);
    const lines = chunk.split('\n');
    
    for (const line of lines) {
      if (line.startsWith('data: ')) {
        const data = JSON.parse(line.slice(6));
        appendToChatUI(data.response); // Append to chat bubble
      }
    }
  }
};
```

### 📖 Get Chat History (Static)
**GET** `/chat/v1/chat/{conversation_id}/messages`

**Purpose**: Retrieve complete chat history as a single HTTP request.

**Headers:**
```
Authorization: Bearer <access_token>
```
**Request Body:**
```json
{
  "conversation_id": uuid_auto generated (store in UI on side bar),
}
```
**Response:**
```json
[
  {
    "role": "human",
    "content": "Hello"
  },
  {
    "role": "ai",
    "content": "Hi there! How can I help you?"
  }
]
```

**Frontend Implementation:**
```javascript
// Use this to load conversation history when opening a chat
const loadChatHistory = async (conversationId) => {
  const response = await fetch(`${API_BASE_URL}/chat/v1/chat/${conversationId}/messages`, {
    headers: {
      'Authorization': `Bearer ${getAuthToken()}`
    }
  });
  
  const messages = await response.json();
  messages.forEach(message => addMessageToChatHistory(message));
};
```


---

## Admin Service (`/admin/`) - Requires staff/admin role

### Get Chat History
**GET** `/admin/v1/chat/{id}/messages`

**Response:**
```json
[
  {
    "role": "human",
    "content": "What's our team performance?"
  },
  {
    "role": "ai",
    "content": "Based on recent data, your team performance shows excellent results..."
  }
]
```

### Team Chat (Streaming)
**POST** `/admin/v1/chat/team/chat/stream`

**Headers:**
```
Authorization: Bearer <access_token>
Content-Type: application/json
```

**Query Parameters:**
```
id: session_id (optional - generates UUID if not provided)
```

**Request Body:**
```json
{
  "message": "What's our sales performance this quarter?"
}
```

**Response (Server-Sent Events):**
```
Content-Type: text/event-stream

event: chunk
data: {"content": "Based on the data", "timestamp": "2025-09-25T14:30:00"}

event: chunk  
data: {"content": " analysis, our sales", "timestamp": "2025-09-25T14:30:01"}

event: chunk
data: {"content": " shows great results.", "title": "Sales performance inquiry", "session_id": "550e8400-e29b-41d4-a716-446655440000", "timestamp": "2025-09-25T14:30:02"}

event: complete
data: {"status": "completed", "title": "Sales performance inquiry", "session_id": "550e8400-e29b-41d4-a716-446655440000", "timestamp": "2025-09-25T14:30:05"}

event: error
data: {"error": "Error message", "timestamp": "2025-09-25T14:30:05"}
```

**Response Structure:**
- **Streaming chunks**: `content` + `timestamp` only
- **Final chunk**: `content` + `title` + `session_id` + `timestamp` 
- **Complete event**: `status` + `title` + `session_id` + `timestamp`
- **Error event**: `error` + `timestamp`


### Report File Upload
**POST** `/admin/v1/chat/report/upload`

**Headers:**
```
Authorization: Bearer <access_token>
Content-Type: multipart/form-data
```

**Request Body (Form Data):**
```
file: <CSV, XLSX, or XLS file>
```

**Response:**
```json
{
  "filename": "sales_report.csv",
  "data": [
    {
      "date": "2025-01-01",
      "sales": 1000,
      "region": "North"
    },
    {
      "date": "2025-01-02",
      "sales": 1200,
      "region": "South"
    }
  ]
}
```

### Report Analysis (Streaming)
**POST** `/admin/v1/chat/report/analyze`

**Headers:**
```
Authorization: Bearer <access_token>
Content-Type: application/x-www-form-urlencoded
```

**Request Body (Form Data):**
```
question: "What is the average sales by region?"
```

**Response (Server-Sent Events):**
```
Content-Type: text/event-stream

event: chunk
data: {"content": "Analyzing", "timestamp": "2025-09-25T14:30:00"}

event: chunk
data: {"content": " the sales data", "timestamp": "2025-09-25T14:30:01"}

event: complete
data: {"status": "completed", "timestamp": "2025-09-25T14:30:03"}

event: error
data: {"error": "Analysis failed", "timestamp": "2025-09-25T14:30:03"}
```



## Quick Reference

### Base URL
```javascript
const API_BASE_URL = 'http://localhost:8090';
```

### Authentication
```javascript
// Login and store token
const response = await fetch(`${API_BASE_URL}/auth/v1/auth/login`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    customer_name_or_email: "user@example.com",
    password: "SecurePass123!"
  })
});
const data = await response.json();
localStorage.setItem('access_token', data.access_token);
```

---

## 🔐 Authentication & Role-Based Access Control

### JWT Token Structure
All authenticated requests require a JWT token in the Authorization header:
```
Authorization: Bearer <JWT_TOKEN>
```

**Token Payload:**
```json
{
  "sub": "USER_abc123def",  // user_id
  "email": "user@example.com",
  "role": "user|staff|admin",
  "exp": 1735689600  // expiration timestamp
}
```

**Token Expiration**: 30 minutes

### Role Hierarchy & Access Control

#### 🟢 **USER Role** (`USER_xxxxxxx`)
**Registration**: Default role for new registrations
**Access Level**: Basic chatbot functionality

**Allowed Endpoints**:
- ✅ All Authentication endpoints (`/auth/v1/auth/*`)
- ✅ Chatbot Service (`/chat/v1/chat/*`)
  - Send messages and get AI responses
  - Access conversation history
  - Subscribe to conversation updates

**Blocked From**:
- ❌ ML predictions and training
- ❌ Admin team chat
- ❌ Report analysis
- ❌ Data preprocessing

---

#### 🟡 **STAFF Role** (`STAFF_xxxxxxx`) 
**Registration**: Must be set during registration with `"role": "staff"`
**Access Level**: Operations and analytics

**Allowed Endpoints**:
- ✅ **All USER permissions** +
- ✅ **ML Service** - Predictions (`/ml/v1/*/predict/`)
  - Sentiment analysis predictions
  - Churn prediction analysis
- ✅ **Admin Service** (`/admin/v1/chat/*`)
  - Team chat (streaming & non-streaming)
  - Report file upload and analysis
  - Chat history access

**Blocked From**:
- ❌ ML model training (`/ml/v1/*/train/`)
- ❌ Training status checks

---

#### 🔴 **ADMIN Role** (`ADMIN_xxxxxxx`)
**Registration**: Must be set during registration with `"role": "admin"`  
**Access Level**: Full system access

**Allowed Endpoints**:
- ✅ **All USER + STAFF permissions** +
- ✅ **ML Service** - Training (`/ml/v1/*/train/`)
  - Model retraining for sentiment and churn
  - Training status monitoring
- ✅ **Data Preprocessing** (`/preprocess/internal/v1/*`)
  - URL processing for RAG, expert knowledge, recommendations
  - PDF processing and ingestion

### Role-Based Authentication Functions

#### **AUTH Service** (`require_role()`)
```python
# Specific role requirement
require_role("admin")    # Admin only
require_role("staff")    # Staff only  
require_role("user")     # User only
```

#### **CHATBOT Service** (`require_user_role()`)
```python
# User role required (basic chat access)
require_user_role()  # user role only
```

#### **ADMIN Service** (`require_store_role()`)
```python
# Staff or Admin required (elevated access)
require_store_role()  # staff OR admin
```

#### **ML Service** (`require_staff_or_admin()` / `require_admin_role()`)
```python
# Predictions: Staff or Admin
require_staff_or_admin()  # staff OR admin

# Training: Admin only  
require_admin_role()     # admin only
```

### User ID Format & Generation

**User ID Patterns**:
- `USER_xxxxxxx` - Regular users
- `STAFF_xxxxxxx` - Staff members  
- `ADMIN_xxxxxxx` - Administrators

**Generation**: 9-character base64-encoded UUID fragment

### Password Requirements
- **Minimum length**: 10 characters
- **Must contain**:
  - At least 1 uppercase letter
  - At least 1 digit
  - At least 1 special character

### Error Responses

**401 Unauthorized**:
```json
{
  "detail": "Token has expired"
}
```

**403 Forbidden**:
```json
{
  "detail": "Forbidden: Access is restricted to admin users only."
}
```

### Frontend Role Checking

```javascript
// Get user role from token or stored user data
const getUserRole = () => {
  return localStorage.getItem('user_role');
};

// Check permissions for UI elements
const canAccessML = () => {
  const role = getUserRole();
  return ['staff', 'admin'].includes(role);
};

const canTrainModels = () => {
  const role = getUserRole();
  return role === 'admin';
};

const canAccessTeamChat = () => {
  const role = getUserRole();
  return ['staff', 'admin'].includes(role);
};

// Use in React/Vue components
const MLSection = () => {
  if (!canAccessML()) {
    return <AccessDenied message="Staff or Admin role required" />;
  }
  
  return (
    <div>
      <SentimentAnalysis />
      <ChurnPrediction />
      {canTrainModels() && <ModelTraining />}
    </div>
  );
};
```

### Complete Access Matrix

| **Feature** | **USER** | **STAFF** | **ADMIN** |
|-------------|----------|-----------|-----------|
| **Authentication** | ✅ | ✅ | ✅ |
| **Chatbot (Personal)** | ✅ | ✅ | ✅ |
| **ML Predictions** | ❌ | ✅ | ✅ |
| **ML Training** | ❌ | ❌ | ✅ |
| **Team Chat** | ❌ | ✅ | ✅ |
| **Report Analysis** | ❌ | ✅ | ✅ |
| **Data Processing** | ❌ | ❌ | ✅ |

---


## Summary

**29 Total Endpoints** across 5 microservices:
- **5 Auth endpoints**: Registration, login, password management
- **8 ML endpoints**: Sentiment & churn prediction/training with status checks
- **6 Preprocessing endpoints**: URL & PDF processing for different data types
- **4 Chat endpoints**: Streaming chat, history, subscriptions
- **6 Admin endpoints**: Chat history, team chat (streaming & non-streaming), report upload/analysis

**Key Features:**
- JWT authentication with role hierarchy
- Real-time streaming via Server-Sent Events
- File upload support (PDF, CSV, Excel)
- Interactive docs at `/docs` for each service
