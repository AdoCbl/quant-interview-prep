"""A dictionary (hash map) built from scratch, using the same broad design as CPython's dict.

Design: "open addressing with linear probing".
- All entries live in one flat table whose size is a power of two.
- To find a key: compute hash(key), take the low bits as the starting slot, and step forward
  one slot at a time until we find the key or an empty slot.
- Deleting leaves a "tombstone" marker instead of emptying the slot. Otherwise a later key that
  had stepped past this slot would become unreachable.
- When the table is two-thirds full (counting tombstones), grow it and re-insert all live keys.
  This keeps chains short, so get/set/delete are O(1) on average.

Interview points:
- Why must keys be hashable and immutable? If a key changes after insertion, its hash changes
  and we would look in the wrong slot, so the entry "disappears".
- Why compare `k is key or k == key`? The identity check is fast and handles objects like NaN
  that are not equal to themselves (Python's dict does the same).
- Alternative design: "separate chaining", where each slot holds a small list of entries.
  It is simpler, but has worse memory locality.
"""

from collections.abc import Iterator
from typing import Any

_EMPTY = object()    # slot never used
_DELETED = object()  # tombstone: slot used before, then deleted


class HashMap:
    _MIN_CAPACITY = 8

    def __init__(self) -> None:
        self._init_table(self._MIN_CAPACITY)

    def _init_table(self, capacity: int) -> None:
        self._keys: list[Any] = [_EMPTY] * capacity
        self._values: list[Any] = [None] * capacity
        self._size = 0   # live entries
        self._used = 0   # live entries + tombstones (both block probing)

    def _find_slot(self, key: Any) -> tuple[int, bool]:
        """Return (slot index, found). If not found, the index is where the key should go."""
        mask = len(self._keys) - 1
        i = hash(key) & mask
        first_tombstone = None
        while True:
            k = self._keys[i]
            if k is _EMPTY:
                return (first_tombstone if first_tombstone is not None else i), False
            if k is _DELETED:
                if first_tombstone is None:
                    first_tombstone = i  # reuse the earliest free slot on insert
            elif k is key or k == key:
                return i, True
            i = (i + 1) & mask  # linear probing; the empty slots guarantee termination

    def _resize(self) -> None:
        old = [(k, v) for k, v in zip(self._keys, self._values) if k is not _EMPTY and k is not _DELETED]
        capacity = self._MIN_CAPACITY
        while capacity < 4 * len(old):  # leave plenty of empty room after growing
            capacity *= 2
        self._init_table(capacity)
        for k, v in old:
            self[k] = v

    def __setitem__(self, key: Any, value: Any) -> None:
        i, found = self._find_slot(key)
        if found:
            self._values[i] = value
            return
        if self._keys[i] is _EMPTY:
            self._used += 1
        self._keys[i] = key
        self._values[i] = value
        self._size += 1
        if 3 * self._used >= 2 * len(self._keys):  # load factor 2/3, as in CPython
            self._resize()

    def __getitem__(self, key: Any) -> Any:
        i, found = self._find_slot(key)
        if not found:
            raise KeyError(key)
        return self._values[i]

    def __delitem__(self, key: Any) -> None:
        i, found = self._find_slot(key)
        if not found:
            raise KeyError(key)
        self._keys[i] = _DELETED
        self._values[i] = None
        self._size -= 1

    def get(self, key: Any, default: Any = None) -> Any:
        i, found = self._find_slot(key)
        return self._values[i] if found else default

    def __contains__(self, key: Any) -> bool:
        return self._find_slot(key)[1]

    def __len__(self) -> int:
        return self._size

    def __iter__(self) -> Iterator[Any]:
        # Order is slot order, not insertion order. CPython keeps a separate
        # insertion-ordered entries array to guarantee insertion order.
        for k in self._keys:
            if k is not _EMPTY and k is not _DELETED:
                yield k

    def items(self) -> Iterator[tuple[Any, Any]]:
        for k, v in zip(self._keys, self._values):
            if k is not _EMPTY and k is not _DELETED:
                yield k, v
