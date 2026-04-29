from typing import List, Union
from collections import deque


def flatten(iterable: List[Union[int, List[int]]]):

    flattend = []

    for elem in iterable:
        if isinstance(elem, (set, tuple, list)):
            tmp = []
            search = deque(elem)
            while search:
                next_elem = search.popleft()
                if isinstance(next_elem, (set, tuple, list)):
                    copied = []
                    for inner_elem in next_elem[::-1]:
                        copied.append(inner_elem)
                    search.extendleft(copied)
                elif next_elem is not None:
                    tmp.append(next_elem)
            flattend.extend(tmp)
        elif elem is not None:
            flattend.append(elem)
    return flattend


