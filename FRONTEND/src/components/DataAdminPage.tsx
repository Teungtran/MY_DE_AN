import React, { useState } from 'react';
import { Link as RouterLink, useLocation } from 'react-router-dom';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Textarea } from './ui/textarea';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { RadioGroup, RadioGroupItem } from './ui/radio-group';
import { LogOut, Upload, FileText, Link, Database, MessageCircle, Brain, CheckCircle, AlertCircle } from 'lucide-react';
import { toast } from 'sonner';
import { FPTLogo } from './FPTLogo';
import { preprocessAPI } from '../utils/api';

interface User {
  id: string;
  email: string;
  role: string;
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
  const [confirmationDialog, setConfirmationDialog] = useState<{
    show: boolean;
    deviceName: string;
    existingDevices: string[];
    urlData: Array<{
      source: string;
      description: string;
      type: string;
      is_active: boolean;
    }>;
  }>({
    show: false,
    deviceName: '',
    existingDevices: [],
    urlData: []
  });


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

    // Parse multiple URLs (separated by newlines or commas)
    const urlLines = url.split(/[\n,]/).map(u => u.trim()).filter(u => u.length > 0);
    
    if (urlLines.length === 0) {
      toast.error('Please enter at least one URL');
      return;
    }

    // Validate all URL formats
    const invalidUrls: string[] = [];
    for (const urlLine of urlLines) {
      try {
        new URL(urlLine);
      } catch {
        invalidUrls.push(urlLine);
      }
    }

    if (invalidUrls.length > 0) {
      toast.error(`Invalid URL format: ${invalidUrls[0]}${invalidUrls.length > 1 ? ` and ${invalidUrls.length - 1} more` : ''}`);
      return;
    }

    const typeText = urlType === 'product' ? 'Store Product' : 
                    urlType === 'agent-knowledge' ? 'Agent Knowledge' : 
                    'Store Policy';

    // Show processing toast
    const urlCount = urlLines.length;
    toast.loading(`Processing ${urlCount} ${typeText} URL${urlCount > 1 ? 's' : ''}: ${urlLines[0]}${urlCount > 1 ? ` and ${urlCount - 1} more` : ''}`, {
      id: 'url-upload'
    });

