# FPT Shop Customer Service Platform - Backend API

## 🎯 MVP Overview
This is a comprehensive customer service and e-commerce platform for FPT Shop, featuring AI-powered chatbots, sentiment analysis, churn prediction, and admin analytics. The system consists of 5 microservices designed to handle everything from user authentication to ML-powered business insights.

### 🏗️ Core MVP Features:
1. **Customer Authentication** - User registration, login, password reset
2. **AI Customer Service Chat** - Smart chatbot for product recommendations, support, and order management
3. **Admin Analytics Dashboard** - Team collaboration tools and report analysis
4. **ML Predictions** - Sentiment analysis and customer churn prediction
5. **Document Processing** - PDF and URL processing for knowledge base

---

## 🚀 Quick Start
```bash
cd BACKEND
docker-compose up --build
```

**Base URL**: `http://localhost:8090`

### 🔐 Authentication
All endpoints (except auth endpoints) require JWT Bearer token authentication:
```typescript
headers: {
  'Authorization': `Bearer ${token}`,
  'Content-Type': 'application/json'
}
```

---

## 🎨 Recommended Frontend Pages

### 1. **Landing Page** (`/`)
- Hero section showcasing FPT Shop customer service platform
- Feature highlights (AI Chat, Analytics, ML Predictions)
- Call-to-action buttons for Login/Register

### 2. **Authentication Pages**
- **Login Page** (`/login`) - Customer/admin login form
- **Register Page** (`/register`) - New user registration
- **Forgot Password** (`/forgot-password`) - Password reset form

### 3. **Customer Dashboard** (`/dashboard`)
- Personal profile management
- Chat history access
- Order management interface
- Preference settings

### 4. **AI Chat Interface** (`/chat`)
- Real-time streaming chat with AI assistant
- Product recommendation display
- File upload for support documents
- Chat history sidebar

### 5. **Admin Dashboard** (`/admin`) - Staff/Admin Only
- **Team Chat** (`/admin/team-chat`) - Multi-agent collaboration interface
- **Report Analytics** (`/admin/reports`) - Upload and analyze business reports
- **File Management** (`/admin/files`) - Manage uploaded documents

### 6. **ML Analytics** (`/ml`) - Staff/Admin Only
- **Sentiment Analysis** (`/ml/sentiment`) - Upload text data for sentiment prediction
- **Churn Prediction** (`/ml/churn`) - Customer churn risk analysis
- **Model Training** (`/ml/training`) - Admin-only model retraining interface

### 7. **Document Processing** (`/documents`) - Internal Admin
- URL processing for knowledge base
- PDF upload and processing
- Document status monitoring

---

## 1. 🔐 AUTH SERVICE
**Base Path**: `/auth/`
**UI Components Needed**: Login form, Registration form, Password reset form

### Authentication & User Management

#### **POST** `/auth/v1/auth/register`
Register a new user account.

**Request Body:**
```typescript
interface RegisterRequest {
  customer_name: string;
  address: string;
  age: number;
  customer_phone: string; // Vietnamese phone format: 09xxxxxxxx, 03xxxxxxxx, 08xxxxxxxx
  password: string;
  email: string; // Valid email format
  preference_brand?: string[]; // Optional array of preferred brands
  min_price?: string; // Optional minimum price preference
  max_price?: string; // Optional maximum price preference
  role?: "admin" | "user" | "staff"; // Default: "user"
}
```

**Response:**
```typescript
interface AuthResponse {
  access_token: string;
  token_type: "bearer";
  user_id: string;
  email: string;
  role: string;
}
```

**Frontend Form Fields:**
- Customer Name (required)
- Email (required, with validation)
- Phone Number (required, Vietnamese format validation)
- Address (required)
- Age (required, number input)
- Password (required, with strength indicator)
- Preferred Brands (optional, multi-select dropdown)
- Price Range (optional, min/max sliders)

#### **POST** `/auth/v1/auth/login`
Authenticate user and get access token.

**Request Body:**
```typescript
interface LoginRequest {
  customer_name_or_email: string; // Username or email
  password: string;
}
```

