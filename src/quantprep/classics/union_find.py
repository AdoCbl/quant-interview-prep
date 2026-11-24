"""Union-find (also called disjoint-set union): track which items belong to the same group,
with near-constant time per operation.

- find(x):     the representative ("root") of x's group
- union(a, b): merge the groups of a and b
Two tricks give almost O(1) per operation:
- union by size: attach the smaller tree under the larger, so trees stay shallow
- path compression: while finding the root, point visited nodes closer to the root

Uses: connected components (e.g. grouping instruments linked by high correlation), detecting
cycles, Kruskal's minimum spanning tree algorithm.
"""


class UnionFind:
    def __init__(self, n: int) -> None:
        self.parent = list(range(n))
        self.size = [1] * n
        self.groups = n

    def find(self, x: int) -> int:
        while self.parent[x] != x:
            self.parent[x] = self.parent[self.parent[x]]  # path halving: skip a level
            x = self.parent[x]
        return x

    def union(self, a: int, b: int) -> bool:
        """Merge the groups; return False if they were already the same group."""
        ra, rb = self.find(a), self.find(b)
        if ra == rb:
            return False
        if self.size[ra] < self.size[rb]:
            ra, rb = rb, ra
        self.parent[rb] = ra
        self.size[ra] += self.size[rb]
        self.groups -= 1
        return True

    def connected(self, a: int, b: int) -> bool:
        return self.find(a) == self.find(b)
