"""Centralized logging configuration for Train-R."""
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

from src.config import LOG_FILENAME, LOG_LEVEL, LOG_MAX_FILE_SIZE_MB, LOG_BACKUP_COUNT, PROJECT_ROOT


def setup_logger():
    """Set up centralized logger with rotation.

    Returns:
        Logger instance that can be used throughout the application
    """
    # Create logs directory if it doesn't exist
    log_dir = PROJECT_ROOT / "logs"
    log_dir.mkdir(exist_ok=True)

    log_path = log_dir / LOG_FILENAME

    # Get or create logger
    logger = logging.getLogger('train-r')

    # Convert string log level to logging constant
    numeric_level = getattr(logging, LOG_LEVEL.upper(), logging.INFO)
    logger.setLevel(numeric_level)

    # Remove existing handlers to avoid duplicates
    logger.handlers.clear()

    # Rotating file handler
    file_handler = RotatingFileHandler(
        log_path,
        maxBytes=LOG_MAX_FILE_SIZE_MB * 1024 * 1024,
        backupCount=LOG_BACKUP_COUNT
    )
    file_handler.setLevel(numeric_level)

    # Formatter with timestamp
    formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(formatter)

    logger.addHandler(file_handler)

    # Log initialization
    logger.info("=" * 60)
    logger.info("Train-R Application Started")
    logger.info("=" * 60)

    return logger
