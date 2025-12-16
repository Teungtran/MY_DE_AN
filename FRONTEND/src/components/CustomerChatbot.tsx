import React, { useState, useRef, useEffect } from 'react';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { ScrollArea } from './ui/scroll-area';
import { Card } from './ui/card';
import { Avatar, AvatarFallback } from './ui/avatar';
import { Send, Plus, Search, Menu, LogOut, Trash2, ChevronLeft, ChevronRight } from 'lucide-react';
import { Sheet, SheetContent, SheetTrigger } from './ui/sheet';
import { FPTLogo } from './FPTLogo';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { chatAPI, generateConversationId } from '../utils/api';

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
  const [conversations, setConversations] = useState<Conversation[]>([]);
  
  const [activeConversation, setActiveConversation] = useState<string>('');
  const [message, setMessage] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [isInitialized, setIsInitialized] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [conversations, activeConversation]);

  // Load conversations from localStorage and fetch history from API on mount
  useEffect(() => {
    if (isInitialized) return; // Prevent multiple initializations

    const createInitialConversation = () => {
      const conversationId = generateConversationId();
      const welcomeMessage: Message = {
        id: 'welcome',
        content: `Hello, ${user.email.split('@')[0]}!

I'm SAGE – your smart shopping assistant at FPT Shop


I'm here to help you:

Find the right products that fit your needs
Recommend the best deals & promotions  
Assist with order processing and tracking

Just tell me what you're looking for – whether it's a new phone, laptop, or accessories – and I'll make sure your shopping experience is fast, simple, and enjoyable.

What can I help you with today?`,
        sender: 'ai',
        timestamp: new Date()
      };

      const newConv: Conversation = {
        id: conversationId,
        title: 'New Conversation',
        lastMessage: 'Welcome to SAGE!',
        timestamp: new Date(),
        messages: [welcomeMessage]
      };
      
      setConversations([newConv]);
      setActiveConversation(newConv.id);
      
      try {
        localStorage.setItem('customer_conversations', JSON.stringify([{
          id: conversationId,
          title: 'New Conversation',
          lastMessage: 'Welcome to SAGE!',
          timestamp: newConv.timestamp.toISOString()
        }]));
      } catch (e) {
        console.error('Failed to save to localStorage:', e);
      }
    };

    const loadConversationsFromStorage = async () => {
      try {
        // Fetch all conversations from backend
        console.log('Fetching all conversations from backend...');
        const allConversationsData = await chatAPI.getAllConversations();
        console.log(`Received ${Object.keys(allConversationsData || {}).length} conversations from backend`);
        
        if (allConversationsData && Object.keys(allConversationsData).length > 0) {
          // We have conversations in backend
          const loadedConversations: Conversation[] = [];
          
          for (const [convId, messages] of Object.entries(allConversationsData)) {
            const messageList = messages as any[];
            // Include conversations even if empty (they might have been created but no messages yet)
            if (!Array.isArray(messageList)) {
              console.warn(`Conversation ${convId} has invalid message format, skipping`);
              continue;
            }
            
            const conversationMessages: Message[] = messageList.map((msg: any, idx: number) => ({
              id: `${convId}-${idx}`,
              content: msg.content || '',
              sender: msg.role === 'human' ? 'user' : 'ai',
              timestamp: new Date()
            }));

            // Get title from localStorage or use default
            let title = 'New Conversation';
            let lastMessage = conversationMessages.length > 0 ? conversationMessages[conversationMessages.length - 1].content : 'No messages yet';
            
            const storedConversations = localStorage.getItem('customer_conversations');
            if (storedConversations) {
              try {
                const conversationMetadata = JSON.parse(storedConversations);
                const meta = conversationMetadata.find((m: any) => m.id === convId);
                if (meta) {
                  title = meta.title || title;
                  lastMessage = meta.lastMessage || (conversationMessages.length > 0 ? conversationMessages[conversationMessages.length - 1].content : 'No messages yet');
                }
              } catch (e) {
                console.error('Error parsing stored conversations:', e);
              }
            }

            console.log(`Loading conversation ${convId}: ${conversationMessages.length} messages, title: ${title}`);

            loadedConversations.push({
              id: convId,
              title: title,
              lastMessage: lastMessage ? lastMessage.substring(0, 50) : 'No messages yet',
              timestamp: new Date(),
              messages: conversationMessages
            });
          }

          // Sort conversations by timestamp (most recent first)
          loadedConversations.sort((a, b) => b.timestamp.getTime() - a.timestamp.getTime());

          setConversations(loadedConversations);
          if (loadedConversations.length > 0) {
            setActiveConversation(loadedConversations[0].id);
          } else {
            // No valid conversations found, create initial one
            createInitialConversation();
            setIsInitialized(true);
            return;
          }
          
          // Update localStorage with backend data
          const conversationMetadata = loadedConversations.map(conv => ({
            id: conv.id,
            title: conv.title,
            lastMessage: conv.lastMessage,
            timestamp: conv.timestamp.toISOString()
          }));
          localStorage.setItem('customer_conversations', JSON.stringify(conversationMetadata));
          
          setIsInitialized(true);
          return;
        }
        
        // No conversations in backend, check localStorage
        const storedConversations = localStorage.getItem('customer_conversations');
        if (storedConversations) {
          try {
            const conversationMetadata = JSON.parse(storedConversations);
            
            if (Array.isArray(conversationMetadata) && conversationMetadata.length > 0) {
              // We have stored conversations but no backend data, create initial one anyway
              createInitialConversation();
              setIsInitialized(true);
              return;
            }
          } catch (e) {
            console.error('Error parsing stored conversations:', e);
          }
        }
        
        // No conversations anywhere, create initial one
        createInitialConversation();
        setIsInitialized(true);
      } catch (error) {
        console.error('Failed to load conversations from storage:', error);
        // Create initial conversation on error
        createInitialConversation();
        setIsInitialized(true);
      }
    };

    loadConversationsFromStorage();
  }, [isInitialized, user.email]); // Only run on mount or when user changes

  const getCurrentConversation = () => {
    return conversations.find(conv => conv.id === activeConversation);
  };

  const sendMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!message.trim()) return;

    const userMessage = message;
    const newMessage: Message = {
      id: Date.now().toString(),
      content: userMessage,
      sender: 'user',
      timestamp: new Date()
    };

    // Add user message
    setConversations(prev => prev.map(conv => 
      conv.id === activeConversation 
        ? { ...conv, messages: [...conv.messages, newMessage], lastMessage: userMessage }
        : conv
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
    setConversations(prev => prev.map(conv => 
      conv.id === activeConversation 
        ? { ...conv, messages: [...conv.messages, aiResponse] }
        : conv
    ));

    try {
      // Use real streaming API
      await chatAPI.sendMessage(
        activeConversation,
        userMessage,
        (chunk) => {
          // Update AI message with streaming chunks
          setConversations(prev => prev.map(conv => 
            conv.id === activeConversation 
              ? { 
                  ...conv, 
                  messages: conv.messages.map(msg => 
                    msg.id === aiMessageId 
                      ? { ...msg, content: msg.content + chunk }
                      : msg
                  ),
                  lastMessage: chunk
                }
              : conv
          ));
        },
        (finalData) => {
          // Handle completion - update conversation title if provided
          if (finalData?.title) {
            setConversations(prev => prev.map(conv => 
              conv.id === activeConversation 
                ? { ...conv, title: finalData.title }
                : conv
            ));

            // Update localStorage with new title
            try {
              const storedConversations = localStorage.getItem('customer_conversations');
              if (storedConversations) {
                const conversationMetadata = JSON.parse(storedConversations);
                const updatedMetadata = conversationMetadata.map((meta: any) => 
                  meta.id === activeConversation 
                    ? { ...meta, title: finalData.title }
                    : meta
                );
                localStorage.setItem('customer_conversations', JSON.stringify(updatedMetadata));
              }
            } catch (error) {
              console.error('Failed to update conversation title in localStorage:', error);
            }
          }
          setIsTyping(false);
        }
      );
    } catch (error) {
      console.error('Chat error:', error);
      // Update AI message with error
      setConversations(prev => prev.map(conv => 
        conv.id === activeConversation 
          ? { 
              ...conv, 
              messages: conv.messages.map(msg => 
                msg.id === aiMessageId 
                  ? { ...msg, content: 'Sorry, I encountered an error. Please try again.' }
                  : msg
              )
            }
          : conv
      ));
      setIsTyping(false);
    }
  };

  // Note: generateAIResponse function removed - now using real streaming API via chatAPI.sendMessage()

  const createNewConversation = () => {
    // Generate UUID for new conversation
    const conversationId = generateConversationId();
    
    const welcomeMessage: Message = {
      id: 'welcome',
      content: `Hello, ${user.email.split('@')[0]}!

I'm SAGE – your smart shopping assistant at FPT Shop


I'm here to help you:

Find the right products that fit your needs
Recommend the best deals & promotions  
Assist with order processing and tracking

Just tell me what you're looking for – whether it's a new phone, laptop, or accessories – and I'll make sure your shopping experience is fast, simple, and enjoyable.

What can I help you with today?`,
      sender: 'ai',
      timestamp: new Date()
    };

    const newConv: Conversation = {
      id: conversationId,
      title: 'New Conversation',
      lastMessage: 'Welcome to SAGE!',
      timestamp: new Date(),
      messages: [welcomeMessage]
    };
    setConversations(prev => [newConv, ...prev]);
    setActiveConversation(newConv.id);
    setSidebarOpen(false);

    // Persist to localStorage
    try {
      const storedConversations = localStorage.getItem('customer_conversations');
      const conversationMetadata = storedConversations ? JSON.parse(storedConversations) : [];
      conversationMetadata.unshift({
        id: conversationId,
        title: 'New Conversation',
        lastMessage: 'Welcome to SAGE!',
        timestamp: newConv.timestamp.toISOString()
      });
      localStorage.setItem('customer_conversations', JSON.stringify(conversationMetadata));
    } catch (error) {
      console.error('Failed to save conversation to localStorage:', error);
    }
  };

  const deleteConversation = (convId: string, e: React.MouseEvent<HTMLButtonElement>) => {
    e.stopPropagation();
    if (conversations.length <= 1) {
      alert('Cannot delete the last conversation. At least one conversation must remain.');
      return;
    }
    
    const convToDelete = conversations.find(conv => conv.id === convId);
    if (convToDelete && window.confirm(`Are you sure you want to delete "${convToDelete.title}"?`)) {
      setConversations(prev => prev.filter(conv => conv.id !== convId));
      
      // Remove from localStorage
      try {
        const storedConversations = localStorage.getItem('customer_conversations');
        if (storedConversations) {
          const conversationMetadata = JSON.parse(storedConversations);
          const updatedMetadata = conversationMetadata.filter((meta: any) => meta.id !== convId);
          localStorage.setItem('customer_conversations', JSON.stringify(updatedMetadata));
        }
      } catch (error) {
        console.error('Failed to remove conversation from localStorage:', error);
      }
      
      // If we're deleting the active conversation, switch to another one
      if (activeConversation === convId) {
        const remainingConvs = conversations.filter(conv => conv.id !== convId);
        if (remainingConvs.length > 0) {
          setActiveConversation(remainingConvs[0].id);
        }
      }
    }
  };

  const clearAllHistory = () => {
    if (window.confirm('Are you sure you want to delete all chat history? This action cannot be undone.')) {
      // Clear localStorage
      try {
        localStorage.removeItem('customer_conversations');
      } catch (error) {
        console.error('Failed to clear conversations from localStorage:', error);
      }
      
      createNewConversation(); // This will create a fresh conversation
      setConversations(prev => prev.slice(0, 1)); // Keep only the new conversation
    }
  };

  const filteredConversations = conversations.filter(conv =>
    conv.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
    conv.lastMessage.toLowerCase().includes(searchQuery.toLowerCase())
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
              <h2 className="text-lg font-semibold">Customer Support</h2>
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
                placeholder="Search conversations..."
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
          {/* New Conversation Button */}
          <div className="p-4">
            <Button
              onClick={createNewConversation}
              className="w-full bg-black hover:bg-gray-800 text-white transform transition-all duration-200 hover:scale-105 active:scale-95 shadow-lg hover:shadow-xl"
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
                  className={`p-3 cursor-pointer transition-all duration-200 border transform hover:scale-102 active:scale-98 group ${
                    activeConversation === conv.id
                      ? 'bg-gray-100 border-gray-300 text-black shadow-lg'
                      : 'bg-white border-gray-200 text-black hover:bg-gray-50 hover:shadow-md hover:border-gray-300'
                  }`}
                  onClick={() => {
                    setActiveConversation(conv.id);
                    setSidebarOpen(false);
                  }}
                >
                  <div className="flex items-center justify-between">
                    <div className="font-medium truncate flex-1">{conv.title}</div>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={(e: React.MouseEvent<HTMLButtonElement>) => deleteConversation(conv.id, e)}
                      className="text-gray-400 hover:text-red-600 hover:bg-red-50 p-1 h-6 w-6 ml-2 flex-shrink-0 opacity-0 group-hover:opacity-100 transition-opacity"
                      title="Delete conversation"
                    >
                      <Trash2 className="h-3 w-3" />
                    </Button>
                  </div>
                  <div className="text-sm opacity-70 truncate mt-1">{conv.lastMessage}</div>
                  <div className="text-xs opacity-50 mt-1">
                    {conv.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                  </div>
                </Card>
              ))}
            </div>
          </ScrollArea>
        </>
      )}
    </div>
  );

  const currentConv = getCurrentConversation();

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
      <div className="flex-1 flex flex-col relative">
        {/* Chat Header */}
        <div className="p-4 border-b border-gray-200 bg-white">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <Sheet>
                <SheetTrigger asChild>
                  <Button variant="ghost" size="sm" className="md:hidden text-black">
                    <Menu className="h-5 w-5" />
                  </Button>
                </SheetTrigger>
              </Sheet>
              <h1 className="text-xl font-semibold text-black">{currentConv?.title || 'Customer Support'}</h1>
            </div>
            <div className="text-sm text-gray-600">
              Welcome, {user.email}
            </div>
          </div>
        </div>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto p-4 bg-gray-50">
          <div className="space-y-4 max-w-4xl mx-auto pb-4">
            {currentConv?.messages.map((msg) => (
              <div
                key={msg.id}
                className={`flex ${msg.sender === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                <div className={`flex space-x-2 ${msg.sender === 'user' ? 'max-w-xs lg:max-w-md flex-row-reverse' : 'max-w-full lg:max-w-4xl'}`}>
                  <Avatar className="h-8 w-8 flex-shrink-0">
                    <AvatarFallback className={msg.sender === 'user' ? 'bg-red-500 text-white' : 'bg-black text-white text-xs'}>
                      {msg.sender === 'user' ? 'U' : 'SAGE'}
                    </AvatarFallback>
                  </Avatar>
                  <div
                    className={`rounded-lg p-4 transform transition-all duration-200 hover:scale-[1.005] ${
                      msg.sender === 'user'
                        ? 'bg-red-500 text-white shadow-lg'
                        : 'bg-white text-black border border-gray-200 shadow-md hover:shadow-lg'
                    }`}
                  >
                    {msg.sender === 'ai' ? (
                      <div className="prose prose-sm max-w-none">
                        <ReactMarkdown
                          remarkPlugins={[remarkGfm]}
                          components={{
                            img: ({ src, alt }) => (
                              <img 
                                src={src} 
                                alt={alt} 
                                className="rounded-lg max-w-full h-auto my-2 shadow-md" 
                                style={{ maxHeight: '200px', objectFit: 'cover' }}
                              />
                            ),
                            h3: ({ children }) => (
                              <h3 className="text-lg font-semibold text-gray-900 mt-4 mb-2">{children}</h3>
                            ),
                            h2: ({ children }) => (
                              <h2 className="text-xl font-bold text-gray-900 mt-4 mb-2">{children}</h2>
                            ),
                            ul: ({ children }) => (
                              <ul className="list-disc list-inside space-y-1 text-gray-700">{children}</ul>
                            ),
                            li: ({ children }) => (
                              <li className="text-gray-700">{children}</li>
                            ),
                            strong: ({ children }) => (
                              <strong className="font-semibold text-gray-900">{children}</strong>
                            ),
                            a: ({ href, children }) => (
                              <a 
                                href={href} 
                                className="text-blue-600 hover:text-blue-800 underline font-medium"
                                target="_blank"
                                rel="noopener noreferrer"
                              >
                                {children}
                              </a>
                            ),
                            // Auto-linkify plain text URLs
                            p: ({ children }) => {
                              const linkifyText = (text: any): any => {
                                if (typeof text !== 'string') return text;
                                
                                const urlRegex = /(https?:\/\/[^\s]+)/g;
                                const parts = text.split(urlRegex);
                                
                                return parts.map((part, i) => {
                                  if (part.match(urlRegex)) {
                                    return (
                                      <a 
                                        key={i}
                                        href={part} 
                                        className="text-blue-600 hover:text-blue-800 underline font-medium"
                                        target="_blank"
                                        rel="noopener noreferrer"
                                      >
                                        {part}
                                      </a>
                                    );
                                  }
                                  return part;
                                });
                              };
                              
                              return (
                                <p className="text-gray-800 mb-2 leading-relaxed">
                                  {React.Children.map(children, child => 
                                    typeof child === 'string' ? linkifyText(child) : child
                                  )}
                                </p>
                              );
                            },
                            table: ({ children }) => (
                              <div className="overflow-x-auto my-4">
                                <table className="min-w-full border-collapse border border-gray-300 text-sm">
                                  {children}
                                </table>
                              </div>
                            ),
                            thead: ({ children }) => (
                              <thead className="bg-gray-100">{children}</thead>
                            ),
                            tbody: ({ children }) => (
                              <tbody className="bg-white">{children}</tbody>
                            ),
                            tr: ({ children }) => (
                              <tr className="border-b border-gray-200 hover:bg-gray-50">{children}</tr>
                            ),
                            th: ({ children }) => (
                              <th className="border border-gray-300 px-4 py-2 text-left font-semibold text-gray-900 bg-gray-100">
                                {children}
                              </th>
                            ),
                            td: ({ children }) => (
                              <td className="border border-gray-300 px-4 py-2 text-gray-700">
                                {children}
                              </td>
                            )
                          }}
                        >
                          {msg.content}
                        </ReactMarkdown>
                      </div>
                    ) : (
                      <p className="whitespace-pre-wrap">{msg.content}</p>
                    )}
                    <p className="text-xs opacity-70 mt-2 text-right">
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
        </div>

        {/* Sticky Message Input */}
        <div className="sticky bottom-0 left-0 right-0 p-4 border-t border-gray-200 bg-white shadow-lg z-10">
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
              className="bg-black hover:bg-gray-800 text-white transform transition-all duration-200 hover:scale-105 active:scale-95 shadow-lg hover:shadow-xl disabled:opacity-50 disabled:cursor-not-allowed disabled:transform-none"
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