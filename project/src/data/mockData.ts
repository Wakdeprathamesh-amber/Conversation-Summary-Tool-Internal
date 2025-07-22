import { LeadData, MessageData } from '../types';

export const mockLeadData: LeadData[] = [
  { 
    id: '1', 
    name: 'John Smith', 
    email: 'john@email.com', 
    phone: '+1234567890', 
    source: 'Website', 
    created_at: '2024-01-15T10:30:00Z' 
  },
  { 
    id: '2', 
    name: 'Sarah Wilson', 
    email: 'sarah@email.com', 
    phone: '+1987654321', 
    source: 'Social Media', 
    created_at: '2024-01-16T14:20:00Z' 
  }
];

export const mockMessages: MessageData[] = [
  { 
    id: '1', 
    type: 'email', 
    content: 'Interested in computer science programs', 
    timestamp: '2024-01-15T11:00:00Z', 
    sender: 'student' 
  },
  { 
    id: '2', 
    type: 'whatsapp', 
    content: 'What are the admission requirements?', 
    timestamp: '2024-01-15T15:30:00Z', 
    sender: 'student' 
  },
  { 
    id: '3', 
    type: 'call', 
    content: '15-minute discussion about course options', 
    timestamp: '2024-01-16T09:15:00Z', 
    sender: 'agent', 
    status: 'completed' 
  },
  { 
    id: '4', 
    type: 'email', 
    content: 'Application deadline confirmation', 
    timestamp: '2024-01-16T16:45:00Z', 
    sender: 'agent' 
  }
];