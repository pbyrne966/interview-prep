import time
from enum import Enum
from threading import Lock, Thread
from datetime import datetime, timedelta


class CircuitBreakerState(Enum):
    OPEN = "OPEN"
    HALF_OPEN = "HALF_OPEN"
    CLOSED = "CLOSED"


class CircuitOpenError(Exception):
    pass


class CircuitBreaker:
    def __init__(
        self, failure_threshold: int, recovery_timeout: float, probe_successes: int
    ):
        """
        failure_threshold  – consecutive failures before tripping to OPEN
        recovery_timeout   – seconds to wait in OPEN before moving to HALF_OPEN
        probe_successes    – consecutive successes in HALF_OPEN needed to close
        """
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.probe_successes = probe_successes
        self.current_state = CircuitBreakerState.CLOSED
        self.entered_open: datetime | None = None
        self.current_fail_states = 0
        self.prob_attempts = 0
        self.lock = Lock()

        t = Thread(target=self.process_state, daemon=True)
        t.start()

    def process_state(self):
        while True:
            with self.lock:
                if self.entered_open is not None:
                    time_passed = datetime.now() - self.entered_open > timedelta(
                        seconds=self.recovery_timeout
                    )
                    if self.current_state == CircuitBreakerState.OPEN and time_passed:
                        self.current_state = CircuitBreakerState.HALF_OPEN
                        self.prob_attempts = 0

                elif self.current_fail_states >= self.failure_threshold:
                    self.current_state = CircuitBreakerState.OPEN

            time.sleep(self.recovery_timeout / 2)

    def reset_state(self):
        self.current_state = CircuitBreakerState.CLOSED
        self.current_fail_states = 0
        self.entered_open = None
        self.prob_attempts = 0
        self.current_fail_states = 0

    def record_fn_call(self, result_type: str) -> None:
        with self.lock:
            if result_type == "Failure":
                if self.current_state == CircuitBreakerState.HALF_OPEN:
                    self.current_state = CircuitBreakerState.OPEN
                    self.entered_open = datetime.now()
                    self.prob_attempts = 0
                    self.current_fail_states = self.failure_threshold
                    return

                self.current_fail_states += 1
                if self.current_fail_states < self.failure_threshold:
                    return
                if self.current_state == CircuitBreakerState.CLOSED:
                    self.entered_open = datetime.now()
                    self.current_state = CircuitBreakerState.OPEN

            elif result_type == "Success":
                if self.current_state == CircuitBreakerState.HALF_OPEN:
                    self.prob_attempts += 1
                    if self.prob_attempts >= self.probe_successes:
                        self.reset_state()
                elif self.current_state == CircuitBreakerState.CLOSED:
                    self.current_fail_states = 0

    def call(self, fn, *args, **kwargs):
        """
        Execute fn(*args, **kwargs) through the breaker.
        - Raises CircuitOpenError if the breaker is OPEN.
        - Propagates the original exception if fn raises, and records the failure.
        - Returns fn's return value on success, and records the success.
        """
        if self.current_state == CircuitBreakerState.OPEN:
            raise CircuitOpenError("The circuit breaker is open")

        try:
            result = fn(*args, **kwargs)
            self.record_fn_call("Success")
            return result
        except Exception as e:
            self.record_fn_call("Failure")
            raise e


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    results = []

    def check(label: str, passed: bool) -> None:
        results.append(passed)
        print(f"[{'PASS' if passed else 'FAIL'}] {label}")

    # ── helpers ────────────────────────────────────────────────────────────

    def good():
        return "ok"

    def bad():
        raise ConnectionError("boom")

    # ── 1. Successful calls work normally ──────────────────────────────────
    cb = CircuitBreaker(failure_threshold=3, recovery_timeout=1.0, probe_successes=2)
    result = cb.call(good)
    check("successful call returns value", result == "ok")

    # ── 2. Failures below threshold don't open the breaker ─────────────────
    cb = CircuitBreaker(failure_threshold=3, recovery_timeout=1.0, probe_successes=2)
    for _ in range(2):
        try:
            cb.call(bad)
        except ConnectionError:
            pass
    result = cb.call(good)
    check("failures below threshold — breaker stays closed", result == "ok")

    # ── 3. Hitting the threshold opens the breaker ─────────────────────────
    cb = CircuitBreaker(failure_threshold=3, recovery_timeout=1.0, probe_successes=2)
    for _ in range(3):
        try:
            cb.call(bad)
        except ConnectionError:
            pass
    open_error_raised = False
    try:
        cb.call(good)
    except CircuitOpenError:
        open_error_raised = True
    check("breaker opens after hitting failure threshold", open_error_raised)

    # ── 4. OPEN breaker does NOT call the function ─────────────────────────
    cb = CircuitBreaker(failure_threshold=3, recovery_timeout=1.0, probe_successes=2)
    for _ in range(3):
        try:
            cb.call(bad)
        except ConnectionError:
            pass
    called = False

    def sentinel():
        # nonlocal called
        called = True

    try:
        cb.call(sentinel)
    except CircuitOpenError:
        pass
    check("OPEN breaker does not execute the function", not called)

    # ── 5. Breaker moves to HALF_OPEN after recovery timeout ───────────────
    cb = CircuitBreaker(failure_threshold=2, recovery_timeout=0.5, probe_successes=2)
    for _ in range(2):
        try:
            cb.call(bad)
        except ConnectionError:
            pass
    time.sleep(0.6)
    result = cb.call(good)
    check(
        "breaker allows call through after recovery timeout (HALF_OPEN)", result == "ok"
    )

    # ── 6. Failure in HALF_OPEN trips back to OPEN ─────────────────────────
    cb = CircuitBreaker(failure_threshold=2, recovery_timeout=0.5, probe_successes=2)
    for _ in range(2):
        try:
            cb.call(bad)
        except ConnectionError:
            pass
    time.sleep(0.6)
    try:
        cb.call(bad)
    except ConnectionError:
        pass
    open_error_raised = False
    try:
        cb.call(good)
    except CircuitOpenError:
        open_error_raised = True
    check("failure in HALF_OPEN trips back to OPEN", open_error_raised)

    # ── 7. Enough successes in HALF_OPEN closes the breaker ────────────────
    cb = CircuitBreaker(failure_threshold=2, recovery_timeout=0.5, probe_successes=2)
    for _ in range(2):
        try:
            cb.call(bad)
        except ConnectionError:
            pass
    time.sleep(0.6)
    cb.call(good)  # probe 1
    cb.call(good)  # probe 2 — should close
    result = cb.call(good)
    check("breaker closes after enough probe successes", result == "ok")

    # ── 8. A success in CLOSED resets the consecutive failure count ─────────
    cb = CircuitBreaker(failure_threshold=3, recovery_timeout=1.0, probe_successes=2)
    try:
        cb.call(bad)
    except ConnectionError:
        pass
    try:
        cb.call(bad)
    except ConnectionError:
        pass
    cb.call(good)  # reset failure count
    try:
        cb.call(bad)
    except ConnectionError:
        pass
    try:
        cb.call(bad)
    except ConnectionError:
        pass
    result = cb.call(
        good
    )  # should still be closed — only 2 consecutive failures since reset
    check("success in CLOSED resets failure count", result == "ok")

    print(f"\n{sum(results)}/{len(results)} tests passed")
