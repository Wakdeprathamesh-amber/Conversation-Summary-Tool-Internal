import React from 'react';
import { CheckCircle2, X, RefreshCw } from 'lucide-react';
import { UploadedFile, UploadSections } from '../../types';
import { getSectionIcon, getSectionColor } from '../../utils/icons';
import { formatFileSize } from '../../utils/formatters';

interface UploadBoxProps {
  section: {
    key: string;
    title: string;
    description: string;
    expectedFile: string;
  };
  uploadedFile: UploadedFile | null;
  isDraggedOver: boolean;
  onDragOver: (e: React.DragEvent, section: string) => void;
  onDragLeave: (e: React.DragEvent) => void;
  onDrop: (e: React.DragEvent) => void;
  onFileUpload: (section: keyof UploadSections, files: FileList | null) => void;
  onRemoveFile: (section: keyof UploadSections) => void;
}

const UploadBox: React.FC<UploadBoxProps> = ({
  section,
  uploadedFile,
  isDraggedOver,
  onDragOver,
  onDragLeave,
  onDrop,
  onFileUpload,
  onRemoveFile
}) => {
  return (
    <div
      className={`relative border-2 border-dashed rounded-lg p-4 transition-all duration-200 ${
        isDraggedOver 
          ? `${getSectionColor(section.key)} border-solid scale-105` 
          : uploadedFile 
            ? 'border-green-300 bg-green-50' 
            : 'border-gray-300 bg-gray-50 hover:border-gray-400'
      }`}
      onDragOver={(e) => onDragOver(e, section.key)}
      onDragLeave={onDragLeave}
      onDrop={onDrop}
    >
      <input
        type="file"
        accept=".csv"
        onChange={(e) => onFileUpload(section.key as keyof UploadSections, e.target.files)}
        className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
        disabled={!!uploadedFile}
      />
      
      <div className="text-center">
        <div className="flex items-center justify-center mb-3">
          {uploadedFile ? (
            <CheckCircle2 className="w-8 h-8 text-green-600" />
          ) : (
            <div className={`p-2 rounded-lg ${getSectionColor(section.key)}`}>
              {getSectionIcon(section.key)}
            </div>
          )}
        </div>
        
        <h4 className="font-medium text-gray-900 mb-1">{section.title}</h4>
        
        {uploadedFile ? (
          <div className="space-y-2">
            <p className="text-sm text-green-700 font-medium">{uploadedFile.name}</p>
            <p className="text-xs text-green-600">
              {formatFileSize(uploadedFile.size)} • {uploadedFile.uploadedAt.toLocaleTimeString()}
            </p>
            <div className="flex space-x-2 justify-center mt-3">
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  onRemoveFile(section.key as keyof UploadSections);
                }}
                className="flex items-center space-x-1 px-3 py-1 text-xs bg-red-100 text-red-700 rounded-md hover:bg-red-200 transition-colors"
              >
                <X className="w-3 h-3" />
                <span>Remove</span>
              </button>
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  onRemoveFile(section.key as keyof UploadSections);
                }}
                className="flex items-center space-x-1 px-3 py-1 text-xs bg-blue-100 text-blue-700 rounded-md hover:bg-blue-200 transition-colors"
              >
                <RefreshCw className="w-3 h-3" />
                <span>Replace</span>
              </button>
            </div>
          </div>
        ) : (
          <div className="space-y-1">
            <p className="text-sm text-gray-600">{section.description}</p>
            <p className="text-xs text-gray-500">Expected: {section.expectedFile}</p>
            <p className="text-xs text-gray-400 mt-2">
              {isDraggedOver ? 'Drop file here' : 'Drag & drop or click to upload'}
            </p>
          </div>
        )}
      </div>
    </div>
  );
};

export default UploadBox;