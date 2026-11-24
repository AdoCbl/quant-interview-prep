"""Trie (prefix tree): stores strings character by character, so that every word with a
given prefix sits under one node. Lookup is O(length of the word), independent of how many
words are stored.

Uses: autocomplete (e.g. instrument symbols as a trader types), prefix matching, spell checks.
"""


class Trie:
    def __init__(self) -> None:
        self._root: dict = {}
        self._END = "$end"  # marks "a word finishes here"

    def insert(self, word: str) -> None:
        node = self._root
        for ch in word:
            node = node.setdefault(ch, {})
        node[self._END] = True

    def _walk(self, prefix: str) -> dict | None:
        node = self._root
        for ch in prefix:
            node = node.get(ch)
            if node is None:
                return None
        return node

    def contains(self, word: str) -> bool:
        node = self._walk(word)
        return node is not None and self._END in node

    def starts_with(self, prefix: str) -> bool:
        return self._walk(prefix) is not None

    def words_with_prefix(self, prefix: str) -> list[str]:
        node = self._walk(prefix)
        if node is None:
            return []
        out = []
        stack = [(node, prefix)]           # depth-first search without recursion
        while stack:
            node, word = stack.pop()
            if self._END in node:
                out.append(word)
            for ch, child in node.items():
                if ch != self._END:
                    stack.append((child, word + ch))
        return sorted(out)
