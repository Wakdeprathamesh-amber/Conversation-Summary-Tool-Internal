import React, { useState, useEffect } from 'react';

interface StorageStats {
  timeline_files: number;
  lead_directories?: number;
  summary_files?: number;
  transcript_files?: number;
  log_files?: number;
  total_size_mb: number;
  oldest_file_days: number;
  newest_file_days: number;
}

interface StorageManagerProps {
  backendApiUrl: string;
  transcriptionApiUrl: string;
}

const StorageManager: React.FC<StorageManagerProps> = ({ backendApiUrl, transcriptionApiUrl }) => {
  const [backendStats, setBackendStats] = useState<StorageStats | null>(null);
  const [transcriptionStats, setTranscriptionStats] = useState<StorageStats | null>(null);
  const [loading, setLoading] = useState(false);
  const [cleanupLoading, setCleanupLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  const fetchStats = async () => {
    setLoading(true);
    setError(null);
    
    try {
      // Fetch backend storage stats
      const backendResponse = await fetch(`${backendApiUrl}/storage/stats`);
      if (backendResponse.ok) {
        const backendData = await backendResponse.json();
        setBackendStats(backendData);
      }
      
      // Fetch transcription storage stats
      const transcriptionResponse = await fetch(`${transcriptionApiUrl}/storage/stats`);
      if (transcriptionResponse.ok) {
        const transcriptionData = await transcriptionResponse.json();
        setTranscriptionStats(transcriptionData);
      }
    } catch (err: any) {
      setError(`Failed to fetch storage stats: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  const triggerCleanup = async (service: 'backend' | 'transcription') => {
    setCleanupLoading(true);
    setError(null);
    setSuccess(null);
    
    try {
      const apiUrl = service === 'backend' ? backendApiUrl : transcriptionApiUrl;
      const response = await fetch(`${apiUrl}/storage/cleanup`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
      });
      
      if (response.ok) {
        const result = await response.json();
        setSuccess(`${service} cleanup completed: ${JSON.stringify(result.stats)}`);
        // Refresh stats after cleanup
        setTimeout(fetchStats, 1000);
      } else {
        const errorData = await response.json();
        setError(`${service} cleanup failed: ${errorData.error || 'Unknown error'}`);
      }
    } catch (err: any) {
      setError(`${service} cleanup failed: ${err.message}`);
    } finally {
      setCleanupLoading(false);
    }
  };

  useEffect(() => {
    fetchStats();
  }, [backendApiUrl, transcriptionApiUrl]);

  const formatSize = (sizeMb: number) => {
    if (sizeMb < 1) return `${(sizeMb * 1024).toFixed(1)} KB`;
    if (sizeMb < 1024) return `${sizeMb.toFixed(1)} MB`;
    return `${(sizeMb / 1024).toFixed(1)} GB`;
  };

  const getStorageStatus = (stats: StorageStats) => {
    const totalItems = (stats.timeline_files || 0) + (stats.lead_directories || 0) + 
                      (stats.summary_files || 0) + (stats.transcript_files || 0) + 
                      (stats.log_files || 0);
    
    if (totalItems > 100 || stats.total_size_mb > 100) return 'warning';
    if (totalItems > 50 || stats.total_size_mb > 50) return 'info';
    return 'success';
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'warning': return 'text-yellow-600 bg-yellow-100';
      case 'info': return 'text-blue-600 bg-blue-100';
      case 'success': return 'text-green-600 bg-green-100';
      default: return 'text-gray-600 bg-gray-100';
    }
  };

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-xl font-semibold text-gray-900">🗄️ Storage Management</h2>
        <button
          onClick={fetchStats}
          disabled={loading}
          className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50"
        >
          {loading ? 'Refreshing...' : 'Refresh Stats'}
        </button>
      </div>

      {error && (
        <div className="mb-4 p-3 bg-red-100 text-red-700 rounded text-sm">
          {error}
        </div>
      )}

      {success && (
        <div className="mb-4 p-3 bg-green-100 text-green-700 rounded text-sm">
          {success}
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Backend Storage */}
        <div className="bg-gray-50 rounded-lg p-4">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Backend Storage</h3>
          {backendStats ? (
            <div className="space-y-3">
              <div className={`inline-block px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(getStorageStatus(backendStats))}`}>
                {getStorageStatus(backendStats).toUpperCase()}
              </div>
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <span className="text-gray-500">Timeline Files:</span>
                  <span className="ml-2 font-medium">{backendStats.timeline_files}</span>
                </div>
                <div>
                  <span className="text-gray-500">Lead Directories:</span>
                  <span className="ml-2 font-medium">{backendStats.lead_directories || 0}</span>
                </div>
                <div>
                  <span className="text-gray-500">Summary Files:</span>
                  <span className="ml-2 font-medium">{backendStats.summary_files || 0}</span>
                </div>
                <div>
                  <span className="text-gray-500">Total Size:</span>
                  <span className="ml-2 font-medium">{formatSize(backendStats.total_size_mb)}</span>
                </div>
                <div>
                  <span className="text-gray-500">Oldest File:</span>
                  <span className="ml-2 font-medium">{backendStats.oldest_file_days} days</span>
                </div>
                <div>
                  <span className="text-gray-500">Newest File:</span>
                  <span className="ml-2 font-medium">{backendStats.newest_file_days} days</span>
                </div>
              </div>
              <button
                onClick={() => triggerCleanup('backend')}
                disabled={cleanupLoading}
                className="w-full px-3 py-2 bg-orange-600 text-white rounded hover:bg-orange-700 disabled:opacity-50 text-sm"
              >
                {cleanupLoading ? 'Cleaning...' : 'Cleanup Backend Storage'}
              </button>
            </div>
          ) : (
            <div className="text-gray-500 text-sm">No data available</div>
          )}
        </div>

        {/* Transcription Storage */}
        <div className="bg-gray-50 rounded-lg p-4">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Transcription Storage</h3>
          {transcriptionStats ? (
            <div className="space-y-3">
              <div className={`inline-block px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(getStorageStatus(transcriptionStats))}`}>
                {getStorageStatus(transcriptionStats).toUpperCase()}
              </div>
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <span className="text-gray-500">Transcript Files:</span>
                  <span className="ml-2 font-medium">{transcriptionStats.transcript_files || 0}</span>
                </div>
                <div>
                  <span className="text-gray-500">Timeline Files:</span>
                  <span className="ml-2 font-medium">{transcriptionStats.timeline_files || 0}</span>
                </div>
                <div>
                  <span className="text-gray-500">Log Files:</span>
                  <span className="ml-2 font-medium">{transcriptionStats.log_files || 0}</span>
                </div>
                <div>
                  <span className="text-gray-500">Total Size:</span>
                  <span className="ml-2 font-medium">{formatSize(transcriptionStats.total_size_mb)}</span>
                </div>
                <div>
                  <span className="text-gray-500">Oldest File:</span>
                  <span className="ml-2 font-medium">{transcriptionStats.oldest_file_days} days</span>
                </div>
                <div>
                  <span className="text-gray-500">Newest File:</span>
                  <span className="ml-2 font-medium">{transcriptionStats.newest_file_days} days</span>
                </div>
              </div>
              <button
                onClick={() => triggerCleanup('transcription')}
                disabled={cleanupLoading}
                className="w-full px-3 py-2 bg-orange-600 text-white rounded hover:bg-orange-700 disabled:opacity-50 text-sm"
              >
                {cleanupLoading ? 'Cleaning...' : 'Cleanup Transcription Storage'}
              </button>
            </div>
          ) : (
            <div className="text-gray-500 text-sm">No data available</div>
          )}
        </div>
      </div>

      <div className="mt-6 p-4 bg-blue-50 rounded-lg">
        <h4 className="text-sm font-medium text-blue-900 mb-2">Storage Management Info</h4>
        <ul className="text-xs text-blue-800 space-y-1">
          <li>• Files older than 7 days are automatically cleaned up</li>
          <li>• Maximum 50 files per mobile number are kept</li>
          <li>• Cleanup is triggered automatically when storage usage is high</li>
          <li>• Manual cleanup is available for immediate cleanup</li>
        </ul>
      </div>
    </div>
  );
};

export default StorageManager; 