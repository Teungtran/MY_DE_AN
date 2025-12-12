// API Configuration and Utilities
// In production (Docker), use relative URL since frontend is served by nginx
// In development, use localhost for direct API access
export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 
  (import.meta.env.MODE === 'production' ? '' : 'http://localhost:8090');

// Auth token management
export const getAuthToken = (): string | null => {
  return localStorage.getItem('access_token');
};

export const setAuthToken = (token: string): void => {
  localStorage.setItem('access_token', token);
};

export const removeAuthToken = (): void => {
  localStorage.removeItem('access_token');
  localStorage.removeItem('user_data');
};

export const getUserData = () => {
  const userData = localStorage.getItem('user_data');
  return userData ? JSON.parse(userData) : null;
};

export const setUserData = (userData: any): void => {
  localStorage.setItem('user_data', JSON.stringify(userData));
};

// API request wrapper with auth
export const apiRequest = async (endpoint: string, options: RequestInit = {}) => {
  const token = getAuthToken();
  const url = `${API_BASE_URL}${endpoint}`;
  
  const config: RequestInit = {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...(token && { Authorization: `Bearer ${token}` }),
      ...options.headers,
    },
  };

  const response = await fetch(url, config);
  
  if (response.status === 401) {
    removeAuthToken();
    window.location.href = '/login';
    throw new Error('Authentication failed');
  }

  return response;
};

// API request wrapper for form data
export const apiRequestFormData = async (endpoint: string, formData: FormData) => {
  const token = getAuthToken();
  const url = `${API_BASE_URL}${endpoint}`;
  
  const config: RequestInit = {
    method: 'POST',
    body: formData,
    headers: {
      ...(token && { Authorization: `Bearer ${token}` }),
    },
  };

  const response = await fetch(url, config);
  
  if (response.status === 401) {
    removeAuthToken();
    window.location.href = '/login';
    throw new Error('Authentication failed');
  }

  return response;
};

// Streaming response handler
export const handleStreamingResponse = async (
  endpoint: string,
  data: any,
  onChunk: (chunk: string) => void,
  onComplete?: () => void,
  onError?: (error: string) => void
) => {
  try {
    const response = await apiRequest(endpoint, {
      method: 'POST',
      body: JSON.stringify(data),
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const reader = response.body?.getReader();
    const decoder = new TextDecoder();

    if (!reader) {
      throw new Error('No reader available');
    }

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      const chunk = decoder.decode(value);
      const lines = chunk.split('\n');

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          try {
            const data = JSON.parse(line.slice(6));
            if (data.response) {
              onChunk(data.response);
            } else if (data.content) {
              onChunk(data.content);
            }
          } catch (e) {
            // Ignore parsing errors for incomplete chunks
          }
        }
      }
    }

    onComplete?.();
  } catch (error) {
    console.error('Streaming error:', error);
    onError?.(error instanceof Error ? error.message : 'Unknown error');
  }
};

// Auth API functions
export const authAPI = {
  register: async (userData: {
    customer_name: string;
    address: string;
    age: number;
    customer_phone: string;
    password: string;
    email: string;
    role: string;
  }) => {
    const response = await apiRequest('/auth/v1/auth/register', {
      method: 'POST',
      body: JSON.stringify(userData),
    });
    return response.json();
  },

  login: async (credentials: {
    customer_name_or_email: string;
    password: string;
  }) => {
    const response = await apiRequest('/auth/v1/auth/login', {
      method: 'POST',
      body: JSON.stringify(credentials),
    });
    return response.json();
  },

  forgotPassword: async (data: {
    customer_name: string;
    email: string;
  }) => {
    const response = await apiRequest('/auth/v1/auth/forgot-password', {
      method: 'POST',
      body: JSON.stringify(data),
    });
    return response.json();
  },

  changePassword: async (data: {
    customer_name: string;
    email: string;
    new_password: string;
  }) => {
    const response = await apiRequest('/auth/v1/auth/change-password', {
      method: 'POST',
      body: JSON.stringify(data),
    });
    return response.json();
  },
};

// ML API functions
export const mlAPI = {
  sentimentPredict: async (file: File, options?: {
    model_version?: string;
    tokenizer_version?: string;
    run_id?: string;
  }) => {
    const formData = new FormData();
    formData.append('file', file);
    if (options?.model_version) formData.append('model_version', options.model_version);
    if (options?.tokenizer_version) formData.append('tokenizer_version', options.tokenizer_version);
    if (options?.run_id) formData.append('run_id', options.run_id);

    const response = await apiRequestFormData('/ml/v1/sentiment/predict/', formData);
    return response.json();
  },

  churnPredict: async (file: File, options?: {
    model_version?: string;
    scaler_version?: string;
    run_id?: string;
  }) => {
    const formData = new FormData();
    formData.append('file', file);
    if (options?.model_version) formData.append('model_version', options.model_version);
    if (options?.scaler_version) formData.append('scaler_version', options.scaler_version);
    if (options?.run_id) formData.append('run_id', options.run_id);

    const response = await apiRequestFormData('/ml/v1/churn/predict/', formData);
    return response.json();
  },

  sentimentTrain: async (file?: File) => {
    const formData = new FormData();
    if (file) formData.append('file', file);

    const response = await apiRequestFormData('/ml/v1/sentiment/train/', formData);
    return response.json();
  },

  churnTrain: async (file?: File) => {
    const formData = new FormData();
    if (file) formData.append('file', file);

    const response = await apiRequestFormData('/ml/v1/churn/train/', formData);
    return response.json();
  },
};

