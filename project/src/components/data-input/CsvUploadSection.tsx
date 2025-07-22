import React from 'react';
import { FileText, CheckCircle2 } from 'lucide-react';
import { UploadSections } from '../../types';
import { useFileUpload } from '../../hooks/useFileUpload';
import UploadBox from './UploadBox';

interface CsvUploadSectionProps {
  uploadedSections: UploadSections;
  onSectionFileUpload: (section: keyof UploadSections, files: FileList | null) => void;
  onRemoveFile: (section: keyof UploadSections) => void;
}

const uploadSections = [
  { key: 'leads', title: 'Leads', description: 'Upload lead_details.csv', expectedFile: 'lead_details.csv' },
  { key: 'whatsapp', title: 'WhatsApp', description: 'Upload whatsapp_messages.csv', expectedFile: 'whatsapp_messages.csv' },
  { key: 'emails', title: 'Emails', description: 'Upload emails.csv', expectedFile: 'emails.csv' },
  { key: 'calls', title: 'Calls', description: 'Upload calls.csv', expectedFile: 'calls.csv' },
  { key: 'other', title: 'Other', description: 'Upload any other CSVs', expectedFile: 'other.csv' }
];

const CsvUploadSection: React.FC<CsvUploadSectionProps> = ({
  uploadedSections,
  onSectionFileUpload,
  onRemoveFile
}) => {
  const { draggedOver, handleDragOver, handleDragLeave, handleDrop } = useFileUpload();

  return (
    <div className="space-y-6">
      <div className="flex items-center space-x-2 mb-4">
        <FileText className="w-5 h-5 text-gray-600" />
        <h3 className="text-lg font-medium text-gray-900">Upload CSVs by Section</h3>
      </div>
      
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {uploadSections.map((section) => (
          <UploadBox
            key={section.key}
            section={section}
            uploadedFile={uploadedSections[section.key as keyof UploadSections]}
            isDraggedOver={draggedOver === section.key}
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={(e) => handleDrop(e, section.key as keyof UploadSections, onSectionFileUpload)}
            onFileUpload={onSectionFileUpload}
            onRemoveFile={onRemoveFile}
          />
        ))}
      </div>

      {Object.values(uploadedSections).some(file => file !== null) && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <div className="flex items-center space-x-2 mb-2">
            <CheckCircle2 className="w-5 h-5 text-blue-600" />
            <h4 className="font-medium text-blue-900">Upload Summary</h4>
          </div>
          <div className="grid grid-cols-2 md:grid-cols-5 gap-2 text-sm">
            {uploadSections.map((section) => {
              const hasFile = uploadedSections[section.key as keyof UploadSections] !== null;
              return (
                <div key={section.key} className="flex items-center space-x-1">
                  {hasFile ? (
                    <CheckCircle2 className="w-4 h-4 text-green-600" />
                  ) : (
                    <div className="w-4 h-4 border-2 border-gray-300 rounded-full" />
                  )}
                  <span className={hasFile ? 'text-green-700' : 'text-gray-500'}>
                    {section.title}
                  </span>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
};

export default CsvUploadSection;