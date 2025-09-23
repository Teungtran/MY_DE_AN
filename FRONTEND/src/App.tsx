import React, { useState } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { LandingPage } from './components/LandingPage';
import { LoginPage } from './components/LoginPage';
import { CustomerChatbot } from './components/CustomerChatbot';
import { EmployeeChatbot } from './components/EmployeeChatbot';
import { DataAdminPage } from './components/DataAdminPage';
import { MLPage } from './components/MLPage';
import { ReportAgentPage } from './components/ReportAgentPage';
import { Toaster } from './components/ui/sonner';

export default function App() {
  const [user, setUser] = useState<{
    id: string;
    email: string;
    role: 'customer' | 'employee' | 'admin';
  } | null>(null);

  const handleLogin = (userData: { email: string; role: 'customer' | 'employee' | 'admin' }) => {
    setUser({
      id: Math.random().toString(36).substr(2, 9),
      ...userData
    });
  };

  const handleLogout = () => {
    setUser(null);
  };

  return (
    <Router>
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