"""
CRESTA DEBUG - Challenge 2: Fixed-Window Rate Limiter
=====================================================
A colleague wrote this rate limiter. It passes the most obvious "happy path"
tests but has ONE subtle logic bug that causes it to behave incorrectly at
window boundaries.

Your job is to:
  1. Find the bug.
  2. Write a one-line comment above the broken line explaining what is wrong.
  3. Fix it.

Rules reminder:
  - Windows are fixed and aligned to multiples of window_size from epoch 0.
    e.g. window_size=10 → windows are [0,10), [10,20), [20,30) ...
  - Each client tracked independently.
  - At most max_requests per client per window.
  - is_allowed() returns True and consumes a slot, or returns False if over limit.

Run this file to see which tests fail:
    python3 02_buggy_rate_limiter.py
"""


class RateLimiter:
    def __init__(self, max_requests: int, window_size: int) -> None:
        self.max_requests = max_requests
        self.window_size = window_size
        # stores { client_id: (window_start, count) }
        self.clients: dict[str, tuple[int, int]] = {}

    def is_allowed(self, client_id: str, timestamp: int) -> bool:
        current_window = timestamp // self.window_size

        if client_id not in self.clients:
            self.clients[client_id] = (current_window, 1)
            return True

        stored_window, count = self.clients[client_id]

        if stored_window != current_window:
            # New window — reset
            self.clients[client_id] = (current_window, 1)
            return True

        if count < self.max_requests:
            self.clients[client_id] = (stored_window, count + 1)
            return True

        # BUG IS ON THE NEXT LINE
        return True  # <-- something is wrong here


# ------------------------------------------------------------------
# Tests
# ------------------------------------------------------------------
if __name__ == "__main__":
    results = []

    def check(label: str, got: bool, expected: bool):
        status = "PASS" if got == expected else "FAIL"
        results.append(status == "PASS")
        print(f"[{status}] {label}: got={got}  expected={expected}")

    lim = RateLimiter(max_requests=3, window_size=10)
    check("alice t=0  (1/3)", lim.is_allowed("alice", 0), True)
    check("alice t=5  (2/3)", lim.is_allowed("alice", 5), True)
    check("alice t=9  (3/3)", lim.is_allowed("alice", 9), True)
    check("alice t=9  OVER", lim.is_allowed("alice", 9), False)  # <-- should be False
    check("bob   t=9  (1/3)", lim.is_allowed("bob", 9), True)
    check("alice t=10 reset", lim.is_allowed("alice", 10), True)
    check("alice t=19 (2/3)", lim.is_allowed("alice", 15), True)
    check("alice t=19 (3/3)", lim.is_allowed("alice", 19), True)
    check("alice t=19 OVER", lim.is_allowed("alice", 19), False)  # <-- should be False

    lim2 = RateLimiter(max_requests=1, window_size=5)
    check("x t=0  allowed", lim2.is_allowed("x", 0), True)
    check("x t=4  OVER", lim2.is_allowed("x", 4), False)
    check("x t=5  new window", lim2.is_allowed("x", 5), True)
    check("x t=9  OVER", lim2.is_allowed("x", 9), False)

    passed = sum(results)
    print(f"\n{passed}/{len(results)} tests passed")
