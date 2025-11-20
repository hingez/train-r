"""Centralized logging configuration for Train-R."""
import logging
from pathlib import Path

from src.config import LOG_FILENAME, LOG_LEVEL, PROJECT_ROOT


def setup_logger():
    """Set up centralized logger. Clears log file on each run.

    Returns:
        Logger instance that can be used throughout the application
    """
    # Create logs directory if it doesn't exist
    log_dir = PROJECT_ROOT / "logs"
    log_dir.mkdir(exist_ok=True)

    log_path = log_dir / LOG_FILENAME

    # Clear the log file
    with open(log_path, 'w') as f:
        f.write("")

    # Get or create logger
    logger = logging.getLogger('train-r')

    # Convert string log level to logging constant
    numeric_level = getattr(logging, LOG_LEVEL.upper(), logging.INFO)
    logger.setLevel(numeric_level)

    # Remove existing handlers to avoid duplicates
    logger.handlers.clear()

    # File handler
    file_handler = logging.FileHandler(log_path)
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
