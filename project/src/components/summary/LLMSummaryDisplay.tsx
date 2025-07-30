import React, { useState, useRef } from 'react';
import ReactMarkdown from 'react-markdown';
import html2pdf from 'html2pdf.js';
import LLMStructuredDisplay from './LLMStructuredDisplay';

interface LLMSummaryDisplayProps {
  summaryMarkdown: string;
  rawData?: any;
}

interface SaveButtonProps {
  onClick: () => Promise<void>;
  label: string;
  isLoading: boolean;
  variant?: 'primary' | 'secondary';
}

const SaveButton: React.FC<SaveButtonProps> = ({ onClick, label, isLoading, variant = 'primary' }) => {
  const baseClasses = "px-4 py-2 rounded font-medium transition-colors duration-200 flex items-center gap-2 disabled:opacity-50";
  const variantClasses = variant === 'primary' 
    ? "bg-blue-600 text-white hover:bg-blue-700" 
    : "bg-gray-600 text-white hover:bg-gray-700";

  return (
    <button
      onClick={onClick}
      disabled={isLoading}
      className={`${baseClasses} ${variantClasses}`}
    >
      {isLoading ? (
        <>
          <svg className="animate-spin h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
          </svg>
          <span>Saving...</span>
        </>
      ) : (
        <span>{label}</span>
      )}
    </button>
  );
};

const FORMSPREE_ENDPOINT = 'https://formspree.io/f/xyzpeyjj';

