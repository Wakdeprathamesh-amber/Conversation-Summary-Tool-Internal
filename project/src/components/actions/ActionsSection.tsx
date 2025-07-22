import React from 'react';
import { Calendar, Sparkles } from 'lucide-react';
import { UploadSections, ConsolidatedData } from '../../types';

interface ActionsSectionProps {
  uploadedSections: UploadSections;
  consolidatedData: ConsolidatedData | null;
  isLoading: boolean;
  onConsolidate: () => void;
  onGenerateSummary: () => void;
}

const ActionsSection: React.FC<ActionsSectionProps> = ({
  uploadedSections,
  consolidatedData,
  isLoading,
  onConsolidate,
  onGenerateSummary
}) => {
  if (!Object.values(uploadedSections).some(file => file !== null) && !consolidatedData) {
    return null;
  }

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-200">
      <div className="p-6">
        <h2 className="text-xl font-semibold text-gray-900 mb-4">Actions</h2>
        <div className="flex space-x-4">
          <button
            onClick={onConsolidate}
            disabled={isLoading}
            className="flex items-center space-x-2 px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors font-medium"
          >
            <Calendar className="w-5 h-5" />
            <span>{isLoading ? 'Consolidating...' : 'Consolidate Data'}</span>
          </button>
          <button
            onClick={onGenerateSummary}
            disabled={!consolidatedData || isLoading}
            className="flex items-center space-x-2 px-6 py-3 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors font-medium"
          >
            <Sparkles className="w-5 h-5" />
            <span>{isLoading ? 'Generating...' : 'Generate Summary'}</span>
          </button>
        </div>
      </div>
    </div>
  );
};

export default ActionsSection;