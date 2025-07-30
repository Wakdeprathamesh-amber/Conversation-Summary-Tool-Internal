import React, { useState } from 'react';
import html2pdf from 'html2pdf.js';

interface Task {
  type: string;
  description: string;
  due: string;
  status: string;
  task_for: string;
  source_reference: string;
}

interface LLMStructuredDisplayProps {
  requirements: {
    user_persona?: {
      booking_for?: string | null;
      name?: string | null;
      mobile?: string[];
      email?: string[];
      whatsapp?: string[];
      student_status?: string | null;
      nationality?: string | null;
    };
    accommodation_requirements?: {
      location?: string[];
      lease_duration_weeks?: number | null;
      room_type?: string | null;
      budget?: {
        max?: number | null;
        currency?: string | null;
      };
      bathroom_type?: string | null;
      kitchen_type?: string | null;
      dual_occupancy?: boolean | null;
      university?: string | null;
      move_in_date?: string | null;
      dependents?: string | null;
      amenities?: string[];
      housing_type?: string | null;
      nearby_preferences?: string[];
      pet_friendly?: boolean | null;
      payment_plan?: string | null;
      course_year?: string | null;
    };
    student_journey?: {
      I20_form?: string[];
      university_acceptance?: string[];
      flight_booking?: string[];
      visa_status?: string[];
      guarantor?: string | null;
    };
    properties_under_consideration?: {
      properties_considered?: string[];
      rooms_considered?: string[];
    };
    other_info?: {
      referral_code_or_offer_discussed?: string | null;
    };
  };
  tasks_and_actionables: {
    tasks: Task[];
    last_agent_response?: string;
    suggested_next_step?: string;
  };
}

