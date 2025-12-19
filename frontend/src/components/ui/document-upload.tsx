import React, { useState, useRef } from 'react';
import { Upload, File, X, CheckCircle, AlertCircle } from 'lucide-react';

interface DocumentUploadProps {
  onFileUpload: (file: File) => void;
  acceptedTypes?: string;
  maxSize?: number; // in MB
  documentType?: string;
}

export function DocumentUpload({ 
  onFileUpload, 
  acceptedTypes = ".pdf,.jpg,.jpeg,.png,.doc,.docx",
  maxSize = 10,
  documentType = "document"
}: DocumentUploadProps) {
  const [uploadedFile, setUploadedFile] = useState<File | null>(null);
  const [uploadStatus, setUploadStatus] = useState<'idle' | 'uploading' | 'success' | 'error'>('idle');
  const [errorMessage, setErrorMessage] = useState<string>('');
  const fileInputRef = useRef<HTMLInputElement>(null);

  const processFile = (file: File) => {
    // Validate file size
    if (file.size > maxSize * 1024 * 1024) {
      setErrorMessage(`File size must be less than ${maxSize}MB`);
      setUploadStatus('error');
      return;
    }

    // Validate file type
    const fileExtension = '.' + file.name.split('.').pop()?.toLowerCase();
    if (!acceptedTypes.includes(fileExtension)) {
      setErrorMessage(`Please upload a valid file type: ${acceptedTypes}`);
      setUploadStatus('error');
      return;
    }

    setUploadedFile(file);
    setUploadStatus('uploading');
    setErrorMessage('');

    // Simulate upload process
    setTimeout(() => {
      setUploadStatus('success');
      onFileUpload(file);
    }, 1500);
  };

  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;
    processFile(file);
  };

  const handleDrop = (event: React.DragEvent<HTMLDivElement>) => {
    event.preventDefault();
    const file = event.dataTransfer.files?.[0];
    if (file) {
      processFile(file);
    }
  };

  const handleDragOver = (event: React.DragEvent<HTMLDivElement>) => {
    event.preventDefault();
  };

  const removeFile = () => {
    setUploadedFile(null);
    setUploadStatus('idle');
    setErrorMessage('');
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const triggerFileSelect = () => {
    fileInputRef.current?.click();
  };

  return (
    <div className="mt-4 p-4 border-2 border-dashed border-gray-300 dark:border-gray-600 rounded-lg bg-gray-50 dark:bg-gray-900">
      <input
        ref={fileInputRef}
        type="file"
        accept={acceptedTypes}
        onChange={handleFileSelect}
        className="hidden"
      />
      
      {uploadStatus === 'idle' && (
        <div
          className="text-center cursor-pointer p-4"
          onDrop={handleDrop}
          onDragOver={handleDragOver}
          onClick={triggerFileSelect}
        >
          <Upload className="mx-auto h-8 w-8 text-gray-400 mb-2" />
          <div className="mb-1">
            <p className="text-sm text-gray-600 dark:text-gray-400">
              Drop your {documentType} here or click to browse
            </p>
          </div>
          <div>
            <p className="text-xs text-gray-500 dark:text-gray-500">
              Accepted formats: {acceptedTypes} (max {maxSize}MB)
            </p>
          </div>
        </div>
      )}

      {uploadStatus === 'uploading' && uploadedFile && (
        <div className="flex items-center space-x-3 p-2">
          <File className="h-6 w-6 text-blue-500" />
          <div className="flex-1">
            <p className="text-sm font-medium text-gray-900 dark:text-gray-100">
              {uploadedFile.name}
            </p>
            <div className="w-full bg-blue-200 dark:bg-blue-800 rounded-full h-2 mt-1">
              <div className="bg-blue-600 dark:bg-blue-400 h-2 rounded-full animate-pulse w-3/4"></div>
            </div>
          </div>
        </div>
      )}

      {uploadStatus === 'success' && uploadedFile && (
        <div className="flex items-center space-x-3 p-2 bg-green-50 dark:bg-green-900/20 rounded-lg">
          <CheckCircle className="h-6 w-6 text-green-500" />
          <div className="flex-1">
            <p className="text-sm font-medium text-green-800 dark:text-green-200">
              {uploadedFile.name}
            </p>
            <div>
              <p className="text-xs text-green-600 dark:text-green-400">
                Upload successful
              </p>
              <p className="text-xs text-green-600 dark:text-green-400" dir="rtl">
                تم الرفع بنجاح
              </p>
            </div>
          </div>
          <button
            onClick={removeFile}
            className="text-green-600 dark:text-green-400 hover:text-green-800 dark:hover:text-green-200"
          >
            <X className="h-4 w-4" />
          </button>
        </div>
      )}

      {uploadStatus === 'error' && (
        <div className="flex items-center space-x-3 p-2 bg-red-50 dark:bg-red-900/20 rounded-lg">
          <AlertCircle className="h-6 w-6 text-red-500" />
          <div className="flex-1">
            <div>
              <p className="text-sm font-medium text-red-800 dark:text-red-200">
                Upload failed
              </p>
              <p className="text-sm font-medium text-red-800 dark:text-red-200" dir="rtl">
                فشل في الرفع
              </p>
            </div>
            <p className="text-xs text-red-600 dark:text-red-400">
              {errorMessage}
            </p>
          </div>
          <button
            onClick={removeFile}
            className="text-red-600 dark:text-red-400 hover:text-red-800 dark:hover:text-red-200"
          >
            <X className="h-4 w-4" />
          </button>
        </div>
      )}
    </div>
  );
} 