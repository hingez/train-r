"""Tests for retry_with_backoff utility."""
import pytest
from unittest.mock import Mock, patch
import time

from src.utils.retry import retry_with_backoff


class TestRetryWithBackoff:
    """Test suite for retry_with_backoff function."""

    def test_succeeds_on_first_attempt(self):
        """Should return result immediately when function succeeds."""
        mock_func = Mock(return_value="success")

        result = retry_with_backoff(
            func=mock_func,
            exception_types=(ValueError,),
            operation_name="test operation"
        )

        assert result == "success"
        assert mock_func.call_count == 1

    def test_retries_on_exception_then_succeeds(self):
        """Should retry and return result when function eventually succeeds."""
        mock_func = Mock(side_effect=[ValueError("fail"), ValueError("fail"), "success"])

        with patch("src.utils.retry.time.sleep"):
            result = retry_with_backoff(
                func=mock_func,
                exception_types=(ValueError,),
                operation_name="test operation",
                max_retries=3
            )

        assert result == "success"
        assert mock_func.call_count == 3

    def test_raises_after_max_retries_exhausted(self):
        """Should raise last exception after all retries fail."""
        mock_func = Mock(side_effect=ValueError("persistent failure"))

        with patch("src.utils.retry.time.sleep"):
            with pytest.raises(ValueError, match="persistent failure"):
                retry_with_backoff(
                    func=mock_func,
                    exception_types=(ValueError,),
                    operation_name="test operation",
                    max_retries=3
                )

        assert mock_func.call_count == 3

    def test_exponential_backoff_timing(self):
        """Should use exponential backoff delays between retries."""
        mock_func = Mock(side_effect=[ValueError("fail"), ValueError("fail"), "success"])
        sleep_calls = []

        def mock_sleep(seconds):
            sleep_calls.append(seconds)

        with patch("src.utils.retry.time.sleep", side_effect=mock_sleep):
            retry_with_backoff(
                func=mock_func,
                exception_types=(ValueError,),
                operation_name="test operation",
                max_retries=3,
                initial_delay=1.0,
                backoff_multiplier=2.0
            )

        # First retry: 1.0 * (2.0 ** 0) = 1.0
        # Second retry: 1.0 * (2.0 ** 1) = 2.0
        assert sleep_calls == [1.0, 2.0]

    def test_only_catches_specified_exceptions(self):
        """Should only retry for specified exception types."""
        mock_func = Mock(side_effect=TypeError("wrong type"))

        with pytest.raises(TypeError, match="wrong type"):
            retry_with_backoff(
                func=mock_func,
                exception_types=(ValueError,),
                operation_name="test operation"
            )

        # Should fail immediately without retrying
        assert mock_func.call_count == 1

    def test_catches_multiple_exception_types(self):
        """Should retry for any of the specified exception types."""
        mock_func = Mock(side_effect=[
            ValueError("value error"),
            KeyError("key error"),
            "success"
        ])

        with patch("src.utils.retry.time.sleep"):
            result = retry_with_backoff(
                func=mock_func,
                exception_types=(ValueError, KeyError),
                operation_name="test operation",
                max_retries=3
            )

        assert result == "success"
        assert mock_func.call_count == 3

    def test_should_retry_func_prevents_retry(self):
        """Should not retry when should_retry_func returns False."""
        mock_func = Mock(side_effect=ValueError("non-retriable"))

        def should_not_retry(exc):
            return False

        with pytest.raises(ValueError, match="non-retriable"):
            retry_with_backoff(
                func=mock_func,
                exception_types=(ValueError,),
                operation_name="test operation",
                should_retry_func=should_not_retry,
                max_retries=3
            )

        # Should fail after first attempt due to should_retry_func
        assert mock_func.call_count == 1

    def test_should_retry_func_allows_retry(self):
        """Should retry when should_retry_func returns True."""
        mock_func = Mock(side_effect=[ValueError("retriable"), "success"])

        def should_retry(exc):
            return True

        with patch("src.utils.retry.time.sleep"):
            result = retry_with_backoff(
                func=mock_func,
                exception_types=(ValueError,),
                operation_name="test operation",
                should_retry_func=should_retry,
                max_retries=3
            )

        assert result == "success"
        assert mock_func.call_count == 2

    def test_should_retry_func_receives_exception(self):
        """Should pass the exception to should_retry_func."""
        mock_func = Mock(side_effect=ValueError("test error"))
        received_exceptions = []

        def capture_exception(exc):
            received_exceptions.append(exc)
            return False

        with pytest.raises(ValueError):
            retry_with_backoff(
                func=mock_func,
                exception_types=(ValueError,),
                operation_name="test operation",
                should_retry_func=capture_exception
            )

        assert len(received_exceptions) == 1
        assert str(received_exceptions[0]) == "test error"

    def test_logs_retry_attempts(self, caplog):
        """Should log warning messages for each retry attempt."""
        mock_func = Mock(side_effect=[ValueError("fail"), "success"])

        with patch("src.utils.retry.time.sleep"):
            with caplog.at_level("WARNING"):
                retry_with_backoff(
                    func=mock_func,
                    exception_types=(ValueError,),
                    operation_name="test operation"
                )

        assert "test operation attempt 1 failed" in caplog.text
        assert "Retrying in" in caplog.text

    def test_logs_success_after_retry(self, caplog):
        """Should log info when succeeding after retries."""
        mock_func = Mock(side_effect=[ValueError("fail"), "success"])

        with patch("src.utils.retry.time.sleep"):
            with caplog.at_level("INFO"):
                retry_with_backoff(
                    func=mock_func,
                    exception_types=(ValueError,),
                    operation_name="test operation"
                )

        assert "test operation succeeded on attempt 2" in caplog.text

    def test_logs_final_failure(self, caplog):
        """Should log error when all retries are exhausted."""
        mock_func = Mock(side_effect=ValueError("persistent"))

        with patch("src.utils.retry.time.sleep"):
            with caplog.at_level("ERROR"):
                with pytest.raises(ValueError):
                    retry_with_backoff(
                        func=mock_func,
                        exception_types=(ValueError,),
                        operation_name="test operation",
                        max_retries=2
                    )

        assert "test operation failed after 2 attempts" in caplog.text

    def test_custom_max_retries(self):
        """Should respect custom max_retries parameter."""
        mock_func = Mock(side_effect=ValueError("fail"))

        with patch("src.utils.retry.time.sleep"):
            with pytest.raises(ValueError):
                retry_with_backoff(
                    func=mock_func,
                    exception_types=(ValueError,),
                    operation_name="test operation",
                    max_retries=5
                )

        assert mock_func.call_count == 5

    def test_custom_initial_delay(self):
        """Should use custom initial delay."""
        mock_func = Mock(side_effect=[ValueError("fail"), "success"])
        sleep_calls = []

        def mock_sleep(seconds):
            sleep_calls.append(seconds)

        with patch("src.utils.retry.time.sleep", side_effect=mock_sleep):
            retry_with_backoff(
                func=mock_func,
                exception_types=(ValueError,),
                operation_name="test operation",
                initial_delay=5.0
            )

        assert sleep_calls[0] == 5.0

    def test_single_retry_no_sleep_after_final_failure(self):
        """Should not sleep after the final failed attempt."""
        mock_func = Mock(side_effect=ValueError("fail"))
        sleep_calls = []

        def mock_sleep(seconds):
            sleep_calls.append(seconds)

        with patch("src.utils.retry.time.sleep", side_effect=mock_sleep):
            with pytest.raises(ValueError):
                retry_with_backoff(
                    func=mock_func,
                    exception_types=(ValueError,),
                    operation_name="test operation",
                    max_retries=2
                )

        # Only 1 sleep call (between attempt 1 and 2), not after final failure
        assert len(sleep_calls) == 1
