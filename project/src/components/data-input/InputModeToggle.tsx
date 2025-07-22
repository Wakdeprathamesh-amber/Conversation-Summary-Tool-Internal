import React from 'react';
import { Search, Upload } from 'lucide-react';
import { InputMode } from '../../types';

interface InputModeToggleProps {
  inputMode: InputMode;
  setInputMode: (mode: InputMode) => void;
}

const InputModeToggle: React.FC<InputModeToggleProps> = ({ inputMode, setInputMode }) => {
  return (
    <div className="flex space-x-1 bg-gray-100 p-1 rounded-lg mb-6 w-fit">
      <button
        onClick={() => setInputMode('lookup')}
        className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
          inputMode === 'lookup' ? 'bg-white text-blue-600 shadow-sm' : 'text-gray-600 hover:text-gray-900'
        }`}
      >
        <Search className="w-4 h-4 inline mr-2" />
        Phone/Email Lookup
      </button>
      <button
        onClick={() => setInputMode('upload')}
        className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
          inputMode === 'upload' ? 'bg-white text-blue-600 shadow-sm' : 'text-gray-600 hover:text-gray-900'
        }`}
      >
        <Upload className="w-4 h-4 inline mr-2" />
        CSV Upload
      </button>
    </div>
  );
};

export default InputModeToggle;