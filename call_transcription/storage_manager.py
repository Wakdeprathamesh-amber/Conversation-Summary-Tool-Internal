import os
import json
import logging
import shutil
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import glob

class StorageManager:
    def __init__(self, max_age_days: int = 7, max_files_per_mobile: int = 50):
        """
        Initialize storage manager with cleanup policies
        
        Args:
            max_age_days: Files older than this will be deleted
            max_files_per_mobile: Maximum files to keep per mobile number
        """
        self.max_age_days = max_age_days
        self.max_files_per_mobile = max_files_per_mobile
        self.base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.transcripts_dir = os.path.join(self.base_dir, 'data', 'transcripts')
        self.timeline_dir = os.path.join(self.base_dir, 'data')
        self.log_dir = os.path.dirname(os.path.abspath(__file__))
        
        # Ensure directories exist
        os.makedirs(self.transcripts_dir, exist_ok=True)
        os.makedirs(self.timeline_dir, exist_ok=True)
        
        logging.info(f"StorageManager initialized with max_age_days={max_age_days}, max_files_per_mobile={max_files_per_mobile}")
    
    def cleanup_old_files(self) -> Dict[str, int]:
        """
        Clean up old files based on age and count policies
        
        Returns:
            Dict with cleanup statistics
        """
        stats = {
            'transcripts_deleted': 0,
            'timeline_files_deleted': 0,
            'log_files_deleted': 0,
            'total_space_freed_mb': 0
        }
        
        try:
            # Clean up old transcript files
            stats['transcripts_deleted'] = self._cleanup_transcripts()
            
            # Clean up old timeline files
            stats['timeline_files_deleted'] = self._cleanup_timeline_files()
            
            # Clean up old log files
            stats['log_files_deleted'] = self._cleanup_log_files()
            
            # Calculate space freed
            stats['total_space_freed_mb'] = self._calculate_space_freed()
            
            logging.info(f"Storage cleanup completed: {stats}")
            return stats
            
        except Exception as e:
            logging.error(f"Storage cleanup failed: {e}")
            return stats
    
    def _cleanup_transcripts(self) -> int:
        """Clean up old transcript files"""
        deleted_count = 0
        cutoff_date = datetime.now() - timedelta(days=self.max_age_days)
        
        # Get all transcript files
        transcript_files = glob.glob(os.path.join(self.transcripts_dir, "*.txt"))
        
        for file_path in transcript_files:
            try:
                file_stat = os.stat(file_path)
                file_date = datetime.fromtimestamp(file_stat.st_mtime)
                
                if file_date < cutoff_date:
                    os.remove(file_path)
                    deleted_count += 1
                    logging.info(f"Deleted old transcript: {file_path}")
            except Exception as e:
                logging.warning(f"Failed to process transcript file {file_path}: {e}")
        
        # Also limit files per mobile number
        mobile_files = {}
        for file_path in glob.glob(os.path.join(self.transcripts_dir, "*.txt")):
            try:
                filename = os.path.basename(file_path)
                # Extract mobile number from filename (format: mobile_timestamp.txt)
                mobile_number = filename.split('_')[0]
                if mobile_number not in mobile_files:
                    mobile_files[mobile_number] = []
                mobile_files[mobile_number].append((file_path, os.path.getmtime(file_path)))
            except Exception as e:
                logging.warning(f"Failed to process file {file_path}: {e}")
        
        # Keep only the most recent files per mobile number
        for mobile_number, files in mobile_files.items():
            if len(files) > self.max_files_per_mobile:
                # Sort by modification time (newest first)
                files.sort(key=lambda x: x[1], reverse=True)
                
                # Delete excess files
                for file_path, _ in files[self.max_files_per_mobile:]:
                    try:
                        os.remove(file_path)
                        deleted_count += 1
                        logging.info(f"Deleted excess transcript for {mobile_number}: {file_path}")
                    except Exception as e:
                        logging.warning(f"Failed to delete file {file_path}: {e}")
        
        return deleted_count
    
    def _cleanup_timeline_files(self) -> int:
        """Clean up old timeline files"""
        deleted_count = 0
        cutoff_date = datetime.now() - timedelta(days=self.max_age_days)
        
        # Get all timeline files
        timeline_files = glob.glob(os.path.join(self.timeline_dir, "timeline_*.json"))
        
        for file_path in timeline_files:
            try:
                file_stat = os.stat(file_path)
                file_date = datetime.fromtimestamp(file_stat.st_mtime)
                
                if file_date < cutoff_date:
                    os.remove(file_path)
                    deleted_count += 1
                    logging.info(f"Deleted old timeline: {file_path}")
            except Exception as e:
                logging.warning(f"Failed to process timeline file {file_path}: {e}")
        
        return deleted_count
    
    def _cleanup_log_files(self) -> int:
        """Clean up old log files"""
        deleted_count = 0
        cutoff_date = datetime.now() - timedelta(days=self.max_age_days)
        
        # Get all log files
        log_files = glob.glob(os.path.join(self.log_dir, "*.log"))
        
        for file_path in log_files:
            try:
                file_stat = os.stat(file_path)
                file_date = datetime.fromtimestamp(file_stat.st_mtime)
                
                if file_date < cutoff_date:
                    os.remove(file_path)
                    deleted_count += 1
                    logging.info(f"Deleted old log: {file_path}")
            except Exception as e:
                logging.warning(f"Failed to process log file {file_path}: {e}")
        
        return deleted_count
    
    def _calculate_space_freed(self) -> float:
        """Calculate approximate space freed in MB"""
        # This is a rough estimate - in production you'd want more precise tracking
        return 0.0  # Placeholder for now
    
    def get_storage_stats(self) -> Dict[str, any]:
        """Get current storage statistics"""
        stats = {
            'transcript_files': 0,
            'timeline_files': 0,
            'log_files': 0,
            'total_size_mb': 0.0,
            'oldest_file_days': 0,
            'newest_file_days': 0
        }
        
        try:
            # Count transcript files
            transcript_files = glob.glob(os.path.join(self.transcripts_dir, "*.txt"))
            stats['transcript_files'] = len(transcript_files)
            
            # Count timeline files
            timeline_files = glob.glob(os.path.join(self.timeline_dir, "timeline_*.json"))
            stats['timeline_files'] = len(timeline_files)
            
            # Count log files
            log_files = glob.glob(os.path.join(self.log_dir, "*.log"))
            stats['log_files'] = len(log_files)
            
            # Calculate total size
            total_size = 0
            all_files = transcript_files + timeline_files + log_files
            
            for file_path in all_files:
                try:
                    total_size += os.path.getsize(file_path)
                except:
                    pass
            
            stats['total_size_mb'] = total_size / (1024 * 1024)
            
            # Find oldest and newest files
            if all_files:
                file_times = []
                for file_path in all_files:
                    try:
                        file_times.append(os.path.getmtime(file_path))
                    except:
                        pass
                
                if file_times:
                    oldest_time = min(file_times)
                    newest_time = max(file_times)
                    now = datetime.now().timestamp()
                    
                    stats['oldest_file_days'] = int((now - oldest_time) / (24 * 3600))
                    stats['newest_file_days'] = int((now - newest_time) / (24 * 3600))
            
        except Exception as e:
            logging.error(f"Failed to get storage stats: {e}")
        
        return stats
    
    def should_cleanup(self) -> bool:
        """Check if cleanup is needed based on storage usage"""
        stats = self.get_storage_stats()
        
        # Cleanup if:
        # 1. More than 100 total files
        # 2. Total size > 50MB
        # 3. Oldest file > 3 days
        total_files = stats['transcript_files'] + stats['timeline_files'] + stats['log_files']
        
        return (total_files > 100 or 
                stats['total_size_mb'] > 50 or 
                stats['oldest_file_days'] > 3) 