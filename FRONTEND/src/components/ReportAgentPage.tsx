import React, { useState, useRef, useEffect } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { ScrollArea } from './ui/scroll-area';
import { Avatar, AvatarFallback } from './ui/avatar';
import { LogOut, Upload, Send, FileText, BarChart3, MessageCircle, Brain, Database } from 'lucide-react';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from './ui/table';
import { FPTLogo } from './FPTLogo';

interface User {
  id: string;
  email: string;
  role: string;
}

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

interface ReportAgentPageProps {
  user: User;
  onLogout: () => void;
}

export function ReportAgentPage({ user, onLogout }: ReportAgentPageProps) {
  const location = useLocation();
  const [messages, setMessages] = useState<Message[]>([
    {
      id: '1',
      content: 'Hello! I\'ve analyzed the uploaded sales report. Here are the key insights I found:\n\n• Total revenue increased by 15% compared to last quarter\n• Top performing product category: Electronics (32% of sales)\n• Customer acquisition rate improved by 8%\n• Peak sales hours: 2-4 PM on weekdays\n\nWould you like me to dive deeper into any specific metric?',
      sender: 'ai',
      timestamp: new Date(Date.now() - 1000 * 60 * 5)
    }
  ]);
  
  const [message, setMessage] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [reports, setReports] = useState<Report[]>([
    {
      id: '1',
      name: 'Q4_Sales_Report.csv',
      uploadedAt: new Date(Date.now() - 1000 * 60 * 30),
      status: 'ready'
    }
  ]);
  const [uploadedData, setUploadedData] = useState<UploadResponse | null>(null);
  
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleFileUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    const newReport: Report = {
      id: Date.now().toString(),
      name: file.name,
      uploadedAt: new Date(),
      status: 'processing'
    };

    setReports(prev => [newReport, ...prev]);

    // Simulate processing and AI analysis
    setTimeout(() => {
      setReports(prev => prev.map(r => 
        r.id === newReport.id ? { ...r, status: 'ready' } : r
      ));

      const aiMessage: Message = {
        id: Date.now().toString(),
        content: `I've successfully processed ${file.name}. Here's what I found:\n\n• ${Math.floor(Math.random() * 1000 + 500)} total records analyzed\n• ${Math.floor(Math.random() * 50 + 20)}% increase in key metrics\n• Identified ${Math.floor(Math.random() * 5 + 3)} significant trends\n• Generated ${Math.floor(Math.random() * 10 + 15)} actionable insights\n\nWhat specific aspect would you like to explore?`,
        sender: 'ai',
        timestamp: new Date()
      };

      setMessages(prev => [...prev, aiMessage]);
    }, 3000);
  };

  const sendMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!message.trim()) return;

    const newMessage: Message = {
      id: Date.now().toString(),
      content: message,
      sender: 'user',
      senderName: user.email.split('@')[0],
      timestamp: new Date()
    };

    setMessages(prev => [...prev, newMessage]);
    setMessage('');
    setIsTyping(true);

    // Simulate AI response
    setTimeout(() => {
      const aiResponse: Message = {
        id: (Date.now() + 1).toString(),
        content: generateAIResponse(message),
        sender: 'ai',
        timestamp: new Date()
      };

      setMessages(prev => [...prev, aiResponse]);
      setIsTyping(false);
    }, 1500);
  };

  const generateAIResponse = (userMessage: string): string => {
    const responses = [
      "Based on the data analysis, I can see some interesting patterns. Let me break down the key findings for you...",
      "That's a great question! Looking at the report data, here's what the numbers show...",
      "I've identified several correlations in the data that might be relevant to your question...",
      "The data suggests some actionable insights. Here are my recommendations based on the analysis...",
      "Let me generate a detailed breakdown of that metric for you with supporting visualizations...",
    ];
    return responses[Math.floor(Math.random() * responses.length)];
  };



  return (
    <div className="h-screen flex flex-col bg-white text-black">
      {/* Header with FPT Logo */}
      <div className="border-b border-gray-200 bg-white">
        <div className="container mx-auto px-4 py-4">
          <FPTLogo />
        </div>
      </div>

      {/* Navigation Tabs */}
      <div className="border-b border-gray-200 bg-white">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <nav className="flex space-x-6">
              <Link
                to="/chat/employee"
                className={`flex items-center space-x-2 px-3 py-2 rounded-md transition-colors ${
                  location.pathname === '/chat/employee'
                    ? 'bg-blue-600 text-white'
                    : 'text-gray-600 hover:text-black hover:bg-gray-100'
                }`}
              >
                <MessageCircle className="h-4 w-4" />
                <span>Chat</span>
              </Link>
              
              <Link
                to="/ml"
                className={`flex items-center space-x-2 px-3 py-2 rounded-md transition-colors ${
                  location.pathname === '/ml'
                    ? 'bg-blue-600 text-white'
                    : 'text-gray-600 hover:text-black hover:bg-gray-100'
                }`}
              >
                <Brain className="h-4 w-4" />
                <span>ML Analysis</span>
              </Link>
              
              <Link
                to="/reports"
                className={`flex items-center space-x-2 px-3 py-2 rounded-md transition-colors ${
                  location.pathname === '/reports'
                    ? 'bg-blue-600 text-white'
                    : 'text-gray-600 hover:text-black hover:bg-gray-100'
                }`}
              >
                <FileText className="h-4 w-4" />
                <span>Report Analysis</span>
              </Link>
              
              {user.role === 'admin' && (
                <Link
                  to="/admin/data"
                  className={`flex items-center space-x-2 px-3 py-2 rounded-md transition-colors ${
                    location.pathname === '/admin/data'
                      ? 'bg-blue-600 text-white'
                      : 'text-gray-600 hover:text-black hover:bg-gray-100'
                  }`}
                >
                  <Database className="h-4 w-4" />
                  <span>Data Admin</span>
                </Link>
              )}
            </nav>
            
            <div className="flex items-center space-x-4">
              <span className="text-gray-600">Welcome, {user.email}</span>
              <Button
                variant="ghost"
                onClick={onLogout}
                className="text-gray-600 hover:text-black"
              >
                <LogOut className="h-4 w-4" />
              </Button>
            </div>
          </div>
        </div>
      </div>

      <div className="flex flex-1 bg-gray-50">
        {/* Left Panel - Chat Discussion */}
        <div className="w-1/2 border-r border-gray-200 flex flex-col bg-white">
          {/* Chat Header */}
          <div className="p-4 border-b border-gray-200 bg-white">
            <div className="flex items-center space-x-3">
              <FileText className="h-6 w-6 text-green-600" />
              <div>
                <h2 className="text-lg font-semibold text-black">Report Discussion</h2>
                <p className="text-sm text-gray-600">Collaborative analysis</p>
              </div>
            </div>
          </div>

        {/* Messages */}
        <ScrollArea className="flex-1 p-4 bg-gray-50">
          <div className="space-y-4">
            {messages.map((msg) => (
              <div
                key={msg.id}
                className={`flex ${msg.sender === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                <div className={`flex space-x-2 max-w-xs lg:max-w-md ${msg.sender === 'user' ? 'flex-row-reverse' : ''}`}>
                  <Avatar className="h-8 w-8">
                    <AvatarFallback className={msg.sender === 'user' ? 'bg-green-600 text-white' : 'bg-black text-white text-xs'}>
                      {msg.sender === 'user' ? 'U' : 'SAGE'}
                    </AvatarFallback>
                  </Avatar>
                  <div
                    className={`rounded-lg p-3 ${
                      msg.sender === 'user'
                        ? 'bg-green-600 text-white'
                        : 'bg-white text-black border border-gray-200'
                    }`}
                  >
                    {msg.senderName && (
                      <p className="text-xs opacity-70 mb-1">{msg.senderName}</p>
                    )}
                    <p className="whitespace-pre-wrap">{msg.content}</p>
                    <p className="text-xs opacity-70 mt-1">
                      {msg.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                    </p>
                  </div>
                </div>
              </div>
            ))}
            
            {isTyping && (
              <div className="flex justify-start">
                <div className="flex space-x-2">
                  <Avatar className="h-8 w-8">
                    <AvatarFallback className="bg-black text-white text-xs">SAGE</AvatarFallback>
                  </Avatar>
                  <div className="bg-white text-black border border-gray-200 rounded-lg p-3">
                    <div className="flex space-x-1">
                      <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                      <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
                      <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                    </div>
                  </div>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>
        </ScrollArea>

        {/* Message Input */}
        <div className="p-4 border-t border-gray-200 bg-white">
          <form onSubmit={sendMessage} className="flex space-x-2">
            <Input
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              placeholder="Ask about the report data..."
              className="flex-1 bg-white border-gray-300 text-black placeholder:text-gray-400"
              disabled={isTyping}
            />
            <Button 
              type="submit" 
              className="bg-black hover:bg-gray-800 text-white"
              disabled={isTyping || !message.trim()}
            >
              <Send className="h-4 w-4" />
            </Button>
          </form>
        </div>
      </div>

      {/* Right Panel - Report Upload & Insights */}
      <div className="w-1/2 flex flex-col bg-white">
        {/* Header */}
        <div className="p-4 border-b border-gray-200 bg-white">
          <div className="flex items-center space-x-3">
            <BarChart3 className="h-6 w-6 text-purple-600" />
            <div>
              <h1 className="text-lg font-semibold text-black">Report Agent</h1>
              <p className="text-sm text-gray-600">Upload & analyze reports</p>
            </div>
          </div>
        </div>

        <ScrollArea className="flex-1 p-4 space-y-6 bg-gray-50">
          {/* File Upload */}
          <Card className="bg-white border-gray-200">
            <CardHeader>
              <CardTitle className="flex items-center text-black">
                <Upload className="h-5 w-5 mr-2" />
                Upload Report
              </CardTitle>
              <CardDescription className="text-gray-600">
                Upload CSV or Excel files for analysis
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center bg-gray-50">
                <Upload className="h-8 w-8 text-gray-400 mx-auto mb-2" />
                <label htmlFor="report-upload" className="cursor-pointer">
                  <span className="text-black">Click to upload</span>
                  <span className="text-gray-600"> or drag and drop</span>
                  <input
                    id="report-upload"
                    type="file"
                    accept=".csv,.xlsx,.xls"
                    className="hidden"
                    onChange={handleFileUpload}
                  />
                </label>
                <p className="text-xs text-gray-500 mt-1">CSV, Excel files up to 10MB</p>
              </div>

              {reports.length > 0 && (
                <div className="mt-4 space-y-2">
                  <h4 className="text-black text-sm font-medium">Recent Reports</h4>
                  {reports.map((report) => (
                    <div key={report.id} className="flex items-center justify-between p-2 bg-gray-100 rounded">
                      <span className="text-black text-sm truncate">{report.name}</span>
                      <div className="flex items-center space-x-2">
                        <span className={`text-xs px-2 py-1 rounded ${
                          report.status === 'ready' ? 'bg-green-600 text-white' : 'bg-yellow-600 text-white'
                        }`}>
                          {report.status}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>


        </ScrollArea>
        </div>
      </div>
    </div>
  );
}