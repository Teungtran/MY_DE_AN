import React, { createContext, useContext, useState, ReactNode } from 'react';
import { mlAPI } from '../utils/api';
import { toast } from 'sonner';

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

interface MLContextType {
  predictionResults: PredictionResult[];
  setPredictionResults: React.Dispatch<React.SetStateAction<PredictionResult[]>>;
  rawData: SentimentData[] | ChurnData[];
  setRawData: React.Dispatch<React.SetStateAction<SentimentData[] | ChurnData[]>>;
  isProcessing: boolean;
  setIsProcessing: React.Dispatch<React.SetStateAction<boolean>>;
  isSentimentRetraining: boolean;
  setIsSentimentRetraining: React.Dispatch<React.SetStateAction<boolean>>;
  isChurnRetraining: boolean;
  setIsChurnRetraining: React.Dispatch<React.SetStateAction<boolean>>;
  selectedFile: File | null;
  setSelectedFile: React.Dispatch<React.SetStateAction<File | null>>;
  selectedSentimentTrainingFile: File | null;
  setSelectedSentimentTrainingFile: React.Dispatch<React.SetStateAction<File | null>>;
  selectedChurnTrainingFile: File | null;
  setSelectedChurnTrainingFile: React.Dispatch<React.SetStateAction<File | null>>;
  predictionType: 'sentiment' | 'churn';
  setPredictionType: React.Dispatch<React.SetStateAction<'sentiment' | 'churn'>>;
  modelVersion: string;
  setModelVersion: React.Dispatch<React.SetStateAction<string>>;
  scalerVersion: string;
  setScalerVersion: React.Dispatch<React.SetStateAction<string>>;
  runId: string;
  setRunId: React.Dispatch<React.SetStateAction<string>>;
  apiSummary: any;
  setApiSummary: React.Dispatch<React.SetStateAction<any>>;
  mlflowUrl: string | null;
  setMlflowUrl: React.Dispatch<React.SetStateAction<string | null>>;
  isTableExpanded: boolean;
  setIsTableExpanded: React.Dispatch<React.SetStateAction<boolean>>;
  handlePrediction: (type?: 'sentiment' | 'churn') => Promise<void>;
  handleSentimentRetrain: (userRole: string) => Promise<void>;
  handleChurnRetrain: (userRole: string) => Promise<void>;
  downloadResults: () => void;
}

const MLContext = createContext<MLContextType | undefined>(undefined);

