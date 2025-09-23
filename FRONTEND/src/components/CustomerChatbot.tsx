import React, { useState, useRef, useEffect } from 'react';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { ScrollArea } from './ui/scroll-area';
import { Card } from './ui/card';
import { Avatar, AvatarFallback } from './ui/avatar';
import { Send, Plus, Search, Menu, LogOut, Paperclip } from 'lucide-react';
import { Sheet, SheetContent, SheetTrigger } from './ui/sheet';

interface User {
  id: string;
  email: string;
  role: string;
}

interface Message {
  id: string;
  content: string;
  sender: 'user' | 'ai';
  timestamp: Date;
}

interface Conversation {
  id: string;
  title: string;
  lastMessage: string;
  timestamp: Date;
  messages: Message[];
}

interface CustomerChatbotProps {
  user: User;
  onLogout: () => void;
}

export function CustomerChatbot({ user, onLogout }: CustomerChatbotProps) {
  const [conversations, setConversations] = useState<Conversation[]>([
    {
      id: '1',
      title: 'Warranty Issue',
      lastMessage: 'I need help with my warranty claim',
      timestamp: new Date(Date.now() - 1000 * 60 * 30),
      messages: [
        {
          id: '1',
          content: 'Hello! I need help with my warranty claim for a product I purchased.',
          sender: 'user',
          timestamp: new Date(Date.now() - 1000 * 60 * 31)
        },
        {
          id: '2',
          content: 'I\'d be happy to help you with your warranty claim! Could you please provide me with your order number or product serial number?',
          sender: 'ai',
          timestamp: new Date(Date.now() - 1000 * 60 * 30)
        }
      ]
    }
  ]);
  
  const [activeConversation, setActiveConversation] = useState<string>('1');
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
  }, [conversations, activeConversation]);

  const getCurrentConversation = () => {
    return conversations.find(conv => conv.id === activeConversation);
  };

  const sendMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!message.trim()) return;

    const newMessage: Message = {
      id: Date.now().toString(),
      content: message,
      sender: 'user',
      timestamp: new Date()
    };

    // Add user message
    setConversations(prev => prev.map(conv => 
      conv.id === activeConversation 
        ? { ...conv, messages: [...conv.messages, newMessage], lastMessage: message }
        : conv
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

      setConversations(prev => prev.map(conv => 
        conv.id === activeConversation 
          ? { ...conv, messages: [...conv.messages, aiResponse], lastMessage: aiResponse.content }
          : conv
      ));
      
      setIsTyping(false);
    }, 1500);
  };

  const generateAIResponse = (userMessage: string): string => {
    const responses = [
      "I understand your concern. Let me help you with that right away. Could you provide more details?",
      "Thank you for reaching out. I've found some relevant information that might help you.",
      "I can definitely assist you with this. Based on what you've told me, here are some options...",
      "That's a great question! Let me check our knowledge base for the most up-to-date information.",
      "I've reviewed your account and I can see the issue. Here's what we can do to resolve it:",
    ];
    return responses[Math.floor(Math.random() * responses.length)];
  };

  const createNewConversation = () => {
    const newConv: Conversation = {
      id: Date.now().toString(),
      title: 'New Conversation',
      lastMessage: '',
      timestamp: new Date(),
      messages: []
    };
    setConversations(prev => [newConv, ...prev]);
    setActiveConversation(newConv.id);
    setSidebarOpen(false);
  };

  const filteredConversations = conversations.filter(conv =>
    conv.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
    conv.lastMessage.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const Sidebar = () => (
    <div className="flex flex-col h-full bg-gray-900 text-white">
      {/* Header */}
      <div className="p-4 border-b border-gray-700">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg">Customer Support</h2>
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
            placeholder="Search conversations..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-10 bg-gray-800 border-gray-600 text-white placeholder:text-gray-400"
          />
        </div>
      </div>

      {/* New Conversation Button */}
      <div className="p-4">
        <Button
          onClick={createNewConversation}
          className="w-full bg-[#FF6B35] hover:bg-[#FF6B35]/90 text-white"
        >
          <Plus className="h-4 w-4 mr-2" />
          New Conversation
        </Button>
      </div>

      {/* Conversations List */}
      <ScrollArea className="flex-1 px-4">
        <div className="space-y-2">
          {filteredConversations.map((conv) => (
            <Card
              key={conv.id}
              className={`p-3 cursor-pointer transition-colors border ${
                activeConversation === conv.id
                  ? 'bg-[#FF6B35] border-[#FF6B35] text-white'
                  : 'bg-gray-800 border-gray-700 text-gray-300 hover:bg-gray-700'
              }`}
              onClick={() => {
                setActiveConversation(conv.id);
                setSidebarOpen(false);
              }}
            >
              <div className="font-medium truncate">{conv.title}</div>
              <div className="text-sm opacity-70 truncate mt-1">{conv.lastMessage}</div>
              <div className="text-xs opacity-50 mt-1">
                {conv.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
              </div>
            </Card>
          ))}
        </div>
      </ScrollArea>
    </div>
  );

  const currentConv = getCurrentConversation();

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
        {/* Chat Header */}
        <div className="p-4 border-b border-gray-700 bg-gray-900">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <Sheet>
                <SheetTrigger asChild>
                  <Button variant="ghost" size="sm" className="md:hidden">
                    <Menu className="h-5 w-5" />
                  </Button>
                </SheetTrigger>
              </Sheet>
              <h1 className="text-xl">{currentConv?.title || 'Customer Support'}</h1>
            </div>
            <div className="text-sm text-gray-400">
              Welcome, {user.email}
            </div>
          </div>
        </div>

        {/* Messages */}
        <ScrollArea className="flex-1 p-4">
          <div className="space-y-4 max-w-4xl mx-auto">
            {currentConv?.messages.map((msg) => (
              <div
                key={msg.id}
                className={`flex ${msg.sender === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                <div className={`flex space-x-2 max-w-xs lg:max-w-md ${msg.sender === 'user' ? 'flex-row-reverse' : ''}`}>
                  <Avatar className="h-8 w-8">
                    <AvatarFallback className={msg.sender === 'user' ? 'bg-[#FF6B35] text-white' : 'bg-gray-700 text-white'}>
                      {msg.sender === 'user' ? 'U' : 'AI'}
                    </AvatarFallback>
                  </Avatar>
                  <div
                    className={`rounded-lg p-3 ${
                      msg.sender === 'user'
                        ? 'bg-[#FF6B35] text-white'
                        : 'bg-gray-800 text-white'
                    }`}
                  >
                    <p>{msg.content}</p>
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
              className="bg-[#FF6B35] hover:bg-[#FF6B35]/90 text-white"
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