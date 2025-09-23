import React, { useState } from 'react';
import { Link as RouterLink, useLocation } from 'react-router-dom';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { RadioGroup, RadioGroupItem } from './ui/radio-group';
import { LogOut, Upload, FileText, Link, Database, MessageCircle, Brain, CheckCircle } from 'lucide-react';
import { toast } from 'sonner@2.0.3';

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
  const [url, setUrl] = useState('');


  const handleFileUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    const typeText = pdfType === 'policy' ? 'Policy' : 'Expert Knowledge';
    
    // Show processing toast
    toast.loading(`Processing ${typeText} PDF: ${file.name}`, {
      id: 'pdf-upload'
    });

    // Simulate processing
    setTimeout(() => {
      toast.success(`${typeText} PDF successfully processed and added to knowledge base!`, {
        id: 'pdf-upload',
        icon: <CheckCircle className="h-4 w-4" />,
        duration: 4000
      });
    }, 3000);

    // Reset file input
    event.target.value = '';
  };

  const handleUrlUpload = (e: React.FormEvent) => {
    e.preventDefault();
    if (!url.trim()) return;

    // Show processing toast
    toast.loading(`Processing URL: ${url}`, {
      id: 'url-upload'
    });

    // Simulate processing
    setTimeout(() => {
      toast.success('URL successfully processed and content added to knowledge base!', {
        id: 'url-upload',
        icon: <CheckCircle className="h-4 w-4" />,
        duration: 4000
      });
    }, 2000);

    setUrl('');
  };



  return (
    <div className="min-h-screen bg-black text-white">
      {/* Navigation Tabs */}
      <div className="border-b border-gray-700 bg-gray-900">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <nav className="flex space-x-6">
              <RouterLink
                to="/chat/employee"
                className={`flex items-center space-x-2 px-3 py-2 rounded-md transition-colors ${
                  location.pathname === '/chat/employee'
                    ? 'bg-[#1B4F72] text-white'
                    : 'text-gray-400 hover:text-white hover:bg-gray-800'
                }`}
              >
                <MessageCircle className="h-4 w-4" />
                <span>Chat</span>
              </RouterLink>
              
              <RouterLink
                to="/ml"
                className={`flex items-center space-x-2 px-3 py-2 rounded-md transition-colors ${
                  location.pathname === '/ml'
                    ? 'bg-[#1B4F72] text-white'
                    : 'text-gray-400 hover:text-white hover:bg-gray-800'
                }`}
              >
                <Brain className="h-4 w-4" />
                <span>ML Analysis</span>
              </RouterLink>
              
              <RouterLink
                to="/reports"
                className={`flex items-center space-x-2 px-3 py-2 rounded-md transition-colors ${
                  location.pathname === '/reports'
                    ? 'bg-[#1B4F72] text-white'
                    : 'text-gray-400 hover:text-white hover:bg-gray-800'
                }`}
              >
                <FileText className="h-4 w-4" />
                <span>Report Analysis</span>
              </RouterLink>
              
              <RouterLink
                to="/admin/data"
                className={`flex items-center space-x-2 px-3 py-2 rounded-md transition-colors ${
                  location.pathname === '/admin/data'
                    ? 'bg-[#1B4F72] text-white'
                    : 'text-gray-400 hover:text-white hover:bg-gray-800'
                }`}
              >
                <Database className="h-4 w-4" />
                <span>Data Admin</span>
              </RouterLink>
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
            <Database className="h-8 w-8 text-purple-400" />
            <div>
              <h1 className="text-2xl">Data Administration</h1>
              <p className="text-gray-400">Manage knowledge base content</p>
            </div>
          </div>
        </div>
      </div>

      <div className="container mx-auto px-4 py-8">
        <div className="space-y-6">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              
              {/* PDF Upload */}
              <Card className="bg-gray-900 border-gray-700">
                <CardHeader>
                  <CardTitle className="flex items-center text-white">
                    <FileText className="h-5 w-5 mr-2" />
                    PDF Upload
                  </CardTitle>
                  <CardDescription className="text-gray-400">
                    Upload PDF documents for knowledge ingestion
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <RadioGroup value={pdfType} onValueChange={(value: 'policy' | 'expert') => setPdfType(value)}>
                    <div className="flex items-center space-x-2">
                      <RadioGroupItem value="policy" id="policy" />
                      <Label htmlFor="policy" className="text-white">Policy PDF</Label>
                    </div>
                    <div className="flex items-center space-x-2">
                      <RadioGroupItem value="expert" id="expert" />
                      <Label htmlFor="expert" className="text-white">Expert Knowledge PDF</Label>
                    </div>
                  </RadioGroup>

                  <div className="border-2 border-dashed border-gray-600 rounded-lg p-8 text-center bg-gray-800/50">
                    <Upload className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                    <Label htmlFor="pdf-upload" className="cursor-pointer">
                      <span className="text-white">Click to upload</span>
                      <span className="text-gray-400"> or drag and drop</span>
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
              <Card className="bg-gray-900 border-gray-700">
                <CardHeader>
                  <CardTitle className="flex items-center text-white">
                    <Link className="h-5 w-5 mr-2" />
                    URL Upload
                  </CardTitle>
                  <CardDescription className="text-gray-400">
                    Add URLs for content scraping and analysis
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <form onSubmit={handleUrlUpload} className="space-y-4">
                    <Input
                      type="url"
                      placeholder="https://example.com/page"
                      value={url}
                      onChange={(e) => setUrl(e.target.value)}
                      className="bg-gray-800 border-gray-600 text-white placeholder:text-gray-400"
                    />
                    <Button 
                      type="submit" 
                      className="w-full bg-purple-600 hover:bg-purple-700 text-white"
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