"""
CRESTA - Challenge 3: LRU Cache (Doubly Linked List + Hashmap)
===============================================================
Implement a Least-Recently-Used (LRU) Cache with O(1) get and put.

The real implementation uses:
  - A Node class with prev/next pointers forming a doubly linked list
  - Two sentinel nodes: self.head (LRU end) and self.tail (MRU end)
  - A hashmap: { key -> Node } for O(1) lookup

                LRU                          MRU
                 |                            |
    head <-> [node] <-> [node] <-> [node] <-> tail
    (dummy)                                (dummy)

The sentinels mean you never have to handle None edge cases when
inserting or removing — there is always a node on both sides.

Key operations you need to implement:
  - _remove(node)         detach a node from wherever it is in the list
  - _insert_at_tail(node) attach a node just before self.tail (MRU position)

  get(key):
    - Miss → return -1
    - Hit  → remove node, reinsert at tail (MRU), return value

  put(key, value):
    - Exists → update value, remove, reinsert at tail (MRU)
    - New    → create node, insert at tail
               if over capacity → evict self.head.next (LRU node),
                                   remove from hashmap too

Rules:
  - get(key)        → value or -1. Marks key as most recently used.
  - put(key, value) → insert or update. Evict LRU if over capacity.
                      Updating an existing key marks it as MRU.
"""


class Node:
    def __init__(self, key: int = 0, value: int = 0) -> None:
        self.key = key
        self.value = value
        self.prev: "Node | None" = None
        self.next: "Node | None" = None


class LRUCache:
    def __init__(self, capacity: int) -> None:
        self.capacity = capacity
        self.cache: dict[int, Node] = {}  # key -> Node

        # Sentinel nodes — never removed, never stored in hashmap
        self.head = Node()  # LRU end  (head.next is the least recently used)
        self.tail = Node()  # MRU end  (tail.prev is the most recently used)
        self.head.next = self.tail
        self.tail.prev = self.head

    def _remove(self, node: Node) -> None:
        """Detach node from the list. YOUR CODE HERE."""
        pass

    def _insert_at_tail(self, node: Node) -> None:
        """Insert node just before self.tail (MRU position). YOUR CODE HERE."""
        pass

    def get(self, key: int) -> int:
        # YOUR CODE HERE
        pass

    def put(self, key: int, value: int) -> None:
        # YOUR CODE HERE
        pass


# ------------------------------------------------------------------
# Tests — run this file directly:  uv run python 03_lru_cache.py
# ------------------------------------------------------------------
if __name__ == "__main__":
    results = []

    def check(label: str, got, expected):
        status = "PASS" if got == expected else "FAIL"
        results.append(status == "PASS")
        print(f"[{status}] {label}: got={got}  expected={expected}")

    # --- scenario 1: from the docstring ---
    c = LRUCache(2)
    c.put(1, 1)
    c.put(2, 2)
    check("get(1) after two puts", c.get(1), 1)
    c.put(3, 3)  # evicts 2
    check("get(2) after eviction", c.get(2), -1)
    c.put(4, 4)  # evicts 1
    check("get(1) after eviction", c.get(1), -1)
    check("get(3) still present", c.get(3), 3)
    check("get(4) still present", c.get(4), 4)

    # --- scenario 2: update refreshes recency ---
    c2 = LRUCache(2)
    c2.put(1, 10)
    c2.put(2, 20)
    c2.put(1, 99)  # update key 1 → should become MRU
    c2.put(3, 30)  # should evict key 2 (LRU), NOT key 1
    check("key 1 updated → not evicted", c2.get(1), 99)
    check("key 2 was LRU → evicted", c2.get(2), -1)
    check("key 3 was just inserted", c2.get(3), 30)

    # --- scenario 3: capacity 1 ---
    c3 = LRUCache(1)
    c3.put(1, 1)
    check("only key present", c3.get(1), 1)
    c3.put(2, 2)  # evicts 1
    check("key 1 evicted", c3.get(1), -1)
    check("key 2 present", c3.get(2), 2)

    # --- scenario 4: get on missing key ---
    c4 = LRUCache(3)
    check("get on empty cache", c4.get(42), -1)

    # --- scenario 5: sequence of gets refreshes order correctly ---
    c5 = LRUCache(3)
    c5.put(1, 1)
    c5.put(2, 2)
    c5.put(3, 3)
    c5.get(1)  # 1 is now MRU → order is 2, 3, 1
    c5.put(4, 4)  # should evict 2 (LRU)
    check("evicts correct LRU after get", c5.get(2), -1)
    check("get-refreshed key survives", c5.get(1), 1)

    passed = sum(results)
    print(f"\n{passed}/{len(results)} tests passed")
