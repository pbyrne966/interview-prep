"""
CRESTA - Challenge 5: Top-K Frequent Words in Conversation
===========================================================
Context: Cresta analyses conversation transcripts to surface insights —
for example, identifying the most frequently mentioned topics or keywords.

Given a list of words, return the k most frequent words sorted by:
  1. Frequency — descending (higher count first)
  2. Alphabetical order — ascending, as a tiebreaker (so "apple" before "banana")

The input words are all lowercase.

Function signature:
    def top_k_frequent(words: list[str], k: int) -> list[str]

Args:
    words: A list of lowercase strings.
    k:     The number of top results to return. Guaranteed 1 <= k <= len(set(words)).

Returns:
    A list of k words satisfying the ordering rules above.

Examples:
    words = ["the", "day", "is", "sunny", "the", "the", "sunny", "is", "is"]
    k = 4
    → Frequencies: "the":3, "is":3, "sunny":2, "day":1
    → Sorted: ["is", "the", "sunny", "day"]   ← "is" < "the" alphabetically at freq=3
    → return ["is", "the", "sunny", "day"]

    words = ["i", "love", "cresta", "i", "love", "cresta", "cresta"]
    k = 2
    → Frequencies: "cresta":3, "i":2, "love":2
    → Top 2: "cresta" (3), then "i" beats "love" alphabetically at freq=2
    → return ["cresta", "i"]

    words = ["a", "b", "c"]
    k = 1
    → All freq=1; alphabetical → "a" first
    → return ["a"]

Hint: Think about how to sort a list of (word, count) tuples so that
     higher count AND lower alphabetical both float to the top.
     A sort key of (-count, word) does both in one pass.
"""

import heapq
from collections import Counter


def top_k_frequent(words: list[str], k: int) -> list[str]:
    freq = Counter(words)
    return heapq.nsmallest(k, freq.keys(), key=lambda w: (-freq[w], w))


# ------------------------------------------------------------------
# Tests — run this file directly:  python 05_top_k_frequent_words.py
# ------------------------------------------------------------------
if __name__ == "__main__":
    results = []

    def check(label: str, got, expected):
        status = "PASS" if got == expected else "FAIL"
        results.append(status == "PASS")
        print(f"[{status}] {label}: got={got}  expected={expected}")

    check(
        "example 1",
        top_k_frequent(
            ["the", "day", "is", "sunny", "the", "the", "sunny", "is", "is"], 4
        ),
        ["is", "the", "sunny", "day"],
    )
    check(
        "example 2 — cresta",
        top_k_frequent(["i", "love", "cresta", "i", "love", "cresta", "cresta"], 2),
        ["cresta", "i"],
    )
    check(
        "all same freq, k=1",
        top_k_frequent(["a", "b", "c"], 1),
        ["a"],
    )
    check(
        "all same freq, k=3",
        top_k_frequent(["z", "m", "a", "a", "z", "m"], 3),
        ["a", "m", "z"],
    )
    check(
        "single word",
        top_k_frequent(["hello"], 1),
        ["hello"],
    )
    check(
        "k equals total unique",
        top_k_frequent(["cat", "dog", "cat", "fish"], 3),
        ["cat", "dog", "fish"],
    )
    check(
        "long list, k=2",
        top_k_frequent(
            [
                "agent",
                "customer",
                "agent",
                "agent",
                "customer",
                "resolution",
                "agent",
                "customer",
                "resolution",
                "resolution",
            ],
            2,
        ),
        [
            "agent",
            "customer",
        ],  # agent:4, customer:3, resolution:3 → alpha tiebreak: 'customer' < 'resolution'
    )

    passed = sum(results)
    print(f"\n{passed}/{len(results)} tests passed")
