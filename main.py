import heapq


def min_meeting_rooms(intervals: list[list[int]]) -> int:
    if not intervals:
        return 0

    intervals.sort()
    heap = []
    max_rooms = 0

    for each_meeting in intervals:
        start, end = each_meeting
        if heap and heap[0] <= start:
            heapq.heappop(heap)

        heapq.heappush(heap, end)
        max_rooms = max(max_rooms, len(heap))

    return max_rooms


if __name__ == "__main__":
    results = []

    def check(label: str, got: int, expected: int) -> None:
        ok = got == expected
        results.append(ok)
        print(f"[{'PASS' if ok else 'FAIL'}] {label}")
        if not ok:
            print(f"       got:      {got!r}")
            print(f"       expected: {expected!r}")

    # No meetings
    # check("empty input", min_meeting_rooms([]), 0)

    # # Single meeting
    # check("single meeting", min_meeting_rooms([[0, 10]]), 1)

    # Two meetings that don't overlap
    check("two non-overlapping meetings", min_meeting_rooms([[7, 10], [2, 4]]), 1)

    # Two meetings that overlap
    check("two overlapping meetings", min_meeting_rooms([[0, 10], [5, 15]]), 2)

    # Classic example — needs 2 rooms
    check("classic example", min_meeting_rooms([[0, 30], [5, 10], [15, 20]]), 2)

    # All meetings at same time — needs N rooms
    check("all overlapping", min_meeting_rooms([[1, 5], [1, 5], [1, 5]]), 3)

    # Meetings back to back — no overlap, 1 room
    check("back to back", min_meeting_rooms([[1, 5], [5, 10], [10, 15]]), 1)

    # Large gap between meetings
    check("large gap", min_meeting_rooms([[0, 5], [100, 200]]), 1)

    # Arrives out of order — tests your sorting
    check("out of order input", min_meeting_rooms([[15, 20], [0, 30], [5, 10]]), 2)

    print(f"\n{sum(results)}/{len(results)} tests passed")