const StatusBadge: React.FC<{ status: string }> = ({ status }) => {
  const getStatusColor = () => {
    switch (status.toLowerCase()) {
      case 'completed':
        return 'bg-green-100 text-green-800';
      case 'in_progress':
        return 'bg-blue-100 text-blue-800';
      case 'pending':
        return 'bg-yellow-100 text-yellow-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  return (
    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getStatusColor()}`}>
      {status.replace('_', ' ')}
    </span>
  );
};

const Section: React.FC<{ title: string; children: React.ReactNode }> = ({ title, children }) => (
  <div className="mb-6 last:mb-0">
    <h3 className="text-lg font-semibold text-gray-900 mb-3">{title}</h3>
    {children}
  </div>
);

const KeyValueTable: React.FC<{ data: Record<string, any> }> = ({ data }) => (
  <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
    <div className="divide-y divide-gray-200">
      {Object.entries(data).map(([key, value]) => (
        <div key={key} className="px-4 py-3 sm:grid sm:grid-cols-3 sm:gap-4">
          <dt className="text-sm font-medium text-gray-500 capitalize">
            {key.replace(/_/g, ' ')}
          </dt>
          <dd className="mt-1 text-sm text-gray-900 sm:mt-0 sm:col-span-2">
            {value === null || value === undefined || value === '' 
              ? 'None'
              : typeof value === 'object' && !Array.isArray(value)
                ? (() => {
                    // Special handling for budget object
                    if (key === 'budget' && value.max && value.currency) {
                      return `${value.max} ${value.currency}`;
                    }
                    // Handle other nested objects
                    return Object.entries(value)
                      .filter(([_, v]) => v !== null && v !== undefined && v !== '')
                      .map(([k, v]) => `${k.replace(/_/g, ' ')}: ${v}`)
                      .join(', ') || 'None';
                  })()
                : Array.isArray(value)
                  ? value.filter(Boolean).join(', ') || 'None'
                  : typeof value === 'boolean'
                    ? value ? 'Yes' : 'No'
                    : value.toString()}
          </dd>
        </div>
      ))}
    </div>
  </div>
);

const TaskList: React.FC<{ tasks: Task[] }> = ({ tasks }) => (
  <div className="space-y-4">
    {tasks.map((task, index) => (
      <div key={index} className="bg-white rounded-lg border border-gray-200 p-4">
        <div className="flex items-start justify-between">
          <div className="space-y-1">
            <div className="flex items-center space-x-2">
              <StatusBadge status={task.status} />
              <span className="text-sm font-medium text-gray-900 capitalize">{task.type.replace(/_/g, ' ')}</span>
            </div>
            <p className="text-sm text-gray-600">{task.description}</p>
          </div>
        </div>
        <div className="mt-3 grid grid-cols-2 gap-4 text-xs text-gray-500">
          {task.due && (
            <div>
              <span className="font-medium">Due:</span> {task.due}
            </div>
          )}
          <div>
            <span className="font-medium">For:</span> {task.task_for}
          </div>
          {task.source_reference && (
            <div className="col-span-2">
              <span className="font-medium">Source:</span> {task.source_reference}
            </div>
          )}
        </div>
      </div>
    ))}
  </div>
);

const SaveButtons: React.FC<{ 
  onSavePDF: () => Promise<void>;
  onSaveJSON: () => Promise<void>;
  isLoadingPDF: boolean;
  isLoadingJSON: boolean;
}> = ({ onSavePDF, onSaveJSON, isLoadingPDF, isLoadingJSON }) => (
  <div className="flex gap-4 mt-6 border-t pt-6">
    <button
      onClick={onSavePDF}
      disabled={isLoadingPDF}
      className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50 flex items-center gap-2"
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
      onClick={onSaveJSON}
      disabled={isLoadingJSON}
      className="px-4 py-2 bg-gray-600 text-white rounded hover:bg-gray-700 disabled:opacity-50 flex items-center gap-2"
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
);

const LLMStructuredDisplay: React.FC<LLMStructuredDisplayProps> = ({ requirements, tasks_and_actionables }) => {
  const [isLoadingReqPDF, setIsLoadingReqPDF] = useState(false);
  const [isLoadingReqJSON, setIsLoadingReqJSON] = useState(false);
  const [isLoadingTasksPDF, setIsLoadingTasksPDF] = useState(false);
  const [isLoadingTasksJSON, setIsLoadingTasksJSON] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSaveRequirementsPDF = async () => {
    setIsLoadingReqPDF(true);
    setError(null);
    
    try {
      const element = document.getElementById('requirements-content');
      if (!element) throw new Error('Requirements content not found');

      const opt = {
        margin: 1,
        filename: `requirements-${new Date().toISOString().split('T')[0]}.pdf`,
        image: { type: 'jpeg', quality: 0.98 },
        html2canvas: { scale: 2 },
        jsPDF: { unit: 'in', format: 'letter', orientation: 'portrait' }
      };
      
      await html2pdf().set(opt).from(element).save();
    } catch (err) {
      setError('Failed to generate PDF. Please try again.');
      console.error('PDF generation error:', err);
    } finally {
      setIsLoadingReqPDF(false);
    }
  };

  const handleSaveRequirementsJSON = async () => {
    setIsLoadingReqJSON(true);
    setError(null);
    
    try {
      const dataStr = JSON.stringify(requirements, null, 2);
      const blob = new Blob([dataStr], { type: 'application/json' });
      const url = window.URL.createObjectURL(blob);
      
      const linkElement = document.createElement('a');
      linkElement.href = url;
      linkElement.download = `requirements-${new Date().toISOString().split('T')[0]}.json`;
      document.body.appendChild(linkElement);
      linkElement.click();
      document.body.removeChild(linkElement);
      window.URL.revokeObjectURL(url);
    } catch (err) {
      setError('Failed to save requirements data. Please try again.');
      console.error('JSON save error:', err);
    } finally {
      setIsLoadingReqJSON(false);
    }
  };

  const handleSaveTasksPDF = async () => {
    setIsLoadingTasksPDF(true);
    setError(null);
    
    try {
      const element = document.getElementById('tasks-content');
      if (!element) throw new Error('Tasks content not found');

      const opt = {
        margin: 1,
        filename: `tasks-and-actionables-${new Date().toISOString().split('T')[0]}.pdf`,
        image: { type: 'jpeg', quality: 0.98 },
        html2canvas: { scale: 2 },
        jsPDF: { unit: 'in', format: 'letter', orientation: 'portrait' }
      };
      
      await html2pdf().set(opt).from(element).save();
    } catch (err) {
      setError('Failed to generate PDF. Please try again.');
      console.error('PDF generation error:', err);
    } finally {
      setIsLoadingTasksPDF(false);
    }
  };

  const handleSaveTasksJSON = async () => {
    setIsLoadingTasksJSON(true);
    setError(null);
    
    try {
      const dataStr = JSON.stringify(tasks_and_actionables, null, 2);
      const blob = new Blob([dataStr], { type: 'application/json' });
      const url = window.URL.createObjectURL(blob);
      
      const linkElement = document.createElement('a');
      linkElement.href = url;
      linkElement.download = `tasks-and-actionables-${new Date().toISOString().split('T')[0]}.json`;
      document.body.appendChild(linkElement);
      linkElement.click();
      document.body.removeChild(linkElement);
      window.URL.revokeObjectURL(url);
    } catch (err) {
      setError('Failed to save tasks data. Please try again.');
      console.error('JSON save error:', err);
    } finally {
      setIsLoadingTasksJSON(false);
    }
  };

  return (
    <div className="space-y-8">
      {error && (
        <div className="p-3 bg-red-100 text-red-700 rounded">
          {error}
        </div>
      )}

      <div className="bg-white rounded-xl shadow border p-6">
        <h2 className="text-xl font-bold mb-6 text-blue-700">Requirements</h2>
        <div id="requirements-content">
          {requirements.user_persona && (
            <Section title="User Persona">
              <KeyValueTable data={requirements.user_persona} />
            </Section>
          )}
          
          {requirements.accommodation_requirements && (
            <Section title="Accommodation Requirements">
              <KeyValueTable data={requirements.accommodation_requirements} />
            </Section>
          )}
          
          {requirements.student_journey && (
            <Section title="Student Journey">
              <KeyValueTable data={requirements.student_journey} />
            </Section>
          )}
          
          {requirements.properties_under_consideration && (
            <Section title="Properties Under Consideration">
              <KeyValueTable data={requirements.properties_under_consideration} />
            </Section>
          )}
          
          {requirements.other_info && (
            <Section title="Other Information">
              <KeyValueTable data={requirements.other_info} />
            </Section>
          )}
        </div>

        <SaveButtons
          onSavePDF={handleSaveRequirementsPDF}
          onSaveJSON={handleSaveRequirementsJSON}
          isLoadingPDF={isLoadingReqPDF}
          isLoadingJSON={isLoadingReqJSON}
        />
      </div>

      <div className="bg-white rounded-xl shadow border p-6">
        <h2 className="text-xl font-bold mb-6 text-blue-700">Tasks & Actionables</h2>
        <div id="tasks-content">
          <Section title="Tasks">
            <TaskList tasks={tasks_and_actionables.tasks} />
          </Section>

          {tasks_and_actionables.last_agent_response && (
            <Section title="Last Agent Response">
              <p className="text-sm text-gray-600 bg-gray-50 rounded-lg p-4">
                {tasks_and_actionables.last_agent_response}
              </p>
            </Section>
          )}

          {tasks_and_actionables.suggested_next_step && (
            <Section title="Suggested Next Step">
              <p className="text-sm text-gray-600 bg-gray-50 rounded-lg p-4">
                {tasks_and_actionables.suggested_next_step}
              </p>
            </Section>
          )}
        </div>

        <SaveButtons
          onSavePDF={handleSaveTasksPDF}
          onSaveJSON={handleSaveTasksJSON}
          isLoadingPDF={isLoadingTasksPDF}
          isLoadingJSON={isLoadingTasksJSON}
        />
      </div>
    </div>
  );
};

export default LLMStructuredDisplay; 