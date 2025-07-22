import React, { useRef, useEffect } from 'react';

interface PhoneEmailLookupProps {
  phoneEmail: string;
  setPhoneEmail: (value: string) => void;
  isLoading: boolean;
  onLookup: () => void;
  error?: string | null;
  validateInput?: (input: string) => boolean;
}

const PhoneEmailLookup: React.FC<PhoneEmailLookupProps> = ({
  phoneEmail,
  setPhoneEmail,
  isLoading,
  onLookup,
  error,
  validateInput
}) => {
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    inputRef.current?.focus();
  }, []);

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' && !isLoading && validateInput && validateInput(phoneEmail)) {
      onLookup();
    }
  };

  const isValid = validateInput ? validateInput(phoneEmail) : !!phoneEmail.trim();

  return (
    <div className="space-y-4">
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Enter Phone Number or Email Address
        </label>
        <div className="flex space-x-3">
          <input
            ref={inputRef}
            type="text"
            value={phoneEmail}
            onChange={(e) => setPhoneEmail(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="john@email.com or +1234567890"
            className="flex-1 px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all"
            disabled={isLoading}
          />
          <button
            onClick={onLookup}
            disabled={!isValid || isLoading}
            className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors font-medium"
          >
            {isLoading ? 'Searching...' : 'Fetch Data'}
          </button>
        </div>
        {error && (
          <div className="mt-2 text-sm text-red-600">{error}</div>
        )}
      </div>
    </div>
  );
};

export default PhoneEmailLookup;