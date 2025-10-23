"""Retry logic with exponential backoff for API calls."""
import time
import logging
from typing import TypeVar, Callable, Type, Optional, Tuple

logger = logging.getLogger('train-r')

# Retry configuration constants
MAX_RETRIES = 3
INITIAL_RETRY_DELAY = 1  # seconds
RETRY_BACKOFF_MULTIPLIER = 2

T = TypeVar('T')


def retry_with_backoff(
    func: Callable[[], T],
    exception_types: Tuple[Type[Exception], ...],
    operation_name: str,
    max_retries: int = MAX_RETRIES,
    initial_delay: float = INITIAL_RETRY_DELAY,
    backoff_multiplier: float = RETRY_BACKOFF_MULTIPLIER,
    should_retry_func: Optional[Callable[[Exception], bool]] = None
) -> T:
    """Execute a function with retry logic and exponential backoff.

    Args:
        func: Function to execute (should take no arguments)
        exception_types: Tuple of exception types to catch and retry
        operation_name: Name of operation for logging (e.g., "API call", "Upload")
        max_retries: Maximum number of retry attempts
        initial_delay: Initial delay in seconds before first retry
        backoff_multiplier: Multiplier for exponential backoff
        should_retry_func: Optional function to determine if exception should be retried
                          Takes exception as argument, returns True to retry

    Returns:
        Result from successful function execution

    Raises:
        Exception: The last exception if all retries are exhausted
    """
    last_exception = None

    for attempt in range(max_retries):
        try:
            result = func()

            # Log success if this was a retry
            if attempt > 0:
                logger.info(f"{operation_name} succeeded on attempt {attempt + 1}")

            return result

        except exception_types as e:
            last_exception = e

            # Check if we should retry this exception
            if should_retry_func and not should_retry_func(e):
                logger.error(f"{operation_name} failed with non-retriable error")
                raise

            # Calculate backoff delay
            if attempt < max_retries - 1:
                delay = initial_delay * (backoff_multiplier ** attempt)
                logger.warning(
                    f"{operation_name} attempt {attempt + 1} failed: {str(e)}. "
                    f"Retrying in {delay}s..."
                )
                time.sleep(delay)
            else:
                logger.error(f"{operation_name} failed after {max_retries} attempts")

    # If we get here, all retries failed
    raise last_exception