**Response:**
```typescript
interface AuthResponse {
  access_token: string;
  token_type: "bearer";
  user_id: string;
  email: string;
  role: string;
}
```

**Frontend Form Fields:**
- Username or Email (required)
- Password (required)
- Remember Me (checkbox)

#### **POST** `/auth/v1/auth/forgot-password`
Initiate password reset process.

**Request Body:**
```typescript
interface ForgotPasswordRequest {
  customer_name: string;
  email: string;
}
```

**Frontend Form Fields:**
- Username (required)
- Email (required)

---

## 2. 👨‍💼 BE_ADMIN SERVICE
**Base Path**: `/admin/`
**Access Control**: Requires `staff` or `admin` role
**UI Components Needed**: Team chat interface, File upload, Report dashboard

### Team Chat & Report Analysis

#### **POST** `/admin/v1/chat/team/chat/stream`
Stream team chat responses with multi-agent collaboration.

**Request Body:**
```typescript
interface TeamChatRequest {
  session_id: string; // Session identifier
  message: string; // User message
}
```

**Response:** Server-Sent Events (SSE) stream
```typescript
// Event stream data
interface StreamResponse {
  type: "chunk" | "error" | "complete";
  content: string;
  timestamp: string;
}
```

**Frontend UI Elements:**
- Chat input with send button
- Message bubbles (user vs AI)
- Typing indicators
- Real-time streaming message display
- Session management ( onside bar show the first message of user like ChatGPT UI)

#### **POST** `/admin/v1/chat/team/chat`
Non-streaming team chat endpoint.

**Request Body:**
```typescript
interface TeamChatRequest {
  session_id: string;
  message: string;
}
```

**Response:**
```typescript
interface TeamChatResponse {
  response: string;
  session_id: string;
  timestamp: string;
}
```

#### **POST** `/admin/v1/chat/report/upload-and-analyze`
Upload and analyze report files (CSV, Excel).

**Request:** Multipart form data
```typescript
interface ReportUploadRequest {
  files: File[]; // CSV or Excel files
  analysis_type?: string; // Optional analysis type
}
```

**Response:**
```typescript
interface ReportAnalysisResponse {
  analysis_results: {
    summary: string;
    insights: string[];
    charts?: any[];
  };
  file_info: {
    filename: string;
    rows: number;
    columns: string[];
  };
}
```

**Frontend UI Elements:**
- Drag & drop file upload area
- File type validation (CSV, Excel)
- Analysis results dashboard

#### **GET** `/admin/v1/chat/report/files`
Get list of uploaded report files.

**Response:**
```typescript
interface ReportFilesResponse {
  files: {
    filename: string;
    upload_date: string;
    size: number;
    status: "processed" | "processing" | "error";
  }[];
}
```

**Frontend UI Elements:**
- File list table
- Status indicators (badges)
- File management actions

---

## 3. 💬 BE_CHATBOT SERVICE
**Base Path**: `/chat/`
**Access Control**: Requires `user`, `staff`, or `admin` role
**UI Components Needed**: Chat interface, Message bubbles, Streaming indicators

### Intelligent Customer Service Chat

#### **POST** `/chat/v1/chat/streaming-answer`
Stream AI-powered customer service responses.

**Request Body:**
```typescript
interface UserInputs {
  message: string; // Customer message
  conversation_id: string; // Conversation identifier
}
```

**Response:** Server-Sent Events (SSE) stream
```typescript
interface StreamChunk {
  type: "chunk" | "tool_call" | "complete" | "error";
  content: string;
  tool?: string; // Tool being called (if applicable)
  metadata?: {
    tokens: number;
    processing_time: number;
  };
}
```

**Features Handled:**
- Product recommendations
- Order management
- IT support
- Appointment booking
- Policy inquiries
- URL content analysis

**Frontend UI Elements:**
- Chat input with send button
- Message bubbles (user vs AI)
- Typing indicators
- Real-time streaming message display
- Session management ( onside bar show the first message of user like ChatGPT UI)