    try {
      // Prepare URL data for all URLs
      const urlData = urlLines.map(urlLine => ({
        source: urlLine,
        description: "URL",
        type: urlType === 'product' ? 'RECOMMEND' : 
              urlType === 'agent-knowledge' ? 'EXPERT_KNOWLEDGE' : 
              'RAG',
        is_active: true
      }));

      // Use real API based on URL type
      let response;
      try {
        if (urlType === 'product') {
          response = await preprocessAPI.processRecommendUrls(urlData);
          
          // Debug log to see what we're getting
          console.log('Product URL response:', response);
          
          // Check if confirmation is required
          if (response && (response.status === 'confirmation_required' || response.message?.includes('already exists'))) {
            console.log('Confirmation required - setting dialog:', {
              status: response.status,
              device_name: response.device_name,
              existing_devices: response.existing_devices,
              message: response.message
            });
            
            // Dismiss loading toast first
            toast.dismiss('url-upload');
            
            // Set dialog state directly
            const deviceName = response.device_name || '';
            const existingDevices = response.existing_devices || (deviceName ? [deviceName] : []);
            
            setConfirmationDialog({
              show: true,
              deviceName: deviceName,
              existingDevices: existingDevices,
              urlData: urlData
            });
            console.log('Dialog state set:', { show: true, deviceName, existingDevices });
            return;
          }
        } else if (urlType === 'agent-knowledge') {
          response = await preprocessAPI.processExpertUrls(urlData);
        } else {
          response = await preprocessAPI.processRagUrls(urlData);
        }
      } catch (apiError: any) {
        console.error('API call error:', apiError);
        throw apiError; // Re-throw to be caught by outer catch
      }
      
      // Ensure response exists before processing
      if (!response) {
        throw new Error('No response received from server');
      }

      // Check if there are any errors in the response message
      // The backend returns a message string, but we need to check for error indicators
      const message = response.message || '';
      const hasGuardrailError = message.includes('Guardrail') || message.includes('INVALID DATA');
      const hasErrors = message.toLowerCase().includes('failed') || message.toLowerCase().includes('error');
      
      if (hasGuardrailError) {
        toast.error(
          `Guardrail verification failed: The content from the URL${urlCount > 1 ? 's' : ''} does not match FPT Shop product requirements. Please ensure the URLs point to valid FPT Shop product pages.`,
          {
            id: 'url-upload',
            duration: 8000
          }
        );
      } else if (hasErrors && !message.toLowerCase().includes('success')) {
        toast.error(message, {
          id: 'url-upload',
          duration: 6000
        });
      } else {
        toast.success(message || `${typeText} URL${urlCount > 1 ? 's' : ''} successfully processed and content added to knowledge base!`, {
          id: 'url-upload',
          icon: <CheckCircle className="h-4 w-4" />,
          duration: 4000
        });
      }
    } catch (error: any) {
      console.error('URL processing error:', error);
      
      // Check if error message contains guardrail information
      const errorMessage = error?.message || error?.response?.data?.detail || 'Unknown error';
      const isGuardrailError = errorMessage.includes('Guardrail') || errorMessage.includes('INVALID DATA');
      
      if (isGuardrailError) {
        toast.error(
          `Guardrail verification failed: The content from the URL${urlCount > 1 ? 's' : ''} does not match FPT Shop product requirements. Please ensure the URLs point to valid FPT Shop product pages.`,
          {
            id: 'url-upload',
            duration: 8000
          }
        );
      } else {
        toast.error(`Failed to process ${typeText} URL${urlCount > 1 ? 's' : ''}: ${errorMessage}`, {
          id: 'url-upload',
          duration: 5000
        });
      }
    }

