import React, { useState } from 'react';
import { Clock, ChevronDown, ChevronUp } from 'lucide-react';
import { formatDate } from '../../utils/formatters';

interface WhatsAppMessage {
  type: string;
  timestamp: string;
  from_number: string;
  to_number: string;
  message_content: string;
  sender_type: 'agent' | 'student';
}

interface WhatsAppMessagesProps {
  messages: WhatsAppMessage[];
}

const WhatsAppMessages: React.FC<WhatsAppMessagesProps> = ({ messages }) => {
  const [showAllMessages, setShowAllMessages] = useState(false);
  const [selectedDay, setSelectedDay] = useState<string | null>(null);

  // Group messages by day
  const groupMessagesByDay = (messages: WhatsAppMessage[]) => {
    const groups: { [key: string]: WhatsAppMessage[] } = {};
    
    messages.forEach(message => {
      const date = new Date(message.timestamp);
      const dayKey = date.toDateString();
      
      if (!groups[dayKey]) {
        groups[dayKey] = [];
      }
      groups[dayKey].push(message);
    });
    
    return groups;
  };

  const messageGroups = groupMessagesByDay(messages);
  const dayKeys = Object.keys(messageGroups).sort((a, b) => new Date(a).getTime() - new Date(b).getTime());
  
  const displayedMessages = showAllMessages ? messages : messages.slice(0, 6);

  const toggleDay = (dayKey: string) => {
    setSelectedDay(selectedDay === dayKey ? null : dayKey);
  };

  const renderMessage = (message: WhatsAppMessage, index: number) => {
    const isAgent = message.sender_type === 'agent';
    
    return (
      <div
        key={index}
        className={`flex ${isAgent ? 'justify-end' : 'justify-start'} mb-3`}
      >
        <div
          className={`max-w-xs lg:max-w-md px-4 py-2 rounded-lg ${
            isAgent
              ? 'bg-blue-500 text-white rounded-br-none'
              : 'bg-gray-200 text-gray-900 rounded-bl-none'
          }`}
        >
          <p className="text-sm">{message.message_content}</p>
          <div className={`text-xs mt-1 ${isAgent ? 'text-blue-100' : 'text-gray-500'}`}>
            <div className="flex items-center space-x-1">
              <Clock className="w-3 h-3" />
              <span>{formatDate(message.timestamp)}</span>
            </div>
          </div>
        </div>
      </div>
    );
  };

  return (
    <div className="space-y-4">
      {/* Day-wise grouping toggle */}
      <div className="flex items-center justify-between">
        <h4 className="text-sm font-semibold text-gray-700">
          💬 WhatsApp Messages ({messages.length} total)
        </h4>
        <div className="flex space-x-2">
          <button
            onClick={() => setShowAllMessages(!showAllMessages)}
            className="text-xs bg-green-100 text-green-700 px-2 py-1 rounded-md hover:bg-green-200 transition-colors"
          >
            {showAllMessages ? 'Show Less' : 'Show All'}
          </button>
        </div>
      </div>

      {/* Group by days view */}
      {showAllMessages && dayKeys.length > 1 && (
        <div className="space-y-2">
          <h5 className="text-xs font-medium text-gray-600">📅 Group by Days:</h5>
          <div className="flex flex-wrap gap-2">
            {dayKeys.map(dayKey => (
              <button
                key={dayKey}
                onClick={() => toggleDay(dayKey)}
                className={`text-xs px-2 py-1 rounded-md transition-colors ${
                  selectedDay === dayKey
                    ? 'bg-green-600 text-white'
                    : 'bg-green-100 text-green-700 hover:bg-green-200'
                }`}
              >
                {new Date(dayKey).toLocaleDateString('en-GB', { 
                  month: 'short', 
                  day: 'numeric' 
                })} ({messageGroups[dayKey].length})
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Messages display */}
      <div className="bg-gray-50 rounded-lg p-4 max-h-96 overflow-y-auto">
        {selectedDay ? (
          // Show messages for selected day
          <div>
            <div className="text-center mb-4">
              <span className="text-xs bg-gray-200 text-gray-600 px-2 py-1 rounded-full">
                {new Date(selectedDay).toLocaleDateString('en-GB', { 
                  weekday: 'long',
                  year: 'numeric',
                  month: 'long',
                  day: 'numeric'
                })}
              </span>
            </div>
            {messageGroups[selectedDay].map((message, index) => renderMessage(message, index))}
          </div>
        ) : (
          // Show all messages or limited view
          <div>
            {!showAllMessages && messages.length > 6 && (
              <div className="text-center mb-4">
                <span className="text-xs bg-yellow-100 text-yellow-700 px-2 py-1 rounded-full">
                  Showing first 6 of {messages.length} messages
                </span>
              </div>
            )}
            
            {displayedMessages.map((message, index) => renderMessage(message, index))}
            
            {!showAllMessages && messages.length > 6 && (
              <div className="text-center mt-4">
                <button
                  onClick={() => setShowAllMessages(true)}
                  className="flex items-center space-x-1 mx-auto text-xs bg-green-100 text-green-700 px-3 py-2 rounded-md hover:bg-green-200 transition-colors"
                >
                  <ChevronDown className="w-3 h-3" />
                  <span>Show {messages.length - 6} more messages</span>
                </button>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Message statistics */}
      <div className="grid grid-cols-3 gap-2 text-xs">
        <div className="bg-blue-50 p-2 rounded text-center">
          <div className="font-medium text-blue-900">
            {messages.filter(m => m.sender_type === 'agent').length}
          </div>
          <div className="text-blue-600">Agent</div>
        </div>
        <div className="bg-green-50 p-2 rounded text-center">
          <div className="font-medium text-green-900">
            {messages.filter(m => m.sender_type === 'student').length}
          </div>
          <div className="text-green-600">Student</div>
        </div>
        <div className="bg-gray-50 p-2 rounded text-center">
          <div className="font-medium text-gray-900">{dayKeys.length}</div>
          <div className="text-gray-600">Days</div>
        </div>
      </div>
    </div>
  );
};

export default WhatsAppMessages;