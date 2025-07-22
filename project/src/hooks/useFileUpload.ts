import { useState } from 'react';
import { UploadSections } from '../types';

export const useFileUpload = () => {
  const [draggedOver, setDraggedOver] = useState<string | null>(null);

  const handleDragOver = (e: React.DragEvent, section: string) => {
    e.preventDefault();
    setDraggedOver(section);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    setDraggedOver(null);
  };

  const handleDrop = (
    e: React.DragEvent, 
    section: keyof UploadSections,
    onFileUpload: (section: keyof UploadSections, files: FileList | null) => void
  ) => {
    e.preventDefault();
    setDraggedOver(null);
    onFileUpload(section, e.dataTransfer.files);
  };

  return {
    draggedOver,
    handleDragOver,
    handleDragLeave,
    handleDrop
  };
};