    setUrl('');
  };

  const handleConfirmReplace = async (replaceExisting: boolean) => {
    const { deviceName, existingDevices, urlData } = confirmationDialog;
    
    // Close dialog first to prevent UI freeze
    setConfirmationDialog({ show: false, deviceName: '', existingDevices: [], urlData: [] });

    const deviceList = existingDevices && existingDevices.length > 0 ? existingDevices : [deviceName].filter(Boolean);
    const deviceCount = deviceList.length;
    const deviceText = deviceCount === 1 ? `device '${deviceList[0]}'` : `${deviceCount} devices`;

    if (!replaceExisting) {
      toast.info(`Processing cancelled. ${deviceText.charAt(0).toUpperCase() + deviceText.slice(1)} ${deviceCount === 1 ? 'was' : 'were'} not updated.`, {
        duration: 3000
      });
      return;
    }

    // Show processing toast
    toast.loading(`Replacing ${deviceText} with new data...`, {
      id: 'url-replace'
    });

    try {
      // Call the API with skip_duplicate_check=true to bypass the check and process directly
      const response = await preprocessAPI.processRecommendUrls(urlData, true);

      // Check response for errors
      const message = response.message || '';
      const hasGuardrailError = message.includes('Guardrail') || message.includes('INVALID DATA');
      const hasErrors = message.toLowerCase().includes('failed') || message.toLowerCase().includes('error');
      
      if (hasGuardrailError) {
        toast.error(
          `Guardrail verification failed: The content does not match FPT Shop product requirements.`,
          {
            id: 'url-replace',
            duration: 8000
          }
        );
      } else if (hasErrors && !message.toLowerCase().includes('success')) {
        toast.error(message, {
          id: 'url-replace',
          duration: 6000
        });
      } else {
        toast.success(message || `Successfully replaced ${deviceText} with new data!`, {
          id: 'url-replace',
          icon: <CheckCircle className="h-4 w-4" />,
          duration: 4000
        });
      }
    } catch (error: any) {
      console.error('URL replacement error:', error);
      toast.error(`Failed to replace device data: ${error?.message || 'Unknown error'}`, {
        id: 'url-replace',
        duration: 5000
      });
    }
  };




  return (
    <>
      {/* Confirmation Dialog - Using conditional render for better control */}
      {confirmationDialog.show && (
        <div 
          className="fixed inset-0 z-[9999] flex items-center justify-center bg-black/50"
          onClick={(e) => {
            // Close on backdrop click
            if (e.target === e.currentTarget) {
              setConfirmationDialog({ show: false, deviceName: '', existingDevices: [], urlData: [] });
            }
          }}
        >
          <div className="bg-white rounded-lg shadow-2xl p-6 max-w-lg w-full mx-4 border-2 border-gray-300">
            {/* Header */}
            <div className="flex items-center gap-2 mb-4">
              <AlertCircle className="h-6 w-6 text-orange-500" />
              <h2 className="text-xl font-semibold text-black">
                {confirmationDialog.existingDevices && confirmationDialog.existingDevices.length > 1 
                  ? 'Multiple Devices Already Exist' 
                  : 'Device Already Exists'}
              </h2>
            </div>
            
            {/* Description */}
            <div className="text-gray-700 mb-6">
              {confirmationDialog.existingDevices && confirmationDialog.existingDevices.length === 1 ? (
                <>
                  The device <strong className="text-black">"{confirmationDialog.existingDevices[0] || confirmationDialog.deviceName}"</strong> already exists in the database. 
                  Do you want to replace the existing data with new information from this URL?
                </>
              ) : confirmationDialog.existingDevices && confirmationDialog.existingDevices.length > 1 ? (
                <>
                  The following <strong className="text-black">{confirmationDialog.existingDevices.length} devices</strong> already exist in the database:
                  <ul className="list-disc list-inside mt-2 mb-2 text-black">
                    {confirmationDialog.existingDevices.map((device, idx) => (
                      <li key={idx}>{device}</li>
                    ))}
                  </ul>
                  Do you want to replace the existing data for all of them with new information from these URLs?
                </>
              ) : (
                <>
                  The device <strong className="text-black">"{confirmationDialog.deviceName}"</strong> already exists in the database. 
                  Do you want to replace the existing data with new information from this URL?
                </>
              )}
              
              <div className="mt-4 p-3 bg-orange-50 border border-orange-200 rounded">
                <p className="text-sm text-orange-700">
                  <strong>Warning:</strong> This will delete all existing chunks in the vector database for {(confirmationDialog.existingDevices && confirmationDialog.existingDevices.length === 1) || !confirmationDialog.existingDevices ? 'this device' : 'these devices'} and replace them with new data.
                </p>
              </div>
            </div>
            
            {/* Buttons */}
            <div className="flex gap-3 justify-end mt-6">
              <Button
                onClick={() => handleConfirmReplace(false)}
                variant="outline"
                className="px-6"
              >
                No, Cancel
              </Button>
              <Button
                onClick={() => handleConfirmReplace(true)}
                className="px-6 bg-red-600 hover:bg-red-700 text-white"
              >
                Yes, Replace
              </Button>
            </div>
          </div>
        </div>
      )}

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
                    Add URLs for content scraping and analysis (one per line or comma-separated)
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
                    <div className="space-y-2">
                      <Label htmlFor="url-input" className="text-black text-sm">
                        URLs (one per line or comma-separated)
                      </Label>
                      <Textarea
                        id="url-input"
                        placeholder="https://example.com/page1&#10;https://example.com/page2&#10;https://example.com/page3"
                        value={url}
                        onChange={(e) => setUrl(e.target.value)}
                        className="bg-white border-gray-300 text-black placeholder:text-gray-400 min-h-[120px] font-mono text-sm"
                        rows={5}
                      />
                      <p className="text-xs text-gray-500">
                        Tip: You can paste multiple URLs separated by newlines or commas
                      </p>
                    </div>
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
    </>
  );
}