import React, { useState } from 'react';
import { Clock, MessageSquare, Phone, Mail, User, ChevronDown, ChevronUp, Play, ExternalLink, Calendar } from 'lucide-react';
import { formatDate, formatFullDate } from '../../utils/formatters';
import WhatsAppMessages from './WhatsAppMessages';

interface TimelineItemProps {
  item: any;
  isLast: boolean;
  isExpanded: boolean;
  onToggleExpand: () => void;
}

const TRANSCRIPTION_API_URL = import.meta.env.VITE_TRANSCRIPTION_API_URL || 'http://localhost:8001';

const TimelineItem: React.FC<TimelineItemProps> = ({
  item,
  isLast,
  isExpanded,
  onToggleExpand
}) => {
  const getItemIcon = () => {
    switch (item.type) {
      case 'whatsapp_pack':
        return <MessageSquare className="w-5 h-5 text-green-600" />;
      case 'call':
        return <Phone className="w-5 h-5 text-purple-600" />;
      case 'email':
        return <Mail className="w-5 h-5 text-blue-600" />;
      case 'lead_info':
        return <User className="w-5 h-5 text-gray-600" />;
      default:
        return <Clock className="w-5 h-5 text-gray-600" />;
    }
  };

  const getItemColor = () => {
    switch (item.type) {
      case 'whatsapp_pack':
        return 'border-green-200 bg-green-50';
      case 'call':
        return 'border-purple-200 bg-purple-50';
      case 'email':
        return 'border-blue-200 bg-blue-50';
      case 'lead_info':
        return 'border-gray-200 bg-gray-50';
      default:
        return 'border-gray-200 bg-gray-50';
    }
  };

  const formatDuration = (seconds: string) => {
    const mins = Math.floor(parseInt(seconds) / 60);
    const secs = parseInt(seconds) % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const getTimeDisplay = () => {
    if (item.type === 'whatsapp_pack') {
      return `${formatDate(item.start_timestamp)} - ${formatDate(item.end_timestamp)}`;
    }
    return formatDate(item.timestamp);
  };

  const renderCollapsedContent = () => {
    switch (item.type) {
      case 'whatsapp_pack':
        return (
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className="flex items-center space-x-2">
                <span className="text-sm font-medium text-gray-900">💬 WhatsApp Session</span>
                <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                  📨 {item.message_count || item.messages?.length || 0} messages
                </span>
              </div>
            </div>
            <div className="flex items-center space-x-2 text-sm text-gray-500">
              <Clock className="w-4 h-4" />
              <span>{getTimeDisplay()}</span>
            </div>
          </div>
        );

      case 'call':
        return (
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <span className="text-sm font-medium text-gray-900">📞 Phone Call</span>
              <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-purple-100 text-purple-800">
                ⏱️ {formatDuration(item.duration)}
              </span>
            </div>
            <div className="flex items-center space-x-2 text-sm text-gray-500">
              <Clock className="w-4 h-4" />
              <span>{formatDate(item.timestamp)}</span>
            </div>
          </div>
        );

      case 'email':
        return (
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <span className="text-sm font-medium text-gray-900">✉️ Email</span>
              <span className="text-sm text-gray-600 truncate max-w-md">{item.subject}</span>
              <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${
                item.direction === 'inbound' ? 'bg-yellow-100 text-yellow-800' : 'bg-blue-100 text-blue-800'
              }`}>
                {item.direction === 'inbound' ? '📥 Inbound' : '📤 Outbound'}
              </span>
            </div>
            <div className="flex items-center space-x-2 text-sm text-gray-500">
              <Clock className="w-4 h-4" />
              <span>{formatDate(item.timestamp)}</span>
            </div>
          </div>
        );

      case 'lead_info':
        return (
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <span className="text-sm font-medium text-gray-900">👤 Lead Information</span>
              <span className="text-sm text-gray-600">{item.user_name}</span>
            </div>
            <div className="flex items-center space-x-2 text-sm text-gray-500">
              <Calendar className="w-4 h-4" />
              <span>{formatDate(item.timestamp)}</span>
            </div>
          </div>
        );

      default:
        return (
          <div className="flex items-center justify-between">
            <span className="text-sm font-medium text-gray-900">{item.type}</span>
            <span className="text-sm text-gray-500">{formatDate(item.timestamp)}</span>
          </div>
        );
    }
  };

  // --- Transcription state ---
  const [transcribing, setTranscribing] = useState(false);
  const [transcript, setTranscript] = useState<string | null>(null);
  const [transcribeError, setTranscribeError] = useState<string | null>(null);

  const effectiveTranscript = item.transcript || transcript;

  const handleTranscribe = async () => {
    setTranscribing(true);
    setTranscribeError(null);
    setTranscript(null);
    try {
      const response = await fetch(`${TRANSCRIPTION_API_URL}/transcribe-call`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ record_url: item.record_url, mobile_number: item.to_number, call_id: item.id }),
      });
      if (!response.ok) throw new Error(await response.text());
      const text = await response.text();
      setTranscript(text);
    } catch (err: any) {
      setTranscribeError(err.message || 'Failed to transcribe');
    } finally {
      setTranscribing(false);
    }
  };

  const renderExpandedContent = () => {
    switch (item.type) {
      case 'whatsapp_pack':
        return (
          <div className="mt-4 pt-4 border-t border-gray-200">
            <WhatsAppMessages messages={item.messages || []} />
          </div>
        );

      case 'call':
        return (
          <div className="mt-4 pt-4 border-t border-gray-200 space-y-3">
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div>
                <span className="text-gray-500">From:</span>
                <span className="ml-2 font-medium">{item.from_number}</span>
              </div>
              <div>
                <span className="text-gray-500">To:</span>
                <span className="ml-2 font-medium">{item.to_number}</span>
              </div>
              <div>
                <span className="text-gray-500">Duration:</span>
                <span className="ml-2 font-medium">{formatDuration(item.duration)}</span>
              </div>
              <div>
                <span className="text-gray-500">Source:</span>
                <span className="ml-2 font-medium capitalize">{item.source}</span>
              </div>
            </div>
            {item.record_url && (
              <div className="flex items-center space-x-2">
                <button className="flex items-center space-x-2 px-3 py-2 bg-purple-100 text-purple-700 rounded-lg hover:bg-purple-200 transition-colors">
                  <Play className="w-4 h-4" />
                  <span className="text-sm font-medium">Play Recording</span>
                </button>
                <a
                  href={item.record_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex items-center space-x-2 px-3 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors"
                >
                  <ExternalLink className="w-4 h-4" />
                  <span className="text-sm font-medium">Open Link</span>
                </a>
                {/* --- Transcribe Button --- */}
                <button
                  className="flex items-center space-x-2 px-3 py-2 bg-blue-100 text-blue-700 rounded-lg hover:bg-blue-200 transition-colors"
                  onClick={handleTranscribe}
                  disabled={transcribing}
                >
                  <span className="text-sm font-medium">{transcribing ? 'Transcribing...' : 'Transcribe'}</span>
                </button>
              </div>
            )}
            {/* --- Transcript Output --- */}
            {transcribeError && (
              <div className="text-red-600 text-xs mt-2">{transcribeError}</div>
            )}
            {effectiveTranscript && (
              <div className="bg-gray-50 rounded-lg p-4 mt-2 max-h-60 overflow-y-auto border border-gray-200">
                <h4 className="text-sm font-semibold mb-2">Transcript</h4>
                <pre className="text-xs whitespace-pre-wrap text-gray-800">{effectiveTranscript}</pre>
              </div>
            )}
            <div className="text-xs text-gray-500">
              <p><strong>Call ID:</strong> {item.id}</p>
              <p><strong>Full Timestamp:</strong> {formatFullDate(item.timestamp)}</p>
            </div>
          </div>
        );

      case 'email':
        return (
          <div className="mt-4 pt-4 border-t border-gray-200 space-y-3">
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div>
                <span className="text-gray-500">From:</span>
                <span className="ml-2 font-medium">{item.sender_email}</span>
              </div>
              <div>
                <span className="text-gray-500">To:</span>
                <span className="ml-2 font-medium">{item.recipient_email}</span>
              </div>
              <div>
                <span className="text-gray-500">Subject:</span>
                <span className="ml-2 font-medium">{item.subject}</span>
              </div>
              <div>
                <span className="text-gray-500">Type:</span>
                <span className="ml-2 font-medium capitalize">{item.sender_type}</span>
              </div>
            </div>
            <div className="bg-gray-50 p-3 rounded-lg">
              <p className="text-sm text-gray-900">{item.message}</p>
            </div>
            <div className="text-xs text-gray-500">
              <p><strong>Full Timestamp:</strong> {formatFullDate(item.timestamp)}</p>
              <p><strong>Direction:</strong> {item.direction}</p>
            </div>
          </div>
        );

      case 'lead_info':
        return (
          <div className="mt-4 pt-4 border-t border-gray-200">
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div>
                <span className="text-gray-500">Name:</span>
                <span className="ml-2 font-medium">{item.user_name}</span>
              </div>
              <div>
                <span className="text-gray-500">Email:</span>
                <span className="ml-2 font-medium">{item.email}</span>
              </div>
              <div>
                <span className="text-gray-500">Phone:</span>
                <span className="ml-2 font-medium">{item.phone}</span>
              </div>
              <div>
                <span className="text-gray-500">University:</span>
                <span className="ml-2 font-medium">{item.university}</span>
              </div>
              <div>
                <span className="text-gray-500">Move-in Date:</span>
                <span className="ml-2 font-medium">{item.move_in_date}</span>
              </div>
              <div>
                <span className="text-gray-500">Budget:</span>
                <span className="ml-2 font-medium">{item.budget}</span>
              </div>
            </div>
            <div className="text-xs text-gray-500 mt-3">
              <p><strong>Lead ID:</strong> {item.lead_id}</p>
            </div>
          </div>
        );

      default:
        return null;
    }
  };

  return (
    <div className="relative">
      {!isLast && (
        <div className="absolute left-6 top-16 w-0.5 h-8 bg-gray-200"></div>
      )}
      <div className="flex items-start space-x-4">
        <div className={`p-3 rounded-full border-2 ${getItemColor()}`}>
          {getItemIcon()}
        </div>
        <div className="flex-1 min-w-0">
          <div 
            className={`rounded-lg p-4 border transition-all duration-200 cursor-pointer hover:shadow-md ${getItemColor()} ${
              isExpanded ? 'shadow-md' : ''
            }`}
            onClick={onToggleExpand}
          >
            <div className="flex items-center justify-between">
              <div className="flex-1 min-w-0">
                {renderCollapsedContent()}
              </div>
              <button className="ml-4 p-1 text-gray-400 hover:text-gray-600 transition-colors">
                {isExpanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
              </button>
            </div>
            {isExpanded && renderExpandedContent()}
          </div>
        </div>
      </div>
    </div>
  );
};

export default TimelineItem;