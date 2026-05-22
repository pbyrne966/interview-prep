"""
CRESTA DEBUG - Challenge 5: Top-K Frequent Words
=================================================
A colleague implemented top_k_frequent. It almost works — it correctly
handles the frequency ordering but has ONE bug in the tiebreaker sort that
makes it return words in the WRONG alphabetical direction when frequencies
are equal.

Your job is to:
  1. Find the bug.
  2. Write a one-line comment above the broken line explaining what is wrong.
  3. Fix it.

Rules reminder:
  - Sort by frequency DESCENDING.
  - Tiebreak alphabetically ASCENDING (so "apple" beats "banana").

Run this file to see which tests fail:
    python3 05_buggy_top_k.py
"""

from collections import Counter


def top_k_frequent(words: list[str], k: int) -> list[str]:
    counts = Counter(words)
    # BUG IS ON THE NEXT LINE — the sort key is almost right, but one sign is wrong
    sorted_words = sorted(
        counts.keys(), key=lambda w: (-counts[w], ord(w[0]))
    )  # <-- look at the tiebreaker
    return sorted_words[:k]


# ------------------------------------------------------------------
# Tests
# ------------------------------------------------------------------
if __name__ == "__main__":
    results = []

    def check(label: str, got, expected):
        status = "PASS" if got == expected else "FAIL"
        results.append(status == "PASS")
        print(f"[{status}] {label}: got={got}  expected={expected}")

    check(
        "example 1 — tiebreak 'is' before 'the'",
        top_k_frequent(
            ["the", "day", "is", "sunny", "the", "the", "sunny", "is", "is"], 4
        ),
        ["is", "the", "sunny", "day"],
    )
    check(
        "example 2 — cresta: 'i' before 'love'",
        top_k_frequent(["i", "love", "cresta", "i", "love", "cresta", "cresta"], 2),
        ["cresta", "i"],
    )
    check(
        "all same freq, k=1 → 'a' first",
        top_k_frequent(["a", "b", "c"], 1),
        ["a"],
    )
    check(
        "all same freq, k=3 → alphabetical",
        top_k_frequent(["z", "m", "a", "a", "z", "m"], 3),
        ["a", "m", "z"],
    )
    check(
        "tiebreak: 'cat' before 'dog' before 'fish'",
        top_k_frequent(["cat", "dog", "cat", "fish"], 3),
        ["cat", "dog", "fish"],
    )
    check(
        "agent/resolution/customer tiebreak",
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
        ["agent", "resolution"],
    )

    passed = sum(results)
    print(f"\n{passed}/{len(results)} tests passed")
