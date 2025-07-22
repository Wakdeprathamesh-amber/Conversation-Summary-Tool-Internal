import React from 'react';
import { MessageSquare, Download } from 'lucide-react';

const Header: React.FC = () => {
  return (
    <div className="bg-white shadow-sm border-b border-gray-200">
      <div className="max-w-7xl mx-auto px-6 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="bg-blue-600 p-2 rounded-lg">
              <MessageSquare className="w-6 h-6 text-white" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-gray-900">Conversation Summariser</h1>
              <p className="text-sm text-gray-600">Amber Student Communication Tool</p>
            </div>
          </div>
          <div className="flex items-center space-x-3">
            <button className="flex items-center space-x-2 px-4 py-2 bg-gray-100 hover:bg-gray-200 rounded-lg transition-colors">
              <Download className="w-4 h-4" />
              <span className="text-sm font-medium">Export</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Header;