export function MLProvider({ children }: { children: ReactNode }) {
  const [predictionResults, setPredictionResults] = useState<PredictionResult[]>([]);
  const [rawData, setRawData] = useState<SentimentData[] | ChurnData[]>([]);
  const [isProcessing, setIsProcessing] = useState(false);
  const [isSentimentRetraining, setIsSentimentRetraining] = useState(false);
  const [isChurnRetraining, setIsChurnRetraining] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [selectedSentimentTrainingFile, setSelectedSentimentTrainingFile] = useState<File | null>(null);
  const [selectedChurnTrainingFile, setSelectedChurnTrainingFile] = useState<File | null>(null);
  const [predictionType, setPredictionType] = useState<'sentiment' | 'churn'>('sentiment');
  const [modelVersion, setModelVersion] = useState<string>('1');
  const [scalerVersion, setScalerVersion] = useState<string>('tokenizer/tokenizer_version_20250810T020107.pkl');
  const [runId, setRunId] = useState<string>('e5eb544e473d4a7b9109b98c5255de04');
  const [apiSummary, setApiSummary] = useState<any>(null);
  const [mlflowUrl, setMlflowUrl] = useState<string | null>(null);
  const [isTableExpanded, setIsTableExpanded] = useState(true);

  const handlePrediction = async (type?: 'sentiment' | 'churn') => {
    if (!selectedFile) {
      toast.error('Please select a file first');
      return;
    }

    const currentType = type || predictionType;
    setIsProcessing(true);
    
    try {
      let response: any;
      
      if (currentType === 'sentiment') {
        response = await mlAPI.sentimentPredict(selectedFile, {
          model_version: modelVersion || undefined,
          tokenizer_version: scalerVersion || undefined,
          run_id: runId || undefined
        });
      } else {
        response = await mlAPI.churnPredict(selectedFile, {
          model_version: modelVersion || undefined,
          scaler_version: scalerVersion || undefined,
          run_id: runId || undefined
        });
      }

      setRawData(response.payload.s3_results_data);
      setApiSummary({
        ...response.payload.summary,
        message: response.payload.message
      });
      setMlflowUrl(response.mlflow_url || null);

      const results: PredictionResult[] = response.payload.s3_results_data.map((item: any, index: number) => ({
        id: index.toString(),
        text: currentType === 'sentiment' ? item.review : `${item.Customer_Name} (${item.customer_id})`,
        prediction: currentType === 'sentiment' ? 
          `Rating: ${item.rating}/5` : 
          `Churn Risk: ${(item.Churn_RATE * 100).toFixed(1)}%`,
        confidence: currentType === 'sentiment' ? item.predicted_sentiment / 5 : item.Churn_RATE,
        rating: item.rating,
        churn_rate: item.Churn_RATE
      }));

      setPredictionType(currentType);
      setPredictionResults(results);
      toast.success(`${currentType === 'sentiment' ? 'Sentiment' : 'Churn'} analysis completed successfully!`);
    } catch (error) {
      console.error('Prediction error:', error);
      toast.error('Prediction failed. Please try again.');
    } finally {
      setIsProcessing(false);
    }
  };

  const handleSentimentRetrain = async (userRole: string) => {
    if (userRole !== 'admin') {
      toast.error('Only administrators can retrain models');
      return;
    }

    if (isSentimentRetraining) {
      toast.warning('Training already in progress');
      return;
    }

    setIsSentimentRetraining(true);

    try {
      toast.info('Training started. This may take several minutes...');
      const response = await mlAPI.sentimentTrain(selectedSentimentTrainingFile || undefined);
      
      setIsSentimentRetraining(false);
      
      if (response.run_id) {
        toast.success(
          `Training completed! Run ID: ${response.run_id}. Click to view in MLflow.`,
          {
            duration: 10000,
            action: response.mlflow_url ? {
              label: 'View MLflow',
              onClick: () => window.open(response.mlflow_url, '_blank')
            } : undefined
          }
        );
      } else {
        toast.success('Sentiment model retrained successfully!');
      }
      
      console.log('Training result:', response);
    } catch (error: any) {
      console.error('Training error:', error);
      setIsSentimentRetraining(false);
      toast.error(error?.message || 'Model retraining failed. Please try again.');
    }
  };

  const handleChurnRetrain = async (userRole: string) => {
    if (userRole !== 'admin') {
      toast.error('Only administrators can retrain models');
      return;
    }

    if (isChurnRetraining) {
      toast.warning('Training already in progress');
      return;
    }

    setIsChurnRetraining(true);

    try {
      toast.info('Training started. This may take several minutes...');
      const response = await mlAPI.churnTrain(selectedChurnTrainingFile || undefined);
      
      setIsChurnRetraining(false);
      
      if (response.run_id) {
        toast.success(
          `Training completed! Run ID: ${response.run_id}. Click to view in MLflow.`,
          {
            duration: 10000,
            action: response.mlflow_url ? {
              label: 'View MLflow',
              onClick: () => window.open(response.mlflow_url, '_blank')
            } : undefined
          }
        );
      } else {
        toast.success('Churn model retrained successfully!');
      }
      
      console.log('Training result:', response);
    } catch (error: any) {
      console.error('Training error:', error);
      setIsChurnRetraining(false);
      toast.error(error?.message || 'Model retraining failed. Please try again.');
    }
  };

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
    <MLContext.Provider value={{
      predictionResults,
      setPredictionResults,
      rawData,
      setRawData,
      isProcessing,
      setIsProcessing,
      isSentimentRetraining,
      setIsSentimentRetraining,
      isChurnRetraining,
      setIsChurnRetraining,
      selectedFile,
      setSelectedFile,
      selectedSentimentTrainingFile,
      setSelectedSentimentTrainingFile,
      selectedChurnTrainingFile,
      setSelectedChurnTrainingFile,
      predictionType,
      setPredictionType,
      modelVersion,
      setModelVersion,
      scalerVersion,
      setScalerVersion,
      runId,
      setRunId,
      apiSummary,
      setApiSummary,
      mlflowUrl,
      setMlflowUrl,
      isTableExpanded,
      setIsTableExpanded,
      handlePrediction,
      handleSentimentRetrain,
      handleChurnRetrain,
      downloadResults
    }}>
      {children}
    </MLContext.Provider>
  );
}

export function useMLContext() {
  const context = useContext(MLContext);
  if (context === undefined) {
    throw new Error('useMLContext must be used within an MLProvider');
  }
  return context;
}
