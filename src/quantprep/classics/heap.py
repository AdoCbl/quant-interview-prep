"""Binary min-heap built from scratch, plus a top-k helper using the standard heapq module.

A heap is a complete binary tree stored in a list, where every parent <= its children,
so the smallest item is always at index 0.
For the node at index i: children are at 2i+1 and 2i+2, and the parent is at (i-1)//2.

- push: append at the end, then "sift up" (swap with the parent while smaller).  O(log n)
- pop:  move the last item to the root, then "sift down" (swap with the smaller child). O(log n)
- heapify: sift down every non-leaf node from the bottom up. O(n), not O(n log n), because
  most nodes are near the bottom and only move a short distance.

Uses: priority queues, schedulers, merging k sorted streams (e.g. tick files from several
venues), top-k, and running medians (see streaming.py).
"""

import heapq
from collections.abc import Iterable


class MinHeap:
    def __init__(self, items: Iterable = ()) -> None:
        self._a = list(items)
        for i in range(len(self._a) // 2 - 1, -1, -1):  # last parent down to the root
            self._sift_down(i)

    def push(self, x) -> None:
        self._a.append(x)
        self._sift_up(len(self._a) - 1)

    def pop(self):
        if not self._a:
            raise IndexError("pop from empty heap")
        last = self._a.pop()
        if not self._a:
            return last
        top, self._a[0] = self._a[0], last
        self._sift_down(0)
        return top

    def peek(self):
        if not self._a:
            raise IndexError("peek at empty heap")
        return self._a[0]

    def __len__(self) -> int:
        return len(self._a)

    def _sift_up(self, i: int) -> None:
        a = self._a
        while i > 0:
            parent = (i - 1) // 2
            if a[i] < a[parent]:
                a[i], a[parent] = a[parent], a[i]
                i = parent
            else:
                break

    def _sift_down(self, i: int) -> None:
        a, n = self._a, len(self._a)
        while True:
            smallest, left, right = i, 2 * i + 1, 2 * i + 2
            if left < n and a[left] < a[smallest]:
                smallest = left
            if right < n and a[right] < a[smallest]:
                smallest = right
            if smallest == i:
                return
            a[i], a[smallest] = a[smallest], a[i]
            i = smallest


def top_k(items: Iterable, k: int) -> list:
    """The k largest items, largest first, in O(n log k) time and O(k) memory.

    Keep a min-heap of the best k seen so far; its root is the weakest of them, so any new
    item larger than the root replaces it. Works on a stream too large for memory.
    """
    if k <= 0:
        return []
    heap: list = []
    for x in items:
        if len(heap) < k:
            heapq.heappush(heap, x)
        elif x > heap[0]:
            heapq.heapreplace(heap, x)  # pop the root and push x in one step
    return sorted(heap, reverse=True)
