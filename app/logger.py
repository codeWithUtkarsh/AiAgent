import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional


class ColoredFormatter(logging.Formatter):
    """Custom formatter with colors for console output"""

    COLORS = {
        'DEBUG': '\033[36m',     # Cyan
        'INFO': '\033[32m',      # Green
        'WARNING': '\033[33m',   # Yellow
        'ERROR': '\033[31m',     # Red
        'CRITICAL': '\033[35m',  # Magenta
        'RESET': '\033[0m'       # Reset
    }

    def format(self, record):
        log_color = self.COLORS.get(record.levelname, self.COLORS['RESET'])
        reset_color = self.COLORS['RESET']

        # Format: [TIMESTAMP] [LEVEL] [MODULE] MESSAGE
        timestamp = datetime.fromtimestamp(record.created).strftime('%Y-%m-%d %H:%M:%S')
        formatted = f"{log_color}[{timestamp}] [{record.levelname}] [{record.name}]{reset_color} {record.getMessage()}"

        if record.exc_info:
            formatted += '\n' + self.formatException(record.exc_info)

        return formatted


def setup_logger(name: str, log_level: str = "INFO") -> logging.Logger:
    """
    Set up a logger with both console and file handlers

    Args:
        name: Logger name
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, log_level.upper()))

    # Prevent duplicate handlers
    if logger.handlers:
        return logger

    # Console handler with colors
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, log_level.upper()))
    console_handler.setFormatter(ColoredFormatter())
    logger.addHandler(console_handler)

    # File handler
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)

    file_handler = logging.FileHandler(
        log_dir / f"ai_agent_{datetime.now().strftime('%Y%m%d')}.log"
    )
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter(
        '[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)

    return logger


def get_logger(name: str) -> logging.Logger:
    """Get or create a logger"""
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    return logging.getLogger(name)
