import React, { useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { Button } from './ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from './ui/table';
import { Badge } from './ui/badge';
import { Progress } from './ui/progress';
import { LogOut, Upload, Brain, TrendingUp, RefreshCw, MessageCircle, FileText, Database, Download } from 'lucide-react';
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip } from 'recharts';

interface User {
  id: string;
  email: string;
  role: string;
}

interface PredictionResult {
  id: string;
  text: string;
  prediction: string;
  confidence: number;
}

interface TrainingRun {
  id: string;
  timestamp: Date;
  status: 'completed' | 'running' | 'failed';
  accuracy: number;
  f1Score: number;
}

interface MLPageProps {
  user: User;
  onLogout: () => void;
}

export function MLPage({ user, onLogout }: MLPageProps) {
  const location = useLocation();
  const [predictionResults, setPredictionResults] = useState<PredictionResult[]>([]);
  const [isProcessing, setIsProcessing] = useState(false);
  const [retrainProgress, setRetrainProgress] = useState(0);
  const [isRetraining, setIsRetraining] = useState(false);



  const handleFileUpload = (type: 'sentiment' | 'churn') => {
    setIsProcessing(true);
    
    // Mock prediction results
    const mockResults: PredictionResult[] = type === 'sentiment' ? [
      { id: '1', text: 'This product is amazing!', prediction: 'Positive', confidence: 0.95 },
      { id: '2', text: 'Not happy with the service', prediction: 'Negative', confidence: 0.88 },
      { id: '3', text: 'It\'s okay, nothing special', prediction: 'Neutral', confidence: 0.72 },
      { id: '4', text: 'Love it! Highly recommend', prediction: 'Positive', confidence: 0.92 },
      { id: '5', text: 'Terrible experience', prediction: 'Negative', confidence: 0.96 }
    ] : [
      { id: '1', text: 'Customer ID: 12345', prediction: 'High Risk', confidence: 0.89 },
      { id: '2', text: 'Customer ID: 67890', prediction: 'Low Risk', confidence: 0.76 },
      { id: '3', text: 'Customer ID: 54321', prediction: 'Medium Risk', confidence: 0.64 },
      { id: '4', text: 'Customer ID: 98765', prediction: 'High Risk', confidence: 0.91 },
      { id: '5', text: 'Customer ID: 13579', prediction: 'Low Risk', confidence: 0.83 }
    ];

    setTimeout(() => {
      setPredictionResults(mockResults);
      setIsProcessing(false);
    }, 2000);
  };

  const handleRetrain = () => {
    setIsRetraining(true);
    setRetrainProgress(0);

    const interval = setInterval(() => {
      setRetrainProgress(prev => {
        if (prev >= 100) {
          clearInterval(interval);
          setIsRetraining(false);
          return 100;
        }
        return prev + 10;
      });
    }, 500);
  };

  const sentimentData = [
    { name: 'Positive', value: 45, fill: '#10B981' },
    { name: 'Negative', value: 30, fill: '#EF4444' },
    { name: 'Neutral', value: 25, fill: '#6B7280' }
  ];

  const churnData = [
    { name: 'Low Risk', value: 60, fill: '#10B981' },
    { name: 'Medium Risk', value: 25, fill: '#F59E0B' },
    { name: 'High Risk', value: 15, fill: '#EF4444' }
  ];

  const downloadResults = () => {
    if (predictionResults.length === 0) return;
    
    const csvContent = [
      ['Text/Customer', 'Prediction', 'Confidence'],
      ...predictionResults.map(result => [
        result.text,
        result.prediction,
        `${(result.confidence * 100).toFixed(1)}%`
      ])
    ].map(row => row.join(',')).join('\n');
    
    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = 'prediction_results.csv';
    link.click();
    window.URL.revokeObjectURL(url);
  };

  return (
    <div className="min-h-screen bg-black text-white">
      {/* Navigation Tabs */}
      <div className="border-b border-gray-700 bg-gray-900">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <nav className="flex space-x-6">
              <Link
                to="/chat/employee"
                className={`flex items-center space-x-2 px-3 py-2 rounded-md transition-colors ${
                  location.pathname === '/chat/employee'
                    ? 'bg-[#1B4F72] text-white'
                    : 'text-gray-400 hover:text-white hover:bg-gray-800'
                }`}
              >
                <MessageCircle className="h-4 w-4" />
                <span>Chat</span>
              </Link>
              
              <Link
                to="/ml"
                className={`flex items-center space-x-2 px-3 py-2 rounded-md transition-colors ${
                  location.pathname === '/ml'
                    ? 'bg-[#1B4F72] text-white'
                    : 'text-gray-400 hover:text-white hover:bg-gray-800'
                }`}
              >
                <Brain className="h-4 w-4" />
                <span>ML Analysis</span>
              </Link>
              
              <Link
                to="/reports"
                className={`flex items-center space-x-2 px-3 py-2 rounded-md transition-colors ${
                  location.pathname === '/reports'
                    ? 'bg-[#1B4F72] text-white'
                    : 'text-gray-400 hover:text-white hover:bg-gray-800'
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
                      ? 'bg-[#1B4F72] text-white'
                      : 'text-gray-400 hover:text-white hover:bg-gray-800'
                  }`}
                >
                  <Database className="h-4 w-4" />
                  <span>Data Admin</span>
                </Link>
              )}
            </nav>
            
            <div className="flex items-center space-x-4">
              <span className="text-gray-400">Welcome, {user.email}</span>
              <Button
                variant="ghost"
                onClick={onLogout}
                className="text-gray-400 hover:text-white"
              >
                <LogOut className="h-4 w-4" />
              </Button>
            </div>
          </div>
        </div>
      </div>

      {/* Header */}
      <div className="border-b border-gray-700 bg-gray-800">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center space-x-3">
            <Brain className="h-8 w-8 text-purple-400" />
            <div>
              <h1 className="text-2xl">Machine Learning</h1>
              <p className="text-gray-400">Predictions & Model Training</p>
            </div>
          </div>
        </div>
      </div>

      <div className="container mx-auto px-4 py-8">
        <Tabs defaultValue="prediction" className="space-y-6">
          <TabsList className="bg-gray-800 border-gray-700">
            <TabsTrigger value="prediction" className="data-[state=active]:bg-gray-700">
              Prediction
            </TabsTrigger>
            {user.role === 'admin' && (
              <TabsTrigger value="retraining" className="data-[state=active]:bg-gray-700">
                Retraining
              </TabsTrigger>
            )}
          </TabsList>

          <TabsContent value="prediction" className="space-y-6">
            {/* Upload & Prediction */}
            <Card className="bg-gray-900 border-gray-700">
              <CardHeader>
                <CardTitle className="flex items-center text-white">
                  <TrendingUp className="h-5 w-5 mr-2" />
                  Data Upload & Prediction
                </CardTitle>
                <CardDescription className="text-gray-400">
                  Upload CSV data for sentiment analysis or churn prediction
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="border-2 border-dashed border-gray-600 rounded-lg p-8 text-center bg-gray-800/50">
                  <Upload className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                  <p className="text-white mb-2">Upload CSV file</p>
                  <p className="text-sm text-gray-500">CSV files up to 5MB</p>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <Button
                    onClick={() => handleFileUpload('sentiment')}
                    disabled={isProcessing}
                    className="bg-blue-600 hover:bg-blue-700 text-white"
                  >
                    {isProcessing ? 'Processing...' : 'Predict Sentiment'}
                  </Button>
                  <Button
                    onClick={() => handleFileUpload('churn')}
                    disabled={isProcessing}
                    className="bg-purple-600 hover:bg-purple-700 text-white"
                  >
                    {isProcessing ? 'Processing...' : 'Predict Churn'}
                  </Button>
                </div>
              </CardContent>
            </Card>

            {/* Results Table */}
            {predictionResults.length > 0 && (
              <Card className="bg-gray-900 border-gray-700">
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <CardTitle className="text-white">Prediction Results</CardTitle>
                    <Button
                      onClick={downloadResults}
                      className="bg-green-600 hover:bg-green-700 text-white"
                      size="sm"
                    >
                      <Download className="h-4 w-4 mr-2" />
                      Download Results
                    </Button>
                  </div>
                </CardHeader>
                <CardContent>
                  <Table>
                    <TableHeader>
                      <TableRow className="border-gray-700">
                        <TableHead className="text-gray-300">Text/Customer</TableHead>
                        <TableHead className="text-gray-300">Prediction</TableHead>
                        <TableHead className="text-gray-300">Confidence</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {predictionResults.map((result) => (
                        <TableRow key={result.id} className="border-gray-700">
                          <TableCell className="text-white max-w-xs truncate">
                            {result.text}
                          </TableCell>
                          <TableCell>
                            <Badge 
                              className={
                                result.prediction.includes('Positive') || result.prediction.includes('Low Risk') 
                                  ? 'bg-green-600 text-white'
                                  : result.prediction.includes('Negative') || result.prediction.includes('High Risk')
                                  ? 'bg-red-600 text-white'
                                  : 'bg-yellow-600 text-white'
                              }
                            >
                              {result.prediction}
                            </Badge>
                          </TableCell>
                          <TableCell className="text-gray-300">
                            {(result.confidence * 100).toFixed(1)}%
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </CardContent>
              </Card>
            )}

            {/* Charts */}
            {predictionResults.length > 0 && (
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <Card className="bg-gray-900 border-gray-700">
                  <CardHeader>
                    <CardTitle className="text-white">Distribution</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <ResponsiveContainer width="100%" height={300}>
                      <PieChart>
                        <Pie
                          data={predictionResults[0]?.prediction.includes('Risk') ? churnData : sentimentData}
                          cx="50%"
                          cy="50%"
                          outerRadius={80}
                          dataKey="value"
                          label={({ name, value }) => `${name}: ${value}%`}
                        >
                          {(predictionResults[0]?.prediction.includes('Risk') ? churnData : sentimentData).map((entry, index) => (
                            <Cell key={`cell-${index}`} fill={entry.fill} />
                          ))}
                        </Pie>
                        <Tooltip 
                          contentStyle={{ 
                            backgroundColor: '#1F2937', 
                            border: '1px solid #374151',
                            borderRadius: '6px',
                            color: '#fff'
                          }}
                        />
                      </PieChart>
                    </ResponsiveContainer>
                  </CardContent>
                </Card>
              </div>
            )}
          </TabsContent>

          {user.role === 'admin' && (
            <TabsContent value="retraining" className="space-y-6">
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                
                {/* Retrain Model */}
                <Card className="bg-gray-900 border-gray-700">
                  <CardHeader>
                    <CardTitle className="flex items-center text-white">
                      <RefreshCw className="h-5 w-5 mr-2" />
                      Model Retraining
                    </CardTitle>
                    <CardDescription className="text-gray-400">
                      Upload new training data and retrain models
                    </CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <div className="border-2 border-dashed border-gray-600 rounded-lg p-8 text-center bg-gray-800/50">
                      <Upload className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                      <p className="text-white mb-2">Upload training data (CSV)</p>
                      <p className="text-sm text-gray-500">Training datasets up to 50MB</p>
                    </div>

                    {isRetraining && (
                      <div className="space-y-2">
                        <div className="flex justify-between text-sm">
                          <span className="text-gray-400">Training Progress</span>
                          <span className="text-white">{retrainProgress}%</span>
                        </div>
                        <Progress value={retrainProgress} className="h-2" />
                      </div>
                    )}

                    <Button
                      onClick={handleRetrain}
                      disabled={isRetraining}
                      className="w-full bg-green-600 hover:bg-green-700 text-white"
                    >
                      {isRetraining ? 'Training...' : 'Trigger Retrain'}
                    </Button>
                  </CardContent>
                </Card>



              </div>
            </TabsContent>
          )}
        </Tabs>
      </div>
    </div>
  );
}