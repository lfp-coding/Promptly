import logging
import shutil
import sys
from pathlib import Path
from typing import Optional, Dict, Any, Union
from datetime import datetime
import json
import traceback

root_dir = Path(__file__).parent.parent.parent
sys.path.append(str(root_dir))
from src.utils.path_manager import get_logs_path

class LogManager:
    """Singleton class for centralized logging management"""
    _instance = None
    
    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = LogManager()
        return cls._instance
        
    def __init__(self):
        if hasattr(self, '_initialized'):
            return
        
        self._initialized = True
        self._settings: Dict[str, Any] = {
            'log_level': logging.INFO,
            'max_log_age_days': 7,
            'log_format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        }
        self._setup_logging()

    

    def _setup_logging(self):
        """
        Setup logging configuration
        """
        try:
            # Create logs directory
            self._log_dir = get_logs_path()
            self._log_dir.mkdir(parents=True, exist_ok=True)
            
            # Create log file with timestamp
            timestamp = datetime.now().strftime("%Y%m%d")
            self._log_file = self._log_dir / f"Promptly_{timestamp}.log"
            
            # Configure root logger
            root_logger = logging.getLogger()
            root_logger.setLevel(self._settings['log_level'])
            
            # Create formatters
            formatter = logging.Formatter(self._settings['log_format'])
            
            # File handler
            file_handler = logging.FileHandler(self._log_file, encoding='utf-8')
            file_handler.setFormatter(formatter)
            root_logger.addHandler(file_handler)
            
            # Console handler
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setFormatter(formatter)
            root_logger.addHandler(console_handler)
            
            # Set specific levels for certain loggers
            logging.getLogger('urllib3').setLevel(logging.WARNING)
            logging.getLogger('PIL').setLevel(logging.WARNING)
            
            # Store handlers for potential reconfiguration
            self._file_handler = file_handler
            self._console_handler = console_handler
            
            self.log_info("LogManager initialized")
            
        except Exception as e:
            print(f"Failed to initialize logging", error = e)
            sys.exit(1)

    def delete_log_dir(self) -> None:
        """
        Delete the logging directory after releasing any file handler
        """
        try:
            # Remove file and console handlers
            root_logger = logging.getLogger()
            if self._file_handler:
                root_logger.removeHandler(self._file_handler)
                self._file_handler.close()
            if self._console_handler:
                root_logger.removeHandler(self._console_handler)
                self._console_handler.close()

            # Delete log directory and its contents
            if self._log_dir.exists():
                shutil.rmtree(self._log_dir)
        except Exception as e:
            self.log_error("Failed to delete log directory", e)

    def api_logging(self, data: Any = None, 
                    response: Any = None):
        """
        Log API interactions with OpenAI
        
        Args:
            data: Request data
            response: API response
        """
        try:
            self.log_info(
                f"\nRequest: {json.dumps(data, indent=2)}"
                f"\nResponse: {json.dumps(response, indent=2)}"
            )
        except Exception as e:
            self.log_error(f"Failed to log API interaction", error = e)

    def input_logging(self, input_type: str, content: str, 
                     processed: bool = False):
        """
        Log user input and text processing
        
        Args:
            input_type: Type of input (e.g., 'selection', 'prompt')
            content: The input content
            processed: Whether this is processed content
        """
        prefix = "Processed" if processed else "Input"
        self.log_info(
            f"{prefix} - {input_type}:\n{content[:1000]}"
            f"{'...' if len(content) > 1000 else ''}"
        )

    def error_logging(self, error: Union[str, Exception], 
                     context: str = "", stack_trace: bool = True) -> None:
        """
        Enhanced error logging with context and stack trace
        
        Args:
            error: Error message or exception
            context: Additional context about where/why the error occurred
            stack_trace: Whether to include stack trace
        """
        try:
            if isinstance(error, Exception):
                error_msg = f"{type(error).__name__}: {str(error)}"
            else:
                error_msg = str(error)

            if context:
                error_msg = f"{context}: {error_msg}"

            if stack_trace and isinstance(error, Exception):
                error_msg += f"\nStack trace:\n{''.join(traceback.format_tb(error.__traceback__))}"

            self.log_error(error_msg)
        except Exception as e:
            self.log_error(f"Failed to log error", error = e)

    def config_logging(self, operation: str, config_data: Dict[str, Any], 
                      success: bool = True) -> None:
        """
        Log configuration changes
        
        Args:
            operation: Type of operation (e.g., 'load', 'save', 'update')
            config_data: Configuration data
            success: Whether operation was successful
        """
        try:
            status = "Successfully" if success else "Failed to"
            self.log_info(
                f"{status} {operation} configuration:\n"
                f"{json.dumps(config_data, indent=2)}"
            )
        except Exception as e:
            self.log_error(f"Failed to log configuration", error = e)

    def startup_logging(self, version: str, config: Dict[str, Any]) -> None:
        """
        Log application startup information
        
        Args:
            version: Application version
            config: Initial configuration
        """
        try:
            self.log_info(
                f"Application Starting\n"
                f"Version: {version}\n"
                f"Python: {sys.version}\n"
                f"Platform: {sys.platform}\n"
                f"Configuration: {json.dumps(config, indent=2)}"
            )
        except Exception as e:
            self.log_error(f"Failed to log startup info", error = e)

    def log_error(self, message: str, error: Optional[Exception] = None) -> None:
        """
        Log an error message with optional exception details
        """
        if error:
            logging.error(f"{message}: {str(error)}", exc_info=True)
        else:
            logging.error(message)

    def log_warning(self, message: str) -> None:
        """Log a warning message"""
        logging.warning(message)

    def log_info(self, message: str) -> None:
        """Log an info message"""
        logging.info(message)

    def log_debug(self, message: str) -> None:
        """Log a debug message"""
        logging.debug(message)

    def set_level(self, level: int) -> None:
        """Set logging level for root logger"""
        try:
            self._settings['log_level'] = level
            logging.getLogger().setLevel(level)
            logging.info(f"Logging level set to: {logging._levelToName[level]}")
        except Exception as e:
            self.log_error("Failed to set logging level", e)

    def get_settings(self) -> Dict[str, Any]:
        """Get current logging settings"""
        return self._settings.copy()

    def update_settings(self, new_settings: Dict[str, Any]) -> None:
        """Update logging settings"""
        try:
            self._settings.update(new_settings)
            self._reconfigure_logging()
            logging.info("Logging settings updated")
        except Exception as e:
            self.log_error("Failed to update logging settings", e)

    def _reconfigure_logging(self) -> None:
        """Reconfigure logging with current settings"""
        try:
            root_logger = logging.getLogger()
            
            # Update level
            root_logger.setLevel(self._settings['log_level'])
            
            # Update formatter
            formatter = logging.Formatter(self._settings['log_format'])
            self._file_handler.setFormatter(formatter)
            self._console_handler.setFormatter(formatter)
            
            logging.info("Logging reconfigured")
        except Exception as e:
            self.log_error("Failed to reconfigure logging", e)

    def cleanup_old_logs(self, days: Optional[int] = None) -> None:
        """Clean up log files older than specified days"""
        try:
            days = days or self._settings['max_log_age_days']
            current_time = datetime.now()
            
            for log_file in self._log_dir.glob("Promptly_*.log"):
                file_time = datetime.fromtimestamp(log_file.stat().st_mtime)
                if (current_time - file_time).days > days:
                    log_file.unlink()
                    logging.info(f"Deleted old log file: {log_file.name}")
                    
        except Exception as e:
            self.log_error("Failed to cleanup old logs", e)

    def get_current_log_file(self) -> Path:
        """Get path to current log file"""
        return self._log_file

    def get_recent_logs(self, lines: int = 100) -> list[str]:
        """Get recent log entries"""
        try:
            with open(self._log_file, 'r', encoding='utf-8') as f:
                return list(f.readlines())[-lines:]
        except Exception as e:
            self.log_error("Failed to read recent logs", e)
            return []

    def export_logs(self, target_file: Path) -> bool:
        """Export current logs to target file"""
        try:
            if self._log_file.exists():
                target_file.parent.mkdir(parents=True, exist_ok=True)
                with open(self._log_file, 'r', encoding='utf-8') as source:
                    with open(target_file, 'w', encoding='utf-8') as target:
                        target.write(source.read())
                logging.info(f"Logs exported to: {target_file}")
                return True
            return False
        except Exception as e:
            self.log_error("Failed to export logs", e)
            return False
        
    