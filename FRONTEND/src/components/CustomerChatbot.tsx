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
  const [conversations, setConversations] = useState<Conversation[]>([
    {
      id: '1',
      title: 'iPhone 13 Features & Recommendations',
      lastMessage: 'Would you like more details on any specific phone, or are you ready to place an order?',
      timestamp: new Date(Date.now() - 1000 * 60 * 30),
      messages: [
        {
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
          timestamp: new Date(Date.now() - 1000 * 60 * 35)
        },
        {
          id: 'user1',
          content: 'Can you tell me more about the iPhone 13 features?',
          sender: 'user',
          timestamp: new Date(Date.now() - 1000 * 60 * 30)
        },
        {
          id: 'ai1',
          content: `Here are the detailed features of the **iPhone 13**:

### Design & Materials
- **Luxurious Design:** The iPhone 13 features a flat design with a premium aluminum frame and super tough Ceramic Shield glass, ensuring both style and durability.
- **Water Resistance:** Rated IP68, it offers protection against water damage during everyday use.
  
![iPhone 13 Design](https://cdn2.fptshop.com.vn/unsafe/564x0/filters:quality(80)/Uploads/images/2015/0511/iphone-13-new-2.JPG)

### Performance
- **Powerful Chip:** Powered by the Apple A15 Bionic chip, it boasts the fastest smartphone processor, with a CPU that is 50% faster than competitors and a GPU that is 30% faster.
  
![A15 Chip](https://cdn.fptshop.com.vn/Uploads/images/2015/Tin-Tuc/QuanLNH2/iphone-13-18.jpg)

### Camera Features
- **Dual-Camera System:** Equipped with large sensors and wide apertures for enhanced low-light performance.
- **Advanced Features:** Includes Sensor-shift optical image stabilization (OIS) and Smart HDR 4 for optimized images.

![iPhone 13 Camera](https://cdn2.fptshop.com.vn/unsafe/564x0/filters:quality(80)/Uploads/images/2015/Tin-Tuc/QuanLNH2/iphone-13-7.jpg)

### Video Capabilities
- **Cinematic Mode:** Allows for professional-quality video recording with depth-of-field effects and smooth focus transitions.

![Cinematic Mode](https://cdn.fptshop.com.vn/Uploads/images/2015/Tin-Tuc/QuanLNH2/iphone-13-12.jpg)

### Battery & Charging
- **Longer Battery Life:** Features a larger battery providing 2.5 hours more usage time compared to its predecessor.
- **Fast Charging:** Supports 20W fast charging, achieving 50% charge in just 30 minutes, and is compatible with Qi and MagSafe wireless charging.

![iPhone 13 Battery](https://cdn2.fptshop.com.vn/unsafe/564x0/filters:quality(80)/Uploads/images/2015/Tin-Tuc/QuanLNH2/iphone-13-3.jpg)

### AI Features
- **Enhanced Camera Quality:** The A15 chip includes an image signal processor (ISP) for improved camera performance and supports augmented reality (AR) applications.

![5G Speed](https://cdn.fptshop.com.vn/Uploads/images/2015/Tin-Tuc/QuanLNH2/iphone-13-20.jpg)

### Comparisons
- **Upgrades:** Compared to the iPhone 12, it has a brighter display (up to 28% brighter), improved battery life, and enhanced camera capabilities.

![iPhone 13 Display](https://cdn2.fptshop.com.vn/unsafe/564x0/filters:quality(80)/Uploads/images/2015/Tin-Tuc/QuanLNH2/iphone-13-17.jpg)

### Sales Perks
- **Discounts:** 
  - Giảm ngay 7,200,000đ áp dụng đến 19/05
  - AirPods giảm đến 500,000đ khi mua kèm iPhone
  - Giảm thêm đến 2 triệu khi mua kèm SIM FPT FVIP150/F299 6-12 tháng

Would you like to proceed with an order for the iPhone 13 or need more information?`,
          sender: 'ai',
          timestamp: new Date(Date.now() - 1000 * 60 * 25)
        },
        {
          id: 'user2',
          content: 'What other phone options do you recommend?',
          sender: 'user',
          timestamp: new Date(Date.now() - 1000 * 60 * 20)
        },
        {
          id: 'ai2',
          content: `Here are some phone recommendations for you:

1. **iPhone 11 64GB**
   - **Sale Price:** 9,190,000 VND (23% discount)
   - **Installment Price:** 777,834 VND
   - **Sales Perks:** 
     - Giảm ngay 2,800,000đ áp dụng đến 19/05
     - AirPods giảm đến 500,000đ khi mua kèm iPhone
     - Trả góp 0%
   - **[View More](https://fptshop.com.vn/dien-thoai/iphone-11-64gb)**
   - ![iPhone 11](https://cdn2.fptshop.com.vn/unsafe/iphone_11_3d0cd738fd.png)

2. **Samsung Galaxy A06 5G 4GB 128GB**
   - **Sale Price:** 3,490,000 VND (13% discount)
   - **Installment Price:** 910,000 VND
   - **Sales Perks:** 
     - Giảm ngay 500,000đ áp dụng đến 19/05
     - Tặng củ sạc 25W chính hãng
     - Trả góp 0%
   - **[View More](https://fptshop.com.vn/dien-thoai/samsung-galaxy-a06)**
   - ![Samsung Galaxy A06](https://cdn2.fptshop.com.vn/unsafe/800x0/samsung_galaxy_a06_5g_6_375f9f5c12.jpg)

3. **iPhone 15 Pro Max 256GB**
   - **Sale Price:** 29,990,000 VND (14% discount)
   - **Installment Price:** 2,261,167 VND
   - **Sales Perks:** 
     - Giảm ngay 5,000,000đ áp dụng đến 19/05
     - Tặng Combo bảo vệ toàn diện
     - Trả góp 0%
   - **[View More](https://fptshop.com.vn/dien-thoai/iphone-15-pro-max)**
   - ![iPhone 15 Pro Max](https://cdn2.fptshop.com.vn/unsafe/800x0/iphone_15_pro_max_19_e4934e6e90.jpg)

4. **iPhone 13 128GB**
   - **Sale Price:** 11,790,000 VND (38% discount)
   - **Installment Price:** 1,011,167 VND
   - **Sales Perks:** 
     - Giảm ngay 7,200,000đ áp dụng đến 19/05
     - AirPods giảm đến 500,000đ khi mua kèm iPhone
   - **[View More](https://fptshop.com.vn/dien-thoai/iphone-13)**
   - ![iPhone 13](https://cdn2.fptshop.com.vn/unsafe/iphone_13_b06d633f18.png)

5. **iPhone 15 Plus 128GB**
   - **Sale Price:** 19,590,000 VND (25% discount)
   - **Installment Price:** 1,661,167 VND
   - **Sales Perks:** 
     - Giảm ngay 6,400,000đ áp dụng đến 19/05
     - AirPods giảm đến 500,000đ khi mua kèm iPhone
   - **[View More](https://fptshop.com.vn/dien-thoai/iphone-15-plus)**
   - ![iPhone 15 Plus](https://cdn2.fptshop.com.vn/unsafe/564x0/filters:quality(80)/Uploads/images/2015/Tin-Tuc/10/1/iphone-15-html-1.png)

Would you like more details on any specific phone, or are you ready to place an order?`,
          sender: 'ai',
          timestamp: new Date(Date.now() - 1000 * 60 * 15)
        }
      ]
    }
  ]);
  
  const [activeConversation, setActiveConversation] = useState<string>('1');
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
  }, [conversations, activeConversation]);

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
                    {conversations.length > 1 && (
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={(e: React.MouseEvent<HTMLButtonElement>) => deleteConversation(conv.id, e)}
                        className="opacity-0 group-hover:opacity-100 transition-opacity text-gray-400 hover:text-red-600 hover:bg-red-50 p-1 h-6 w-6"
                        title="Delete conversation"
                      >
                        <Trash2 className="h-3 w-3" />
                      </Button>
                    )}
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
      <div className="flex-1 flex flex-col">
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
        <ScrollArea className="flex-1 p-4 bg-gray-50">
          <div className="space-y-4 max-w-4xl mx-auto">
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
                            p: ({ children }) => (
                              <p className="text-gray-800 mb-2 leading-relaxed">{children}</p>
                            ),
                            strong: ({ children }) => (
                              <strong className="font-semibold text-gray-900">{children}</strong>
                            ),
                            a: ({ href, children }) => (
                              <a 
                                href={href} 
                                className="text-blue-600 hover:text-blue-800 underline"
                                target="_blank"
                                rel="noopener noreferrer"
                              >
                                {children}
                              </a>
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