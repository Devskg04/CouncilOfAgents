"""
Structured JSON Logger
Free logging solution for observability
"""

import logging
import json
from datetime import datetime
from typing import Any, Dict, Optional


class JSONFormatter(logging.Formatter):
    """Format logs as JSON for structured logging"""
    
    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        
        # Add extra fields if present
        if hasattr(record, "agent"):
            log_data["agent"] = record.agent
        if hasattr(record, "session_id"):
            log_data["session_id"] = record.session_id
        if hasattr(record, "data"):
            log_data["data"] = record.data
        
        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        return json.dumps(log_data)


def setup_logger(name: str, level: int = logging.INFO) -> logging.Logger:
    """Setup a structured JSON logger"""
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Console handler with JSON formatting
    handler = logging.StreamHandler()
    handler.setFormatter(JSONFormatter())
    logger.addHandler(handler)
    
    return logger


def log_with_context(
    logger: logging.Logger,
    level: str,
    message: str,
    agent: Optional[str] = None,
    session_id: Optional[str] = None,
    data: Optional[Dict[str, Any]] = None
):
    """Log with additional context"""
    extra = {}
    if agent:
        extra["agent"] = agent
    if session_id:
        extra["session_id"] = session_id
    if data:
        extra["data"] = data
    
    log_method = getattr(logger, level.lower())
    log_method(message, extra=extra)
