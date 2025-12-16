import React, { createContext, useContext, useState, ReactNode } from 'react';
import { preprocessAPI } from '../utils/api';
import { toast } from 'sonner';

interface AdminContextType {
  pdfType: 'policy' | 'expert';
  setPdfType: React.Dispatch<React.SetStateAction<'policy' | 'expert'>>;
  urlType: 'product' | 'agent-knowledge' | 'store-policy';
  setUrlType: React.Dispatch<React.SetStateAction<'product' | 'agent-knowledge' | 'store-policy'>>;
  url: string;
  setUrl: React.Dispatch<React.SetStateAction<string>>;
  confirmationDialog: {
    show: boolean;
    deviceName: string;
    existingDevices: string[];
    urlData: Array<{
      source: string;
      description: string;
      type: string;
      is_active: boolean;
    }>;
  };
  setConfirmationDialog: React.Dispatch<React.SetStateAction<{
    show: boolean;
    deviceName: string;
    existingDevices: string[];
    urlData: Array<{
      source: string;
      description: string;
      type: string;
      is_active: boolean;
    }>;
  }>>;
  handleFileUpload: (event: React.ChangeEvent<HTMLInputElement>) => Promise<void>;
  handleUrlUpload: (e: React.FormEvent) => Promise<void>;
  handleConfirmReplace: (replaceExisting: boolean) => Promise<void>;
}

const AdminContext = createContext<AdminContextType | undefined>(undefined);

export function AdminProvider({ children }: { children: ReactNode }) {
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

    if (file.type !== 'application/pdf') {
      toast.error('Please upload a PDF file');
      return;
    }

    const typeText = pdfType === 'policy' ? 'Policy' : 'Expert Knowledge';
    
    toast.loading(`Processing ${typeText} PDF: ${file.name}`, {
      id: 'pdf-upload'
    });

    try {
      if (pdfType === 'policy') {
        await preprocessAPI.processRagPdfs([file]);
      } else {
        await preprocessAPI.processExpertPdfs([file]);
      }

      toast.success(`${typeText} PDF successfully processed and added to knowledge base!`, {
        id: 'pdf-upload',
        duration: 4000
      });
    } catch (error: any) {
      console.error('PDF processing error:', error);
      toast.error(`Failed to process ${typeText} PDF: ${error?.message || 'Unknown error'}`, {
        id: 'pdf-upload',
        duration: 5000
      });
    }

    event.target.value = '';
  };

  const handleUrlUpload = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!url.trim()) return;

    const urlLines = url.split(/[\n,]/).map(u => u.trim()).filter(u => u.length > 0);
    
    if (urlLines.length === 0) {
      toast.error('Please enter at least one URL');
      return;
    }

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

    const urlCount = urlLines.length;
    toast.loading(`Processing ${urlCount} ${typeText} URL${urlCount > 1 ? 's' : ''}: ${urlLines[0]}${urlCount > 1 ? ` and ${urlCount - 1} more` : ''}`, {
      id: 'url-upload'
    });

    try {
      const urlData = urlLines.map(urlLine => ({
        source: urlLine,
        description: "URL",
        type: urlType === 'product' ? 'RECOMMEND' : 
              urlType === 'agent-knowledge' ? 'EXPERT_KNOWLEDGE' : 
              'RAG',
        is_active: true
      }));

      let response;
      try {
        if (urlType === 'product') {
          response = await preprocessAPI.processRecommendUrls(urlData);
          
          console.log('Product URL response:', response);
          
          if (response && (response.status === 'confirmation_required' || response.message?.includes('already exists'))) {
            console.log('Confirmation required - setting dialog:', {
              status: response.status,
              device_name: response.device_name,
              existing_devices: response.existing_devices,
              message: response.message
            });
            
            toast.dismiss('url-upload');
            
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
        throw apiError;
      }
      
      if (!response) {
        throw new Error('No response received from server');
      }

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
          duration: 4000
        });
      }
    } catch (error: any) {
      console.error('URL processing error:', error);
      
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

    toast.loading(`Replacing ${deviceText} with new data...`, {
      id: 'url-replace'
    });

    try {
      const response = await preprocessAPI.processRecommendUrls(urlData, true);

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
    <AdminContext.Provider value={{
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
    }}>
      {children}
    </AdminContext.Provider>
  );
}

export function useAdminContext() {
  const context = useContext(AdminContext);
  if (context === undefined) {
    throw new Error('useAdminContext must be used within an AdminProvider');
  }
  return context;
}