#### **GET** `/chat/{conversation_id}/subscribe`
Subscribe to real-time chat updates.

**Response:** SSE stream for conversation updates

#### **GET** `/chat/{conversation_id}/messages`
Get chat history for a conversation. and show them in UI for that conversation_id (like ChatGPT)

**Response:**
```typescript
interface ChatMessage {
  role: "user" | "assistant";
  content: string;
  timestamp: string;
  metadata?: any;
}

type ChatHistory = ChatMessage[];
```
## ADD a thread, SSE endpoint in UI to listen to redis pubsub so when the backend has data , FRONTEND has data also

Example in Python (Streamlit):
```python
def load_chat_history():
    if st.session_state.user_id:
        messages = redis_client.lrange(f"chat:{st.session_state.user_id}", 0, -1)
        if messages:
            try:
                st.session_state.messages = [json.loads(msg.decode('utf-8') if isinstance(msg, bytes) else msg) for msg in messages]
            except json.JSONDecodeError as e:
                st.error(f"Error loading chat history: {e}")
                print(f"Skipping invalid JSON message: {e}")

def listen_to_sse():
    while st.session_state.sse_active:
        user_id = st.session_state.user_id
        with requests.get(SSE_URL.format(user_id=user_id), stream=True) as response:
            if response.status_code != 200:
                continue
            for line in response.iter_lines():
                if not st.session_state.sse_active:
                    break
                if line:
                    line = line.decode("utf-8").strip()
                    if line.startswith("data: "):
                        line = line.replace("data: ", "", 1).strip()
                    try:
                        message_data = json.loads(line)
                        st.session_state.messages.append(message_data)
                        st.rerun()
                    except json.JSONDecodeError:
                        print(f"Skipping invalid SSE message: {line}")   
  

user_id_input = st.sidebar.text_input("Enter user_id", st.session_state.user_id)
if not st.session_state.sse_active or (user_id_input and user_id_input != st.session_state.user_id):
    if user_id_input and user_id_input != st.session_state.user_id:
        st.session_state.sse_active = False  
        st.session_state.user_id = user_id_input
        st.session_state.messages = [] 
    load_chat_history()
    st.session_state.sse_active = True
    threading.Thread(target=listen_to_sse, daemon=True).start()
```
**Frontend UI Elements:**
- Chat history sidebar
- Conversation list
- Message search functionality

---

## 4. ⚙️ BE_PREPROCESS SERVICE
**Base Path**: `/preprocess/`
**Access Control**: Internal service endpoints
**UI Components Needed**: Admin file management interface

### Document Processing & Vector Storage

#### **POST** `/preprocess/internal/v1/urls-rag/`
Process URLs for RAG (Retrieval-Augmented Generation) system.

**Request Body:**
```typescript
interface UrlsRequest {
  urls: DocumentMetadata[];
}

interface DocumentMetadata {
  source: string; // URL to process
  type: "RECOMMEND" | "RAG" | "EXPERT_KNOWLEDGE";
  is_active?: boolean;
  update_at?: string; // ISO datetime
  description: "URL" | "PDF";
}
```

**Frontend UI Elements:**
- URL input forms
- Document type selection
- Processing status indicators
- Document management table

#### **POST** `/preprocess/internal/v1/pdf-rag/`
Process PDF files for RAG system.

**Request:** Multipart form data
```typescript
interface PDFUploadRequest {
  files: File[]; // PDF files only
}
```

**Frontend UI Elements:**
- PDF drag & drop upload
- Processing progress bars
- File validation messages

---

## 5. 🤖 ML SERVICE
**Base Path**: `/ml/`
**UI Components Needed**: File upload forms, Results dashboards, Training status monitors

### Machine Learning Predictions & Training

#### **POST** `/ml/v1/sentiment/predict/`
Predict sentiment from text data.
**Access Control**: Requires `staff` or `admin` role

**Request:** Multipart form data
```typescript
interface SentimentPredictRequest {
  file: File; // CSV file with text data
  model_version?: string; // Default: "1"
  tokenizer_version?: string; // Default: "tokenizer/tokenizer_version_20250810T020107.pkl"
  run_id?: string; // MLflow run ID
}
```

