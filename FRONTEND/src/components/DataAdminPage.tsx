import { Link as RouterLink, useLocation } from 'react-router-dom';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Textarea } from './ui/textarea';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { RadioGroup, RadioGroupItem } from './ui/radio-group';
import { LogOut, Upload, FileText, Link, Database, MessageCircle, Brain, AlertCircle } from 'lucide-react';
import { FPTLogo } from './FPTLogo';
import { useAdminContext } from '../contexts/AdminContext';

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
  const {
    pdfType,
    setPdfType,
    urlType,
    setUrlType,
    url,
    setUrl,
    confirmationDialog,
    setConfirmationDialog,
    handleFileUpload,
    handleUrlUpload,
    handleConfirmReplace
  } = useAdminContext();






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