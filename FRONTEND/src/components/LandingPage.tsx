import React from 'react';
import { Link } from 'react-router-dom';
import { Button } from './ui/button';
import { Card, CardContent } from './ui/card';
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from './ui/accordion';
import { 
  MessageCircle, 
  Brain, 
  BarChart3, 
  Users, 
  Database,
  ArrowRight,
  Settings,
  TrendingUp,
  FileText,
  Search,
  Zap,
  Target,
  RefreshCw,
  Upload,
  Globe
} from 'lucide-react';

export function LandingPage() {
  return (
    <div className="min-h-screen bg-white text-black">
      {/* Header */}
      <header className="bg-white border-b border-gray-100">
        <div className="container mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            {/* Logo */}
            <div className="flex items-center space-x-3 hover:opacity-80 transition-opacity duration-200">
              <div className="w-8 h-8 bg-gray-700 rounded-full flex items-center justify-center">
                <span className="text-white font-bold text-sm">S</span>
              </div>
              <span className="text-xl font-semibold text-gray-800">SAGE</span>
              <span className="text-sm text-gray-500 ml-2">AI Platform</span>
            </div>
            
            {/* Navigation */}
            <nav className="hidden md:flex items-center space-x-8">
              <a href="#features" className="text-gray-600 hover:text-gray-900 hover:bg-gray-100 px-3 py-2 rounded-md transition-all duration-200">Features</a>
              <a href="#solutions" className="text-gray-600 hover:text-gray-900 hover:bg-gray-100 px-3 py-2 rounded-md transition-all duration-200">Solutions</a>
              <a href="#about" className="text-gray-600 hover:text-gray-900 hover:bg-gray-100 px-3 py-2 rounded-md transition-all duration-200">About</a>
              <a href="#contact" className="text-gray-600 hover:text-gray-900 hover:bg-gray-100 px-3 py-2 rounded-md transition-all duration-200">Contact</a>
            </nav>

            <div className="flex items-center space-x-4">
              <Link to="/login" className="text-gray-600 hover:text-gray-900 hover:bg-gray-100 px-3 py-2 rounded-md transition-all duration-200">
                Sign In
              </Link>
              <Link to="/login">
                <Button className="bg-gray-800 text-white hover:bg-gray-900 px-4 py-2 rounded-md transition-all duration-200">
                  Get Started
                </Button>
              </Link>
            </div>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <section className="bg-gray-50 py-20">
        <div className="container mx-auto px-6">
          <div className="flex items-center justify-between">
            <div className="flex-1 max-w-2xl">
              <div className="inline-flex items-center bg-gray-100 rounded-full px-4 py-2 mb-8">
                <span className="text-sm text-gray-600">✨ AI-Powered Enterprise Platform</span>
              </div>
              
              <h1 className="text-5xl font-bold text-gray-900 mb-6 leading-tight">
                Transform FPT Shop with SAGE AI
              </h1>
              
              <p className="text-xl text-gray-600 mb-8 leading-relaxed">
                Comprehensive AI platform featuring multi-agentic chatbots, MLOps systems, and intelligent data management. Empower your retail operations with cutting-edge artificial intelligence.
              </p>
              
              <Button className="bg-gray-800 text-white hover:bg-gray-900 px-6 py-3 rounded-md inline-flex items-center space-x-2 transition-all duration-200 transform hover:scale-105">
                <span>Get Started</span>
                <ArrowRight className="h-4 w-4" />
              </Button>
            </div>
            
            <div className="flex-1 flex justify-end">
              <div className="relative">
                <div className="w-96 h-80 bg-gradient-to-br from-blue-900 via-purple-800 to-blue-700 rounded-2xl flex items-center justify-center relative overflow-hidden">
                  {/* Isometric illustration placeholder */}
                  <div className="absolute inset-0 bg-gradient-to-br from-purple-600/20 via-blue-600/30 to-pink-600/20"></div>
                  <div className="relative z-10 text-center">
                    <div className="w-32 h-32 bg-gradient-to-br from-purple-400 to-pink-400 rounded-lg mx-auto mb-4 flex items-center justify-center">
                      <Brain className="h-16 w-16 text-white" />
                    </div>
                    <div className="text-white text-sm font-medium">AI Processing</div>
                    <div className="text-white/70 text-xs">Real-time Analytics</div>
                  </div>
                  
                  {/* Floating badges */}
                  <div className="absolute top-4 right-4 bg-gray-800 text-white px-3 py-1 rounded-full text-xs">
                    AI Processing
                  </div>
                  <div className="absolute bottom-4 left-4 bg-gray-800 text-white px-3 py-1 rounded-full text-xs">
                    Multi-Agent
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Platform Capabilities */}
      <section id="features" className="py-20 bg-white">
        <div className="container mx-auto px-6">
          <div className="text-center mb-16">
            <div className="inline-flex items-center bg-gray-100 rounded-full px-4 py-2 mb-6">
              <span className="text-sm text-gray-600">Enterprise AI Features</span>
            </div>
            <h2 className="text-4xl font-bold text-gray-900 mb-4">
              Comprehensive AI Platform for Modern Retail
            </h2>
            <p className="text-xl text-gray-600 max-w-4xl mx-auto">
              SAGE delivers a complete suite of AI-powered tools designed specifically for FPT Shop's unique operational needs and customer requirements.
            </p>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 max-w-7xl mx-auto">
            {/* AI Sales Assistant */}
            <Card className="p-8 border border-gray-200 hover:shadow-lg hover:bg-gray-50 transition-all duration-200 transform hover:scale-102">
              <CardContent className="p-0">
                <div className="flex items-start space-x-4">
                  <div className="w-12 h-12 bg-gray-100 rounded-lg flex items-center justify-center flex-shrink-0">
                    <MessageCircle className="h-6 w-6 text-gray-700" />
                  </div>
                  <div className="flex-1">
                    <div className="text-sm text-gray-500 mb-1">Multi-Agentic Chatbot</div>
                    <h3 className="text-2xl font-bold text-gray-900 mb-3">AI Sales Assistant</h3>
                    <p className="text-gray-600 mb-6">
                      Intelligent chatbot that serves as your virtual salesperson, providing personalized product recommendations and seamless customer support.
                    </p>
                    
                    <div className="mb-4">
                      <h4 className="font-semibold text-gray-900 mb-3">Key Capabilities:</h4>
                      <ul className="space-y-2">
                        <li className="flex items-center text-gray-600">
                          <div className="w-1.5 h-1.5 bg-gray-400 rounded-full mr-3"></div>
                          Product Recommendations
                        </li>
                        <li className="flex items-center text-gray-600">
                          <div className="w-1.5 h-1.5 bg-gray-400 rounded-full mr-3"></div>
                          IT Support After-Sales
                        </li>
                        <li className="flex items-center text-gray-600">
                          <div className="w-1.5 h-1.5 bg-gray-400 rounded-full mr-3"></div>
                          Store Policy Q&A
                        </li>
                        <li className="flex items-center text-gray-600">
                          <div className="w-1.5 h-1.5 bg-gray-400 rounded-full mr-3"></div>
                          Voz Creating Integration
                        </li>
                        <li className="flex items-center text-gray-600">
                          <div className="w-1.5 h-1.5 bg-gray-400 rounded-full mr-3"></div>
                          Order Management Automation
                        </li>
                      </ul>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Store Assistant System */}
            <Card className="p-8 border border-gray-200 hover:shadow-lg hover:bg-gray-50 transition-all duration-200 transform hover:scale-102">
              <CardContent className="p-0">
                <div className="flex items-start space-x-4">
                  <div className="w-12 h-12 bg-gray-100 rounded-lg flex items-center justify-center flex-shrink-0">
                    <Users className="h-6 w-6 text-gray-700" />
                  </div>
                  <div className="flex-1">
                    <div className="text-sm text-gray-500 mb-1">Supervisor Multi-Agent</div>
                    <h3 className="text-2xl font-bold text-gray-900 mb-3">Store Assistant System</h3>
                    <p className="text-gray-600 mb-6">
                      Advanced AI system designed for staff and admin operations, providing intelligent search, database management, and strategic consultation.
                    </p>
                    
                    <div className="mb-4">
                      <h4 className="font-semibold text-gray-900 mb-3">Key Capabilities:</h4>
                      <ul className="space-y-2">
                        <li className="flex items-center text-gray-600">
                          <div className="w-1.5 h-1.5 bg-gray-400 rounded-full mr-3"></div>
                          Advanced Search Engine
                        </li>
                        <li className="flex items-center text-gray-600">
                          <div className="w-1.5 h-1.5 bg-gray-400 rounded-full mr-3"></div>
                          Database Management & Access
                        </li>
                        <li className="flex items-center text-gray-600">
                          <div className="w-1.5 h-1.5 bg-gray-400 rounded-full mr-3"></div>
                          Strategy Consulting
                        </li>
                        <li className="flex items-center text-gray-600">
                          <div className="w-1.5 h-1.5 bg-gray-400 rounded-full mr-3"></div>
                          Automated Ad Tracking
                        </li>
                        <li className="flex items-center text-gray-600">
                          <div className="w-1.5 h-1.5 bg-gray-400 rounded-full mr-3"></div>
                          Real-time Data Crawling
                        </li>
                      </ul>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Machine Learning Operations */}
            <Card className="p-8 border border-gray-200 hover:shadow-lg hover:bg-gray-50 transition-all duration-200 transform hover:scale-102">
              <CardContent className="p-0">
                <div className="flex items-start space-x-4">
                  <div className="w-12 h-12 bg-gray-100 rounded-lg flex items-center justify-center flex-shrink-0">
                    <Settings className="h-6 w-6 text-gray-700" />
                  </div>
                  <div className="flex-1">
                    <div className="text-sm text-gray-500 mb-1">MLOps System</div>
                    <h3 className="text-2xl font-bold text-gray-900 mb-3">Machine Learning Operations</h3>
                    <p className="text-gray-600 mb-6">
                      Comprehensive ML management platform for customer analytics, churn prediction, and streamlined development lifecycle management.
                    </p>
                    
                    <div className="mb-4">
                      <h4 className="font-semibold text-gray-900 mb-3">Key Capabilities:</h4>
                      <ul className="space-y-2">
                        <li className="flex items-center text-gray-600">
                          <div className="w-1.5 h-1.5 bg-gray-400 rounded-full mr-3"></div>
                          Customer Analysis Models
                        </li>
                        <li className="flex items-center text-gray-600">
                          <div className="w-1.5 h-1.5 bg-gray-400 rounded-full mr-3"></div>
                          Churn Prediction Systems
                        </li>
                        <li className="flex items-center text-gray-600">
                          <div className="w-1.5 h-1.5 bg-gray-400 rounded-full mr-3"></div>
                          MLflow Integration
                        </li>
                        <li className="flex items-center text-gray-600">
                          <div className="w-1.5 h-1.5 bg-gray-400 rounded-full mr-3"></div>
                          Model Versioning
                        </li>
                        <li className="flex items-center text-gray-600">
                          <div className="w-1.5 h-1.5 bg-gray-400 rounded-full mr-3"></div>
                          Automated Deployment
                        </li>
                      </ul>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* AI-Powered Insights */}
            <Card className="p-8 border border-gray-200 hover:shadow-lg hover:bg-gray-50 transition-all duration-200 transform hover:scale-102">
              <CardContent className="p-0">
                <div className="flex items-start space-x-4">
                  <div className="w-12 h-12 bg-gray-100 rounded-lg flex items-center justify-center flex-shrink-0">
                    <BarChart3 className="h-6 w-6 text-gray-700" />
                  </div>
                  <div className="flex-1">
                    <div className="text-sm text-gray-500 mb-1">Report Analysis</div>
                    <h3 className="text-2xl font-bold text-gray-900 mb-3">AI-Powered Insights</h3>
                    <p className="text-gray-600 mb-6">
                      Intelligent report analysis system that extracts actionable insights from CSV and Excel files using advanced AI algorithms.
                    </p>
                    
                    <div className="mb-4">
                      <h4 className="font-semibold text-gray-900 mb-3">Key Capabilities:</h4>
                      <ul className="space-y-2">
                        <li className="flex items-center text-gray-600">
                          <div className="w-1.5 h-1.5 bg-gray-400 rounded-full mr-3"></div>
                          CSV/Excel Processing
                        </li>
                        <li className="flex items-center text-gray-600">
                          <div className="w-1.5 h-1.5 bg-gray-400 rounded-full mr-3"></div>
                          Automated Insight Generation
                        </li>
                        <li className="flex items-center text-gray-600">
                          <div className="w-1.5 h-1.5 bg-gray-400 rounded-full mr-3"></div>
                          Data Visualization
                        </li>
                        <li className="flex items-center text-gray-600">
                          <div className="w-1.5 h-1.5 bg-gray-400 rounded-full mr-3"></div>
                          Trend Analysis
                        </li>
                        <li className="flex items-center text-gray-600">
                          <div className="w-1.5 h-1.5 bg-gray-400 rounded-full mr-3"></div>
                          Custom Report Generation
                        </li>
                      </ul>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Knowledge Base System - Full Width */}
          <div className="mt-8 max-w-4xl mx-auto">
            <Card className="p-8 border border-gray-200 hover:shadow-lg hover:bg-gray-50 transition-all duration-200 transform hover:scale-102">
              <CardContent className="p-0">
                <div className="flex items-start space-x-4">
                  <div className="w-12 h-12 bg-gray-100 rounded-lg flex items-center justify-center flex-shrink-0">
                    <Database className="h-6 w-6 text-gray-700" />
                  </div>
                  <div className="flex-1">
                    <div className="text-sm text-gray-500 mb-1">Data Management</div>
                    <h3 className="text-2xl font-bold text-gray-900 mb-3">Knowledge Base System</h3>
                    <p className="text-gray-600 mb-6">
                      Comprehensive data management solution with web crawling capabilities for seamless knowledge base and product catalog updates.
                    </p>
                    
                    <div className="mb-4">
                      <h4 className="font-semibold text-gray-900 mb-3">Key Capabilities:</h4>
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-x-8">
                        <ul className="space-y-2">
                          <li className="flex items-center text-gray-600">
                            <div className="w-1.5 h-1.5 bg-gray-400 rounded-full mr-3"></div>
                            Dynamic Data Updates
                          </li>
                          <li className="flex items-center text-gray-600">
                            <div className="w-1.5 h-1.5 bg-gray-400 rounded-full mr-3"></div>
                            Web Crawling Integration
                          </li>
                          <li className="flex items-center text-gray-600">
                            <div className="w-1.5 h-1.5 bg-gray-400 rounded-full mr-3"></div>
                            Product Catalog Management
                          </li>
                        </ul>
                        <ul className="space-y-2">
                          <li className="flex items-center text-gray-600">
                            <div className="w-1.5 h-1.5 bg-gray-400 rounded-full mr-3"></div>
                            Knowledge Base Optimization
                          </li>
                          <li className="flex items-center text-gray-600">
                            <div className="w-1.5 h-1.5 bg-gray-400 rounded-full mr-3"></div>
                            Real-time Synchronization
                          </li>
                        </ul>
                      </div>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </section>

      {/* FAQ Section */}
      <section className="py-20 bg-gray-50">
        <div className="container mx-auto px-6">
          <div className="text-center mb-16">
            <h2 className="text-4xl font-bold text-gray-900 mb-4">
              Frequently Asked Questions
            </h2>
            <p className="text-xl text-gray-600 max-w-3xl mx-auto">
              Everything you need to know about SAGE AI platform for FPT Shop operations.
            </p>
          </div>

          <div className="max-w-4xl mx-auto">
            <Accordion type="single" collapsible className="space-y-4">
              <AccordionItem value="item-1" className="bg-white border border-gray-200 rounded-lg px-6 hover:bg-gray-50 transition-colors duration-200">
                <AccordionTrigger className="text-left">
                  What is SAGE AI and how does it work?
                </AccordionTrigger>
                <AccordionContent className="text-gray-600">
                  SAGE AI is a comprehensive enterprise platform designed specifically for FPT Shop's retail operations. It combines multi-agentic chatbots, machine learning operations, and intelligent data management to enhance customer service, streamline store operations, and provide actionable business insights through advanced AI technologies.
                </AccordionContent>
              </AccordionItem>

              <AccordionItem value="item-2" className="bg-white border border-gray-200 rounded-lg px-6 hover:bg-gray-50 transition-colors duration-200">
                <AccordionTrigger className="text-left">
                  What are the different user roles and access levels?
                </AccordionTrigger>
                <AccordionContent className="text-gray-600">
                  SAGE AI supports three main user roles: Customer (access to AI Sales Assistant for product recommendations and support), Employee (access to Store Assistant System, ML Analytics, and Report Analysis), and Admin (full platform access including Data Management and system administration capabilities).
                </AccordionContent>
              </AccordionItem>

              <AccordionItem value="item-3" className="bg-white border border-gray-200 rounded-lg px-6 hover:bg-gray-50 transition-colors duration-200">
                <AccordionTrigger className="text-left">
                  How does the AI Sales Assistant help customers?
                </AccordionTrigger>
                <AccordionContent className="text-gray-600">
                  The AI Sales Assistant provides personalized product recommendations, handles IT support after-sales inquiries, answers store policy questions, integrates with Voz for enhanced functionality, and automates order management processes to deliver seamless customer experiences.
                </AccordionContent>
              </AccordionItem>

              <AccordionItem value="item-4" className="bg-white border border-gray-200 rounded-lg px-6 hover:bg-gray-50 transition-colors duration-200">
                <AccordionTrigger className="text-left">
                  What machine learning capabilities does SAGE offer?
                </AccordionTrigger>
                <AccordionContent className="text-gray-600">
                  SAGE's MLOps system includes customer analysis models, churn prediction systems, MLflow integration for model management, automated model versioning and deployment, enabling data-driven decision making and predictive analytics for retail operations.
                </AccordionContent>
              </AccordionItem>

              <AccordionItem value="item-5" className="bg-white border border-gray-200 rounded-lg px-6 hover:bg-gray-50 transition-colors duration-200">
                <AccordionTrigger className="text-left">
                  How does the Knowledge Base System work?
                </AccordionTrigger>
                <AccordionContent className="text-gray-600">
                  The Knowledge Base System provides comprehensive data management with dynamic updates, web crawling integration, product catalog management, knowledge base optimization, and real-time synchronization to ensure all information stays current and accurate across the platform.
                </AccordionContent>
              </AccordionItem>

              <AccordionItem value="item-6" className="bg-white border border-gray-200 rounded-lg px-6 hover:bg-gray-50 transition-colors duration-200">
                <AccordionTrigger className="text-left">
                  Is SAGE AI secure and compliant with data protection standards?
                </AccordionTrigger>
                <AccordionContent className="text-gray-600">
                  Yes, SAGE AI implements enterprise-grade security with role-based access control, encrypted data transmission, secure authentication systems, and compliance with industry data protection standards. All sensitive data is protected and access is controlled based on user roles and permissions.
                </AccordionContent>
              </AccordionItem>
            </Accordion>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-20 bg-white">
        <div className="container mx-auto px-6 text-center">
          <h2 className="text-4xl font-bold text-gray-900 mb-6">
            Ready to transform your retail operations with SAGE AI?
          </h2>
          <p className="text-xl text-gray-600 mb-8 max-w-3xl mx-auto">
            Join FPT Shop teams already using SAGE to deliver exceptional customer experiences and streamline store management with cutting-edge AI technology.
          </p>
          <div className="flex items-center justify-center space-x-4">
            <Link to="/login">
              <Button className="bg-gray-800 text-white hover:bg-gray-900 px-8 py-3 rounded-md inline-flex items-center space-x-2 transition-all duration-200 transform hover:scale-105">
                <span>Get Started</span>
                <ArrowRight className="h-4 w-4" />
              </Button>
            </Link>
            <Link to="/login">
              <Button variant="outline" className="border-gray-300 text-gray-700 hover:bg-gray-100 px-8 py-3 rounded-md transition-all duration-200 transform hover:scale-105">
                Schedule Demo
              </Button>
            </Link>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-gray-50 border-t border-gray-200 py-12">
        <div className="container mx-auto px-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className="w-8 h-8 bg-gray-700 rounded-full flex items-center justify-center">
                <span className="text-white font-bold text-sm">S</span>
              </div>
              <span className="text-xl font-semibold text-gray-800">SAGE</span>
              <span className="text-sm text-gray-500 ml-2">AI Platform</span>
            </div>
            <div className="text-center text-gray-500">
              © 2025 SAGE - FPT Shop AI Platform. All rights reserved.
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}