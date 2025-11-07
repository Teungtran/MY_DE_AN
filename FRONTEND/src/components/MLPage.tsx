import React, { useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { Button } from './ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from './ui/table';
import { Badge } from './ui/badge';
import { Progress } from './ui/progress';
import { Input } from './ui/input';
import { LogOut, Upload, Brain, TrendingUp, RefreshCw, MessageCircle, FileText, Database, Download, ChevronDown, ChevronUp } from 'lucide-react';
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip, BarChart, Bar, XAxis, YAxis, CartesianGrid, Legend } from 'recharts';
import { FPTLogo } from './FPTLogo';
import { toast } from 'sonner';
import { mlAPI } from '../utils/api';

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
  rating?: number;
  churn_rate?: number;
}

interface SentimentData {
  review: string;
  predicted_sentiment: number;
  rating: number;
}

interface ChurnData {
  customer_id: string;
  Customer_Name: string;
  Frequency: number;
  TotalSpent: number;
  Recency: number;
  Churn_RATE: number;
  LastPurchaseDate: string;
}

interface MLPageProps {
  user: User;
  onLogout: () => void;
}

export function MLPage({ user, onLogout }: MLPageProps) {
  const location = useLocation();
  const [predictionResults, setPredictionResults] = useState<PredictionResult[]>([]);
  const [rawData, setRawData] = useState<SentimentData[] | ChurnData[]>([]);
  const [isProcessing, setIsProcessing] = useState(false);
  const [retrainProgress, setRetrainProgress] = useState(0);
  const [isRetraining, setIsRetraining] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [selectedSentimentTrainingFile, setSelectedSentimentTrainingFile] = useState<File | null>(null);
  const [selectedChurnTrainingFile, setSelectedChurnTrainingFile] = useState<File | null>(null);
  const [predictionType, setPredictionType] = useState<'sentiment' | 'churn'>('sentiment');
  const [modelVersion, setModelVersion] = useState<string>('1');
  const [scalerVersion, setScalerVersion] = useState<string>('scaler_churn_version_20250701T105905.pkl');
  const [runId, setRunId] = useState<string>('b523ba441ea0465085716dcebb916294');
  const [apiSummary, setApiSummary] = useState<any>(null);
  const [isTableExpanded, setIsTableExpanded] = useState(true);



  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      setSelectedFile(file);
    }
  };

  const handleSentimentTrainingFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      setSelectedSentimentTrainingFile(file);
    }
  };

  const handleChurnTrainingFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      setSelectedChurnTrainingFile(file);
    }
  };

  const handlePrediction = async () => {
    if (!selectedFile) {
      toast.error('Please select a file first');
      return;
    }

    setIsProcessing(true);
    try {
      let response: any;
      
      if (predictionType === 'sentiment') {
        response = await mlAPI.sentimentPredict(selectedFile, {
          model_version: modelVersion || undefined,
          tokenizer_version: undefined,
          run_id: runId || undefined
        });
      } else {
        response = await mlAPI.churnPredict(selectedFile, {
          model_version: modelVersion || undefined,
          scaler_version: scalerVersion || undefined,
          run_id: runId || undefined
        });
      }

      // Store raw data for visualization
      setRawData(response.payload.s3_results_data);
      setApiSummary(response.payload.summary);

      // Transform data for prediction results table
      const results: PredictionResult[] = response.payload.s3_results_data.map((item: any, index: number) => ({
        id: index.toString(),
        text: predictionType === 'sentiment' ? item.review : `${item.Customer_Name} (${item.customer_id})`,
        prediction: predictionType === 'sentiment' ? 
          `Rating: ${item.rating}/5` : 
          `Churn Risk: ${(item.Churn_RATE * 100).toFixed(1)}%`,
        confidence: predictionType === 'sentiment' ? item.predicted_sentiment / 5 : item.Churn_RATE,
        rating: item.rating,
        churn_rate: item.Churn_RATE
      }));

      setPredictionResults(results);
      toast.success(`${predictionType === 'sentiment' ? 'Sentiment' : 'Churn'} analysis completed successfully!`);
    } catch (error) {
      console.error('Prediction error:', error);
      toast.error('Prediction failed. Please try again.');
    } finally {
      setIsProcessing(false);
    }
  };



  const handleSentimentRetrain = async () => {
    if (user.role !== 'admin') {
      toast.error('Only administrators can retrain models');
      return;
    }

    setIsRetraining(true);
    setRetrainProgress(0);

    try {
      // Simulate progress for UX
      const progressInterval = setInterval(() => {
        setRetrainProgress(prev => Math.min(prev + 5, 95));
      }, 1000);

      const response = await mlAPI.sentimentTrain(selectedSentimentTrainingFile || undefined);
      
      clearInterval(progressInterval);
      setRetrainProgress(100);
      setIsRetraining(false);
      
      toast.success('Sentiment model retrained successfully!');
      console.log('Training result:', response);
    } catch (error: any) {
      console.error('Training error:', error);
      setIsRetraining(false);
      setRetrainProgress(0);
      toast.error(error?.message || 'Model retraining failed. Please try again.');
    }
  };

  const handleChurnRetrain = async () => {
    if (user.role !== 'admin') {
      toast.error('Only administrators can retrain models');
      return;
    }

    setIsRetraining(true);
    setRetrainProgress(0);

    try {
      // Simulate progress for UX
      const progressInterval = setInterval(() => {
        setRetrainProgress(prev => Math.min(prev + 5, 95));
      }, 1000);

      const response = await mlAPI.churnTrain(selectedChurnTrainingFile || undefined);
      
      clearInterval(progressInterval);
      setRetrainProgress(100);
      setIsRetraining(false);
      
      toast.success('Churn model retrained successfully!');
      console.log('Training result:', response);
    } catch (error: any) {
      console.error('Training error:', error);
      setIsRetraining(false);
      setRetrainProgress(0);
      toast.error(error?.message || 'Model retraining failed. Please try again.');
    }
  };

  // Generate sentiment chart data from raw data
  const generateSentimentChartData = () => {
    if (!rawData || rawData.length === 0) return { pieData: [], barData: [] };

    const sentimentData = rawData as SentimentData[];
    
    // Rating distribution for bar chart
    const ratingCounts = [1, 2, 3, 4, 5].map(rating => ({
      rating: `${rating} Star`,
      count: sentimentData.filter(item => item.rating === rating).length
    }));

    // Sentiment distribution for pie chart
    const positiveCount = sentimentData.filter(item => item.predicted_sentiment >= 3.5).length;
    const negativeCount = sentimentData.filter(item => item.predicted_sentiment < 2.5).length;
    const neutralCount = sentimentData.length - positiveCount - negativeCount;
    
    const total = sentimentData.length;
    const pieData = [
      { name: 'Positive', value: Math.round((positiveCount / total) * 100), fill: '#10B981' },
      { name: 'Negative', value: Math.round((negativeCount / total) * 100), fill: '#EF4444' },
      { name: 'Neutral', value: Math.round((neutralCount / total) * 100), fill: '#6B7280' }
    ];

    return { pieData, barData: ratingCounts };
  };

  // Generate churn chart data from raw data
  const generateChurnChartData = () => {
    if (!rawData || rawData.length === 0) return { pieData: [], barData: [] };

    const churnData = rawData as ChurnData[];
    
    // Churn rate distribution for bar chart
    const churnRanges = [
      { range: '0-20%', min: 0, max: 0.2 },
      { range: '21-40%', min: 0.2, max: 0.4 },
      { range: '41-60%', min: 0.4, max: 0.6 },
      { range: '61-80%', min: 0.6, max: 0.8 },
      { range: '81-100%', min: 0.8, max: 1.0 }
    ];

    const barData = churnRanges.map(range => ({
      range: range.range,
      count: churnData.filter(item => 
        item.Churn_RATE >= range.min && item.Churn_RATE < range.max
      ).length
    }));

    // Risk level distribution for pie chart
    const lowRisk = churnData.filter(item => item.Churn_RATE < 0.3).length;
    const mediumRisk = churnData.filter(item => item.Churn_RATE >= 0.3 && item.Churn_RATE < 0.7).length;
    const highRisk = churnData.filter(item => item.Churn_RATE >= 0.7).length;
    
    const total = churnData.length;
    const pieData = [
      { name: 'Low Risk', value: Math.round((lowRisk / total) * 100), fill: '#10B981' },
      { name: 'Medium Risk', value: Math.round((mediumRisk / total) * 100), fill: '#F59E0B' },
      { name: 'High Risk', value: Math.round((highRisk / total) * 100), fill: '#EF4444' }
    ];

    return { pieData, barData };
  };

  const sentimentCharts = generateSentimentChartData();
  const churnCharts = generateChurnChartData();

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
    <div className="min-h-screen bg-white text-black">
      {/* Header with FPT Logo */}
      <div className="border-b border-gray-200 bg-white">
        <div className="container mx-auto px-4 py-4">
          <FPTLogo />
        </div>
      </div>

      {/* Navigation Tabs */}
      <div className="border-b border-gray-200 bg-white">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <nav className="flex space-x-6">
              <Link
                to="/chat/employee"
                className={`flex items-center space-x-2 px-3 py-2 rounded-md transition-colors ${
                  location.pathname === '/chat/employee'
                    ? 'bg-blue-600 text-white'
                    : 'text-gray-600 hover:text-black hover:bg-gray-100'
                }`}
              >
                <MessageCircle className="h-4 w-4" />
                <span>Chat</span>
              </Link>
              
              <Link
                to="/ml"
                className={`flex items-center space-x-2 px-3 py-2 rounded-md transition-colors ${
                  location.pathname === '/ml'
                    ? 'bg-blue-600 text-white'
                    : 'text-gray-600 hover:text-black hover:bg-gray-100'
                }`}
              >
                <Brain className="h-4 w-4" />
                <span>ML Analysis</span>
              </Link>
              
              <Link
                to="/reports"
                className={`flex items-center space-x-2 px-3 py-2 rounded-md transition-colors ${
                  location.pathname === '/reports'
                    ? 'bg-blue-600 text-white'
                    : 'text-gray-600 hover:text-black hover:bg-gray-100'
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
                      ? 'bg-blue-600 text-white'
                      : 'text-gray-600 hover:text-black hover:bg-gray-100'
                  }`}
                >
                  <Database className="h-4 w-4" />
                  <span>Data Admin</span>
                </Link>
              )}
            </nav>
            
            <div className="flex items-center space-x-4">
              <span className="text-gray-600">Welcome, {user.email}</span>
              <Button
                variant="ghost"
                onClick={onLogout}
                className="text-gray-600 hover:text-black"
              >
                <LogOut className="h-4 w-4" />
              </Button>
            </div>
          </div>
        </div>
      </div>

      {/* Header */}
      <div className="border-b border-gray-200 bg-white">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center space-x-3">
            <Brain className="h-8 w-8 text-purple-600" />
            <div>
              <h1 className="text-2xl font-semibold text-black">Machine Learning</h1>
              <p className="text-gray-600">Predictions & Model Training</p>
            </div>
          </div>
        </div>
      </div>

      <div className="container mx-auto px-4 py-8 bg-gray-50 min-h-screen">
        <Tabs defaultValue="prediction" className="space-y-6">
          <TabsList className="bg-white border-gray-200">
            <TabsTrigger value="prediction" className="data-[state=active]:bg-gray-100">
              Prediction
            </TabsTrigger>
            {user.role === 'admin' && (
              <TabsTrigger value="retraining" className="data-[state=active]:bg-gray-100">
                Retraining
              </TabsTrigger>
            )}
          </TabsList>

          <TabsContent value="prediction" className="space-y-6">
            {/* Upload & Prediction */}
            <Card className="bg-white border-gray-200">
              <CardHeader>
                <CardTitle className="flex items-center text-black">
                  <TrendingUp className="h-5 w-5 mr-2" />
                  Data Upload & Prediction
                </CardTitle>
                <CardDescription className="text-gray-600">
                  Upload CSV data for sentiment analysis or churn prediction
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center bg-gray-50">
                  <Upload className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                  <Input
                    type="file"
                    accept=".csv"
                    onChange={handleFileSelect}
                    className="mb-4"
                  />
                  <p className="text-black mb-2">{selectedFile ? selectedFile.name : 'Upload CSV file'}</p>
                  <p className="text-sm text-gray-500">CSV files up to 5MB</p>
                </div>

                {/* Optional Parameters */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-6">
                  <div>
                    <label className="text-sm text-gray-600 mb-1 block">Model Version (Optional)</label>
                    <Input
                      type="text"
                      value={modelVersion}
                      onChange={(e) => setModelVersion(e.target.value)}
                      placeholder="e.g., 1"
                      className="bg-white border-gray-300"
                    />
                  </div>
                  <div>
                    <label className="text-sm text-gray-600 mb-1 block">Scaler Version (Optional)</label>
                    <Input
                      type="text"
                      value={scalerVersion}
                      onChange={(e) => setScalerVersion(e.target.value)}
                      placeholder="e.g., scaler_churn_version_..."
                      className="bg-white border-gray-300"
                    />
                  </div>
                  <div>
                    <label className="text-sm text-gray-600 mb-1 block">Run ID (Optional)</label>
                    <Input
                      type="text"
                      value={runId}
                      onChange={(e) => setRunId(e.target.value)}
                      placeholder="e.g., b523ba441ea0465..."
                      className="bg-white border-gray-300"
                    />
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <Button
                    onClick={() => {
                      setPredictionType('sentiment');
                      handlePrediction();
                    }}
                    disabled={isProcessing || !selectedFile}
                    className="bg-blue-600 hover:bg-blue-700 text-white"
                  >
                    {isProcessing ? 'Processing...' : 'Predict Sentiment'}
                  </Button>
                  <Button
                    onClick={() => {
                      setPredictionType('churn');
                      handlePrediction();
                    }}
                    disabled={isProcessing || !selectedFile}
                    className="bg-purple-600 hover:bg-purple-700 text-white"
                  >
                    {isProcessing ? 'Processing...' : 'Predict Churn'}
                  </Button>
                </div>
              </CardContent>
            </Card>

            {/* API Summary */}
            {apiSummary && (
              <Card className="bg-white border-gray-200">
                <CardHeader>
                  <CardTitle className="text-black">Analysis Summary</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div className="bg-blue-50 p-4 rounded-lg">
                      <h4 className="text-sm text-gray-600 mb-1">Total Records</h4>
                      <p className="text-2xl text-black">{apiSummary.total_records}</p>
                    </div>
                    {apiSummary.average_rating && (
                      <div className="bg-green-50 p-4 rounded-lg">
                        <h4 className="text-sm text-gray-600 mb-1">Average Rating</h4>
                        <p className="text-2xl text-black">{apiSummary.average_rating}/5.0</p>
                      </div>
                    )}
                    <div className="bg-purple-50 p-4 rounded-lg">
                      <h4 className="text-sm text-gray-600 mb-1">Analysis Type</h4>
                      <p className="text-lg text-black">{predictionType === 'sentiment' ? 'Sentiment Analysis' : 'Churn Prediction'}</p>
                    </div>
                  </div>
                  {apiSummary.rating_distribution && (
                    <div className="mt-4">
                      <h4 className="text-sm text-gray-600 mb-2">Rating Distribution</h4>
                      <div className="grid grid-cols-5 gap-2">
                        {Object.entries(apiSummary.rating_distribution).map(([rating, count]) => (
                          <div key={rating} className="text-center p-2 bg-gray-50 rounded">
                            <div className="text-xs text-gray-600">{rating} Star</div>
                            <div className="text-lg text-black">{count as number}</div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </CardContent>
              </Card>
            )}

            {/* Results Table */}
            {predictionResults.length > 0 && (
              <Card className="bg-white border-gray-200">
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-2">
                      <CardTitle className="text-black">Prediction Results</CardTitle>
                      <Badge variant="secondary" className="bg-gray-100 text-black">
                        {predictionResults.length} records
                      </Badge>
                    </div>
                    <div className="flex items-center space-x-2">
                      <Button
                        onClick={downloadResults}
                        className="bg-green-600 hover:bg-green-700 text-white"
                        size="sm"
                      >
                        <Download className="h-4 w-4 mr-2" />
                        Download
                      </Button>
                      <Button
                        onClick={() => setIsTableExpanded(!isTableExpanded)}
                        variant="ghost"
                        size="sm"
                        className="text-gray-600 hover:text-black"
                      >
                        {isTableExpanded ? (
                          <>
                            <ChevronUp className="h-4 w-4 mr-1" />
                            Collapse
                          </>
                        ) : (
                          <>
                            <ChevronDown className="h-4 w-4 mr-1" />
                            Expand
                          </>
                        )}
                      </Button>
                    </div>
                  </div>
                </CardHeader>
                {isTableExpanded && (
                  <CardContent>
                    <div className="overflow-auto border border-gray-200 rounded-lg" style={{ maxHeight: '500px' }}>
                      <Table>
                        <TableHeader className="bg-gray-50 sticky top-0 z-10">
                          <TableRow className="border-gray-200">
                            <TableHead className="text-black font-semibold sticky top-0 bg-gray-50">
                              #
                            </TableHead>
                            <TableHead className="text-black font-semibold sticky top-0 bg-gray-50">
                              Text/Customer
                            </TableHead>
                            <TableHead className="text-black font-semibold sticky top-0 bg-gray-50">
                              Prediction
                            </TableHead>
                            <TableHead className="text-black font-semibold sticky top-0 bg-gray-50">
                              Confidence
                            </TableHead>
                          </TableRow>
                        </TableHeader>
                        <TableBody>
                          {predictionResults.map((result, index) => (
                            <TableRow key={result.id} className="border-gray-200 hover:bg-gray-50">
                              <TableCell className="text-gray-600 font-medium">
                                {index + 1}
                              </TableCell>
                              <TableCell className="text-black max-w-md">
                                <div className="truncate" title={result.text}>
                                  {result.text}
                                </div>
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
                              <TableCell className="text-black font-medium">
                                {(result.confidence * 100).toFixed(1)}%
                              </TableCell>
                            </TableRow>
                          ))}
                        </TableBody>
                      </Table>
                    </div>
                    {predictionResults.length > 10 && (
                      <div className="mt-3 text-sm text-gray-500 text-center">
                        Showing all {predictionResults.length} results. Scroll to view more.
                      </div>
                    )}
                  </CardContent>
                )}
              </Card>
            )}

            {/* Charts */}
            {predictionResults.length > 0 && (
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* Pie Chart - Distribution */}
                <Card className="bg-white border-gray-200">
                  <CardHeader>
                    <CardTitle className="text-black">
                      {predictionType === 'sentiment' ? 'Sentiment Distribution' : 'Risk Level Distribution'}
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <ResponsiveContainer width="100%" height={300}>
                      <PieChart>
                        <Pie
                          data={predictionType === 'sentiment' ? sentimentCharts.pieData : churnCharts.pieData}
                          cx="50%"
                          cy="50%"
                          outerRadius={80}
                          dataKey="value"
                          label={({ name, value }) => `${name}: ${value}%`}
                        >
                          {(predictionType === 'sentiment' ? sentimentCharts.pieData : churnCharts.pieData).map((entry, index) => (
                            <Cell key={`cell-${index}`} fill={entry.fill} />
                          ))}
                        </Pie>
                        <Tooltip 
                          contentStyle={{ 
                            backgroundColor: '#ffffff', 
                            border: '1px solid #d1d5db',
                            borderRadius: '6px',
                            color: '#000'
                          }}
                        />
                      </PieChart>
                    </ResponsiveContainer>
                  </CardContent>
                </Card>

                {/* Bar Chart - Detailed Distribution */}
                <Card className="bg-white border-gray-200">
                  <CardHeader>
                    <CardTitle className="text-black">
                      {predictionType === 'sentiment' ? 'Rating Distribution' : 'Churn Rate Distribution'}
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <ResponsiveContainer width="100%" height={300}>
                      <BarChart data={predictionType === 'sentiment' ? sentimentCharts.barData : churnCharts.barData}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                        <XAxis 
                          dataKey={predictionType === 'sentiment' ? 'rating' : 'range'} 
                          stroke="#6b7280"
                        />
                        <YAxis stroke="#6b7280" />
                        <Tooltip 
                          contentStyle={{ 
                            backgroundColor: '#ffffff', 
                            border: '1px solid #d1d5db',
                            borderRadius: '6px',
                            color: '#000'
                          }}
                        />
                        <Legend />
                        <Bar 
                          dataKey="count" 
                          fill={predictionType === 'sentiment' ? '#3B82F6' : '#8B5CF6'}
                          name={predictionType === 'sentiment' ? 'Number of Reviews' : 'Number of Customers'}
                        />
                      </BarChart>
                    </ResponsiveContainer>
                  </CardContent>
                </Card>
              </div>
            )}
          </TabsContent>

          {user.role === 'admin' && (
            <TabsContent value="retraining" className="space-y-6">
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                
                {/* Sentiment Model Retraining */}
                <Card className="bg-white border-gray-200">
                  <CardHeader>
                    <CardTitle className="flex items-center text-black">
                      <RefreshCw className="h-5 w-5 mr-2" />
                      Sentiment Model Retraining
                    </CardTitle>
                    <CardDescription className="text-gray-600">
                      Upload new sentiment training data and retrain model
                    </CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <div className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center bg-gray-50">
                      <Upload className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                      <Input
                        type="file"
                        accept=".csv"
                        onChange={handleSentimentTrainingFileSelect}
                        className="mb-4"
                      />
                      <p className="text-black mb-2">{selectedSentimentTrainingFile ? selectedSentimentTrainingFile.name : 'Upload sentiment training data (CSV)'}</p>
                      <p className="text-sm text-gray-500">Training datasets up to 50MB</p>
                    </div>

                    {isRetraining && (
                      <div className="space-y-2">
                        <div className="flex justify-between text-sm">
                          <span className="text-gray-600">Training Progress</span>
                          <span className="text-black">{retrainProgress}%</span>
                        </div>
                        <Progress value={retrainProgress} className="h-2" />
                      </div>
                    )}

                    <Button
                      onClick={handleSentimentRetrain}
                      disabled={isRetraining || !selectedSentimentTrainingFile}
                      className="w-full bg-blue-600 hover:bg-blue-700 text-white"
                    >
                      {isRetraining ? 'Training...' : 'Retrain Sentiment Model'}
                    </Button>
                  </CardContent>
                </Card>

                {/* Churn Model Retraining */}
                <Card className="bg-white border-gray-200">
                  <CardHeader>
                    <CardTitle className="flex items-center text-black">
                      <RefreshCw className="h-5 w-5 mr-2" />
                      Churn Model Retraining
                    </CardTitle>
                    <CardDescription className="text-gray-600">
                      Upload new churn training data and retrain model
                    </CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <div className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center bg-gray-50">
                      <Upload className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                      <Input
                        type="file"
                        accept=".csv"
                        onChange={handleChurnTrainingFileSelect}
                        className="mb-4"
                      />
                      <p className="text-black mb-2">{selectedChurnTrainingFile ? selectedChurnTrainingFile.name : 'Upload churn training data (CSV)'}</p>
                      <p className="text-sm text-gray-500">Training datasets up to 50MB</p>
                    </div>

                    {isRetraining && (
                      <div className="space-y-2">
                        <div className="flex justify-between text-sm">
                          <span className="text-gray-600">Training Progress</span>
                          <span className="text-black">{retrainProgress}%</span>
                        </div>
                        <Progress value={retrainProgress} className="h-2" />
                      </div>
                    )}

                    <Button
                      onClick={handleChurnRetrain}
                      disabled={isRetraining || !selectedChurnTrainingFile}
                      className="w-full bg-purple-600 hover:bg-purple-700 text-white"
                    >
                      {isRetraining ? 'Training...' : 'Retrain Churn Model'}
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