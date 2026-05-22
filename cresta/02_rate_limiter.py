import time
from collections import defaultdict, deque
from threading import Lock, Thread


class RateLimiter:
    def __init__(self, max_requests: int, window_size: int) -> None:
        self.max_requests = max_requests
        self.window_size = window_size
        self.requests = defaultdict(deque)
        self.lock = Lock()
        t = Thread(target=self.cleanup, daemon=True)
        t.start()

    def cleanup(self):
        while True:
            with self.lock:
                inactive_users = []

                for k, q in self.requests.items():
                    while q and time.time() - q[0] >= self.window_size:
                        q.popleft()

                    if not q:
                        inactive_users.append(k)

                for user in inactive_users:
                    del self.requests[user]

            time.sleep(self.window_size)

    def is_allowed(self, client_id: str) -> bool:
        current_time = int(time.time())
        with self.lock:
            q = self.requests[client_id]

            while q and current_time - q[0] >= self.window_size:
                q.popleft()

            if len(q) >= self.max_requests:
                return False

            q.append(current_time)
            return True


# ------------------------------------------------------------------
# Tests — run this file directly:  uv run python 02_rate_limiter.py
#
# Your implementation uses a deque of real timestamps internally.
# To control time in tests we monkey-patch time.time on the instance
# via a _now() helper — override that to simulate time passing.
# ------------------------------------------------------------------
if __name__ == "__main__":
    import unittest.mock as mock

    results = []

    def check(label: str, got: bool, expected: bool):
        status = "PASS" if got == expected else "FAIL"
        results.append(status == "PASS")
        print(f"[{status}] {label}: got={got}  expected={expected}")

    # --- scenario 1: basic window behaviour (window_size=10) ---
    # Patch time.time so we control the clock
    with mock.patch("time.time", return_value=0):
        lim = RateLimiter(max_requests=3, window_size=10)
        check("alice (1/3)", lim.is_allowed("alice"), True)
        check("alice (2/3)", lim.is_allowed("alice"), True)
        check("alice (3/3)", lim.is_allowed("alice"), True)
        check("alice OVER", lim.is_allowed("alice"), False)
        check("bob   (1/3)", lim.is_allowed("bob"), True)

    with mock.patch("time.time", return_value=10):  # advance past window
        check("alice reset", lim.is_allowed("alice"), True)
        check("alice (2/3)", lim.is_allowed("alice"), True)
        check("alice (3/3)", lim.is_allowed("alice"), True)
        check("alice OVER", lim.is_allowed("alice"), False)

    # --- scenario 2: window boundary (window_size=5) ---
    with mock.patch("time.time", return_value=0):
        lim2 = RateLimiter(max_requests=1, window_size=5)
        check("x (1/1)", lim2.is_allowed("x"), True)
        check("x OVER", lim2.is_allowed("x"), False)

    with mock.patch("time.time", return_value=5):
        check("x new window", lim2.is_allowed("x"), True)
        check("x OVER again", lim2.is_allowed("x"), False)

    # --- scenario 3: large gap (many windows elapsed) ---
    with mock.patch("time.time", return_value=0):
        lim3 = RateLimiter(max_requests=2, window_size=60)
        check("y (1/2)", lim3.is_allowed("y"), True)
        check("y (2/2)", lim3.is_allowed("y"), True)
        check("y OVER", lim3.is_allowed("y"), False)

    with mock.patch("time.time", return_value=60000):  # huge jump
        check("y big jump reset", lim3.is_allowed("y"), True)

    # --- scenario 4: multiple independent clients ---
    with mock.patch("time.time", return_value=0):
        lim4 = RateLimiter(max_requests=2, window_size=10)
        check("a (1/2)", lim4.is_allowed("a"), True)
        check("b (1/2)", lim4.is_allowed("b"), True)
        check("a (2/2)", lim4.is_allowed("a"), True)
        check("b (2/2)", lim4.is_allowed("b"), True)
        check("a OVER", lim4.is_allowed("a"), False)
        check("b OVER", lim4.is_allowed("b"), False)

    passed = sum(results)
    print(f"\n{passed}/{len(results)} tests passed")
