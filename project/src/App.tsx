import React, { useState } from 'react';
import Header from './components/common/Header';
import DataInputSection from './components/data-input/DataInputSection';
import TimelineSection from './components/timeline/TimelineSection';
import StorageManager from './components/common/StorageManager';
import { useDataInput } from './hooks/useDataInput';

function App() {
  const [showStorageManager, setShowStorageManager] = useState(false);
  
  const {
    phoneEmail,
    setPhoneEmail,
    timeline,
    isLoading,
    error,
    handleLookup,
    validateInput,
    summary,
    isSummaryLoading,
    handleGenerateSummary
  } = useDataInput();

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50">
      <Header />

      <div className="max-w-7xl mx-auto px-6 py-8 space-y-8">
        <div className="flex justify-between items-center">
          <div className="flex-1">
            <DataInputSection
              phoneEmail={phoneEmail}
              setPhoneEmail={setPhoneEmail}
              isLoading={isLoading}
              onLookup={handleLookup}
              error={error}
              validateInput={validateInput}
            />
          </div>
          <div className="ml-4">
            <button
              onClick={() => setShowStorageManager(!showStorageManager)}
              className="px-4 py-2 bg-gray-600 text-white rounded hover:bg-gray-700 text-sm"
            >
              {showStorageManager ? 'Hide Storage' : 'Storage Manager'}
            </button>
          </div>
        </div>

        {showStorageManager && (
          <StorageManager
            backendApiUrl={import.meta.env.VITE_BACKEND_API_URL || 'http://localhost:8000'}
            transcriptionApiUrl={import.meta.env.VITE_TRANSCRIPTION_API_URL || 'http://localhost:8001'}
          />
        )}

        {isLoading && (
          <div className="flex justify-center items-center py-8">
            <div className="flex flex-col items-center space-y-2">
              <svg className="animate-spin h-8 w-8 text-blue-600" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z"></path>
              </svg>
              <span className="text-blue-700 font-medium text-lg">Generating timeline, please wait...</span>
            </div>
          </div>
        )}

        {timeline && !isLoading && (
          <TimelineSection
            timelineData={timeline}
            handleGenerateSummary={handleGenerateSummary}
            isSummaryLoading={isSummaryLoading}
            summary={summary}
          />
        )}
      </div>
    </div>
  );
}

export default App;