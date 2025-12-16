import React, { createContext, useContext, useState, ReactNode } from 'react';
import { adminAPI, generateConversationId } from '../utils/api';

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

interface ChatContextType {
  sessions: Session[];
  setSessions: React.Dispatch<React.SetStateAction<Session[]>>;
  activeSession: string;
  setActiveSession: React.Dispatch<React.SetStateAction<string>>;
  isTyping: boolean;
  setIsTyping: React.Dispatch<React.SetStateAction<boolean>>;
  isInitialized: boolean;
  setIsInitialized: React.Dispatch<React.SetStateAction<boolean>>;
  initializeSessions: (userId: string, userEmail: string) => Promise<void>;
  sendMessage: (message: string, userId: string, userEmail: string) => Promise<void>;
  createNewSession: (userEmail: string) => void;
  deleteSession: (sessionId: string) => void;
  clearAllHistory: (userEmail: string) => void;
}

const ChatContext = createContext<ChatContextType | undefined>(undefined);

export function ChatProvider({ children }: { children: ReactNode }) {
  const [sessions, setSessions] = useState<Session[]>([]);
  const [activeSession, setActiveSession] = useState<string>('');
  const [isTyping, setIsTyping] = useState(false);
  const [isInitialized, setIsInitialized] = useState(false);

  const initializeSessions = async (userId: string, userEmail: string) => {
    if (isInitialized) return;

    try {
      console.log(`Fetching all sessions from backend for user ${userId}...`);
      const allSessionsData = await adminAPI.getAllConversations(userId);
      console.log(`Received ${Object.keys(allSessionsData || {}).length} sessions from backend`);
      
      if (allSessionsData && Object.keys(allSessionsData).length > 0) {
        const loadedSessions: Session[] = [];
        
        for (const [sessionId, messages] of Object.entries(allSessionsData)) {
          const messageList = messages as any[];
          if (!Array.isArray(messageList)) {
            console.warn(`Session ${sessionId} has invalid message format, skipping`);
            continue;
          }
          
          const sessionMessages: Message[] = messageList.map((msg: any, idx: number) => ({
            id: `${sessionId}-${idx}`,
            content: msg.content || '',
            sender: msg.role === 'human' ? 'user' : 'ai',
            timestamp: new Date()
          }));

          let title = 'New Session';
          let lastMessage = sessionMessages.length > 0 ? sessionMessages[sessionMessages.length - 1].content : 'No messages yet';
          let status: 'active' | 'closed' = 'active';
          let participants = [userEmail.split('@')[0]];
          
          const storedSessions = localStorage.getItem('employee_sessions');
          if (storedSessions) {
            try {
              const sessionMetadata = JSON.parse(storedSessions);
              const meta = sessionMetadata.find((m: any) => m.id === sessionId);
              if (meta) {
                title = meta.title || title;
                lastMessage = meta.lastMessage || (sessionMessages.length > 0 ? sessionMessages[sessionMessages.length - 1].content : 'No messages yet');
                status = meta.status || 'active';
                participants = meta.participants || participants;
              }
            } catch (e) {
              console.error('Error parsing stored sessions:', e);
            }
          }

          loadedSessions.push({
            id: sessionId,
            title: title,
            lastMessage: lastMessage ? lastMessage.substring(0, 50) : 'No messages yet',
            timestamp: new Date(),
            status: status,
            participants: participants,
            messages: sessionMessages
          });
        }

        loadedSessions.sort((a, b) => b.timestamp.getTime() - a.timestamp.getTime());
        setSessions(loadedSessions);
        if (loadedSessions.length > 0) {
          setActiveSession(loadedSessions[0].id);
        } else {
          createInitialSession(userEmail);
          return;
        }
        
        const sessionMetadata = loadedSessions.map(session => ({
          id: session.id,
          title: session.title,
          lastMessage: session.lastMessage,
          timestamp: session.timestamp.toISOString(),
          status: session.status,
          participants: session.participants
        }));
        localStorage.setItem('employee_sessions', JSON.stringify(sessionMetadata));
        
        setIsInitialized(true);
        return;
      }
      
      const storedSessions = localStorage.getItem('employee_sessions');
      if (storedSessions) {
        try {
          const sessionMetadata = JSON.parse(storedSessions);
          if (Array.isArray(sessionMetadata) && sessionMetadata.length > 0) {
            createInitialSession(userEmail);
            setIsInitialized(true);
            return;
          }
        } catch (e) {
          console.error('Error parsing stored sessions:', e);
        }
      }
      
      createInitialSession(userEmail);
      setIsInitialized(true);
    } catch (error) {
      console.error('Failed to load sessions from storage:', error);
      createInitialSession(userEmail);
      setIsInitialized(true);
    }
  };

  const createInitialSession = (userEmail: string) => {
    const sessionId = generateConversationId();
    const welcomeMessage: Message = {
      id: 'welcome',
      content: `Hello, ${userEmail.split('@')[0]}!

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
      participants: [userEmail.split('@')[0]],
      messages: [welcomeMessage]
    };
    
    setSessions([newSession]);
    setActiveSession(newSession.id);
    
    try {
      localStorage.setItem('employee_sessions', JSON.stringify([{
        id: sessionId,
        title: 'New Session',
        lastMessage: 'Welcome to SAGE!',
        timestamp: newSession.timestamp.toISOString(),
        status: 'active',
        participants: [userEmail.split('@')[0]]
      }]));
    } catch (e) {
      console.error('Failed to save to localStorage:', e);
    }
  };

  const sendMessage = async (message: string, _userId: string, userEmail: string) => {
    if (!message.trim()) return;

    const newMessage: Message = {
      id: Date.now().toString(),
      content: message,
      sender: 'user',
      senderName: userEmail.split('@')[0],
      timestamp: new Date()
    };

    setSessions(prev => prev.map(session => 
      session.id === activeSession 
        ? { ...session, messages: [...session.messages, newMessage], lastMessage: message }
        : session
    ));

    setIsTyping(true);

    const aiMessageId = (Date.now() + 1).toString();
    const aiResponse: Message = {
      id: aiMessageId,
      content: '',
      sender: 'ai',
      timestamp: new Date()
    };

    setSessions(prev => prev.map(session => 
      session.id === activeSession 
        ? { ...session, messages: [...session.messages, aiResponse] }
        : session
    ));

    try {
      const response = await adminAPI.teamChatStream(message, activeSession);
      
      setSessions(prev => prev.map(session => 
        session.id === activeSession 
          ? { 
              ...session, 
              messages: session.messages.map(msg => 
                msg.id === aiMessageId 
                  ? { ...msg, content: response.content || '' }
                  : msg
              ),
              lastMessage: response.content || '',
              ...(response.title && { title: response.title })
            }
          : session
      ));
      
      if (response.title) {
        try {
          const storedSessions = localStorage.getItem('employee_sessions');
          if (storedSessions) {
            const sessionMetadata = JSON.parse(storedSessions);
            const updatedMetadata = sessionMetadata.map((meta: any) => 
              meta.id === activeSession 
                ? { ...meta, title: response.title }
                : meta
            );
            localStorage.setItem('employee_sessions', JSON.stringify(updatedMetadata));
          }
        } catch (error) {
          console.error('Failed to update session title in localStorage:', error);
        }
      }
      
      setIsTyping(false);
    } catch (error) {
      console.error('Team chat error:', error);
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

  const createNewSession = (userEmail: string) => {
    const sessionId = generateConversationId();
    
    const welcomeMessage: Message = {
      id: 'welcome',
      content: `Hello, ${userEmail.split('@')[0]}!

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
      participants: [userEmail.split('@')[0]],
      messages: [welcomeMessage]
    };
    setSessions(prev => [newSession, ...prev]);
    setActiveSession(newSession.id);

    try {
      const storedSessions = localStorage.getItem('employee_sessions');
      const sessionMetadata = storedSessions ? JSON.parse(storedSessions) : [];
      sessionMetadata.unshift({
        id: sessionId,
        title: 'New Session',
        lastMessage: 'Welcome to SAGE!',
        timestamp: newSession.timestamp.toISOString(),
        status: 'active',
        participants: [userEmail.split('@')[0]]
      });
      localStorage.setItem('employee_sessions', JSON.stringify(sessionMetadata));
    } catch (error) {
      console.error('Failed to save session to localStorage:', error);
    }
  };

  const deleteSession = (sessionId: string) => {
    if (sessions.length <= 1) {
      alert('Cannot delete the last session. At least one session must remain.');
      return;
    }
    
    const sessionToDelete = sessions.find(session => session.id === sessionId);
    if (sessionToDelete && window.confirm(`Are you sure you want to delete "${sessionToDelete.title}"?`)) {
      setSessions(prev => prev.filter(session => session.id !== sessionId));
      
      try {
        const storedSessions = localStorage.getItem('employee_sessions');
        if (storedSessions) {
          const sessionMetadata = JSON.parse(storedSessions);
          const updatedMetadata = sessionMetadata.filter((meta: any) => meta.id !== sessionId);
          localStorage.setItem('employee_sessions', JSON.stringify(updatedMetadata));
        }
      } catch (error) {
        console.error('Failed to remove session from localStorage:', error);
      }
      
      if (activeSession === sessionId) {
        const remainingSessions = sessions.filter(session => session.id !== sessionId);
        if (remainingSessions.length > 0) {
          setActiveSession(remainingSessions[0].id);
        }
      }
    }
  };

  const clearAllHistory = (userEmail: string) => {
    if (window.confirm('Are you sure you want to delete all chat history? This action cannot be undone.')) {
      try {
        localStorage.removeItem('employee_sessions');
      } catch (error) {
        console.error('Failed to clear sessions from localStorage:', error);
      }
      
      createNewSession(userEmail);
      setSessions(prev => prev.slice(0, 1));
    }
  };

  return (
    <ChatContext.Provider value={{
      sessions,
      setSessions,
      activeSession,
      setActiveSession,
      isTyping,
      setIsTyping,
      isInitialized,
      setIsInitialized,
      initializeSessions,
      sendMessage,
      createNewSession,
      deleteSession,
      clearAllHistory
    }}>
      {children}
    </ChatContext.Provider>
  );
}

export function useChatContext() {
  const context = useContext(ChatContext);
  if (context === undefined) {
    throw new Error('useChatContext must be used within a ChatProvider');
  }
  return context;
}
