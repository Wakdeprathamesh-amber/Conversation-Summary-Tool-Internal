import { Mail, MessageSquare, Phone, FileText, User } from 'lucide-react';
import { MessageType, TabType } from '../types';

export const getChannelIcon = (type: MessageType) => {
  const iconMap = {
    email: Mail,
    whatsapp: MessageSquare,
    call: Phone,
    other: FileText
  };
  
  const IconComponent = iconMap[type];
  return <IconComponent className="w-4 h-4" />;
};

export const getChannelColor = (type: MessageType): string => {
  const colorMap = {
    email: 'bg-blue-100 text-blue-700 border-blue-200',
    whatsapp: 'bg-green-100 text-green-700 border-green-200',
    call: 'bg-purple-100 text-purple-700 border-purple-200',
    other: 'bg-gray-100 text-gray-700 border-gray-200'
  };
  
  return colorMap[type];
};

export const getSectionIcon = (section: TabType) => {
  const iconMap = {
    leads: User,
    whatsapp: MessageSquare,
    emails: Mail,
    calls: Phone,
    other: FileText
  };
  
  const IconComponent = iconMap[section];
  return <IconComponent className="w-5 h-5" />;
};

export const getSectionColor = (section: TabType): string => {
  const colorMap = {
    leads: 'border-blue-300 bg-blue-50',
    whatsapp: 'border-green-300 bg-green-50',
    emails: 'border-blue-300 bg-blue-50',
    calls: 'border-purple-300 bg-purple-50',
    other: 'border-gray-300 bg-gray-50'
  };
  
  return colorMap[section];
};