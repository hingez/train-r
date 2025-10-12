"""Centralized logging configuration for Train-R."""
import logging
from pathlib import Path


LOG_DIR = "logs"
LOG_FILE = "train-r.log"


def setup_logger():
    """Set up centralized logger. Clears log file on each run.

    Returns:
        Logger instance that can be used throughout the application
    """
    # Create logs directory if it doesn't exist
    Path(LOG_DIR).mkdir(exist_ok=True)

    log_path = Path(LOG_DIR) / LOG_FILE

    # Clear the log file
    with open(log_path, 'w') as f:
        f.write("")

    # Get or create logger
    logger = logging.getLogger('train-r')
    logger.setLevel(logging.INFO)

    # Remove existing handlers to avoid duplicates
    logger.handlers.clear()

    # File handler
    file_handler = logging.FileHandler(log_path)
    file_handler.setLevel(logging.INFO)

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


def get_logger():
    """Get the application logger.

    Returns:
        Logger instance
    """
    return logging.getLogger('train-r')
