import React, { useState } from 'react';
import { UploadSections, ConsolidatedData, TabType } from '../../types';
import PreviewTabs from './PreviewTabs';
import PreviewTable from './PreviewTable';

interface DataPreviewSectionProps {
  uploadedSections: UploadSections;
  consolidatedData: ConsolidatedData | null;
}

const DataPreviewSection: React.FC<DataPreviewSectionProps> = ({
  uploadedSections,
  consolidatedData
}) => {
  const [activeTab, setActiveTab] = useState<TabType>('leads');

  const getTabStatus = (tab: TabType) => {
    return uploadedSections[tab] !== null;
  };

  if (!Object.values(uploadedSections).some(file => file !== null) && !consolidatedData) {
    return null;
  }

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-200">
      <div className="p-6 border-b border-gray-200">
        <h2 className="text-xl font-semibold text-gray-900 mb-4">Data Preview</h2>
        
        <PreviewTabs
          activeTab={activeTab}
          setActiveTab={setActiveTab}
          getTabStatus={getTabStatus}
        />

        <PreviewTable
          activeTab={activeTab}
          getTabStatus={getTabStatus}
        />
      </div>
    </div>
  );
};

export default DataPreviewSection;