const LLMSummaryDisplay: React.FC<LLMSummaryDisplayProps> = ({ summaryMarkdown, rawData }) => {
  const [isLoadingPDF, setIsLoadingPDF] = useState(false);
  const [isLoadingJSON, setIsLoadingJSON] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [openSections, setOpenSections] = useState<Set<number>>(new Set([0])); // First section open by default
  const [feedback, setFeedback] = useState('');
  const [feedbackLoading, setFeedbackLoading] = useState(false);
  const [feedbackSuccess, setFeedbackSuccess] = useState(false);
  const [feedbackError, setFeedbackError] = useState<string | null>(null);
  const [agentEmail, setAgentEmail] = useState('');
  const [rating, setRating] = useState(0);

  // Refs for PDF generation
  const summaryRef = useRef<HTMLDivElement>(null);
  const requirementsRef = useRef<HTMLDivElement>(null);

  // Handle both markdown and structured summary formats
  // Check if conversation_summary has sections or if it's directly structured
  const conversationSummary = rawData?.conversation_summary?.conversation_summary || rawData?.conversation_summary;
  const isStructuredSummary = conversationSummary && typeof conversationSummary === 'object' && 
    !Array.isArray(conversationSummary) && Object.keys(conversationSummary).length > 0;
  
  // Debug: Log the raw data structure
  console.log('Conversation summary:', conversationSummary);
  console.log('Is structured summary:', isStructuredSummary);
  
  let sections: string[] = [];
  let sectionTitles: string[] = [];
  
  if (isStructuredSummary) {
    // Handle structured summary format - convert to readable paragraphs
    const structuredSections = conversationSummary;
    console.log('Structured sections:', structuredSections);
    
    // Check if the sections are directly the values we need
    if (typeof structuredSections === 'object' && structuredSections !== null) {
      // Check if we have a nested sections structure
      const actualSections = structuredSections.sections || structuredSections;
      console.log('Actual sections:', actualSections);
      
      sectionTitles = Object.keys(actualSections).map(key => 
        key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())
      );
      sections = Object.values(actualSections).map((section: any) => {
      if (typeof section === 'object' && section !== null) {
        // Convert structured data to readable paragraphs
        const paragraphs = Object.entries(section)
          .filter(([_, value]) => value && value !== 'Not mentioned' && value !== 'Unknown' && value !== null)
          .map(([key, value]) => {
            const fieldName = key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
            // Handle nested objects (like budget)
            if (typeof value === 'object' && value !== null) {
              const nestedValues = Object.entries(value)
                .filter(([_, v]) => v && v !== 'Not mentioned' && v !== 'Unknown' && v !== null)
                .map(([k, v]) => `${k.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}: ${v}`)
                .join(', ');
              return `${fieldName}: ${nestedValues}`;
            }
            return `${fieldName}: ${value}`;
          });
        
        if (paragraphs.length === 0) {
          return 'No specific information available for this section.';
        }
        
        return paragraphs.join('. ') + '.';
      } else if (typeof section === 'string') {
        // Handle string sections
        return section;
      }
              return section || 'No information available for this section.';
      });
      

    }
  } else {
    // Handle markdown format
    sections = summaryMarkdown.split(/^## /gm).filter(Boolean);
    sectionTitles = sections.map((_, idx) => `Section ${idx + 1}`);
  }

  const toggleSection = (idx: number) => {
    const newOpenSections = new Set(openSections);
    if (newOpenSections.has(idx)) {
      newOpenSections.delete(idx);
    } else {
      newOpenSections.add(idx);
    }
    setOpenSections(newOpenSections);
  };

  const handleSaveAsPDF = async () => {
    setIsLoadingPDF(true);
    setError(null);
    
    try {
      const element = document.getElementById('summary-content');
      if (!element) throw new Error('Summary content not found');

      // Open all sections before generating PDF
      const allSections = new Set(sections.map((_, idx) => idx));
      setOpenSections(allSections);

      // Wait for state update and reflow
      await new Promise(resolve => setTimeout(resolve, 100));

      const opt = {
        margin: 1,
        filename: `conversation-summary-${new Date().toISOString().split('T')[0]}.pdf`,
        image: { type: 'jpeg', quality: 0.98 },
        html2canvas: { scale: 2 },
        jsPDF: { unit: 'in', format: 'letter', orientation: 'portrait' }
      };
      
      await html2pdf().set(opt).from(element).save();
    } catch (err) {
      setError('Failed to generate PDF. Please try again.');
      console.error('PDF generation error:', err);
    } finally {
      setIsLoadingPDF(false);
    }
  };

  const handleSaveRaw = async () => {
    setIsLoadingJSON(true);
    setError(null);
    
    try {
      const dataToSave = rawData || { markdown: summaryMarkdown };
      const dataStr = JSON.stringify(dataToSave, null, 2);
      const blob = new Blob([dataStr], { type: 'application/json' });
      const url = window.URL.createObjectURL(blob);
      
      const linkElement = document.createElement('a');
      linkElement.href = url;
      linkElement.download = `summary-data-${new Date().toISOString().split('T')[0]}.json`;
      document.body.appendChild(linkElement);
      linkElement.click();
      document.body.removeChild(linkElement);
      window.URL.revokeObjectURL(url);
    } catch (err) {
      setError('Failed to save raw data. Please try again.');
      console.error('Raw data save error:', err);
    } finally {
      setIsLoadingJSON(false);
    }
  };

  // --- Feedback Submission ---
  const handleFeedbackSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setFeedbackLoading(true);
    setFeedbackSuccess(false);
    setFeedbackError(null);
    try {
      // Prepare FormData
      const formData = new FormData();
      if (feedback.trim()) formData.append('message', feedback.trim());
      if (agentEmail.trim()) formData.append('email', agentEmail.trim());
      formData.append('rating', rating.toString());
      // Send to Formspree
      const response = await fetch(FORMSPREE_ENDPOINT, {
        method: 'POST',
        body: formData,
        headers: {
          'Accept': 'application/json'
        }
      });
      const text = await response.text();
      if (!response.ok) {
        console.error('Formspree error response:', text);
        throw new Error(text || 'Failed to submit feedback.');
      }
      setFeedbackSuccess(true);
      setFeedback('');
      setAgentEmail('');
      setRating(0);
    } catch (err: any) {
      setFeedbackError(err.message || 'Submission failed.');
    } finally {
      setFeedbackLoading(false);
    }
  };

  return (
    <div className="space-y-8">
      {/* Conversation Summary Section */}
      <div className="bg-white rounded-xl shadow border p-6" ref={summaryRef} id="summary-content">
        <div id="summary-content" className="mb-8">
          <h2 className="text-xl font-bold mb-6 text-blue-700">Conversation Summary</h2>
          <div className="space-y-6">
            {sections.map((section, idx) => {
              const heading = isStructuredSummary ? sectionTitles[idx] : section.split('\n')[0];
              const content = isStructuredSummary ? section : section.substring(heading.length).trim();
              const isOpen = openSections.has(idx);
              
              return (
                <div key={idx} className="border rounded-lg overflow-hidden">
                  <button
                    onClick={() => toggleSection(idx)}
                    className="w-full text-left px-4 py-3 bg-gray-50 hover:bg-gray-100 transition-colors duration-150 flex justify-between items-center"
                  >
                    <span className="font-semibold text-lg text-gray-900">
                      {heading}
                    </span>
                    <svg
                      className={`w-5 h-5 transform transition-transform duration-200 ${isOpen ? 'rotate-180' : ''}`}
                      fill="none"
                      viewBox="0 0 24 24"
                      stroke="currentColor"
                    >
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                    </svg>
                  </button>
                  
                  {isOpen && (
                    <div className="px-4 py-3 bg-white border-t">
                      <div className="prose prose-sm max-w-none text-gray-700">
                        {isStructuredSummary ? (
                          <p className="mb-3 last:mb-0 leading-relaxed">{content}</p>
                        ) : (
                          <ReactMarkdown
                            components={{
                              p: ({ children }) => <p className="mb-3 last:mb-0">{children}</p>,
                              ul: ({ children }) => <ul className="list-disc pl-4 mb-3 last:mb-0 space-y-1">{children}</ul>,
                              li: ({ children }) => <li>{children}</li>,
                            }}
                          >
                            {content}
                          </ReactMarkdown>
                        )}
                      </div>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>

        {error && (
          <div className="mb-4 p-3 bg-red-100 text-red-700 rounded">
            {error}
          </div>
        )}

        <div className="flex gap-4 pt-4 border-t">
          <button
            onClick={handleSaveAsPDF}
            disabled={isLoadingPDF}
            className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50 flex items-center gap-2 min-w-[120px] justify-center"
          >
            {isLoadingPDF ? (
              <>
                <svg className="animate-spin h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                <span>Saving...</span>
              </>
            ) : (
              <span>Save as PDF</span>
            )}
          </button>
          
          <button
            onClick={handleSaveRaw}
            disabled={isLoadingJSON}
            className="px-4 py-2 bg-gray-600 text-white rounded hover:bg-gray-700 disabled:opacity-50 flex items-center gap-2 min-w-[120px] justify-center"
          >
            {isLoadingJSON ? (
              <>
                <svg className="animate-spin h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                <span>Saving...</span>
              </>
            ) : (
              <span>Save Raw Data</span>
            )}
          </button>
        </div>
      </div>

      {/* Structured Requirements and Tasks Display */}
      {rawData?.requirements && rawData?.tasks_and_actionables && (
        <div ref={requirementsRef} id="requirements-content">
          <LLMStructuredDisplay
            requirements={rawData.requirements}
            tasks_and_actionables={rawData.tasks_and_actionables}
          />
        </div>
      )}

      {/* Feedback Section */}
      <div className="bg-white rounded-xl shadow border p-6">
        <h3 className="text-lg font-semibold mb-2 text-blue-700">Give Feedback</h3>
        <form onSubmit={handleFeedbackSubmit} className="space-y-4">
          <input
            type="email"
            className="w-full border rounded p-2"
            placeholder="Your email (optional)"
            value={agentEmail}
            onChange={e => setAgentEmail(e.target.value)}
            disabled={feedbackLoading}
          />
          <div className="flex items-center space-x-2">
            <span className="text-gray-700">Rating:</span>
            {[0, 1, 2, 3, 4, 5].map((star) => (
              <button
                key={star}
                type="button"
                className={
                  star <= rating
                    ? 'text-yellow-400 text-2xl focus:outline-none'
                    : 'text-gray-300 text-2xl focus:outline-none'
                }
                onClick={() => setRating(star)}
                disabled={feedbackLoading}
                aria-label={`Rate ${star} star${star !== 1 ? 's' : ''}`}
              >
                ★
              </button>
            ))}
            <span className="ml-2 text-sm text-gray-500">{rating} / 5</span>
          </div>
          <textarea
            className="w-full border rounded p-2 min-h-[80px]"
            placeholder="Add your feedback or comments (optional)"
            value={feedback}
            onChange={e => setFeedback(e.target.value)}
            disabled={feedbackLoading}
          />
          <button
            type="submit"
            className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50"
            disabled={feedbackLoading}
          >
            {feedbackLoading ? 'Submitting...' : 'Submit Feedback'}
          </button>
          {feedbackSuccess && <div className="text-green-700 mt-2">Feedback sent successfully!</div>}
          {feedbackError && <div className="text-red-700 mt-2">{feedbackError}</div>}
        </form>
      </div>
    </div>
  );
};

// --- New KeyValue Panels for Requirements and Tasks/Actionables ---

interface LLMKeyValuePanelsProps {
  requirements?: any;
  tasksAndActionables?: any;
}

export const LLMKeyValuePanels: React.FC<LLMKeyValuePanelsProps> = ({ requirements, tasksAndActionables }) => {
  // Helper to render key-value pairs
  const renderKeyValue = (obj: any) => (
    <table className="min-w-full text-sm mb-4">
      <tbody>
        {Object.entries(obj || {}).map(([key, value]) => (
          <tr key={key} className="border-b last:border-b-0">
            <td className="font-medium text-gray-700 py-1 pr-4 capitalize whitespace-nowrap">{key.replace(/_/g, ' ')}</td>
            <td className="py-1 text-gray-900">
              {Array.isArray(value) ? value.join(', ') : value === null || value === undefined ? <span className="text-gray-400">N/A</span> : value.toString()}
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  );

  // Helper to render tasks/actionables
  const renderTasks = (tasks: any[]) => (
    <ul className="space-y-2">
      {tasks.map((task, idx) => (
        <li key={idx} className="flex items-start space-x-3 p-3 bg-gray-50 rounded-lg border border-gray-200">
          <span className={`inline-block w-2 h-2 mt-2 rounded-full ${
            task.status === 'done' ? 'bg-green-500' : task.status === 'pending' ? 'bg-yellow-400' : 'bg-blue-400'
          }`} />
          <div className="flex-1">
            <div className="font-medium text-gray-900">{task.type || 'Task'}</div>
            <div className="text-xs text-gray-500 mb-1">{task.description}</div>
            <div className="flex items-center space-x-2 text-xs">
              {task.due && <span className="text-gray-600">Due: {task.due}</span>}
              {task.status && <span className={`px-2 py-0.5 rounded-full font-semibold ${
                task.status === 'done' ? 'bg-green-100 text-green-700' : task.status === 'pending' ? 'bg-yellow-100 text-yellow-700' : 'bg-blue-100 text-blue-700'
              }`}>{task.status}</span>}
              {task.task_for && <span className="text-gray-400">• {task.task_for}</span>}
            </div>
          </div>
        </li>
      ))}
    </ul>
  );

  return (
    <div className="space-y-8">
      {requirements && (
        <div className="bg-white rounded-xl shadow border p-6">
          <h3 className="text-lg font-bold mb-4 text-blue-700">Requirements</h3>
          {renderKeyValue(requirements.user_persona)}
          {renderKeyValue(requirements.accommodation_requirements)}
          {requirements.properties_under_consideration && (
            <div className="mt-2">
              <div className="font-semibold text-gray-700 mb-1">Properties Under Consideration:</div>
              {renderKeyValue(requirements.properties_under_consideration)}
            </div>
          )}
        </div>
      )}
      {tasksAndActionables && (
        <div className="bg-white rounded-xl shadow border p-6">
          <h3 className="text-lg font-bold mb-4 text-purple-700">Tasks & Actionables</h3>
          {tasksAndActionables.tasks && renderTasks(tasksAndActionables.tasks)}
          {tasksAndActionables.suggested_next_step && (
            <div className="mt-4 text-sm text-blue-700 font-medium">Next Step: {tasksAndActionables.suggested_next_step}</div>
          )}
        </div>
      )}
    </div>
  );
};

export default LLMSummaryDisplay; 