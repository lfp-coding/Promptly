import os
import json
import tempfile
import logging
import psutil
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict

class ProcessSingleton:
    """
    A singleton class to ensure only one instance of a specific process type is running.
    Uses a lock file in the system's temp directory to track running processes.
    """
    _instances: Dict[str, 'ProcessSingleton'] = {}
    
    def __init__(self, name: str):
        """
        Initialize ProcessSingleton for a specific process type
        
        Args:
            name (str): Unique identifier for the process type (e.g., 'main', 'chat')
        """
        self._name = name
        self._lockfile = Path(tempfile.gettempdir()) / f"Promptly_{name}.lock"
        self._logger = logging.getLogger(__name__)
        self._pid: Optional[int] = None
        
    @classmethod
    def get_instance(cls, name: str) -> 'ProcessSingleton':
        """
        Get or create singleton instance for a specific process type
        
        Args:
            name (str): Process type identifier
            
        Returns:
            ProcessSingleton: Singleton instance for the specified process type
        """
        if name not in cls._instances:
            cls._instances[name] = ProcessSingleton(name)
        return cls._instances[name]
        
    def acquire(self) -> bool:
        """
        Try to acquire the process lock
        
        Returns:
            bool: True if lock acquired, False if already locked by another running process
        """
        try:
            if self._lockfile.exists():
                # Read existing lock file
                with open(self._lockfile, 'r') as f:
                    data = json.load(f)
                    
                # Check if process is still running
                pid = data.get('pid')
                name = data.get('name')
                if pid and self._is_process_running(pid, name):
                    self._logger.info(f"Process '{self._name}' already running with PID {pid}")
                    return False
                else:
                    self._logger.info(f"Removing stale lock file for {name}")
                    
                # Process not running, remove stale lock
                self._logger.info(f"Removing stale lock file for '{self._name}'")
                self._lockfile.unlink()
            
            # Create new lock file
            self._pid = os.getpid()
            lock_data = {
                'pid': self._pid,
                'name': self._name,
                'timestamp': datetime.now().isoformat(),
                'temp_dir': tempfile.gettempdir()
            }
            
            with open(self._lockfile, 'w') as f:
                json.dump(lock_data, f, indent=4)
                
            self._logger.info(f"Lock acquired for '{self._name}' with PID {self._pid}")
            return True
            
        except Exception as e:
            self._logger.error(f"Error acquiring lock for '{self._name}'", error = e)
            return False
            
    def release(self):
        """
        Release the process lock
        """
        try:
            if self._lockfile.exists():
                self._lockfile.unlink()
                self._logger.info(f"Lock released for '{self._name}'")
                self._pid = None
            
        except Exception as e:
            self._logger.error(f"Error releasing lock for '{self._name}'", error = e)
            
    def is_running(self) -> bool:
        """
        Check if the process is currently running
        
        Returns:
            bool: True if process is running, False otherwise
        """
        try:
            if not self._lockfile.exists():
                return False
                
            with open(self._lockfile, 'r') as f:
                data = json.load(f)
                pid = data.get('pid')
                return bool(pid and self._is_process_running(pid))
                
        except Exception as e:
            self._logger.error(f"Error checking process status for '{self._name}'", error = e)
            return False
            
    def _is_process_running(self, pid: int, expected_name= 'Promptly.exe') -> bool:
        """
        Check if a process with given PID is running
        
        Args:
            pid (int): Process ID to check
            
        Returns:
            bool: True if process is running, False otherwise
        """
        try:
            process = psutil.Process(pid)
            if process.is_running() and process.name() == expected_name:
                return True
            else:
                return False
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            return False
        except Exception as e:
            self._logger.error(f"Error checking process {pid}", error = e)
            return False

    def __del__(self):
        """
        Cleanup when object is destroyed
        """
        try:
            if hasattr(self, 'pid') and self._pid == os.getpid():
                self.release()
        except Exception as e:
            self._logger.error(f"Error in destructor for '{self._name}'", error = e)

            