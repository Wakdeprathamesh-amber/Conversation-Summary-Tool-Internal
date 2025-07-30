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
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.data_dir = os.path.join(self.base_dir, 'data')
        self.timeline_dir = os.path.join(self.base_dir, 'data')
        
        # Ensure directories exist
        os.makedirs(self.data_dir, exist_ok=True)
        os.makedirs(self.timeline_dir, exist_ok=True)
        
        logging.info(f"StorageManager initialized with max_age_days={max_age_days}, max_files_per_mobile={max_files_per_mobile}")
    
    def cleanup_old_files(self) -> Dict[str, int]:
        """
        Clean up old files based on age and count policies
        
        Returns:
            Dict with cleanup statistics
        """
        stats = {
            'timeline_files_deleted': 0,
            'lead_files_deleted': 0,
            'summary_files_deleted': 0,
            'total_space_freed_mb': 0
        }
        
        try:
            # Clean up old timeline files
            stats['timeline_files_deleted'] = self._cleanup_timeline_files()
            
            # Clean up old lead files
            stats['lead_files_deleted'] = self._cleanup_lead_files()
            
            # Clean up old summary files
            stats['summary_files_deleted'] = self._cleanup_summary_files()
            
            # Calculate space freed
            stats['total_space_freed_mb'] = self._calculate_space_freed()
            
            logging.info(f"Storage cleanup completed: {stats}")
            return stats
            
        except Exception as e:
            logging.error(f"Storage cleanup failed: {e}")
            return stats
    
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
    
    def _cleanup_lead_files(self) -> int:
        """Clean up old lead files"""
        deleted_count = 0
        cutoff_date = datetime.now() - timedelta(days=self.max_age_days)
        
        # Get all lead directories
        lead_dirs = glob.glob(os.path.join(self.data_dir, "Lead*"))
        
        for lead_dir in lead_dirs:
            try:
                dir_stat = os.stat(lead_dir)
                dir_date = datetime.fromtimestamp(dir_stat.st_mtime)
                
                if dir_date < cutoff_date:
                    shutil.rmtree(lead_dir)
                    deleted_count += 1
                    logging.info(f"Deleted old lead directory: {lead_dir}")
            except Exception as e:
                logging.warning(f"Failed to process lead directory {lead_dir}: {e}")
        
        return deleted_count
    
    def _cleanup_summary_files(self) -> int:
        """Clean up old summary files"""
        deleted_count = 0
        cutoff_date = datetime.now() - timedelta(days=self.max_age_days)
        
        # Get all summary files (assuming they have specific patterns)
        summary_files = glob.glob(os.path.join(self.data_dir, "*summary*.json"))
        summary_files.extend(glob.glob(os.path.join(self.data_dir, "*summary*.txt")))
        
        for file_path in summary_files:
            try:
                file_stat = os.stat(file_path)
                file_date = datetime.fromtimestamp(file_stat.st_mtime)
                
                if file_date < cutoff_date:
                    os.remove(file_path)
                    deleted_count += 1
                    logging.info(f"Deleted old summary file: {file_path}")
            except Exception as e:
                logging.warning(f"Failed to process summary file {file_path}: {e}")
        
        return deleted_count
    
    def _calculate_space_freed(self) -> float:
        """Calculate approximate space freed in MB"""
        # This is a rough estimate - in production you'd want more precise tracking
        return 0.0  # Placeholder for now
    
    def get_storage_stats(self) -> Dict[str, any]:
        """Get current storage statistics"""
        stats = {
            'timeline_files': 0,
            'lead_directories': 0,
            'summary_files': 0,
            'total_size_mb': 0.0,
            'oldest_file_days': 0,
            'newest_file_days': 0
        }
        
        try:
            # Count timeline files
            timeline_files = glob.glob(os.path.join(self.timeline_dir, "timeline_*.json"))
            stats['timeline_files'] = len(timeline_files)
            
            # Count lead directories
            lead_dirs = glob.glob(os.path.join(self.data_dir, "Lead*"))
            stats['lead_directories'] = len(lead_dirs)
            
            # Count summary files
            summary_files = glob.glob(os.path.join(self.data_dir, "*summary*.json"))
            summary_files.extend(glob.glob(os.path.join(self.data_dir, "*summary*.txt")))
            stats['summary_files'] = len(summary_files)
            
            # Calculate total size
            total_size = 0
            all_files = timeline_files + summary_files
            
            # Add size of lead directories
            for lead_dir in lead_dirs:
                try:
                    for root, dirs, files in os.walk(lead_dir):
                        for file in files:
                            try:
                                total_size += os.path.getsize(os.path.join(root, file))
                            except:
                                pass
                except:
                    pass
            
            for file_path in all_files:
                try:
                    total_size += os.path.getsize(file_path)
                except:
                    pass
            
            stats['total_size_mb'] = total_size / (1024 * 1024)
            
            # Find oldest and newest files
            all_file_paths = timeline_files + summary_files
            for lead_dir in lead_dirs:
                try:
                    for root, dirs, files in os.walk(lead_dir):
                        for file in files:
                            all_file_paths.append(os.path.join(root, file))
                except:
                    pass
            
            if all_file_paths:
                file_times = []
                for file_path in all_file_paths:
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
        # 1. More than 50 total files/directories
        # 2. Total size > 100MB
        # 3. Oldest file > 3 days
        total_items = stats['timeline_files'] + stats['lead_directories'] + stats['summary_files']
        
        return (total_items > 50 or 
                stats['total_size_mb'] > 100 or 
                stats['oldest_file_days'] > 3) 