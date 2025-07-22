import React from 'react';
import PhoneEmailLookup from './PhoneEmailLookup';

interface DataInputSectionProps {
  phoneEmail: string;
  setPhoneEmail: (value: string) => void;
  isLoading: boolean;
  onLookup: () => void;
  error?: string | null;
  validateInput?: (input: string) => boolean;
}

const DataInputSection: React.FC<DataInputSectionProps> = ({
  phoneEmail,
  setPhoneEmail,
  isLoading,
  onLookup,
  error,
  validateInput
}) => {
  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-200">
      <div className="p-6 border-b border-gray-200">
        <h2 className="text-xl font-semibold text-gray-900 mb-4">Data Input</h2>
        <PhoneEmailLookup
          phoneEmail={phoneEmail}
          setPhoneEmail={setPhoneEmail}
          isLoading={isLoading}
          onLookup={onLookup}
          error={error}
          validateInput={validateInput}
        />
      </div>
    </div>
  );
};

export default DataInputSection;