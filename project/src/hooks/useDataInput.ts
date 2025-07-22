import { useState } from 'react';

const API_URL = import.meta.env.VITE_BACKEND_API_URL || 'http://localhost:8000';

export const useDataInput = () => {
  const [phoneEmail, setPhoneEmail] = useState('');
  const [timeline, setTimeline] = useState<any[] | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [summary, setSummary] = useState<any | null>(null);
  const [isSummaryLoading, setIsSummaryLoading] = useState(false);

  const validateInput = (input: string) => {
    if (!input.trim()) return false;
    if (input.includes('@')) {
      // Basic email regex
      return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(input);
    } else {
      // Basic phone validation (10-15 digits)
      return /^\+?\d{10,15}$/.test(input);
    }
  };

  const handleLookup = async () => {
    setError(null);
    if (!validateInput(phoneEmail)) {
      setError('Please enter a valid phone number or email address.');
      return;
    }
    setIsLoading(true);
    try {
      const isEmail = phoneEmail.includes('@');
      const param = isEmail ? `email=${encodeURIComponent(phoneEmail)}` : `mobile=${encodeURIComponent(phoneEmail)}`;
      const response = await fetch(`${API_URL}/generate-timeline?${param}`);
      if (!response.ok) {
        throw new Error('Failed to fetch timeline');
      }
      const timelineData = await response.json();
      setTimeline(timelineData);
      setError(null);
    } catch (error: any) {
      setError('Error fetching timeline: ' + (error.message || error));
      setTimeline(null);
    }
    setIsLoading(false);
  };

  const handleGenerateSummary = async () => {
    setError(null);
    setIsSummaryLoading(true);
    setSummary(null);
    if (!validateInput(phoneEmail)) {
      setError('Please enter a valid phone number or email address.');
      setIsSummaryLoading(false);
      return;
    }
    try {
      const isEmail = phoneEmail.includes('@');
      const param = isEmail ? `email=${encodeURIComponent(phoneEmail)}` : `mobile=${encodeURIComponent(phoneEmail)}`;
      const response = await fetch(`${API_URL}/generate-summary?${param}`);
      if (!response.ok) {
        throw new Error('Failed to generate summary');
      }
      const data = await response.json();
      setSummary(data);
      setError(null);
    } catch (error: any) {
      setError('Error generating summary: ' + (error.message || error));
      setSummary(null);
    }
    setIsSummaryLoading(false);
  };

  return {
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
  };
};