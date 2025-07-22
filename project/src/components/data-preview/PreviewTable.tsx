import React from 'react';
import { AlertCircle } from 'lucide-react';
import { TabType } from '../../types';
import { mockLeadData, mockMessages } from '../../data/mockData';
import { getChannelIcon, getChannelColor } from '../../utils/icons';
import { formatDate } from '../../utils/formatters';

interface PreviewTableProps {
  activeTab: TabType;
  getTabStatus: (tab: TabType) => boolean;
}

const PreviewTable: React.FC<PreviewTableProps> = ({
  activeTab,
  getTabStatus
}) => {
  const renderTableHeaders = () => {
    if (activeTab === 'leads') {
      return (
        <>
          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Name</th>
          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Email</th>
          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Phone</th>
          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Source</th>
          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Created</th>
        </>
      );
    }
    
    return (
      <>
        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Type</th>
        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Content</th>
        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Sender</th>
        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Timestamp</th>
      </>
    );
  };

  const renderTableRows = () => {
    if (activeTab === 'leads') {
      if (!getTabStatus('leads')) {
        return (
          <tr>
            <td colSpan={5} className="px-6 py-8 text-center text-gray-500">
              <AlertCircle className="w-8 h-8 mx-auto mb-2 text-gray-400" />
              <p>No leads data uploaded yet</p>
              <p className="text-sm">Upload lead_details.csv to see data here</p>
            </td>
          </tr>
        );
      }

      return mockLeadData.map((lead, index) => (
        <tr key={lead.id} className={index % 2 === 0 ? 'bg-white' : 'bg-gray-50'}>
          <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">{lead.name}</td>
          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">{lead.email}</td>
          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">{lead.phone}</td>
          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">{lead.source}</td>
          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">{formatDate(lead.created_at)}</td>
        </tr>
      ));
    }

    if (!getTabStatus(activeTab)) {
      return (
        <tr>
          <td colSpan={4} className="px-6 py-8 text-center text-gray-500">
            <AlertCircle className="w-8 h-8 mx-auto mb-2 text-gray-400" />
            <p>No {activeTab} data uploaded yet</p>
            <p className="text-sm">Upload {activeTab}.csv to see data here</p>
          </td>
        </tr>
      );
    }

    return mockMessages
      .filter(msg => {
        switch (activeTab) {
          case 'whatsapp': return msg.type === 'whatsapp';
          case 'emails': return msg.type === 'email';
          case 'calls': return msg.type === 'call';
          case 'other': return msg.type === 'other';
          default: return false;
        }
      })
      .map((message, index) => (
        <tr key={message.id} className={index % 2 === 0 ? 'bg-white' : 'bg-gray-50'}>
          <td className="px-6 py-4 whitespace-nowrap">
            <div className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium capitalize ${getChannelColor(message.type)}`}>
              {getChannelIcon(message.type)}
              <span className="ml-1">{message.type}</span>
            </div>
          </td>
          <td className="px-6 py-4 text-sm text-gray-900 max-w-xs truncate">{message.content}</td>
          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600 capitalize">{message.sender}</td>
          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">{formatDate(message.timestamp)}</td>
        </tr>
      ));
  };

  return (
    <div className="overflow-x-auto">
      <table className="w-full">
        <thead>
          <tr className="bg-gray-50">
            {renderTableHeaders()}
          </tr>
        </thead>
        <tbody className="bg-white divide-y divide-gray-200">
          {renderTableRows()}
        </tbody>
      </table>
    </div>
  );
};

export default PreviewTable;