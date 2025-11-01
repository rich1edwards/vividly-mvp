"""
Circuit Breaker Pattern for External API Resilience

Implements circuit breaker to prevent cascading failures when external
APIs (Nano Banana, Vertex AI) are experiencing issues.

States:
- CLOSED: Normal operation, requests pass through
- OPEN: Too many failures, requests fail fast
- HALF_OPEN: Testing if service has recovered

Inspired by Michael Nygard's "Release It!" pattern.
"""

import time
import logging
from enum import Enum
from typing import Callable, Any, Optional, Dict
from datetime import datetime, timedelta
from functools import wraps
import threading
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


class CircuitState(Enum):
    """Circuit breaker states."""

    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Failing fast
    HALF_OPEN = "half_open"  # Testing recovery


@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker behavior."""

    # Failure threshold
    failure_threshold: int = 5  # Failures before opening circuit
    failure_timeout: int = 60  # Window for counting failures (seconds)

    # Recovery
    recovery_timeout: int = 60  # Time to wait before trying again (seconds)
    success_threshold: int = 2  # Successes needed to close circuit

    # Timeouts
    call_timeout: Optional[float] = 10.0  # Max time for single call (seconds)

    # Monitoring
    name: str = "default"  # Circuit breaker name for logging


@dataclass
class CircuitBreakerStats:
    """Statistics for monitoring circuit breaker health."""

    state: CircuitState = CircuitState.CLOSED
    failure_count: int = 0
    success_count: int = 0
    last_failure_time: Optional[datetime] = None
    last_state_change: datetime = field(default_factory=datetime.utcnow)
    total_calls: int = 0
    total_failures: int = 0
    total_successes: int = 0

    def to_dict(self) -> Dict:
        """Convert stats to dictionary for monitoring."""
        return {
            "state": self.state.value,
            "failure_count": self.failure_count,
            "success_count": self.success_count,
            "last_failure_time": self.last_failure_time.isoformat()
            if self.last_failure_time
            else None,
            "last_state_change": self.last_state_change.isoformat(),
            "total_calls": self.total_calls,
            "total_failures": self.total_failures,
            "total_successes": self.total_successes,
        }


class CircuitBreakerError(Exception):
    """Raised when circuit breaker is open."""

    pass


class CircuitBreaker:
    """
    Circuit breaker for protecting against cascading failures.

    Usage:
        breaker = CircuitBreaker(name="nano_banana_api", failure_threshold=3)

        @breaker
        def call_external_api():
            return requests.post(...)

        try:
            result = call_external_api()
        except CircuitBreakerError:
            # Circuit is open, fail fast
            return fallback_response()
    """

    def __init__(self, config: Optional[CircuitBreakerConfig] = None, **kwargs):
        """
        Initialize circuit breaker.

        Args:
            config: CircuitBreakerConfig object
            **kwargs: Override config values (name, failure_threshold, etc.)
        """
        self.config = config or CircuitBreakerConfig(**kwargs)
        self.stats = CircuitBreakerStats()
        self._lock = threading.RLock()

        logger.info(
            f"Circuit breaker '{self.config.name}' initialized: "
            f"failure_threshold={self.config.failure_threshold}, "
            f"recovery_timeout={self.config.recovery_timeout}s"
        )

    @property
    def state(self) -> CircuitState:
        """Get current circuit state."""
        return self.stats.state

    def _record_success(self):
        """Record successful call."""
        with self._lock:
            self.stats.success_count += 1
            self.stats.total_successes += 1

            if self.stats.state == CircuitState.HALF_OPEN:
                if self.stats.success_count >= self.config.success_threshold:
                    self._transition_to_closed()

    def _record_failure(self):
        """Record failed call."""
        with self._lock:
            self.stats.failure_count += 1
            self.stats.total_failures += 1
            self.stats.last_failure_time = datetime.utcnow()

            if self.stats.state == CircuitState.HALF_OPEN:
                # Any failure in half-open immediately reopens circuit
                self._transition_to_open()
            elif self.stats.state == CircuitState.CLOSED:
                # Check if we've exceeded failure threshold
                if self.stats.failure_count >= self.config.failure_threshold:
                    self._transition_to_open()

    def _transition_to_open(self):
        """Transition to OPEN state."""
        self.stats.state = CircuitState.OPEN
        self.stats.last_state_change = datetime.utcnow()
        logger.warning(
            f"Circuit breaker '{self.config.name}' OPENED after "
            f"{self.stats.failure_count} failures"
        )

    def _transition_to_half_open(self):
        """Transition to HALF_OPEN state."""
        self.stats.state = CircuitState.HALF_OPEN
        self.stats.success_count = 0  # Reset success counter
        self.stats.last_state_change = datetime.utcnow()
        logger.info(f"Circuit breaker '{self.config.name}' entering HALF_OPEN state")

    def _transition_to_closed(self):
        """Transition to CLOSED state."""
        self.stats.state = CircuitState.CLOSED
        self.stats.failure_count = 0  # Reset failure counter
        self.stats.success_count = 0
        self.stats.last_state_change = datetime.utcnow()
        logger.info(f"Circuit breaker '{self.config.name}' CLOSED - service recovered")

    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt recovery."""
        if self.stats.state != CircuitState.OPEN:
            return False

        if not self.stats.last_failure_time:
            return False

        time_since_failure = (
            datetime.utcnow() - self.stats.last_failure_time
        ).total_seconds()
        return time_since_failure >= self.config.recovery_timeout

    def _reset_failure_window(self):
        """Reset failure count if outside failure timeout window."""
        if not self.stats.last_failure_time:
            return

        time_since_failure = (
            datetime.utcnow() - self.stats.last_failure_time
        ).total_seconds()
        if time_since_failure >= self.config.failure_timeout:
            self.stats.failure_count = 0

    def call(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute function with circuit breaker protection.

        Args:
            func: Function to call
            *args: Positional arguments for func
            **kwargs: Keyword arguments for func

        Returns:
            Result from func

        Raises:
            CircuitBreakerError: If circuit is open
            Exception: Any exception raised by func
        """
        with self._lock:
            self.stats.total_calls += 1

            # Check if we should attempt reset
            if self._should_attempt_reset():
                self._transition_to_half_open()

            # Reset failure count if outside window
            if self.stats.state == CircuitState.CLOSED:
                self._reset_failure_window()

            # Fail fast if circuit is open
            if self.stats.state == CircuitState.OPEN:
                raise CircuitBreakerError(
                    f"Circuit breaker '{self.config.name}' is OPEN. "
                    f"Service will be retried after {self.config.recovery_timeout}s"
                )

        # Execute the call
        try:
            result = func(*args, **kwargs)
            self._record_success()
            return result
        except Exception as e:
            self._record_failure()
            logger.error(
                f"Circuit breaker '{self.config.name}' call failed: {str(e)}",
                exc_info=True,
            )
            raise

    def __call__(self, func: Callable) -> Callable:
        """
        Decorator for wrapping functions with circuit breaker.

        Usage:
            @circuit_breaker
            def my_api_call():
                return requests.get(...)
        """

        @wraps(func)
        def wrapper(*args, **kwargs):
            return self.call(func, *args, **kwargs)

        return wrapper

    def get_stats(self) -> Dict:
        """Get current circuit breaker statistics."""
        return self.stats.to_dict()

    def reset(self):
        """Manually reset circuit breaker to CLOSED state."""
        with self._lock:
            self._transition_to_closed()
            logger.info(f"Circuit breaker '{self.config.name}' manually reset")


# Global circuit breakers for external services
_circuit_breakers: Dict[str, CircuitBreaker] = {}
_breakers_lock = threading.Lock()


def get_circuit_breaker(name: str, **config_overrides) -> CircuitBreaker:
    """
    Get or create a named circuit breaker.

    Args:
        name: Circuit breaker name
        **config_overrides: Override default config (failure_threshold, etc.)

    Returns:
        CircuitBreaker instance
    """
    with _breakers_lock:
        if name not in _circuit_breakers:
            config = CircuitBreakerConfig(name=name, **config_overrides)
            _circuit_breakers[name] = CircuitBreaker(config)
        return _circuit_breakers[name]


def get_all_circuit_breaker_stats() -> Dict[str, Dict]:
    """Get statistics for all circuit breakers."""
    with _breakers_lock:
        return {
            name: breaker.get_stats() for name, breaker in _circuit_breakers.items()
        }


# Pre-configured circuit breakers for Vividly services
nano_banana_breaker = get_circuit_breaker(
    name="nano_banana_api",
    failure_threshold=5,
    recovery_timeout=120,  # 2 minutes - API may need time to recover
    call_timeout=300.0,  # 5 minutes - video generation is slow
)

vertex_ai_breaker = get_circuit_breaker(
    name="vertex_ai",
    failure_threshold=3,
    recovery_timeout=60,  # 1 minute
    call_timeout=30.0,  # 30 seconds
)

gemini_breaker = get_circuit_breaker(
    name="gemini_api",
    failure_threshold=3,
    recovery_timeout=60,
    call_timeout=30.0,
)


def with_circuit_breaker(breaker_name: str, **config_overrides):
    """
    Decorator factory for applying circuit breaker to functions.

    Usage:
        @with_circuit_breaker("my_service", failure_threshold=10)
        def call_my_service():
            return requests.post(...)
    """
    breaker = get_circuit_breaker(breaker_name, **config_overrides)
    return breaker
