"""LRU (least recently used) cache: keeps at most `capacity` items and, when full,
evicts the item that was used longest ago.

Two implementations, both O(1) for get and put:

1. LRUCacheOrdered: uses OrderedDict, which already remembers order and can move a key to
   the end in O(1). This is the answer to give first in an interview ("use the right tool").
2. LRUCache: dict + doubly linked list, built by hand. This is what interviewers usually ask
   for next ("now without OrderedDict"):
   - The dict maps key -> list node, so a node is found in O(1).
   - The list is ordered from least recent (front) to most recent (back).
   - A node can be removed from the middle in O(1) because it knows both neighbours.
   - Two dummy "sentinel" nodes at the ends remove all the edge cases for an empty list.

Also: lru_memoize, a decorator built on LRUCache (like functools.lru_cache).
"""

import functools
from collections import OrderedDict
from collections.abc import Callable
from typing import Any

_MISSING = object()


class LRUCacheOrdered:
    def __init__(self, capacity: int) -> None:
        if capacity <= 0:
            raise ValueError("capacity must be positive")
        self.capacity = capacity
        self._data: OrderedDict = OrderedDict()

    def get(self, key, default=None):
        if key not in self._data:
            return default
        self._data.move_to_end(key)          # mark as most recently used
        return self._data[key]

    def put(self, key, value) -> None:
        self._data[key] = value
        self._data.move_to_end(key)
        if len(self._data) > self.capacity:
            self._data.popitem(last=False)   # evict the least recently used (front)

    def __len__(self) -> int:
        return len(self._data)


class _Node:
    __slots__ = ("key", "next", "prev", "value")  # many small objects: save memory

    def __init__(self, key=None, value=None) -> None:
        self.key = key
        self.value = value
        self.prev: _Node | None = None
        self.next: _Node | None = None


class LRUCache:
    def __init__(self, capacity: int) -> None:
        if capacity <= 0:
            raise ValueError("capacity must be positive")
        self.capacity = capacity
        self._map: dict[Any, _Node] = {}
        self._head = _Node()  # sentinel before the least recently used node
        self._tail = _Node()  # sentinel after the most recently used node
        self._head.next = self._tail
        self._tail.prev = self._head

    def _unlink(self, node: _Node) -> None:
        node.prev.next = node.next
        node.next.prev = node.prev

    def _append(self, node: _Node) -> None:
        """Insert just before the tail sentinel (= most recently used position)."""
        last = self._tail.prev
        last.next = node
        node.prev = last
        node.next = self._tail
        self._tail.prev = node

    def get(self, key, default=None):
        node = self._map.get(key)
        if node is None:
            return default
        self._unlink(node)
        self._append(node)
        return node.value

    def put(self, key, value) -> None:
        node = self._map.get(key)
        if node is not None:
            node.value = value
            self._unlink(node)
            self._append(node)
            return
        if len(self._map) == self.capacity:
            oldest = self._head.next
            self._unlink(oldest)
            del self._map[oldest.key]   # the node stores its key so we can do this
        node = _Node(key, value)
        self._map[key] = node
        self._append(node)

    def keys_oldest_first(self) -> list:
        out, node = [], self._head.next
        while node is not self._tail:
            out.append(node.key)
            node = node.next
        return out

    def __len__(self) -> int:
        return len(self._map)


def lru_memoize(maxsize: int = 128) -> Callable:
    """Decorator: remember the results of the last `maxsize` distinct calls.

    Arguments must be hashable, because they become the cache key.
    """
    def decorator(fn: Callable) -> Callable:
        cache = LRUCache(maxsize)

        @functools.wraps(fn)  # keep fn's name and docstring
        def wrapper(*args, **kwargs):
            key = (args, tuple(sorted(kwargs.items())))
            result = cache.get(key, _MISSING)
            if result is _MISSING:   # a sentinel, so that a cached None still counts as a hit
                result = fn(*args, **kwargs)
                cache.put(key, result)
            return result

        wrapper.cache = cache
        return wrapper
    return decorator
