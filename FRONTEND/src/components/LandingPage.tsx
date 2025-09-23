import React from 'react';
import { Link } from 'react-router-dom';
import { Button } from './ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { MessageCircle, Users, Brain, FileText, ArrowRight } from 'lucide-react';

export function LandingPage() {
  return (
    <div className="min-h-screen bg-black text-white">
      {/* Hero Section */}
      <section className="relative overflow-hidden">
        <div className="container mx-auto px-4 py-20 text-center">
          <h1 className="text-6xl md:text-8xl mb-6 bg-gradient-to-r from-white to-gray-300 bg-clip-text text-transparent">
            SAGE Platform
          </h1>
          <p className="text-xl md:text-2xl text-gray-300 mb-8 max-w-3xl mx-auto">
            Intelligent customer service automation with AI-powered chatbots, ML predictions, and comprehensive reporting
          </p>
          <Link to="/login">
            <Button 
              size="lg" 
              className="bg-[#FF6B35] hover:bg-[#FF6B35]/90 text-white px-8 py-4 text-lg"
            >
              Get Started
              <ArrowRight className="ml-2 h-5 w-5" />
            </Button>
          </Link>
        </div>
      </section>

      {/* Features Section */}
      <section className="py-20 bg-gray-900">
        <div className="container mx-auto px-4">
          <h2 className="text-4xl text-center mb-16">Platform Features</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-8 max-w-6xl mx-auto">
            
            {/* Customer Chatbot */}
            <Card className="bg-gradient-to-br from-[#FF6B35] to-red-600 border-none text-white">
              <CardHeader>
                <div className="flex items-center space-x-3">
                  <MessageCircle className="h-8 w-8" />
                  <CardTitle className="text-2xl">Customer Chatbot</CardTitle>
                </div>
              </CardHeader>
              <CardContent>
                <CardDescription className="text-white/90 text-base">
                  AI-powered customer support with instant responses, warranty tracking, 
                  and seamless issue resolution. Available 24/7 for your customers.
                </CardDescription>
              </CardContent>
            </Card>

            {/* Employee Chatbot */}
            <Card className="bg-gradient-to-br from-[#1B4F72] to-blue-700 border-none text-white">
              <CardHeader>
                <div className="flex items-center space-x-3">
                  <Users className="h-8 w-8" />
                  <CardTitle className="text-2xl">Employee Chatbot</CardTitle>
                </div>
              </CardHeader>
              <CardContent>
                <CardDescription className="text-white/90 text-base">
                  Internal AI assistant for employees with access to company knowledge base, 
                  policies, and collaborative session management.
                </CardDescription>
              </CardContent>
            </Card>

            {/* ML Predictions */}
            <Card className="bg-gradient-to-br from-purple-600 to-purple-800 border-none text-white">
              <CardHeader>
                <div className="flex items-center space-x-3">
                  <Brain className="h-8 w-8" />
                  <CardTitle className="text-2xl">ML Predictions</CardTitle>
                </div>
              </CardHeader>
              <CardContent>
                <CardDescription className="text-white/90 text-base">
                  Advanced machine learning for sentiment analysis, churn prediction, 
                  and customer behavior insights with customizable retraining.
                </CardDescription>
              </CardContent>
            </Card>

            {/* Report Agent */}
            <Card className="bg-gradient-to-br from-green-600 to-green-800 border-none text-white">
              <CardHeader>
                <div className="flex items-center space-x-3">
                  <FileText className="h-8 w-8" />
                  <CardTitle className="text-2xl">Report Agent</CardTitle>
                </div>
              </CardHeader>
              <CardContent>
                <CardDescription className="text-white/90 text-base">
                  Intelligent report analysis with automated insights, collaborative discussions, 
                  and data visualization for informed decision making.
                </CardDescription>
              </CardContent>
            </Card>

          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-black border-t border-gray-800 py-12">
        <div className="container mx-auto px-4">
          <div className="flex flex-col md:flex-row justify-between items-center space-y-4 md:space-y-0">
            <div className="text-2xl font-bold">SAGE</div>
            <div className="flex space-x-8">
              <a href="#" className="text-gray-400 hover:text-white transition-colors">About</a>
              <a href="#" className="text-gray-400 hover:text-white transition-colors">Contact</a>
              <a href="#" className="text-gray-400 hover:text-white transition-colors">Terms</a>
            </div>
          </div>
          <div className="text-center text-gray-500 mt-8">
            © 2024 SAGE Platform. All rights reserved.
          </div>
        </div>
      </footer>
    </div>
  );
}