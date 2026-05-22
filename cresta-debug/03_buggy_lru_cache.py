"""
CRESTA DEBUG - Challenge 3: LRU Cache
======================================
A colleague implemented an LRU Cache using OrderedDict. The code looks
reasonable and passes basic get/put tests — but there is ONE bug that causes
incorrect eviction behaviour when an existing key is updated via put().

Your job is to:
  1. Find the bug.
  2. Write a one-line comment above the broken line explaining what is wrong.
  3. Fix it.

Rules reminder:
  - get(key)        → return value or -1. Marks key as most-recently used.
  - put(key, value) → insert or update. If over capacity, evict LRU item.
                      Updating an existing key marks it as most-recently used.

Run this file to see which tests fail:
    python3 03_buggy_lru_cache.py
"""

from collections import OrderedDict


class LRUCache:
    def __init__(self, capacity: int) -> None:
        self.capacity = capacity
        self.cache: OrderedDict = OrderedDict()

    def get(self, key: int) -> int:
        if key not in self.cache:
            return -1
        self.cache.move_to_end(key)  # mark as most-recently used
        return self.cache[key]

    def put(self, key: int, value: int) -> None:
        if key in self.cache:
            # BUG IS ON THE NEXT LINE — update the value but forget something
            self.cache[key] = value  # <-- something is missing here
        else:
            self.cache[key] = value
            if len(self.cache) > self.capacity:
                self.cache.popitem(last=False)  # evict LRU (front of OrderedDict)


# ------------------------------------------------------------------
# Tests
# ------------------------------------------------------------------
if __name__ == "__main__":
    results = []

    def check(label: str, got, expected):
        status = "PASS" if got == expected else "FAIL"
        results.append(status == "PASS")
        print(f"[{status}] {label}: got={got}  expected={expected}")

    # basic scenario
    c = LRUCache(2)
    c.put(1, 1)
    c.put(2, 2)
    check("get(1)", c.get(1), 1)
    c.put(3, 3)  # should evict key 2 (LRU), not key 1
    check("get(2) evicted", c.get(2), -1)
    c.put(4, 4)  # should evict key 1
    check("get(1) evicted", c.get(1), -1)
    check("get(3) present", c.get(3), 3)
    check("get(4) present", c.get(4), 4)

    # THE FAILING SCENARIO: updating a key must refresh its recency
    c2 = LRUCache(2)
    c2.put(1, 10)
    c2.put(2, 20)
    c2.put(1, 99)  # update key 1 → should become MRU
    c2.put(3, 30)  # should evict key 2 (LRU), NOT key 1
    check("key 1 updated, not evicted", c2.get(1), 99)
    check("key 2 was LRU, evicted", c2.get(2), -1)
    check("key 3 just inserted", c2.get(3), 30)

    # capacity 1
    c3 = LRUCache(1)
    c3.put(1, 1)
    check("cap=1 get(1)", c3.get(1), 1)
    c3.put(2, 2)
    check("cap=1 evict 1", c3.get(1), -1)
    check("cap=1 get(2)", c3.get(2), 2)

    # missing key
    c4 = LRUCache(3)
    check("missing key", c4.get(99), -1)

    passed = sum(results)
    print(f"\n{passed}/{len(results)} tests passed")
