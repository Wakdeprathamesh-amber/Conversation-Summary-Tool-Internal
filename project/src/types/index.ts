export interface LeadData {
  id: string;
  name: string;
  email: string;
  phone: string;
  source: string;
  created_at: string;
}

export interface MessageData {
  id: string;
  type: 'whatsapp' | 'email' | 'call' | 'other';
  content: string;
  timestamp: string;
  sender: string;
  status?: string;
}

export interface LeadStatus {
  funnel_stage?: string;
  intent?: string;
  urgency?: string;
  tags?: string[];
}

export interface ConversationSummarySection {
  [section: string]: string;
}

export interface ConversationSummary {
  format: string;
  sections: ConversationSummarySection;
}

export interface LLMConversationSummary {
  conversation_summary: ConversationSummary;
}

export interface Summary {
  lead_status?: LeadStatus;
  conversation_summary?: LLMConversationSummary;
  // Add other fields as needed from your LLM response
  [key: string]: any;
}

export interface ConsolidatedData {
  student_profile: {
    name: string;
    email: string;
    phone: string;
    source: string;
  };
  messages: MessageData[];
  summary?: Summary;
}

export interface UploadedFile {
  name: string;
  size: number;
  uploadedAt: Date;
}

export interface UploadSections {
  leads: UploadedFile | null;
  whatsapp: UploadedFile | null;
  emails: UploadedFile | null;
  calls: UploadedFile | null;
  other: UploadedFile | null;
}

export type InputMode = 'lookup' | 'upload';
export type TabType = 'leads' | 'whatsapp' | 'emails' | 'calls' | 'other';
export type MessageType = 'whatsapp' | 'email' | 'call' | 'other';

// Timeline event types
export interface TimelineEvent {
  type: 'whatsapp_pack' | 'email' | 'call' | 'lead_info';
  timestamp?: string;
  start_timestamp?: string;
  end_timestamp?: string;
}

export interface WhatsAppPack extends TimelineEvent {
  type: 'whatsapp_pack';
  start_timestamp: string;
  end_timestamp: string;
  message_count?: number;
  messages: WhatsAppMessage[];
}

export interface WhatsAppMessage {
  type: 'whatsapp';
  timestamp: string;
  from_number: string;
  to_number: string;
  message_content: string;
  sender_type: 'agent' | 'student';
}

export interface CallEvent extends TimelineEvent {
  type: 'call';
  timestamp: string;
  id: string;
  duration: string;
  to_number: string;
  from_number: string;
  source: string;
  record_url?: string;
}

export interface EmailEvent extends TimelineEvent {
  type: 'email';
  timestamp: string;
  sender_email: string;
  recipient_email: string;
  subject: string;
  message: string;
  snippet?: string;
  direction: 'inbound' | 'outbound';
  sender_type: 'agent' | 'student';
}

export interface LeadInfoEvent extends TimelineEvent {
  type: 'lead_info';
  timestamp: string;
  lead_id: string;
  user_name: string;
  email: string;
  phone: string;
  university?: string;
  move_in_date?: string;
  budget?: string;
}