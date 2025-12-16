import React, { createContext, useContext, useState, ReactNode } from 'react';
import { adminAPI } from '../utils/api';
import { toast } from 'sonner';

interface Message {
  id: string;
  content: string;
  sender: 'user' | 'ai';
  senderName?: string;
  timestamp: Date;
}

interface Report {
  id: string;
  name: string;
  uploadedAt: Date;
  status: 'processing' | 'ready';
}

interface UploadResponse {
  filename: string;
  data: Record<string, any>[];
}

interface ReportContextType {
  messages: Message[];
  setMessages: React.Dispatch<React.SetStateAction<Message[]>>;
  message: string;
  setMessage: React.Dispatch<React.SetStateAction<string>>;
  isTyping: boolean;
  setIsTyping: React.Dispatch<React.SetStateAction<boolean>>;
  reports: Report[];
  setReports: React.Dispatch<React.SetStateAction<Report[]>>;
  uploadedData: UploadResponse | null;
  setUploadedData: React.Dispatch<React.SetStateAction<UploadResponse | null>>;
  showDataTable: boolean;
  setShowDataTable: React.Dispatch<React.SetStateAction<boolean>>;
  chatCollapsed: boolean;
  setChatCollapsed: React.Dispatch<React.SetStateAction<boolean>>;
  dataCollapsed: boolean;
  setDataCollapsed: React.Dispatch<React.SetStateAction<boolean>>;
  handleFileUpload: (event: React.ChangeEvent<HTMLInputElement>) => Promise<void>;
  sendMessage: () => Promise<void>;
  clearChat: () => void;
}

const ReportContext = createContext<ReportContextType | undefined>(undefined);

export function ReportProvider({ children }: { children: ReactNode }) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [message, setMessage] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [reports, setReports] = useState<Report[]>([]);
  const [uploadedData, setUploadedData] = useState<UploadResponse | null>(null);
  const [showDataTable, setShowDataTable] = useState(false);
  const [chatCollapsed, setChatCollapsed] = useState(false);
  const [dataCollapsed, setDataCollapsed] = useState(false);

  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    const allowedTypes = ['text/csv', 'application/vnd.ms-excel', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'];
    if (!allowedTypes.includes(file.type)) {
      toast.error('Please upload a CSV, XLS, or XLSX file');
      return;
    }

    setUploadedData(null);
    setShowDataTable(false);

    const newReport: Report = {
      id: Date.now().toString(),
      name: file.name,
      uploadedAt: new Date(),
      status: 'processing'
    };

    setReports([newReport]);

    try {
      const response = await adminAPI.uploadReport(file);
      
      setReports(prev => prev.map(r => 
        r.id === newReport.id ? { ...r, status: 'ready' } : r
      ));

      if (response && response.data) {
        setUploadedData(response);
        setShowDataTable(true);
        
        const welcomeMessage: Message = {
          id: 'upload-success',
          content: `📊 **Report Analysis Ready**

I've successfully processed your file: **${file.name}**

**Data Summary:**
- Total records: ${response.data.length}
- Columns detected: ${Object.keys(response.data[0] || {}).length}

I can help you analyze this data! Here are some things you can ask me:

🔍 **Data Exploration:**
- "Show me a summary of the data"
- "What are the key trends?"
- "Analyze the performance metrics"

📈 **Insights & Analysis:**
- "What patterns do you see?"
- "Generate insights from this data"
- "Create a report summary"

📊 **Specific Questions:**
- Ask about specific columns or metrics
- Request comparisons or correlations
- Get recommendations based on the data

What would you like to explore first?`,
          sender: 'ai',
          timestamp: new Date()
        };
        
        setMessages([welcomeMessage]);
        toast.success(`Report uploaded successfully! ${response.data.length} records processed.`);
      }
    } catch (error: any) {
      console.error('Upload error:', error);
      setReports(prev => prev.map(r => 
        r.id === newReport.id ? { ...r, status: 'ready' } : r
      ));
      toast.error(`Failed to upload report: ${error?.message || 'Unknown error'}`);
    }

    event.target.value = '';
  };

  const sendMessage = async () => {
    if (!message.trim()) return;

    const userMessage = message;
    const newMessage: Message = {
      id: Date.now().toString(),
      content: userMessage,
      sender: 'user',
      senderName: 'User',
      timestamp: new Date()
    };

    setMessages(prev => [...prev, newMessage]);
    setMessage('');
    setIsTyping(true);

    const aiMessageId = (Date.now() + 1).toString();
    const aiResponse: Message = {
      id: aiMessageId,
      content: '',
      sender: 'ai',
      timestamp: new Date()
    };

    setMessages(prev => [...prev, aiResponse]);

    try {
      let context = '';
      if (uploadedData && uploadedData.data && uploadedData.data.length > 0) {
        const sampleData = uploadedData.data.slice(0, 5);
        context = `\n\nContext: User has uploaded a report file "${uploadedData.filename}" with ${uploadedData.data.length} records. Here's a sample of the data:\n${JSON.stringify(sampleData, null, 2)}`;
      }

      const response = await adminAPI.analyzeReport(userMessage + context);
      
      setMessages(prev => prev.map(msg => 
        msg.id === aiMessageId 
          ? { ...msg, content: response.content || '' }
          : msg
      ));
      
      setIsTyping(false);
    } catch (error) {
      console.error('Report chat error:', error);
      setMessages(prev => prev.map(msg => 
        msg.id === aiMessageId 
          ? { ...msg, content: 'Sorry, I encountered an error analyzing your report. Please try again.' }
          : msg
      ));
      setIsTyping(false);
    }
  };

  const clearChat = () => {
    if (window.confirm('Are you sure you want to clear the chat history?')) {
      setMessages([]);
    }
  };

  return (
    <ReportContext.Provider value={{
      messages,
      setMessages,
      message,
      setMessage,
      isTyping,
      setIsTyping,
      reports,
      setReports,
      uploadedData,
      setUploadedData,
      showDataTable,
      setShowDataTable,
      chatCollapsed,
      setChatCollapsed,
      dataCollapsed,
      setDataCollapsed,
      handleFileUpload,
      sendMessage,
      clearChat
    }}>
      {children}
    </ReportContext.Provider>
  );
}

export function useReportContext() {
  const context = useContext(ReportContext);
  if (context === undefined) {
    throw new Error('useReportContext must be used within a ReportProvider');
  }
  return context;
}
