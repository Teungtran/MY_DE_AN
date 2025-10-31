import React, { useState, useRef, useEffect } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { ScrollArea } from './ui/scroll-area';
import { Card } from './ui/card';
import { Avatar, AvatarFallback } from './ui/avatar';
import { Badge } from './ui/badge';
import { Send, Plus, Search, Menu, LogOut, Users, MessageCircle, Brain, FileText, Database, Trash2, ChevronLeft, ChevronRight } from 'lucide-react';
import { Sheet, SheetContent, SheetTrigger } from './ui/sheet';
import { FPTLogo } from './FPTLogo';
import { adminAPI, generateConversationId } from '../utils/api';

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
  const [sessions, setSessions] = useState<Session[]>([]);
  
  const [activeSession, setActiveSession] = useState<string>('');
  const [message, setMessage] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
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

    const userMessage = message;
    const newMessage: Message = {
      id: Date.now().toString(),
      content: userMessage,
      sender: 'user',
      senderName: user.email.split('@')[0],
      timestamp: new Date()
    };

    // Add user message
    setSessions(prev => prev.map(session => 
      session.id === activeSession 
        ? { ...session, messages: [...session.messages, newMessage], lastMessage: userMessage }
        : session
    ));

    setMessage('');
    setIsTyping(true);

    // Create AI response message that will be updated with streaming chunks
    const aiMessageId = (Date.now() + 1).toString();
    const aiResponse: Message = {
      id: aiMessageId,
      content: '',
      sender: 'ai',
      timestamp: new Date()
    };

    // Add empty AI message
    setSessions(prev => prev.map(session => 
      session.id === activeSession 
        ? { ...session, messages: [...session.messages, aiResponse] }
        : session
    ));

    try {
      // Use real admin team chat streaming API
      await adminAPI.teamChatStream(
        userMessage,
        activeSession, // Use session ID
        (chunk) => {
          // Update AI message with streaming chunks
          setSessions(prev => prev.map(session => 
            session.id === activeSession 
              ? { 
                  ...session, 
                  messages: session.messages.map(msg => 
                    msg.id === aiMessageId 
                      ? { ...msg, content: msg.content + chunk }
                      : msg
                  ),
                  lastMessage: chunk
                }
              : session
          ));
        }
      );
      setIsTyping(false);
    } catch (error) {
      console.error('Team chat error:', error);
      // Update AI message with error
      setSessions(prev => prev.map(session => 
        session.id === activeSession 
          ? { 
              ...session, 
              messages: session.messages.map(msg => 
                msg.id === aiMessageId 
                  ? { ...msg, content: 'Sorry, I encountered an error. Please try again.' }
                  : msg
              )
            }
          : session
      ));
      setIsTyping(false);
    }
  };

  // Note: generateAIResponse function removed - now using real streaming API via adminAPI.teamChatStream()

  const createNewSession = () => {
    // Generate UUID for new session
    const sessionId = generateConversationId();
    
    const welcomeMessage: Message = {
      id: 'welcome',
      content: `Hello, ${user.email.split('@')[0]}!

I'm SAGE – your smart business assistant at FPT

Ready to assist you with:
      
Competitor insights & market analysis
Strategic planning & decision support  
Business intelligence & data insights
Research & knowledge discovery

Just ask me what you need – from competitor insights to strategy ideas – and I'll bring the right information to your fingertips.

What can I help you explore today?`,
      sender: 'ai',
      timestamp: new Date()
    };

    const newSession: Session = {
      id: sessionId,
      title: 'New Session',
      lastMessage: 'Welcome to SAGE!',
      timestamp: new Date(),
      status: 'active',
      participants: [user.email.split('@')[0]],
      messages: [welcomeMessage]
    };
    setSessions(prev => [newSession, ...prev]);
    setActiveSession(newSession.id);
    setSidebarOpen(false);
  };

  const deleteSession = (sessionId: string, e: React.MouseEvent<HTMLButtonElement>) => {
    e.stopPropagation();
    if (sessions.length <= 1) {
      alert('Cannot delete the last session. At least one session must remain.');
      return;
    }
    
    const sessionToDelete = sessions.find(session => session.id === sessionId);
    if (sessionToDelete && window.confirm(`Are you sure you want to delete "${sessionToDelete.title}"?`)) {
      setSessions(prev => prev.filter(session => session.id !== sessionId));
      
      // If we're deleting the active session, switch to another one
      if (activeSession === sessionId) {
        const remainingSessions = sessions.filter(session => session.id !== sessionId);
        if (remainingSessions.length > 0) {
          setActiveSession(remainingSessions[0].id);
        }
      }
    }
  };

  const clearAllHistory = () => {
    if (window.confirm('Are you sure you want to delete all chat history? This action cannot be undone.')) {
      createNewSession(); // This will create a fresh session
      setSessions(prev => prev.slice(0, 1)); // Keep only the new session
    }
  };

  const filteredSessions = sessions.filter(session =>
    session.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
    session.lastMessage.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const Sidebar = () => (
    <div className={`flex flex-col h-full bg-white text-black border-r border-gray-200 transition-all duration-300 ${sidebarCollapsed ? 'w-16' : 'w-80'}`}>
      {/* Header */}
      <div className="p-4 border-b border-gray-200">
        {!sidebarCollapsed && (
          <>
            <div className="mb-4">
              <FPTLogo />
            </div>
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold">Employee Hub</h2>
              <div className="flex items-center space-x-1">
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={clearAllHistory}
                  className="text-gray-600 hover:text-red-600 hover:bg-red-50"
                  title="Clear all chat history"
                >
                  <Trash2 className="h-4 w-4" />
                </Button>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={onLogout}
                  className="text-gray-600 hover:text-black"
                >
                  <LogOut className="h-4 w-4" />
                </Button>
              </div>
            </div>
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
              <Input
                placeholder="Search sessions..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-10 bg-gray-50 border-gray-300 text-black placeholder:text-gray-400"
              />
            </div>
          </>
        )}
        
        {/* Collapse Toggle Button */}
        <div className={`flex ${sidebarCollapsed ? 'justify-center' : 'justify-end'} mt-2`}>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setSidebarCollapsed(!sidebarCollapsed)}
            className="text-gray-600 hover:text-black hover:bg-gray-100"
            title={sidebarCollapsed ? "Expand sidebar" : "Collapse sidebar"}
          >
            {sidebarCollapsed ? <ChevronRight className="h-4 w-4" /> : <ChevronLeft className="h-4 w-4" />}
          </Button>
        </div>
      </div>

      {!sidebarCollapsed && (
        <>
          {/* New Session Button */}
          <div className="p-4">
            <Button
              onClick={createNewSession}
              className="w-full bg-black hover:bg-gray-800 text-white transform transition-all duration-200 hover:scale-105 active:scale-95 shadow-lg hover:shadow-xl"
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
                  className={`p-3 cursor-pointer transition-all duration-200 border transform hover:scale-102 active:scale-98 group ${
                    activeSession === session.id
                      ? 'bg-gray-100 border-gray-300 text-black shadow-lg'
                      : 'bg-white border-gray-200 text-black hover:bg-gray-50 hover:shadow-md hover:border-gray-300'
                  }`}
                  onClick={() => {
                    setActiveSession(session.id);
                    setSidebarOpen(false);
                  }}
                >
                  <div className="flex items-center justify-between mb-2">
                    <div className="font-medium truncate flex-1">{session.title}</div>
                    <div className="flex items-center space-x-1">
                      <Badge 
                        variant={session.status === 'active' ? 'default' : 'secondary'}
                        className={session.status === 'active' ? 'bg-green-600' : 'bg-gray-600'}
                      >
                        {session.status}
                      </Badge>
                      {sessions.length > 1 && (
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={(e: React.MouseEvent<HTMLButtonElement>) => deleteSession(session.id, e)}
                          className="text-gray-400 hover:text-red-600 hover:bg-red-50 p-1 h-6 w-6 flex-shrink-0"
                          title="Delete session"
                        >
                          <Trash2 className="h-3 w-3" />
                        </Button>
                      )}
                    </div>
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
        </>
      )}
    </div>
  );

  const currentSession = getCurrentSession();

  return (
    <div className="h-screen flex bg-white text-black">
      {/* Desktop Sidebar */}
      <div className={`hidden md:block border-r border-gray-200 transition-all duration-300 ${sidebarCollapsed ? 'w-16' : 'w-80'}`}>
        <Sidebar />
      </div>

      {/* Mobile Sidebar */}
      <Sheet open={sidebarOpen} onOpenChange={setSidebarOpen}>
        <SheetContent side="left" className="p-0 w-80 bg-white">
          <Sidebar />
        </SheetContent>
      </Sheet>

      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col">
        {/* Navigation Tabs */}
        <div className="border-b border-gray-200 bg-white">
          <div className="flex items-center justify-between p-4">
            <div className="flex items-center space-x-6">
              <Sheet>
                <SheetTrigger asChild>
                  <Button variant="ghost" size="sm" className="md:hidden text-black">
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
                      ? 'bg-gray-100 text-black'
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
                      ? 'bg-gray-100 text-black'
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
                      ? 'bg-gray-100 text-black'
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
                        ? 'bg-gray-100 text-black'
                        : 'text-gray-600 hover:text-black hover:bg-gray-100'
                    }`}
                  >
                    <Database className="h-4 w-4" />
                    <span>Data Admin</span>
                  </Link>
                )}
              </nav>
            </div>
            
            <div className="flex items-center space-x-4">
              <span className="text-sm text-gray-600">Welcome, {user.email}</span>
              <Button
                variant="ghost"
                size="sm"
                onClick={onLogout}
                className="text-gray-600 hover:text-black"
              >
                <LogOut className="h-4 w-4" />
              </Button>
            </div>
          </div>
        </div>

        {/* Chat Header */}
        <div className="p-4 border-b border-gray-200 bg-white">
          <div className="flex items-center space-x-3">
            <div>
              <h1 className="text-xl font-semibold text-black">{currentSession?.title || 'Employee Hub'}</h1>
              {currentSession && (
                <div className="flex items-center space-x-2 mt-1">
                  <Badge 
                    variant={currentSession.status === 'active' ? 'default' : 'secondary'}
                    className={currentSession.status === 'active' ? 'bg-green-600' : 'bg-gray-600'}
                  >
                    {currentSession.status}
                  </Badge>
                  <span className="text-sm text-gray-600">
                    {currentSession.participants.join(', ')}
                  </span>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Messages */}
        <ScrollArea className="flex-1 p-4 bg-gray-50">
          <div className="space-y-4 max-w-4xl mx-auto">
            {currentSession?.messages.map((msg) => (
              <div
                key={msg.id}
                className={`flex ${msg.sender === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                <div className={`flex space-x-2 max-w-xs lg:max-w-md ${msg.sender === 'user' ? 'flex-row-reverse' : ''}`}>
                  <Avatar className="h-8 w-8">
                    <AvatarFallback className={
                      msg.sender === 'user' ? 'bg-blue-600 text-white' : 
                      msg.sender === 'employee' ? 'bg-green-600 text-white' :
                      'bg-black text-white text-xs'
                    }>
                      {msg.sender === 'user' ? 'U' : msg.sender === 'employee' ? 'E' : 'SAGE'}
                    </AvatarFallback>
                  </Avatar>
                  <div
                    className={`rounded-lg p-3 ${
                      msg.sender === 'user'
                        ? 'bg-blue-600 text-white'
                        : msg.sender === 'employee'
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
          <form onSubmit={sendMessage} className="flex space-x-2 max-w-4xl mx-auto">
            <Input
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              placeholder="Type your message..."
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
    </div>
  );
}