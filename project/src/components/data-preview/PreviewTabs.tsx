import React from 'react';
import { CheckCircle2, AlertCircle } from 'lucide-react';
import { TabType } from '../../types';

interface PreviewTabsProps {
  activeTab: TabType;
  setActiveTab: (tab: TabType) => void;
  getTabStatus: (tab: TabType) => boolean;
}

const tabs: TabType[] = ['leads', 'whatsapp', 'emails', 'calls', 'other'];

const PreviewTabs: React.FC<PreviewTabsProps> = ({
  activeTab,
  setActiveTab,
  getTabStatus
}) => {
  return (
    <div className="flex space-x-1 bg-gray-100 p-1 rounded-lg mb-6 w-fit">
      {tabs.map(tab => {
        const hasData = getTabStatus(tab);
        return (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={`flex items-center space-x-2 px-4 py-2 rounded-md text-sm font-medium transition-colors capitalize ${
              activeTab === tab ? 'bg-white text-blue-600 shadow-sm' : 'text-gray-600 hover:text-gray-900'
            }`}
          >
            <span>{tab}</span>
            {hasData ? (
              <CheckCircle2 className="w-4 h-4 text-green-600" />
            ) : (
              <AlertCircle className="w-4 h-4 text-gray-400" />
            )}
          </button>
        );
      })}
    </div>
  );
};

export default PreviewTabs;