// Chat API functions
export const chatAPI = {
  sendMessage: async (
    conversationId: string, 
    message: string, 
    onChunk: (chunk: string, data?: any) => void,
    onComplete?: (data: any) => void
  ) => {
    try {
      const response = await apiRequest('/chat/v1/chat/streaming-answer', {
        method: 'POST',
        body: JSON.stringify({ conversation_id: conversationId, message }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const reader = response.body?.getReader();
      const decoder = new TextDecoder();

      if (!reader) {
        throw new Error('No reader available');
      }

      let lastData: any = null;

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value);
        const lines = chunk.split('\n');

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.slice(6));
              lastData = data;
              if (data.response) {
                onChunk(data.response, data);
              }
            } catch (e) {
              // Ignore parsing errors for incomplete chunks
            }
          }
        }
      }

      if (onComplete && lastData) {
        onComplete(lastData);
      }
    } catch (error) {
      console.error('Streaming error:', error);
      throw error;
    }
  },

  getChatHistory: async (conversationId: string) => {
    const response = await apiRequest(`/chat/v1/chat/${conversationId}/messages`);
    return response.json();
  },

  getAllConversations: async () => {
    const response = await apiRequest('/chat/v1/chat/messages');
    return response.json();
  },
};

// Admin API functions
export const adminAPI = {
  getChatHistory: async (id: string) => {
    const response = await apiRequest(`/admin/v1/chat/${id}/messages`);
    return response.json();
  },

  getAllConversations: async (userId: string) => {
    const response = await apiRequest(`/admin/v1/chat/messages?user_id=${userId}`);
    return response.json();
  },

  teamChatStream: async (message: string, sessionId?: string) => {
    const url = sessionId ? `/admin/v1/chat/team/chat/stream?id=${sessionId}` : '/admin/v1/chat/team/chat/stream';
    const response = await apiRequest(url, {
      method: 'POST',
      body: JSON.stringify({ message }),
    });
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    return response.json();
  },

  uploadReport: async (file: File) => {
    const formData = new FormData();
    formData.append('file', file);

    const response = await apiRequestFormData('/admin/v1/chat/report/upload', formData);
    
    if (!response.ok) {
      const errorText = await response.text().catch(() => 'Unknown error');
      let errorMessage = `HTTP error! status: ${response.status}`;
      try {
        const errorJson = JSON.parse(errorText);
        errorMessage = errorJson.detail || errorMessage;
      } catch {
        errorMessage = errorText || errorMessage;
      }
      throw new Error(errorMessage);
    }
    
    return response.json();
  },

  analyzeReport: async (question: string) => {
    const formData = new FormData();
    formData.append('question', question);

    const response = await apiRequestFormData('/admin/v1/chat/report/analyze', formData);
    
    if (!response.ok) {
      const errorText = await response.text().catch(() => 'Unknown error');
      throw new Error(`HTTP error! status: ${response.status}, message: ${errorText}`);
    }
    
    return response.json();
  },
};

// Preprocessing API functions
export const preprocessAPI = {
  processRagUrls: async (urls: Array<{
    source: string;
    description: string;
    type: string;
    is_active: boolean;
  }>) => {
    const response = await apiRequest('/preprocess/internal/v1/url/urls-rag/', {
      method: 'POST',
      body: JSON.stringify({ urls }),
    });
    return response.json();
  },

  processExpertUrls: async (urls: Array<{
    source: string;
    description: string;
    type: string;
    is_active: boolean;
  }>) => {
    const response = await apiRequest('/preprocess/internal/v1/url/urls-expert/', {
      method: 'POST',
      body: JSON.stringify({ urls }),
    });
    return response.json();
  },

  processRecommendUrls: async (urls: Array<{
    source: string;
    description: string;
    type: string;
    is_active: boolean;
  }>) => {
    const response = await apiRequest('/preprocess/internal/v1/url/recommend/', {
      method: 'POST',
      body: JSON.stringify({ urls }),
    });
    return response.json();
  },

  processRagPdfs: async (files: File[]) => {
    const formData = new FormData();
    files.forEach(file => formData.append('files', file));

    const response = await apiRequestFormData('/preprocess/internal/v1/pdf/pdf-rag/', formData);
    return response.json();
  },

  processExpertPdfs: async (files: File[]) => {
    const formData = new FormData();
    files.forEach(file => formData.append('files', file));

    const response = await apiRequestFormData('/preprocess/internal/v1/pdf/pdf-expert/', formData);
    return response.json();
  },
};

// Utility functions
export const generateConversationId = (): string => {
  // Generate UUID v4 format
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
    const r = Math.random() * 16 | 0;
    const v = c === 'x' ? r : (r & 0x3 | 0x8);
    return v.toString(16);
  });
};

export const mapBackendRoleToFrontend = (backendRole: string): 'customer' | 'employee' | 'admin' => {
  if (backendRole === 'user') return 'customer';
  if (backendRole === 'staff') return 'employee';
  if (backendRole === 'admin') return 'admin';
  return 'customer'; // fallback
};

export const mapFrontendRoleToBackend = (frontendRole: 'customer' | 'employee' | 'admin'): string => {
  if (frontendRole === 'customer') return 'user';
  if (frontendRole === 'employee') return 'staff';
  if (frontendRole === 'admin') return 'admin';
  return 'user'; // fallback
};