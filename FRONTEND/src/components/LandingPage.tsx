import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { FPTLogo } from './FPTLogo';
import { motion, useScroll, useTransform } from 'motion/react';
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
  const { scrollY } = useScroll();
  const opacity = useTransform(scrollY, [0, 300], [1, 0]);
  const scale = useTransform(scrollY, [0, 300], [1, 0.8]);
  const [mousePosition, setMousePosition] = useState({ x: 0, y: 0 });

  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      setMousePosition({ x: e.clientX, y: e.clientY });
    };

    window.addEventListener('mousemove', handleMouseMove);
    return () => window.removeEventListener('mousemove', handleMouseMove);
  }, []);

  return (
    <div className="min-h-screen bg-white text-black relative overflow-hidden">
      {/* Header */}
      <header className="bg-white border-b border-gray-100">
        <div className="container mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            {/* Logo */}
            <div className="hover:opacity-80 transition-opacity duration-200">
              <FPTLogo />
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
            </div>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <motion.section 
        className="bg-gray-50 py-20 relative"
        style={{ opacity, scale }}
      >
        {/* Animated background gradient */}
        <div 
          className="absolute inset-0 opacity-10 transition-all duration-1000 ease-out"
          style={{
            background: `radial-gradient(600px circle at ${mousePosition.x}px ${mousePosition.y}px, rgba(59, 130, 246, 0.1), transparent 80%)`
          }}
        />
        
        <div className="container mx-auto px-6 relative z-10">
          <div className="flex items-center justify-between">
            <motion.div 
              className="flex-1 max-w-2xl"
              initial={{ opacity: 0, x: -50 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.8, ease: "easeOut" }}
            >
              <motion.div 
                className="inline-flex items-center bg-gray-100 rounded-full px-4 py-2 mb-8"
                initial={{ opacity: 0, y: 30 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.8, delay: 0.1 }}
                whileHover={{ scale: 1.05 }}
              >
                <span className="text-sm text-gray-600">✨ AI-Powered Enterprise Platform</span>
              </motion.div>
              
              <motion.h1 
                className="text-5xl font-bold text-gray-900 mb-6 leading-tight"
                initial={{ opacity: 0, y: 30 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.8, delay: 0.2 }}
              >
                Transform FPT Shop with SAGE AI
              </motion.h1>
              
              <motion.p 
                className="text-xl text-gray-600 mb-8 leading-relaxed"
                initial={{ opacity: 0, y: 30 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.8, delay: 0.4 }}
              >
                Comprehensive AI platform featuring multi-agentic chatbots, MLOps systems, and intelligent data management. Empower your retail operations with cutting-edge artificial intelligence.
              </motion.p>
              
              <motion.div
                initial={{ opacity: 0, y: 30 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.8, delay: 0.6 }}
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
              >
                <Link to="/login">
                  <Button className="bg-gradient-to-r from-red-600 to-red-700 text-white hover:from-red-700 hover:to-red-800 px-8 py-4 rounded-xl inline-flex items-center space-x-2 transition-all duration-300 transform hover:scale-105 hover:shadow-2xl shadow-lg group">
                    <span className="text-lg font-semibold">Get Started</span>
                    <ArrowRight className="h-5 w-5 group-hover:translate-x-2 transition-transform duration-300" />
                  </Button>
                </Link>
              </motion.div>
            </motion.div>

          </div>
        </div>
      </motion.section>

      {/* Platform Capabilities */}
      <motion.section 
        id="features" 
        className="py-20 bg-white"
        initial={{ opacity: 0 }}
        whileInView={{ opacity: 1 }}
        transition={{ duration: 0.8 }}
        viewport={{ once: true }}
      >
        <div className="container mx-auto px-6">
          <motion.div 
            className="text-center mb-16"
            initial={{ opacity: 0, y: 50 }}
            whileInView={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8 }}
            viewport={{ once: true }}
          >
            <motion.div 
              className="inline-flex items-center bg-gray-100 rounded-full px-4 py-2 mb-6"
              whileHover={{ scale: 1.05 }}
            >
              <span className="text-sm text-gray-600">Enterprise AI Features</span>
            </motion.div>
            <h2 className="text-4xl font-bold text-gray-900 mb-4">
              Comprehensive AI Platform for Modern Retail
            </h2>
            <p className="text-xl text-gray-600 max-w-4xl mx-auto">
              SAGE delivers a complete suite of AI-powered tools designed specifically for FPT Shop's unique operational needs and customer requirements.
            </p>
          </motion.div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 max-w-7xl mx-auto">
            {/* AI Sales Assistant */}
            <motion.div
              initial={{ opacity: 0, y: 50 }}
              whileInView={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: 0.1 }}
              viewport={{ once: true }}
              whileHover={{ scale: 1.02, y: -5 }}
            >
              <Card className="p-8 border-2 border-gray-100 hover:border-red-200 rounded-2xl shadow-md hover:shadow-2xl hover:bg-gradient-to-br hover:from-white hover:to-red-50 transition-all duration-300 h-full group">
              <CardContent className="p-0">
                <div className="flex items-start space-x-4">
                  <div className="w-14 h-14 bg-gradient-to-br from-red-500 to-red-600 rounded-xl flex items-center justify-center flex-shrink-0 shadow-lg group-hover:scale-110 transition-transform duration-300">
                    <MessageCircle className="h-7 w-7 text-white" />
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
            </motion.div>

            {/* Store Assistant System */}
            <motion.div
              initial={{ opacity: 0, y: 50 }}
              whileInView={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: 0.2 }}
              viewport={{ once: true }}
              whileHover={{ scale: 1.02, y: -5 }}
            >
              <Card className="p-8 border-2 border-gray-100 hover:border-blue-200 rounded-2xl shadow-md hover:shadow-2xl hover:bg-gradient-to-br hover:from-white hover:to-blue-50 transition-all duration-300 h-full group">
              <CardContent className="p-0">
                <div className="flex items-start space-x-4">
                  <div className="w-14 h-14 bg-gradient-to-br from-blue-500 to-blue-600 rounded-xl flex items-center justify-center flex-shrink-0 shadow-lg group-hover:scale-110 transition-transform duration-300">
                    <Users className="h-7 w-7 text-white" />
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
            </motion.div>

            {/* Machine Learning Operations */}
            <motion.div
              initial={{ opacity: 0, y: 50 }}
              whileInView={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: 0.3 }}
              viewport={{ once: true }}
              whileHover={{ scale: 1.02, y: -5 }}
            >
              <Card className="p-8 border-2 border-gray-100 hover:border-purple-200 rounded-2xl shadow-md hover:shadow-2xl hover:bg-gradient-to-br hover:from-white hover:to-purple-50 transition-all duration-300 h-full group">
              <CardContent className="p-0">
                <div className="flex items-start space-x-4">
                  <div className="w-14 h-14 bg-gradient-to-br from-purple-500 to-purple-600 rounded-xl flex items-center justify-center flex-shrink-0 shadow-lg group-hover:scale-110 transition-transform duration-300">
                    <Settings className="h-7 w-7 text-white" />
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
            </motion.div>

            {/* AI-Powered Insights */}
            <motion.div
              initial={{ opacity: 0, y: 50 }}
              whileInView={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: 0.4 }}
              viewport={{ once: true }}
              whileHover={{ scale: 1.02, y: -5 }}
            >
              <Card className="p-8 border-2 border-gray-100 hover:border-green-200 rounded-2xl shadow-md hover:shadow-2xl hover:bg-gradient-to-br hover:from-white hover:to-green-50 transition-all duration-300 h-full group">
              <CardContent className="p-0">
                <div className="flex items-start space-x-4">
                  <div className="w-14 h-14 bg-gradient-to-br from-green-500 to-green-600 rounded-xl flex items-center justify-center flex-shrink-0 shadow-lg group-hover:scale-110 transition-transform duration-300">
                    <BarChart3 className="h-7 w-7 text-white" />
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
            </motion.div>
          </div>

          {/* Knowledge Base System - Full Width */}
          <motion.div 
            className="mt-8 max-w-4xl mx-auto"
            initial={{ opacity: 0, y: 50 }}
            whileInView={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.5 }}
            viewport={{ once: true }}
            whileHover={{ scale: 1.02, y: -5 }}
          >
            <Card className="p-8 border-2 border-gray-100 hover:border-orange-200 rounded-2xl shadow-md hover:shadow-2xl hover:bg-gradient-to-br hover:from-white hover:to-orange-50 transition-all duration-300 h-full group">
              <CardContent className="p-0">
                <div className="flex items-start space-x-4">
                  <div className="w-14 h-14 bg-gradient-to-br from-orange-500 to-orange-600 rounded-xl flex items-center justify-center flex-shrink-0 shadow-lg group-hover:scale-110 transition-transform duration-300">
                    <Database className="h-7 w-7 text-white" />
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
          </motion.div>
        </div>
      </motion.section>

      {/* FAQ Section */}
      <motion.section 
        className="py-20 bg-gray-50"
        initial={{ opacity: 0 }}
        whileInView={{ opacity: 1 }}
        transition={{ duration: 0.8 }}
        viewport={{ once: true }}
      >
        <div className="container mx-auto px-6">
          <motion.div 
            className="text-center mb-16"
            initial={{ opacity: 0, y: 50 }}
            whileInView={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8 }}
            viewport={{ once: true }}
          >
            <h2 className="text-4xl font-bold text-gray-900 mb-4">
              Frequently Asked Questions
            </h2>
            <p className="text-xl text-gray-600 max-w-3xl mx-auto">
              Everything you need to know about SAGE AI platform for FPT Shop operations.
            </p>
          </motion.div>

          <div className="max-w-4xl mx-auto">
            <Accordion type="single" collapsible className="space-y-4">
              <AccordionItem value="item-1" className="bg-white border-2 border-gray-100 rounded-2xl px-6 hover:border-red-200 hover:shadow-lg transition-all duration-300">
                <AccordionTrigger className="text-left">
                  What is SAGE AI and how does it work?
                </AccordionTrigger>
                <AccordionContent className="text-gray-600">
                  SAGE AI is a comprehensive enterprise platform designed specifically for FPT Shop's retail operations. It combines multi-agentic chatbots, machine learning operations, and intelligent data management to enhance customer service, streamline store operations, and provide actionable business insights through advanced AI technologies.
                </AccordionContent>
              </AccordionItem>

              <AccordionItem value="item-2" className="bg-white border-2 border-gray-100 rounded-2xl px-6 hover:border-blue-200 hover:shadow-lg transition-all duration-300">
                <AccordionTrigger className="text-left">
                  What are the different user roles and access levels?
                </AccordionTrigger>
                <AccordionContent className="text-gray-600">
                  SAGE AI supports three main user roles: Customer (access to AI Sales Assistant for product recommendations and support), Employee (access to Store Assistant System, ML Analytics, and Report Analysis), and Admin (full platform access including Data Management and system administration capabilities).
                </AccordionContent>
              </AccordionItem>

              <AccordionItem value="item-3" className="bg-white border-2 border-gray-100 rounded-2xl px-6 hover:border-purple-200 hover:shadow-lg transition-all duration-300">
                <AccordionTrigger className="text-left">
                  How does the AI Sales Assistant help customers?
                </AccordionTrigger>
                <AccordionContent className="text-gray-600">
                  The AI Sales Assistant provides personalized product recommendations, handles IT support after-sales inquiries, answers store policy questions, integrates with Voz for enhanced functionality, and automates order management processes to deliver seamless customer experiences.
                </AccordionContent>
              </AccordionItem>

              <AccordionItem value="item-4" className="bg-white border-2 border-gray-100 rounded-2xl px-6 hover:border-green-200 hover:shadow-lg transition-all duration-300">
                <AccordionTrigger className="text-left">
                  What machine learning capabilities does SAGE offer?
                </AccordionTrigger>
                <AccordionContent className="text-gray-600">
                  SAGE's MLOps system includes customer analysis models, churn prediction systems, MLflow integration for model management, automated model versioning and deployment, enabling data-driven decision making and predictive analytics for retail operations.
                </AccordionContent>
              </AccordionItem>

              <AccordionItem value="item-5" className="bg-white border-2 border-gray-100 rounded-2xl px-6 hover:border-orange-200 hover:shadow-lg transition-all duration-300">
                <AccordionTrigger className="text-left">
                  How does the Knowledge Base System work?
                </AccordionTrigger>
                <AccordionContent className="text-gray-600">
                  The Knowledge Base System provides comprehensive data management with dynamic updates, web crawling integration, product catalog management, knowledge base optimization, and real-time synchronization to ensure all information stays current and accurate across the platform.
                </AccordionContent>
              </AccordionItem>

              <AccordionItem value="item-6" className="bg-white border-2 border-gray-100 rounded-2xl px-6 hover:border-indigo-200 hover:shadow-lg transition-all duration-300">
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
      </motion.section>

      {/* CTA Section */}
      <motion.section 
        className="py-20 bg-white"
        initial={{ opacity: 0 }}
        whileInView={{ opacity: 1 }}
        transition={{ duration: 0.8 }}
        viewport={{ once: true }}
      >
        <div className="container mx-auto px-6 text-center">
          <motion.h2 
            className="text-4xl font-bold text-gray-900 mb-6"
            initial={{ opacity: 0, y: 30 }}
            whileInView={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8 }}
            viewport={{ once: true }}
          >
            Ready to transform your retail operations with SAGE AI?
          </motion.h2>
          <motion.p 
            className="text-xl text-gray-600 mb-8 max-w-3xl mx-auto"
            initial={{ opacity: 0, y: 30 }}
            whileInView={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8, delay: 0.2 }}
            viewport={{ once: true }}
          >
            Join FPT Shop teams already using SAGE to deliver exceptional customer experiences and streamline store management with cutting-edge AI technology.
          </motion.p>
          <motion.div 
            className="flex items-center justify-center space-x-4"
            initial={{ opacity: 0, y: 30 }}
            whileInView={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8, delay: 0.4 }}
            viewport={{ once: true }}
          >
            <motion.div whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }}>
              <Link to="/login">
                <Button className="bg-gradient-to-r from-red-600 to-red-700 text-white hover:from-red-700 hover:to-red-800 px-10 py-4 rounded-xl inline-flex items-center space-x-2 transition-all duration-300 transform hover:shadow-2xl shadow-lg group text-lg font-semibold">
                  <span>Get Started</span>
                  <ArrowRight className="h-5 w-5 group-hover:translate-x-2 transition-transform duration-300" />
                </Button>
              </Link>
            </motion.div>
            <motion.div whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }}>
              <Link to="/login">
                <Button variant="outline" className="border-2 border-gray-300 text-gray-700 hover:bg-gradient-to-r hover:from-gray-50 hover:to-gray-100 hover:border-gray-400 px-10 py-4 rounded-xl transition-all duration-300 transform hover:shadow-xl shadow-md text-lg font-semibold">
                  Schedule Demo
                </Button>
              </Link>
            </motion.div>
          </motion.div>
        </div>
      </motion.section>

      {/* Footer */}
      <footer className="bg-gray-50 border-t border-gray-200 py-12">
        <div className="container mx-auto px-6">
          <div className="flex items-center justify-between">
            <div>
              <FPTLogo />
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