**Response:**
```typescript
interface SentimentResponse {
  payload: {
    predictions?: {
      text: string;
      sentiment: "positive" | "negative" | "neutral";
      confidence: number;
    }[];
    error?: string;
  };
  user_info: {
    user_id: string;
    role: string;
    email: string;
  };
}
```

**Frontend UI Elements:**
- CSV file upload area
- Model version selectors
- Sentiment results table
- Confidence score indicators
- Sentiment distribution charts

#### **POST** `/ml/v1/churn/predict/`
Predict customer churn probability.

**Response:**
```typescript
interface ChurnResponse {
  payload: {
    predictions?: {
      customer_id: string;
      churn_probability: number;
      risk_level: "low" | "medium" | "high";
    }[];
    error?: string;
  };
}
```

**Frontend UI Elements:**
- Customer data upload
- Risk level badges
- Churn probability charts
- High-risk customer alerts

#### **POST** `/ml/v1/sentiment/train/` & **POST** `/ml/v1/churn/train/`
Model retraining endpoints.
**Access Control**: Requires `admin` role only

**Frontend UI Elements:**
- Training data upload
- Training progress indicators
- Model performance metrics
- Training history logs

#### **GET** `/ml/v1/sentiment/train/status` & **GET** `/ml/v1/churn/train/status`
Check model training status.

**Response:**
```typescript
interface TrainingStatus {
  status: "ready" | "training" | "error";
  data_file_exists: boolean;
  message: string;
}
```

**Frontend UI Elements:**
- Status badges
- Progress indicators
- Error message displays

---

## 🎨 Frontend Design Recommendations

### Color Scheme & Branding:
- **Primary**: FPT Orange (#FF6B35) and Blue (#1B4F72)
- **Secondary**: Clean whites and light grays
- **Accent**: Success greens, warning yellows, error reds

### Key UI Components Needed:
1. **Authentication Forms** - Login, register, forgot password
2. **Chat Interface** - Real-time messaging with streaming
3. **File Upload Components** - Drag & drop areas with validation
4. **Dataframes** - For reports render for report agent and ML when user upload file
5. **Status Indicators** - Badges, progress bars, loading states
6. **Navigation** - Role-based menu system

### Responsive Design:
- Web application

---

## 🔐 Role-Based Access Control

### User Roles:
- **`user`**: Basic customer access (chat, view products)
- **`staff`**: Employee access (all user permissions + ML predictions)
- **`admin`**: Full system access (all permissions + model training, admin features)

### Page Access Matrix:
| Page | User | Staff | Admin |
|------|------|-------|-------|
| Landing, Login, Register | ✅ | ✅ | ✅ |
| Customer Dashboard, Chat | ✅ | ✅ | ✅ |
| Admin Team Chat, Reports | ❌ | ✅ | ✅ |
| ML Predictions | ❌ | ✅ | ✅ |
| Model Training, Document Processing | ❌ | ❌ | ✅ |

---

## 🚀 Frontend Integration Checklist

### Essential Features to Implement:
- [ ] JWT token management with auto-refresh
- [ ] Role-based route protection
- [ ] Server-Sent Events for real-time features
- [ ] File upload with progress indicators
- [ ] Form validation matching backend requirements
- [ ] Error handling with user-friendly messages
- [ ] Loading states for all async operations
- [ ] Responsive design for all screen sizes
- [ ] Dark/light theme toggle
- [ ] Accessibility compliance (WCAG 2.1)

### Performance Optimizations:
- [ ] Lazy loading for heavy components
- [ ] Image optimization
- [ ] Code splitting by routes
- [ ] API response caching
- [ ] Debounced search inputs

### Security Considerations:
- [ ] XSS protection
- [ ] CSRF tokens where needed
- [ ] Secure token storage
- [ ] Input sanitization
- [ ] File upload validation

---

This documentation provides everything needed to generate a comprehensive, production-ready frontend application with v0/Vercel AI that integrates seamlessly with your microservices backend.