"""
Structured Logging Infrastructure

Provides:
- JSON structured logging
- Log levels and filtering
- Context injection
- Performance logging
- Error tracking
"""

import logging
import json
import time
from typing import Any, Dict, Optional
from datetime import datetime
from pathlib import Path
from contextlib import contextmanager


class JSONFormatter(logging.Formatter):
    """
    JSON log formatter for structured logging
    
    Outputs logs in JSON format for easy parsing and analysis
    """
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON"""
        log_data = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }
        
        # Add exception info if present
        if record.exc_info:
            log_data['exception'] = self.formatException(record.exc_info)
        
        # Add extra fields
        if hasattr(record, 'context'):
            log_data['context'] = record.context
        
        if hasattr(record, 'duration'):
            log_data['duration_ms'] = record.duration
        
        if hasattr(record, 'session_id'):
            log_data['session_id'] = record.session_id
        
        return json.dumps(log_data)


class AureusLogger:
    """
    Aureus logging system
    
    Features:
    - Structured JSON logging
    - Context injection
    - Performance tracking
    - Multiple handlers (file, console)
    """
    
    def __init__(
        self,
        name: str = "aureus",
        log_level: str = "INFO",
        log_dir: Optional[Path] = None,
        json_format: bool = True
    ):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(getattr(logging, log_level.upper()))
        self.logger.handlers.clear()
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        if json_format:
            console_handler.setFormatter(JSONFormatter())
        else:
            console_handler.setFormatter(
                logging.Formatter(
                    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
                )
            )
        
        self.logger.addHandler(console_handler)
        
        # File handler (if log_dir specified)
        if log_dir:
            log_dir.mkdir(parents=True, exist_ok=True)
            log_file = log_dir / f"aureus_{datetime.now().strftime('%Y%m%d')}.log"
            
            file_handler = logging.FileHandler(log_file)
            file_handler.setLevel(logging.DEBUG)
            file_handler.setFormatter(JSONFormatter())
            
            self.logger.addHandler(file_handler)
        
        self._context = {}
    
    def set_context(self, **kwargs):
        """Set logging context (e.g., session_id, user_id)"""
        self._context.update(kwargs)
    
    def clear_context(self):
        """Clear logging context"""
        self._context.clear()
    
    def _add_context(self, extra: Optional[Dict] = None) -> Dict:
        """Add context to log extra data"""
        log_extra = {'context': self._context.copy()}
        if extra:
            log_extra.update(extra)
        return log_extra
    
    def debug(self, message: str, **kwargs):
        """Log debug message"""
        self.logger.debug(message, extra=self._add_context(kwargs))
    
    def info(self, message: str, **kwargs):
        """Log info message"""
        self.logger.info(message, extra=self._add_context(kwargs))
    
    def warning(self, message: str, **kwargs):
        """Log warning message"""
        self.logger.warning(message, extra=self._add_context(kwargs))
    
    def error(self, message: str, exc_info: bool = True, **kwargs):
        """Log error message"""
        self.logger.error(message, exc_info=exc_info, extra=self._add_context(kwargs))
    
    def critical(self, message: str, exc_info: bool = True, **kwargs):
        """Log critical message"""
        self.logger.critical(message, exc_info=exc_info, extra=self._add_context(kwargs))
    
    @contextmanager
    def performance_log(self, operation: str):
        """
        Context manager for performance logging
        
        Example:
            with logger.performance_log("build_feature"):
                # ... do work ...
                pass
        """
        start_time = time.time()
        
        try:
            self.info(f"Starting: {operation}")
            yield
            
        finally:
            duration_ms = (time.time() - start_time) * 1000
            self.info(
                f"Completed: {operation}",
                duration=duration_ms
            )
    
    @contextmanager
    def session_context(self, session_id: str):
        """
        Context manager for session logging
        
        Example:
            with logger.session_context("abc123"):
                logger.info("Processing request")
        """
        old_context = self._context.copy()
        self._context['session_id'] = session_id
        
        try:
            yield
        finally:
            self._context = old_context


# Global logger instance
_global_logger: Optional[AureusLogger] = None


def get_logger(
    name: str = "aureus",
    log_level: str = "INFO",
    log_dir: Optional[Path] = None
) -> AureusLogger:
    """
    Get or create global logger instance
    
    Args:
        name: Logger name
        log_level: Logging level
        log_dir: Directory for log files
        
    Returns:
        AureusLogger instance
    """
    global _global_logger
    
    if _global_logger is None:
        _global_logger = AureusLogger(
            name=name,
            log_level=log_level,
            log_dir=log_dir
        )
    
    return _global_logger


def configure_logging(
    log_level: str = "INFO",
    log_dir: Optional[Path] = None,
    json_format: bool = True
):
    """
    Configure global logging
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_dir: Directory for log files
        json_format: Use JSON formatting
    """
    global _global_logger
    _global_logger = AureusLogger(
        name="aureus",
        log_level=log_level,
        log_dir=log_dir,
        json_format=json_format
    )
