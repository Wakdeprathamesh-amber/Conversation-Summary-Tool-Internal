import React, { useState, useCallback, useRef } from 'react';
import TimelineItem from './TimelineItem';
import LLMSummaryDisplay from '../summary/LLMSummaryDisplay';

interface TimelineSectionProps {
  timelineData: any[];
  handleGenerateSummary: () => void;
  isSummaryLoading: boolean;
  summary: any | null;
}

const TimelineSection: React.FC<TimelineSectionProps> = ({
  timelineData,
  handleGenerateSummary,
  isSummaryLoading,
  summary
}) => {
  const [expandedItems, setExpandedItems] = useState<Record<string, boolean>>({});
  const [transcribingAll, setTranscribingAll] = useState(false);
  const [transcribeProgress, setTranscribeProgress] = useState<number>(0);
  const [transcribeErrors, setTranscribeErrors] = useState<string[]>([]);
  const [transcripts, setTranscripts] = useState<Record<string, string>>({});
  const [individualTranscribing, setIndividualTranscribing] = useState<Record<string, boolean>>({});
  const [individualTranscribeErrors, setIndividualTranscribeErrors] = useState<Record<string, string>>({});
  
  // Keep track of items that should stay expanded during transcription
  const [forceExpandedItems, setForceExpandedItems] = useState<Record<string, boolean>>({});
  
  // Use ref to track expanded state immediately
  const expandedItemsRef = useRef<Record<string, boolean>>({});
  const forceExpandedItemsRef = useRef<Record<string, boolean>>({});

  const toggleExpanded = (itemId: string) => {
    setExpandedItems(prev => ({
      ...prev,
      [itemId]: !prev[itemId]
    }));
    // Clear force expanded when manually toggled
    setForceExpandedItems(prev => ({
      ...prev,
      [itemId]: false
    }));
  };

  // Get the conversation summary markdown from the summary object
  const summaryMarkdown = summary?.conversation_summary?.conversation_summary?.sections
    ? Object.entries(summary.conversation_summary.conversation_summary.sections)
        .map(([heading, content]) => `## ${heading}\n${content}`)
        .join('\n\n')
    : '';

  // Transcribe all calls logic
  const TRANSCRIPTION_API_URL = import.meta.env.VITE_TRANSCRIPTION_API_URL || 'http://localhost:8001';
  
  // Individual transcription handler
  const handleIndividualTranscribe = useCallback(async (item: any) => {
    // Use the same robust key generation as in the render
    const itemId = item.id || `item-${timelineData.findIndex(i => i === item)}`;
    const itemKey = `${itemId}-${item.type}`;
    
    // Ensure the item stays expanded during transcription - use immediate state update
    setExpandedItems(prev => {
      const newState = { ...prev, [itemKey]: true };
      expandedItemsRef.current = newState;
      return newState;
    });
    setForceExpandedItems(prev => {
      const newState = { ...prev, [itemKey]: true };
      forceExpandedItemsRef.current = newState;
      return newState;
    });
    
    setIndividualTranscribing(prev => ({ ...prev, [itemKey]: true }));
    setIndividualTranscribeErrors(prev => ({ ...prev, [itemKey]: '' }));
    
    try {
      const response = await fetch(`${TRANSCRIPTION_API_URL}/transcribe-call`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ record_url: item.record_url, mobile_number: item.to_number, call_id: item.id }),
      });
      if (!response.ok) throw new Error(await response.text());
      const text = await response.text();
      setTranscripts(prev => ({ ...prev, [itemKey]: text }));
    } catch (err: any) {
      setIndividualTranscribeErrors(prev => ({ ...prev, [itemKey]: err.message || 'Failed to transcribe' }));
    } finally {
      setIndividualTranscribing(prev => ({ ...prev, [itemKey]: false }));
      // Clear force expanded after transcription completes
      setForceExpandedItems(prev => ({ ...prev, [itemKey]: false }));
    }
  }, [expandedItems]);
  
  const handleTranscribeAll = async () => {
    setTranscribingAll(true);
    setTranscribeProgress(0);
    setTranscribeErrors([]);
    const callItems = timelineData.filter(item => item.type === 'call' && item.record_url);
    const newTranscripts: Record<string, string> = { ...transcripts };
    let completed = 0;
    for (const item of callItems) {
      try {
        const itemId = item.id || `item-${timelineData.findIndex(i => i === item)}`;
        const itemKey = `${itemId}-${item.type}`;
        
        const response = await fetch(`${TRANSCRIPTION_API_URL}/transcribe-call`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ record_url: item.record_url, mobile_number: item.to_number, call_id: item.id }),
        });
        if (!response.ok) throw new Error(await response.text());
        const text = await response.text();
        newTranscripts[itemKey] = text;
      } catch (err: any) {
        const itemId = item.id || `item-${timelineData.findIndex(i => i === item)}`;
        setTranscribeErrors(prev => [...prev, `Call ${itemId}: ${err.message || 'Failed to transcribe'}`]);
      }
      completed++;
      setTranscribeProgress(Math.round((completed / callItems.length) * 100));
    }
    setTranscripts(newTranscripts);
    setTranscribingAll(false);
  };

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-200">
      <div className="p-6 border-b border-gray-200">
        <div className="flex items-center justify-between">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">📋 Communication Timeline</h2>
          <div className="text-sm text-gray-500 bg-gray-100 px-3 py-1 rounded-full">
            {timelineData.length} events
          </div>
        </div>
      </div>
      <div className="p-6">
        {/* Transcribe All Calls Button */}
        <div className="flex justify-end mb-2">
          <button
            onClick={handleTranscribeAll}
            disabled={transcribingAll}
            className="px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700 disabled:opacity-50"
          >
            {transcribingAll ? `Transcribing... (${transcribeProgress}%)` : 'Transcribe all calls'}
          </button>
        </div>
        {transcribeErrors.length > 0 && (
          <div className="mb-2 p-2 bg-red-100 text-red-700 rounded text-sm">
            {transcribeErrors.map((err, idx) => <div key={idx}>{err}</div>)}
          </div>
        )}
        <div className="space-y-4">
          {timelineData.map((item, index) => {
            // Create a robust key that handles undefined IDs
            const itemId = item.id || `item-${index}`;
            const itemKey = `${itemId}-${item.type}`;
            const uniqueKey = `${itemId}-${item.type}-${index}`;
            
            return (
              <TimelineItem
                key={uniqueKey}
                item={{ ...item, transcript: transcripts[itemKey] }}
                isLast={index === timelineData.length - 1}
                isExpanded={!!expandedItems[itemKey] || !!forceExpandedItems[itemKey] || !!expandedItemsRef.current[itemKey] || !!forceExpandedItemsRef.current[itemKey]}

                onToggleExpand={() => toggleExpanded(itemKey)}
                onTranscribe={() => handleIndividualTranscribe(item)}
                isTranscribing={individualTranscribing[itemKey] || false}
                transcribeError={individualTranscribeErrors[itemKey] || null}
              />
            );
          })}
        </div>

        {/* Generate Summary Button */}
        <div className="flex justify-center mt-8">
          <button
            onClick={handleGenerateSummary}
            disabled={isSummaryLoading}
            className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isSummaryLoading ? 'Generating Summary...' : 'Generate Summary'}
          </button>
        </div>

        {/* LLM Summary Output Section */}
        {summaryMarkdown && (
          <div className="mt-8">
            <LLMSummaryDisplay 
              summaryMarkdown={summaryMarkdown}
              rawData={summary}
            />
          </div>
        )}
      </div>
    </div>
  );
};

export default TimelineSection;