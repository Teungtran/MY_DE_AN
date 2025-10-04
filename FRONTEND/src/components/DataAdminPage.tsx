import React, { useState } from 'react';
import { Link as RouterLink, useLocation } from 'react-router-dom';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { RadioGroup, RadioGroupItem } from './ui/radio-group';
import { LogOut, Upload, FileText, Link, Database, MessageCircle, Brain, CheckCircle } from 'lucide-react';
import { toast } from 'sonner';
import { FPTLogo } from './FPTLogo';
import { preprocessAPI } from '../utils/api';

interface User {
  id: string;
  email: string;
  role: string;
}

interface UploadedFile {
  id: string;
  name: string;
  type: 'policy-pdf' | 'expert-pdf' | 'product-url' | 'store-policy-url' | 'agent-knowledge-url';
  status: 'processing' | 'ready' | 'error';
  uploadedAt: Date;
}

interface DataAdminPageProps {
  user: User;
  onLogout: () => void;
}

export function DataAdminPage({ user, onLogout }: DataAdminPageProps) {
  const location = useLocation();
  const [pdfType, setPdfType] = useState<'policy' | 'expert'>('policy');
  const [urlType, setUrlType] = useState<'product' | 'agent-knowledge' | 'store-policy'>('product');
  const [url, setUrl] = useState('');


  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    // Validate file type
    if (file.type !== 'application/pdf') {
      toast.error('Please upload a PDF file');
      return;
    }

    const typeText = pdfType === 'policy' ? 'Policy' : 'Expert Knowledge';
    
    // Show processing toast
    toast.loading(`Processing ${typeText} PDF: ${file.name}`, {
      id: 'pdf-upload'
    });

    try {
      // Use real API based on PDF type
      if (pdfType === 'policy') {
        await preprocessAPI.processRagPdfs([file]);
      } else {
        await preprocessAPI.processExpertPdfs([file]);
      }

      toast.success(`${typeText} PDF successfully processed and added to knowledge base!`, {
        id: 'pdf-upload',
        icon: <CheckCircle className="h-4 w-4" />,
        duration: 4000
      });
    } catch (error: any) {
      console.error('PDF processing error:', error);
      toast.error(`Failed to process ${typeText} PDF: ${error?.message || 'Unknown error'}`, {
        id: 'pdf-upload',
        duration: 5000
      });
    }

    // Reset file input
    event.target.value = '';
  };

  const handleUrlUpload = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!url.trim()) return;

    // Validate URL format
    try {
      new URL(url);
    } catch {
      toast.error('Please enter a valid URL');
      return;
    }

    const typeText = urlType === 'product' ? 'Store Product' : 
                    urlType === 'agent-knowledge' ? 'Agent Knowledge' : 
                    'Store Policy';

    // Show processing toast
    toast.loading(`Processing ${typeText} URL: ${url}`, {
      id: 'url-upload'
    });

    try {
      // Prepare URL data
      const urlData = [{
        source: url,
        description: `${typeText} content from ${url}`,
        type: urlType === 'product' ? 'RECOMMEND' : 
              urlType === 'agent-knowledge' ? 'EXPERT_KNOWLEDGE' : 
              'RAG',
        is_active: true
      }];

      // Use real API based on URL type
      if (urlType === 'product') {
        await preprocessAPI.processRecommendUrls(urlData);
      } else if (urlType === 'agent-knowledge') {
        await preprocessAPI.processExpertUrls(urlData);
      } else {
        await preprocessAPI.processRagUrls(urlData);
      }

      toast.success(`${typeText} URL successfully processed and content added to knowledge base!`, {
        id: 'url-upload',
        icon: <CheckCircle className="h-4 w-4" />,
        duration: 4000
      });
    } catch (error: any) {
      console.error('URL processing error:', error);
      toast.error(`Failed to process ${typeText} URL: ${error?.message || 'Unknown error'}`, {
        id: 'url-upload',
        duration: 5000
      });
    }

    setUrl('');
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
              <RouterLink
                to="/chat/employee"
                className={`flex items-center space-x-2 px-3 py-2 rounded-md transition-colors ${
                  location.pathname === '/chat/employee'
                    ? 'bg-blue-600 text-white'
                    : 'text-gray-600 hover:text-black hover:bg-gray-100'
                }`}
              >
                <MessageCircle className="h-4 w-4" />
                <span>Chat</span>
              </RouterLink>
              
              <RouterLink
                to="/ml"
                className={`flex items-center space-x-2 px-3 py-2 rounded-md transition-colors ${
                  location.pathname === '/ml'
                    ? 'bg-blue-600 text-white'
                    : 'text-gray-600 hover:text-black hover:bg-gray-100'
                }`}
              >
                <Brain className="h-4 w-4" />
                <span>ML Analysis</span>
              </RouterLink>
              
              <RouterLink
                to="/reports"
                className={`flex items-center space-x-2 px-3 py-2 rounded-md transition-colors ${
                  location.pathname === '/reports'
                    ? 'bg-blue-600 text-white'
                    : 'text-gray-600 hover:text-black hover:bg-gray-100'
                }`}
              >
                <FileText className="h-4 w-4" />
                <span>Report Analysis</span>
              </RouterLink>
              
              <RouterLink
                to="/admin/data"
                className={`flex items-center space-x-2 px-3 py-2 rounded-md transition-colors ${
                  location.pathname === '/admin/data'
                    ? 'bg-blue-600 text-white'
                    : 'text-gray-600 hover:text-black hover:bg-gray-100'
                }`}
              >
                <Database className="h-4 w-4" />
                <span>Data Admin</span>
              </RouterLink>
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
            <Database className="h-8 w-8 text-purple-600" />
            <div>
              <h1 className="text-2xl font-semibold text-black">Data Administration</h1>
              <p className="text-gray-600">Manage knowledge base content</p>
            </div>
          </div>
        </div>
      </div>

      <div className="container mx-auto px-4 py-8 bg-gray-50 min-h-screen">
        <div className="space-y-6">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              
              {/* PDF Upload */}
              <Card className="bg-white border-gray-200">
                <CardHeader>
                  <CardTitle className="flex items-center text-black">
                    <FileText className="h-5 w-5 mr-2" />
                    PDF Upload
                  </CardTitle>
                  <CardDescription className="text-gray-600">
                    Upload PDF documents for knowledge ingestion
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <RadioGroup value={pdfType} onValueChange={(value: 'policy' | 'expert') => setPdfType(value)}>
                    <div className="flex items-center space-x-2">
                      <RadioGroupItem value="policy" id="policy" />
                      <Label htmlFor="policy" className="text-black">Policy PDF</Label>
                    </div>
                    <div className="flex items-center space-x-2">
                      <RadioGroupItem value="expert" id="expert" />
                      <Label htmlFor="expert" className="text-black">Expert Knowledge PDF</Label>
                    </div>
                  </RadioGroup>

                  <div className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center bg-gray-50">
                    <Upload className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                    <Label htmlFor="pdf-upload" className="cursor-pointer">
                      <span className="text-black">Click to upload</span>
                      <span className="text-gray-600"> or drag and drop</span>
                      <Input
                        id="pdf-upload"
                        type="file"
                        accept=".pdf"
                        className="hidden"
                        onChange={handleFileUpload}
                      />
                    </Label>
                    <p className="text-sm text-gray-500 mt-2">PDF files up to 10MB</p>
                  </div>
                </CardContent>
              </Card>

              {/* URL Upload */}
              <Card className="bg-white border-gray-200">
                <CardHeader>
                  <CardTitle className="flex items-center text-black">
                    <Link className="h-5 w-5 mr-2" />
                    URL Upload
                  </CardTitle>
                  <CardDescription className="text-gray-600">
                    Add URLs for content scraping and analysis
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <RadioGroup value={urlType} onValueChange={(value: 'product' | 'agent-knowledge' | 'store-policy') => setUrlType(value)}>
                    <div className="flex items-center space-x-2">
                      <RadioGroupItem value="product" id="product" />
                      <Label htmlFor="product" className="text-black">Update Store Product</Label>
                    </div>
                    <div className="flex items-center space-x-2">
                      <RadioGroupItem value="agent-knowledge" id="agent-knowledge" />
                      <Label htmlFor="agent-knowledge" className="text-black">Update Agent Knowledge</Label>
                    </div>
                    <div className="flex items-center space-x-2">
                      <RadioGroupItem value="store-policy" id="store-policy" />
                      <Label htmlFor="store-policy" className="text-black">Update Store Policy</Label>
                    </div>
                  </RadioGroup>
                  
                  <form onSubmit={handleUrlUpload} className="space-y-4">
                    <Input
                      type="url"
                      placeholder="https://example.com/page"
                      value={url}
                      onChange={(e) => setUrl(e.target.value)}
                      className="bg-white border-gray-300 text-black placeholder:text-gray-400"
                    />
                    <Button 
                      type="submit" 
                      className="w-full bg-black hover:bg-gray-800 text-white"
                      disabled={!url.trim()}
                    >
                      Upload & Process
                    </Button>
                  </form>
                </CardContent>
              </Card>

            </div>
        </div>
      </div>
    </div>
  );
}