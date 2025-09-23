import React, { useState, useRef, useEffect } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { ScrollArea } from './ui/scroll-area';
import { Card } from './ui/card';
import { Avatar, AvatarFallback } from './ui/avatar';
import { Badge } from './ui/badge';
import { Send, Plus, Search, Menu, LogOut, Users, MessageCircle, Brain, FileText, Database } from 'lucide-react';
import { Sheet, SheetContent, SheetTrigger } from './ui/sheet';

interface User {
  id: string;
  email: string;
  role: string;
}

interface Message {
  id: string;
  content: string;
  sender: 'user' | 'ai' | 'employee';
  senderName?: string;
  timestamp: Date;
}

interface Session {
  id: string;
  title: string;
  lastMessage: string;
  timestamp: Date;
  status: 'active' | 'closed';
  participants: string[];
  messages: Message[];
}

interface EmployeeChatbotProps {
  user: User;
  onLogout: () => void;
}

export function EmployeeChatbot({ user, onLogout }: EmployeeChatbotProps) {
  const location = useLocation();
  const [sessions, setSessions] = useState<Session[]>([
    {
      id: '1',
      title: 'Customer Support Training',
      lastMessage: 'How should we handle warranty disputes?',
      timestamp: new Date(Date.now() - 1000 * 60 * 15),
      status: 'active',
      participants: ['John D.', 'Sarah M.'],
      messages: [
        {
          id: '1',
          content: 'I need guidance on handling warranty disputes from customers.',
          sender: 'user',
          senderName: 'John D.',
          timestamp: new Date(Date.now() - 1000 * 60 * 16)
        },
        {
          id: '2',
          content: 'For warranty disputes, please follow these steps:\n\n1. Verify the purchase date and warranty period\n2. Check if the issue is covered under warranty terms\n3. Request photos or documentation of the problem\n4. If valid, initiate the replacement/repair process\n\nWould you like me to elaborate on any of these steps?',
          sender: 'ai',
          timestamp: new Date(Date.now() - 1000 * 60 * 15)
        }
      ]
    },
    {
      id: '2',
      title: 'Policy Update Discussion',
      lastMessage: 'The new return policy takes effect next week',
      timestamp: new Date(Date.now() - 1000 * 60 * 60),
      status: 'closed',
      participants: ['Mike R.', 'Lisa K.', 'Tom B.'],
      messages: []
    }
  ]);
  
  const [activeSession, setActiveSession] = useState<string>('1');
  const [message, setMessage] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [sessions, activeSession]);

  const getCurrentSession = () => {
    return sessions.find(session => session.id === activeSession);
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

    // Add user message
    setSessions(prev => prev.map(session => 
      session.id === activeSession 
        ? { ...session, messages: [...session.messages, newMessage], lastMessage: message }
        : session
    ));

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

      setSessions(prev => prev.map(session => 
        session.id === activeSession 
          ? { ...session, messages: [...session.messages, aiResponse], lastMessage: aiResponse.content }
          : session
      ));
      
      setIsTyping(false);
    }, 1500);
  };

  const generateAIResponse = (userMessage: string): string => {
    const responses = [
      "Based on our company policies, here's the recommended approach for this situation...",
      "I've checked our knowledge base and found relevant procedures. Let me walk you through them:",
      "That's an excellent question. According to our latest guidelines, you should:",
      "I can help you with that. Here are the step-by-step instructions:",
      "This is covered in our training materials. The best practice is to:",
      "Let me provide you with the most current information on this topic...",
    ];
    return responses[Math.floor(Math.random() * responses.length)];
  };

  const createNewSession = () => {
    const newSession: Session = {
      id: Date.now().toString(),
      title: 'New Session',
      lastMessage: '',
      timestamp: new Date(),
      status: 'active',
      participants: [user.email.split('@')[0]],
      messages: []
    };
    setSessions(prev => [newSession, ...prev]);
    setActiveSession(newSession.id);
    setSidebarOpen(false);
  };

  const filteredSessions = sessions.filter(session =>
    session.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
    session.lastMessage.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const Sidebar = () => (
    <div className="flex flex-col h-full bg-gray-900 text-white">
      {/* Header */}
      <div className="p-4 border-b border-gray-700">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg">Employee Hub</h2>
          <Button
            variant="ghost"
            size="sm"
            onClick={onLogout}
            className="text-gray-400 hover:text-white"
          >
            <LogOut className="h-4 w-4" />
          </Button>
        </div>
        <div className="relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
          <Input
            placeholder="Search sessions..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-10 bg-gray-800 border-gray-600 text-white placeholder:text-gray-400"
          />
        </div>
      </div>

      {/* New Session Button */}
      <div className="p-4">
        <Button
          onClick={createNewSession}
          className="w-full bg-[#1B4F72] hover:bg-[#1B4F72]/90 text-white"
        >
          <Plus className="h-4 w-4 mr-2" />
          Start New Session
        </Button>
      </div>

      {/* Sessions List */}
      <ScrollArea className="flex-1 px-4">
        <div className="space-y-2">
          {filteredSessions.map((session) => (
            <Card
              key={session.id}
              className={`p-3 cursor-pointer transition-colors border ${
                activeSession === session.id
                  ? 'bg-[#1B4F72] border-[#1B4F72] text-white'
                  : 'bg-gray-800 border-gray-700 text-gray-300 hover:bg-gray-700'
              }`}
              onClick={() => {
                setActiveSession(session.id);
                setSidebarOpen(false);
              }}
            >
              <div className="flex items-center justify-between mb-2">
                <div className="font-medium truncate">{session.title}</div>
                <Badge 
                  variant={session.status === 'active' ? 'default' : 'secondary'}
                  className={session.status === 'active' ? 'bg-green-600' : 'bg-gray-600'}
                >
                  {session.status}
                </Badge>
              </div>
              <div className="text-sm opacity-70 truncate mb-2">{session.lastMessage}</div>
              <div className="flex items-center justify-between">
                <div className="flex items-center text-xs opacity-50">
                  <Users className="h-3 w-3 mr-1" />
                  {session.participants.length}
                </div>
                <div className="text-xs opacity-50">
                  {session.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                </div>
              </div>
            </Card>
          ))}
        </div>
      </ScrollArea>
    </div>
  );

  const currentSession = getCurrentSession();

  return (
    <div className="h-screen flex bg-black text-white">
      {/* Desktop Sidebar */}
      <div className="hidden md:block w-80 border-r border-gray-700">
        <Sidebar />
      </div>

      {/* Mobile Sidebar */}
      <Sheet open={sidebarOpen} onOpenChange={setSidebarOpen}>
        <SheetContent side="left" className="p-0 w-80 bg-gray-900">
          <Sidebar />
        </SheetContent>
      </Sheet>

      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col">
        {/* Navigation Tabs */}
        <div className="border-b border-gray-700 bg-gray-900">
          <div className="flex items-center justify-between p-4">
            <div className="flex items-center space-x-6">
              <Sheet>
                <SheetTrigger asChild>
                  <Button variant="ghost" size="sm" className="md:hidden">
                    <Menu className="h-5 w-5" />
                  </Button>
                </SheetTrigger>
              </Sheet>
              
              {/* Navigation Links */}
              <nav className="flex space-x-6">
                <Link
                  to="/chat/employee"
                  className={`flex items-center space-x-2 px-3 py-2 rounded-md transition-colors ${
                    location.pathname === '/chat/employee'
                      ? 'bg-[#1B4F72] text-white'
                      : 'text-gray-400 hover:text-white hover:bg-gray-800'
                  }`}
                >
                  <MessageCircle className="h-4 w-4" />
                  <span>Chat</span>
                </Link>
                
                <Link
                  to="/ml"
                  className={`flex items-center space-x-2 px-3 py-2 rounded-md transition-colors ${
                    location.pathname === '/ml'
                      ? 'bg-[#1B4F72] text-white'
                      : 'text-gray-400 hover:text-white hover:bg-gray-800'
                  }`}
                >
                  <Brain className="h-4 w-4" />
                  <span>ML Analysis</span>
                </Link>
                
                <Link
                  to="/reports"
                  className={`flex items-center space-x-2 px-3 py-2 rounded-md transition-colors ${
                    location.pathname === '/reports'
                      ? 'bg-[#1B4F72] text-white'
                      : 'text-gray-400 hover:text-white hover:bg-gray-800'
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
                        ? 'bg-[#1B4F72] text-white'
                        : 'text-gray-400 hover:text-white hover:bg-gray-800'
                    }`}
                  >
                    <Database className="h-4 w-4" />
                    <span>Data Admin</span>
                  </Link>
                )}
              </nav>
            </div>
            
            <div className="flex items-center space-x-4">
              <span className="text-sm text-gray-400">Welcome, {user.email}</span>
              <Button
                variant="ghost"
                size="sm"
                onClick={onLogout}
                className="text-gray-400 hover:text-white"
              >
                <LogOut className="h-4 w-4" />
              </Button>
            </div>
          </div>
        </div>

        {/* Chat Header */}
        <div className="p-4 border-b border-gray-700 bg-gray-800">
          <div className="flex items-center space-x-3">
            <div>
              <h1 className="text-xl">{currentSession?.title || 'Employee Hub'}</h1>
              {currentSession && (
                <div className="flex items-center space-x-2 mt-1">
                  <Badge 
                    variant={currentSession.status === 'active' ? 'default' : 'secondary'}
                    className={currentSession.status === 'active' ? 'bg-green-600' : 'bg-gray-600'}
                  >
                    {currentSession.status}
                  </Badge>
                  <span className="text-sm text-gray-400">
                    {currentSession.participants.join(', ')}
                  </span>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Messages */}
        <ScrollArea className="flex-1 p-4">
          <div className="space-y-4 max-w-4xl mx-auto">
            {currentSession?.messages.map((msg) => (
              <div
                key={msg.id}
                className={`flex ${msg.sender === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                <div className={`flex space-x-2 max-w-xs lg:max-w-md ${msg.sender === 'user' ? 'flex-row-reverse' : ''}`}>
                  <Avatar className="h-8 w-8">
                    <AvatarFallback className={
                      msg.sender === 'user' ? 'bg-[#1B4F72] text-white' : 
                      msg.sender === 'employee' ? 'bg-blue-600 text-white' :
                      'bg-gray-700 text-white'
                    }>
                      {msg.sender === 'user' ? 'U' : msg.sender === 'employee' ? 'E' : 'AI'}
                    </AvatarFallback>
                  </Avatar>
                  <div
                    className={`rounded-lg p-3 ${
                      msg.sender === 'user'
                        ? 'bg-[#1B4F72] text-white'
                        : msg.sender === 'employee'
                        ? 'bg-blue-600 text-white'
                        : 'bg-gray-800 text-white'
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
                    <AvatarFallback className="bg-gray-700 text-white">AI</AvatarFallback>
                  </Avatar>
                  <div className="bg-gray-800 text-white rounded-lg p-3">
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
        <div className="p-4 border-t border-gray-700 bg-gray-900">
          <form onSubmit={sendMessage} className="flex space-x-2 max-w-4xl mx-auto">
            <Input
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              placeholder="Type your message..."
              className="flex-1 bg-gray-800 border-gray-600 text-white placeholder:text-gray-400"
              disabled={isTyping}
            />
            <Button 
              type="submit" 
              className="bg-[#1B4F72] hover:bg-[#1B4F72]/90 text-white"
              disabled={isTyping || !message.trim()}
            >
              <Send className="h-4 w-4" />
            </Button>
          </form>
        </div>
      </div>
    </div>
  );
}