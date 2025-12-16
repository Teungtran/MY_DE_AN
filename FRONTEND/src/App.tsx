import { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { LandingPage } from './components/LandingPage';
import { LoginPage } from './components/LoginPage';
import { CustomerChatbot } from './components/CustomerChatbot';
import { EmployeeChatbot } from './components/EmployeeChatbot';
import { DataAdminPage } from './components/DataAdminPage';
import { MLPage } from './components/MLPage';
import { ReportAgentPage } from './components/ReportAgentPage';
import { Toaster } from './components/ui/sonner';
import { getUserData, removeAuthToken } from './utils/api';
import { ChatProvider } from './contexts/ChatContext';
import { MLProvider } from './contexts/MLContext';
import { ReportProvider } from './contexts/ReportContext';
import { AdminProvider } from './contexts/AdminContext';

export default function App() {
  const [user, setUser] = useState<{
    id: string;
    email: string;
    role: 'customer' | 'employee' | 'admin';
  } | null>(null);

  // Check for stored user data on app load
  useEffect(() => {
    const userData = getUserData();
    if (userData) {
      setUser(userData);
    }
  }, []);

  const handleLogin = (userData: { email: string; role: 'customer' | 'employee' | 'admin' }) => {
    setUser({
      id: Math.random().toString(36).substr(2, 9),
      ...userData
    });
  };

  const handleLogout = () => {
    removeAuthToken();
    // Clear chat history from localStorage
    localStorage.removeItem('customer_conversations');
    localStorage.removeItem('employee_sessions');
    setUser(null);
  };

  return (
    <Router>
      <ChatProvider>
        <MLProvider>
          <ReportProvider>
            <AdminProvider>
              <div className="min-h-screen bg-background">
                <Routes>
                  <Route path="/" element={<LandingPage />} />
                  <Route 
                    path="/login" 
                    element={
                      user ? <Navigate to={getDashboardPath(user.role)} replace /> : 
                      <LoginPage onLogin={handleLogin} />
                    } 
                  />
                  <Route 
                    path="/chat/customer" 
                    element={
                      user && user.role === 'customer' ? 
                      <CustomerChatbot user={user} onLogout={handleLogout} /> : 
                      <Navigate to="/login" replace />
                    } 
                  />
                  <Route 
                    path="/chat/employee" 
                    element={
                      user && (user.role === 'employee' || user.role === 'admin') ? 
                      <EmployeeChatbot user={user} onLogout={handleLogout} /> : 
                      <Navigate to="/login" replace />
                    } 
                  />
                  <Route 
                    path="/admin/data" 
                    element={
                      user && user.role === 'admin' ? 
                      <DataAdminPage user={user} onLogout={handleLogout} /> : 
                      <Navigate to="/login" replace />
                    } 
                  />
                  <Route 
                    path="/ml" 
                    element={
                      user && (user.role === 'employee' || user.role === 'admin') ? 
                      <MLPage user={user} onLogout={handleLogout} /> : 
                      <Navigate to="/login" replace />
                    } 
                  />
                  <Route 
                    path="/reports" 
                    element={
                      user && (user.role === 'employee' || user.role === 'admin') ? 
                      <ReportAgentPage user={user} onLogout={handleLogout} /> : 
                      <Navigate to="/login" replace />
                    } 
                  />
                  <Route path="*" element={<Navigate to="/" replace />} />
                </Routes>
                <Toaster />
              </div>
            </AdminProvider>
          </ReportProvider>
        </MLProvider>
      </ChatProvider>
    </Router>
  );
}

function getDashboardPath(role: 'customer' | 'employee' | 'admin'): string {
  switch (role) {
    case 'customer':
      return '/chat/customer';
    case 'employee':
      return '/chat/employee';
    case 'admin':
      return '/chat/employee'; // Admin starts at employee chat with nav tabs
    default:
      return '/';
  }
}