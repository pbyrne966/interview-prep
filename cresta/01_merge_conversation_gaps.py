from typing import List, Tuple


def total_silence_time(snippets: List[Tuple[int, int]]) -> int:
    if not snippets:
        return 0

    snippets = sorted(snippets)

    gaps = 0
    _, current_end = snippets[0]

    for start, end in snippets[1:]:
        if current_end > start:
            current_end = max(current_end, end)
        else:
            gaps += start - current_end
            current_end = end

    return gaps


# ------------------------------------------------------------------
# Tests — run this file directly:  python 01_merge_conversation_gaps.py
# ------------------------------------------------------------------
if __name__ == "__main__":
    test_cases = [
        # (input,                          expected)
        ([(0, 5), (10, 15)], 5),
        ([(0, 10), (3, 7)], 0),
        ([(2, 4), (8, 10), (6, 9)], 2),
        ([], 0),
        ([(5, 5)], 0),
        ([(1, 3), (5, 8), (10, 12)], 4),  # two gaps: [3..5]=2, [8..10]=2
        ([(0, 100)], 0),
        ([(0, 2), (2, 5), (5, 9)], 0),  # back-to-back, no gaps
        ([(10, 20), (0, 5)], 5),  # unsorted input
    ]

    passed = 0
    for i, (inp, expected) in enumerate(test_cases):
        result = total_silence_time(inp)
        status = "PASS" if result == expected else "FAIL"
        if status == "PASS":
            passed += 1
        print(
            f"[{status}] Test {i + 1}: total_silence_time({inp}) = {result}  (expected {expected})"
        )

    print(f"\n{passed}/{len(test_cases)} tests passed")
