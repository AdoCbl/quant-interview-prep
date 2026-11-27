# Data Structures and Algorithms

Coding-interview patterns with one short template each, worked problems (several with a trading
flavour), and the complexity facts you need to justify a solution. Each term is explained the first
time it appears; a glossary is at the end.

Every code block runs on its own (`uv run python file.py`); the comments show its output. The same
patterns in C++, with the standard library and its pitfalls, are in [cpp.md](cpp.md). Related
pages: tested from-scratch structures (hash map, heap, LRU cache, union-find, trie, running median,
binary search) are in [Python, section 12](../python/README.md#12-classic-implementations-with-code);
a tested limit order book is in
[`src/quantprep/systems/order_book.py`](../../src/quantprep/systems/order_book.py).

Contents:

1. [How to run a coding interview](#1-how-to-run-a-coding-interview)
2. [Complexity in one page](#2-complexity-in-one-page)
3. [Pattern picker](#3-pattern-picker)
4. [Arrays: two pointers, sliding window, prefix sums](#4-arrays-two-pointers-sliding-window-prefix-sums)
5. [Stacks, heaps and hashing](#5-stacks-heaps-and-hashing)
6. [Graphs](#6-graphs)
7. [Intervals and binary search on the answer](#7-intervals-and-binary-search-on-the-answer)
8. [Dynamic programming and backtracking](#8-dynamic-programming-and-backtracking)
9. [Trading-flavoured problems](#9-trading-flavoured-problems)
10. [Python and C++ containers side by side](#10-python-and-c-containers-side-by-side)
11. [Interview questions](#11-interview-questions)
12. [Glossary](#12-glossary)

---

## 1. How to run a coding interview

1. **Restate and ask.** Input size? Sorted? Duplicates? Negative numbers? Empty input? What should be returned when there is no answer?
2. **Give a small example by hand**, including one edge case.
3. **State the brute force and its cost** ("check every pair: O(n²)"). This shows you can always deliver something.
4. **Improve it** by naming the pattern (section 3) and the new cost. Agree on it before you type.
5. **Code it cleanly**: clear names, small helper functions, no premature tricks.
6. **Test out loud**: walk the example through the code, then the edge cases (empty, one element, all equal, very large).
7. **State the final time and space cost**, and one way it could be extended (streaming input, many queries, multiple threads).

The interviewer scores communication as much as the code. Silence for five minutes is worse than a slower solution explained clearly.

---

## 2. Complexity in one page

**Big-O** describes how running time (or memory) grows with input size n, ignoring constant factors. **Amortised** O(1) means a single call can be slow but the average over many calls is O(1) (e.g. `list.append`, which occasionally copies the whole list to a bigger buffer).

**What fits in about one second** (roughly 10⁷–10⁸ simple steps in C++, 10⁶–10⁷ in pure Python):

| n up to | Acceptable cost | Typical algorithm |
|---|---|---|
| 10–12 | O(n!) | All permutations |
| 20–25 | O(2ⁿ) | All subsets, bitmask DP |
| 500 | O(n³) | Triple loop, Floyd-Warshall |
| 5,000 | O(n²) | Double loop, simple DP |
| 10⁶ | O(n log n) | Sort, heap, binary search per item |
| 10⁸ | O(n) | One pass |
| any | O(log n) or O(1) | Binary search, formula |

**Costs of Python built-ins**:

| Operation | Cost | Note |
|---|---|---|
| `list.append`, `list.pop()` | O(1) amortised | End of the list only |
| `list.insert(0, x)`, `list.pop(0)` | O(n) | Use `collections.deque` instead (O(1) at both ends) |
| `x in list` | O(n) | Use a `set` (O(1) on average) |
| `dict` / `set` get, set, delete | O(1) on average | O(n) in the worst case (many collisions) |
| `sorted`, `list.sort` | O(n log n) | Stable: equal items keep their order |
| `heapq.heappush` / `heappop` | O(log n) | Min-heap; push `-x` for a max-heap |
| `heapq.heapify` | O(n) | Faster than n pushes |
| `bisect.bisect_left` | O(log n) | But `insort` is O(n) because the list shifts |
| `s1 + s2` on strings in a loop | O(n²) total | Collect parts in a list, then `"".join(parts)` |

**Recursion cost formula (master theorem).** T(n) = a·T(n/b) + O(nᵈ), where:

- `a` = number of recursive calls made at each step,
- `b` = factor by which the input shrinks in each call (each call gets size n/b),
- `d` = exponent of the extra work done outside the calls (splitting and combining).

`a` and `b` are separate because the calls need not split the input into disjoint pieces. A call can ignore part of the input (binary search: 1 call on half, so a = 1, b = 2), or several calls can work on overlapping or derived inputs of the same size (Karatsuba multiplication: 3 calls on half-size numbers, so a = 3, b = 2). Only when the input is cut into equal, disjoint pieces that are all processed is a = b (merge sort).

Compare d with the critical exponent log_b a. The number of subproblems grows by a factor of a per level, and the work per subproblem shrinks by a factor of bᵈ:

- d > log_b a: the top level dominates, so T(n) = O(nᵈ).
- d = log_b a: every level costs the same, and there are log_b n levels, so T(n) = O(nᵈ log n).
- d < log_b a: the leaves dominate (there are a^(log_b n) = n^(log_b a) of them), so T(n) = O(n^(log_b a)).

| Algorithm | a | b | d | log_b a | Case | Cost |
|---|---|---|---|---|---|---|
| Binary search | 1 | 2 | 0 | 0 | equal | O(log n) |
| Merge sort | 2 | 2 | 1 | 1 | equal | O(n log n) |
| Tree traversal (balanced) | 2 | 2 | 0 | 1 | leaves | O(n) |
| Karatsuba multiplication | 3 | 2 | 1 | 1.585 | leaves | O(n^1.585) |
| Strassen matrix multiply | 7 | 2 | 2 | 2.807 | leaves | O(n^2.807) |
| Quickselect (good pivots) | 1 | 2 | 1 | 0 | top | O(n) |

The theorem needs subproblems of *equal* size n/b. Quicksort with a random pivot does not fit it directly; its O(n log n) expected cost comes from a separate argument.

---

## 3. Pattern picker

| If the problem says or implies... | Try | Usual cost |
|---|---|---|
| Sorted array, find a pair or triple | Two pointers from both ends | O(n) |
| Best contiguous run / substring with a condition | Sliding window | O(n) |
| Sum of a subarray, many range-sum queries | Prefix sums (+ hash map of seen sums) | O(n) |
| "Have I seen this before?", counting, grouping | Hash map / set | O(n) |
| Next greater / smaller element, spans | Monotonic stack | O(n) |
| Top k, k-th largest, merge k sorted lists, scheduling | Heap | O(n log k) |
| Sorted data, or a yes/no test that flips once as a number grows | Binary search | O(log n) per search |
| Shortest path, fewest steps, unweighted | Breadth-first search (BFS) | O(V + E) |
| Connected regions, all paths, cycle detection | Depth-first search (DFS) | O(V + E) |
| Order with dependencies | Topological sort | O(V + E) |
| Shortest path with weights ≥ 0 | Dijkstra | O(E log V) |
| Negative weights, or "is there a profitable cycle?" | Bellman-Ford | O(V·E) |
| Groups that merge over time | Union-find | almost O(1) per operation |
| Overlapping ranges, meetings, sessions | Sort by start, then sweep | O(n log n) |
| "Number of ways", "min / max cost", choices that overlap | Dynamic programming | states × choices |
| "List all" combinations, permutations, placements | Backtracking | exponential |

V = number of vertices (nodes), E = number of edges.

---

## 4. Arrays: two pointers, sliding window, prefix sums

- **Two pointers**: one index at each end of a sorted array, move the one that brings you closer to the target. Each step discards a whole row of pairs, so O(n) instead of O(n²).
- **Sliding window**: grow the right edge each step; shrink the left edge only while the window breaks the rule. Each index enters and leaves once: O(n).
- **Prefix sums**: P[i] = a[0] + ... + a[i−1], so sum(a[i:j]) = P[j] − P[i]. "Subarray sums to k" becomes "have I seen P[j] − k before?", answered by a hash map.
- **Kadane's algorithm** (best subarray sum): the best run ending at i is either a[i] alone or a[i] added to the best run ending at i−1.

```python
from collections import defaultdict
from itertools import pairwise


def two_sum_sorted(a: list[int], target: int) -> tuple[int, int] | None:
    i, j = 0, len(a) - 1
    while i < j:
        s = a[i] + a[j]
        if s == target:
            return i, j
        if s < target:
            i += 1          # need a bigger sum
        else:
            j -= 1          # need a smaller sum
    return None


def longest_unique_run(s: str) -> int:
    """Length of the longest substring with no repeated character (sliding window)."""
    last: dict[str, int] = {}
    best = start = 0
    for i, ch in enumerate(s):
        if last.get(ch, -1) >= start:   # repeat inside the window: move the left edge past it
            start = last[ch] + 1
        last[ch] = i
        best = max(best, i - start + 1)
    return best


def count_subarrays_with_sum(a: list[int], k: int) -> int:
    """Prefix sums + hash map. Works with negative numbers, unlike a sliding window."""
    seen = defaultdict(int, {0: 1})     # prefix sum -> how many times seen
    total = count = 0
    for x in a:
        total += x
        count += seen[total - k]
        seen[total] += 1
    return count


def max_subarray(a: list[float]) -> float:
    """Kadane: best sum of a contiguous run."""
    best = cur = a[0]
    for x in a[1:]:
        cur = max(x, cur + x)
        best = max(best, cur)
    return best


def max_profit(prices: list[float]) -> float:
    """One buy then one sell: track the lowest price so far."""
    low, best = prices[0], 0.0
    for p in prices[1:]:
        best = max(best, p - low)
        low = min(low, p)
    return best


def max_drawdown(prices: list[float]) -> float:
    """Largest fall from a running peak, as a fraction. Same shape as max_profit."""
    peak, worst = prices[0], 0.0
    for p in prices:
        peak = max(peak, p)
        worst = max(worst, 1 - p / peak)
    return worst


prices = [100, 104, 98, 95, 103, 110, 99, 107]
print(two_sum_sorted([1, 3, 4, 6, 8, 11], 10))      # (2, 3)
print(longest_unique_run("abcabcbb"))               # 3
print(count_subarrays_with_sum([1, 2, -1, 2, 1, -2, 3], 3))  # 6
print(max_subarray([d - u for u, d in pairwise(prices)]))  # 15
print(max_profit(prices))                           # 15
print(f"{max_drawdown(prices):.4f}")                # 0.1000
```

The `max_subarray` line shows a useful fact: the best single trade equals the best run of daily price changes.

---

## 5. Stacks, heaps and hashing

- **Stack** (last in, first out): matching brackets, undo, evaluating expressions, DFS without recursion.
- **Monotonic stack**: a stack kept in increasing or decreasing order. When a new item breaks the order, pop items and record that the new item is their "next greater" element. Each index is pushed and popped once: O(n).
- **Heap**: a tree in a list where the parent is never larger than its children, so the minimum is at index 0. Keep a heap of size k to track the k largest of a stream in O(n log k).
- **Hash map + array**: the array gives O(1) access by position; the map gives O(1) lookup of position by value. Together they support O(1) insert, delete and pick-at-random.

```python
import heapq
import random
from collections import Counter


def is_balanced(s: str) -> bool:
    pairs = {")": "(", "]": "[", "}": "{"}
    stack: list[str] = []
    for ch in s:
        if ch in "([{":
            stack.append(ch)
        elif ch in pairs and (not stack or stack.pop() != pairs[ch]):
            return False
    return not stack


def days_until_higher(prices: list[float]) -> list[int]:
    """For each day, days to wait for a strictly higher price (0 if never). Monotonic stack."""
    out = [0] * len(prices)
    stack: list[int] = []               # indices still waiting; their prices are decreasing
    for i, p in enumerate(prices):
        while stack and prices[stack[-1]] < p:
            j = stack.pop()
            out[j] = i - j
        stack.append(i)
    return out


def kth_largest(a: list[int], k: int) -> int:
    heap: list[int] = []                # min-heap of the k largest seen so far
    for x in a:
        heapq.heappush(heap, x)
        if len(heap) > k:
            heapq.heappop(heap)         # drop the smallest of the k + 1
    return heap[0]


class RandomizedSet:
    """O(1) insert, remove and get_random."""

    def __init__(self) -> None:
        self.items: list[int] = []
        self.pos: dict[int, int] = {}

    def insert(self, x: int) -> bool:
        if x in self.pos:
            return False
        self.pos[x] = len(self.items)
        self.items.append(x)
        return True

    def remove(self, x: int) -> bool:
        if x not in self.pos:
            return False
        i, last = self.pos.pop(x), self.items.pop()
        if i < len(self.items):         # move the last item into the hole
            self.items[i], self.pos[last] = last, i
        return True

    def get_random(self, rng: random.Random) -> int:
        return rng.choice(self.items)


print(is_balanced("{[()()]}"), is_balanced("([)]"))         # True False
print(days_until_higher([73, 74, 75, 71, 69, 72, 76, 73]))  # [1, 1, 4, 2, 1, 1, 0, 0]
print(kth_largest([3, 2, 1, 5, 6, 4], 2))                   # 5
trades = ["AAPL", "MSFT", "AAPL", "TSLA", "AAPL", "MSFT"]
print(Counter(trades).most_common(2))                       # [('AAPL', 3), ('MSFT', 2)]

# Merge already-sorted streams (e.g. per-venue tick files) in O(n log k)
venue_a = [(1, "A", 100.0), (4, "A", 100.2)]
venue_b = [(2, "B", 100.1), (3, "B", 100.1), (5, "B", 100.3)]
print([t for t, _, _ in heapq.merge(venue_a, venue_b)])     # [1, 2, 3, 4, 5]

s = RandomizedSet()
for x in (10, 20, 30):
    s.insert(x)
s.remove(10)
print(sorted(s.items), s.get_random(random.Random(0)) in {20, 30})  # [20, 30] True
```

---

## 6. Graphs

A **graph** is a set of nodes joined by edges. Store it as an **adjacency list**: `dict[node, list[neighbour]]`.

- **BFS** visits nodes in rings of distance 1, 2, 3, ... using a queue, so the first time it reaches a node is by a shortest path (when every edge costs the same).
- **DFS** goes as deep as possible first, using a stack or recursion. Use it to explore regions or detect cycles. Python's recursion limit is about 1,000, so use an explicit stack on big inputs.
- **Topological sort** (Kahn's algorithm): repeatedly take a node with no unfinished prerequisites. If some nodes are never taken, there is a cycle.
- **Dijkstra**: like BFS but with a heap ordered by distance so far. Correct only when all edge weights are ≥ 0.
- **Bellman-Ford**: relax every edge V − 1 times. If an edge can still be improved after that, there is a **negative cycle**. With weight −log(rate), a cycle whose rates multiply to more than 1 has negative total weight, so this finds **currency arbitrage**.

```python
import heapq
import math
from collections import deque


def shortest_path_grid(grid: list[str], start: tuple[int, int], goal: tuple[int, int]) -> int:
    """Fewest steps through '.' cells (BFS). -1 if unreachable."""
    rows, cols = len(grid), len(grid[0])
    dist = {start: 0}
    queue = deque([start])
    while queue:
        r, c = queue.popleft()
        if (r, c) == goal:
            return dist[r, c]
        for nr, nc in ((r + 1, c), (r - 1, c), (r, c + 1), (r, c - 1)):
            if 0 <= nr < rows and 0 <= nc < cols and grid[nr][nc] == "." and (nr, nc) not in dist:
                dist[nr, nc] = dist[r, c] + 1
                queue.append((nr, nc))
    return -1


def count_islands(grid: list[str]) -> int:
    """Connected groups of '#' cells (DFS with an explicit stack)."""
    seen: set[tuple[int, int]] = set()
    islands = 0
    for r0, row in enumerate(grid):
        for c0, cell in enumerate(row):
            if cell != "#" or (r0, c0) in seen:
                continue
            islands += 1
            stack = [(r0, c0)]
            seen.add((r0, c0))
            while stack:
                r, c = stack.pop()
                for nr, nc in ((r + 1, c), (r - 1, c), (r, c + 1), (r, c - 1)):
                    if (0 <= nr < len(grid) and 0 <= nc < len(row)
                            and grid[nr][nc] == "#" and (nr, nc) not in seen):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
    return islands


def topo_order(needs: dict[str, list[str]]) -> list[str]:
    """needs[x] = jobs that must finish before x. Raises on a cycle."""
    waiting = {job: len(pre) for job, pre in needs.items()}
    unlocks: dict[str, list[str]] = {job: [] for job in needs}
    for job, pre in needs.items():
        for p in pre:
            unlocks[p].append(job)
    ready = deque(job for job, n in waiting.items() if n == 0)
    order = []
    while ready:
        job = ready.popleft()
        order.append(job)
        for nxt in unlocks[job]:
            waiting[nxt] -= 1
            if waiting[nxt] == 0:
                ready.append(nxt)
    if len(order) != len(needs):
        raise ValueError("dependency cycle")
    return order


def dijkstra(graph: dict[str, list[tuple[str, float]]], src: str) -> dict[str, float]:
    dist = {src: 0.0}
    heap = [(0.0, src)]
    while heap:
        d, u = heapq.heappop(heap)
        if d > dist[u]:
            continue                    # stale entry: a shorter path was already found
        for v, w in graph[u]:
            if d + w < dist.get(v, math.inf):
                dist[v] = d + w
                heapq.heappush(heap, (d + w, v))
    return dist


def has_arbitrage(rates: dict[tuple[str, str], float]) -> bool:
    """Bellman-Ford on weight -log(rate): a negative cycle means a profitable loop."""
    nodes = {c for pair in rates for c in pair}
    dist = dict.fromkeys(nodes, 0.0)    # start from every node at once
    edges = [(a, b, -math.log(r)) for (a, b), r in rates.items()]
    for _ in range(len(nodes) - 1):
        for a, b, w in edges:
            dist[b] = min(dist[b], dist[a] + w)
    return any(dist[a] + w < dist[b] - 1e-12 for a, b, w in edges)


maze = ["..#.",
        ".##.",
        "...."]
print(shortest_path_grid(maze, (0, 0), (0, 3)))    # 7
print(count_islands(["##..", "#..#", "..##", "#..."]))  # 3
print(topo_order({"fixings": [], "ois_curve": ["fixings"], "fx": [],
                  "swap_pv": ["ois_curve"], "risk": ["swap_pv", "fx"]}))
# ['fixings', 'fx', 'ois_curve', 'swap_pv', 'risk']
latency_us = {"NY": [("CHI", 7.0), ("LDN", 30.0)], "CHI": [("LDN", 35.0), ("TKY", 70.0)],
              "LDN": [("TKY", 45.0)], "TKY": []}
print(dijkstra(latency_us, "NY"))   # {'NY': 0.0, 'CHI': 7.0, 'LDN': 30.0, 'TKY': 75.0}
fx = {("USD", "EUR"): 0.90, ("EUR", "GBP"): 0.86, ("GBP", "USD"): 1.30,
      ("EUR", "USD"): 1.10, ("GBP", "EUR"): 1.15, ("USD", "GBP"): 0.76}
print(has_arbitrage(fx), round(0.90 * 0.86 * 1.30, 4))     # True 1.0062
```

Why not Dijkstra for arbitrage: −log(rate) is negative whenever rate > 1, and Dijkstra assumes a node's distance is final once popped, which negative edges break.

---

## 7. Intervals and binary search on the answer

- **Intervals**: sort by start time, then sweep left to right. Two intervals overlap when the next one starts before the current one ends.
- **How many run at once** (meeting rooms, open orders, servers needed): keep a min-heap of end times. Before adding an interval, pop every interval that has already ended. The largest heap size is the answer.
- **Binary search on the answer**: when the question is "the smallest X such that a test passes" and the test only flips once (false, false, ..., true, true), binary-search X. Cost = O(log(range) × cost of one test).

```python
import heapq


def merge_intervals(iv: list[tuple[int, int]]) -> list[tuple[int, int]]:
    out: list[tuple[int, int]] = []
    for s, e in sorted(iv):
        if out and s <= out[-1][1]:
            out[-1] = (out[-1][0], max(out[-1][1], e))
        else:
            out.append((s, e))
    return out


def max_concurrent(iv: list[tuple[int, int]]) -> int:
    ends: list[int] = []
    best = 0
    for s, e in sorted(iv):
        while ends and ends[0] <= s:    # finished before this one starts
            heapq.heappop(ends)
        heapq.heappush(ends, e)
        best = max(best, len(ends))
    return best


def min_daily_capacity(orders: list[int], days: int) -> int:
    """Smallest daily volume cap that fills the orders, in sequence, within `days`."""
    def fits(cap: int) -> bool:
        used, load = 1, 0
        for q in orders:
            if load + q > cap:          # start a new day
                used, load = used + 1, 0
            load += q
        return used <= days

    lo, hi = max(orders), sum(orders)   # answer lies in [lo, hi]
    while lo < hi:
        mid = (lo + hi) // 2
        if fits(mid):
            hi = mid                    # mid works; try smaller
        else:
            lo = mid + 1
    return lo


print(merge_intervals([(1, 3), (8, 10), (2, 6), (15, 18), (17, 20)]))  # [(1, 6), (8, 10), (15, 20)]
print(max_concurrent([(0, 30), (5, 10), (15, 20), (25, 35)]))        # 2
print(min_daily_capacity([1, 2, 3, 4, 5, 6, 7, 8, 9, 10], 5))        # 15
```

---

## 8. Dynamic programming and backtracking

**Dynamic programming (DP)** works when the answer is built from answers to smaller versions of the same problem, and those smaller problems repeat. Four steps:

1. **State**: what does `dp[i]` (or `dp[i][j]`) mean, in words?
2. **Transition**: the formula from smaller states.
3. **Base case**: the smallest states, set directly.
4. **Order**: fill states so every input is ready when needed. Cost = number of states × cost per transition.

Top-down (a recursive function with `@functools.cache`) and bottom-up (a loop over a table) give the same answer; bottom-up avoids the recursion limit and often lets you keep only the last row.

| Problem | State | Transition | Cost |
|---|---|---|---|
| Coin change (fewest coins to make `a`) | `dp[a]` | `dp[a] = 1 + min(dp[a − c])` over coins c | O(amount × coins) |
| Longest increasing subsequence | `tails[k]` = smallest tail of a run of length k+1 | binary-search where x goes | O(n log n) |
| Edit distance (insert, delete, replace) | `dp[i][j]` for prefixes `s[:i]`, `t[:j]` | `min(dp[i−1][j]+1, dp[i][j−1]+1, dp[i−1][j−1] + (s[i−1] ≠ t[j−1]))` | O(n·m) |
| 0/1 knapsack (pick items under a budget) | `dp[b]` = best value with budget b | `dp[b] = max(dp[b], dp[b − cost] + value)`, b looping **down** | O(n × budget) |

**Backtracking** builds a candidate step by step, and undoes the last step ("backtracks") when it cannot lead to a valid answer. Sort the input first so you can stop early.

```python
from bisect import bisect_left
from functools import cache


def coin_change(coins: list[int], amount: int) -> int:
    inf = amount + 1
    dp = [0] + [inf] * amount
    for a in range(1, amount + 1):
        dp[a] = 1 + min((dp[a - c] for c in coins if c <= a), default=inf)
    return dp[amount] if dp[amount] <= amount else -1


def lis_length(a: list[int]) -> int:
    tails: list[int] = []
    for x in a:
        k = bisect_left(tails, x)
        if k == len(tails):
            tails.append(x)
        else:
            tails[k] = x                # same length, smaller tail: easier to extend
    return len(tails)


def edit_distance(s: str, t: str) -> int:
    @cache
    def d(i: int, j: int) -> int:       # distance between s[:i] and t[:j]
        if i == 0 or j == 0:
            return i + j
        return min(d(i - 1, j) + 1, d(i, j - 1) + 1, d(i - 1, j - 1) + (s[i - 1] != t[j - 1]))
    return d(len(s), len(t))


def knapsack(items: list[tuple[int, float]], budget: int) -> float:
    """items = (cost, value); each item used at most once."""
    dp = [0.0] * (budget + 1)
    for cost, value in items:
        for b in range(budget, cost - 1, -1):   # downwards, so an item is not reused
            dp[b] = max(dp[b], dp[b - cost] + value)
    return dp[budget]


def combination_sum(cands: list[int], target: int) -> list[list[int]]:
    """All combinations (reuse allowed) that add up to target."""
    out: list[list[int]] = []
    path: list[int] = []

    def go(start: int, left: int) -> None:
        if left == 0:
            out.append(path.copy())
            return
        for i in range(start, len(cands)):
            if cands[i] > left:
                break                   # sorted, so every later candidate is too big
            path.append(cands[i])
            go(i, left - cands[i])
            path.pop()                  # undo: this is the "backtrack"

    cands = sorted(cands)
    go(0, target)
    return out


print(coin_change([1, 5, 10, 25], 63), coin_change([2], 3))   # 6 -1
print(lis_length([10, 9, 2, 5, 3, 7, 101, 18]))               # 4
print(edit_distance("kitten", "sitting"))                     # 3
# Choose trades under a capital limit of 10: (capital used, expected P&L)
print(knapsack([(5, 10.0), (4, 40.0), (6, 30.0), (3, 50.0)], 10))  # 90.0
print(combination_sum([2, 3, 6, 7], 7))                       # [[2, 2, 3], [7]]
```

---

## 9. Trading-flavoured problems

These come up in quant-developer interviews because they mix a standard pattern with market data.

| Problem | Pattern | Cost per update |
|---|---|---|
| Rolling VWAP (volume-weighted average price) over the last T seconds | Deque of trades + running sums | O(1) amortised |
| Rolling max / min price over a window | Monotonic deque | O(1) amortised |
| Running median of a stream | Two heaps (see [Python section 12](../python/README.md#12-classic-implementations-with-code)) | O(log n) |
| Limit order book: best bid/ask, add, cancel | Heaps per side + lazy delete, or sorted map of price levels | O(log n) |
| Volume traded below price p, with updates | Fenwick tree over price ticks | O(log n) |
| Build 1-minute OHLC bars (open, high, low, close) from ticks | Group by `t // 60` in one pass | O(1) |

**Fenwick tree** (also called a binary indexed tree): an array where cell i stores the sum of a block of cells ending at i, with block length equal to the lowest set bit of i. Both "add to one cell" and "sum of the first i cells" touch only O(log n) cells.

```python
import heapq
from collections import deque


class RollingVWAP:
    """VWAP = sum(price * size) / sum(size) over trades in the last `window` seconds."""

    def __init__(self, window: float) -> None:
        self.window = window
        self.trades: deque[tuple[float, float, float]] = deque()
        self.pv = self.vol = 0.0

    def add(self, t: float, price: float, size: float) -> float:
        self.trades.append((t, price, size))
        self.pv += price * size
        self.vol += size
        while self.trades[0][0] <= t - self.window:     # drop trades older than the window
            _, p, q = self.trades.popleft()
            self.pv -= p * q
            self.vol -= q
        return self.pv / self.vol


def rolling_max(prices: list[float], w: int) -> list[float]:
    dq: deque[int] = deque()            # indices; their prices are decreasing
    out = []
    for i, p in enumerate(prices):
        while dq and prices[dq[-1]] <= p:
            dq.pop()                    # can never be the max again
        dq.append(i)
        if dq[0] <= i - w:
            dq.popleft()                # fell out of the window
        if i >= w - 1:
            out.append(prices[dq[0]])
    return out


class Fenwick:
    def __init__(self, n: int) -> None:
        self.tree = [0.0] * (n + 1)     # 1-based

    def add(self, i: int, x: float) -> None:
        i += 1
        while i < len(self.tree):
            self.tree[i] += x
            i += i & -i                 # jump to the next block that covers i

    def prefix(self, i: int) -> float:
        """Sum of cells 0 .. i-1."""
        s = 0.0
        while i > 0:
            s += self.tree[i]
            i -= i & -i                 # strip the lowest set bit
        return s


class TopOfBook:
    """Best bid and ask with cancels. Lazy delete: cancelled ids are skipped when they surface."""

    def __init__(self) -> None:
        self.bids: list[tuple[float, int]] = []   # (-price, id): max-heap through negation
        self.asks: list[tuple[float, int]] = []   # (price, id)
        self.live: set[int] = set()

    def add(self, oid: int, side: str, price: float) -> None:
        heapq.heappush(self.bids if side == "B" else self.asks,
                       (-price if side == "B" else price, oid))
        self.live.add(oid)

    def cancel(self, oid: int) -> None:
        self.live.discard(oid)

    def best(self) -> tuple[float | None, float | None]:
        for heap in (self.bids, self.asks):
            while heap and heap[0][1] not in self.live:
                heapq.heappop(heap)
        bid = -self.bids[0][0] if self.bids else None
        ask = self.asks[0][0] if self.asks else None
        return bid, ask


v = RollingVWAP(window=60)
for t, p, q in [(0, 100.0, 200), (20, 100.5, 100), (50, 101.0, 300), (70, 100.8, 100)]:
    vwap = v.add(t, p, q)
print(f"{vwap:.4f}")                                    # 100.8600

print(rolling_max([3, 1, 4, 1, 5, 9, 2, 6], 3))        # [4, 4, 5, 9, 9, 9]

fw = Fenwick(10)                    # price ticks 0..9
for tick, size in [(2, 100), (5, 300), (7, 50), (2, 25)]:
    fw.add(tick, size)
print(fw.prefix(6))                 # volume at ticks 0..5: 425.0

book = TopOfBook()
book.add(1, "B", 99.5)
book.add(2, "B", 99.7)
book.add(3, "S", 100.1)
book.add(4, "S", 100.0)
book.cancel(2)
book.cancel(4)
print(book.best())                  # (99.5, 100.1)
```

The order book above only tracks the top of book. A full book with queues per price level, partial fills and price-time priority is in [`order_book.py`](../../src/quantprep/systems/order_book.py).

---

## 10. Python and C++ containers side by side

| Need | Python | C++ standard library | Note |
|---|---|---|---|
| Growable array | `list` | `std::vector` | `reserve()` in C++ avoids repeated copies |
| Both-ends queue | `collections.deque` | `std::deque` | |
| Hash map / set | `dict` / `set` | `std::unordered_map` / `unordered_set` | C++ version is slower than a flat open-addressing table (e.g. `absl::flat_hash_map`) |
| Sorted map | none built in (`sortedcontainers` package, or `bisect` on a list) | `std::map` (red-black tree) | Order book price levels in C++ |
| Heap | `heapq` (min-heap on a list) | `std::priority_queue` (max-heap by default) | Opposite defaults: a common bug |
| Binary search | `bisect.bisect_left` / `bisect_right` | `std::lower_bound` / `upper_bound` | Same meaning |
| Sort | `sorted` (stable) | `std::sort` (not stable), `std::stable_sort` | |

---

## 11. Interview questions

1. **Find a duplicate in an array of n + 1 numbers in the range 1..n, with O(1) extra memory.**
   Treat `i → a[i]` as a linked list; a duplicate creates a cycle. Floyd's tortoise and hare: a slow pointer moves one step, a fast pointer two; after they meet, restart one from the start and move both one step at a time; they meet at the duplicate. O(n) time, O(1) memory.

2. **Why is sorting at least O(n log n)?**
   A comparison sort must tell apart all n! orderings. Each comparison has 2 outcomes, so it needs at least log₂(n!) ≈ n log₂ n comparisons. Counting sort and radix sort beat this by not comparing (they need small integer keys).

3. **Detect a cycle in a linked list.**
   Floyd again: if the fast pointer ever equals the slow pointer, there is a cycle. O(1) memory, versus O(n) for a set of seen nodes.

4. **Quickselect: k-th smallest without sorting.**
   Partition around a random pivot, then recurse into the side that holds index k only. Expected cost n + n/2 + n/4 + ... = 2n, so O(n) on average; O(n²) worst case with bad pivots. A heap of size k gives O(n log k) and works on a stream.

5. **Sliding window vs prefix sums for "subarray with sum k"?**
   A sliding window needs the sum to grow as the window grows, so all numbers must be ≥ 0. With negative numbers, use prefix sums and a hash map (section 4).

6. **How would you find the median of a stream of prices?**
   Two heaps: a max-heap for the lower half and a min-heap for the upper half, sizes differing by at most 1. Median = top of the bigger heap, or the mean of both tops. O(log n) per price, O(1) to read.

7. **Hash map worst case and how to avoid it.**
   If many keys land in the same slot, lookups degrade to O(n). Defences: a good hash with a random seed (Python randomises string hashes), resizing at a load factor (Python grows at 2/3 full), or a balanced tree per slot (Java does this).

8. **Given ticks for many symbols, return the k symbols with the most volume.**
   One pass with a hash map from symbol to total volume, O(n); then `heapq.nlargest(k, ...)`, O(m log k) for m symbols. If the data does not fit in memory, hash symbols to files, solve each file, and merge the per-file top-k lists.

9. **When is recursion a bad idea in Python?**
   Depth over about 1,000 hits the recursion limit, and each call is slow. Convert to an explicit stack (DFS) or a bottom-up table (DP).

10. **Design an LRU cache.**
    A hash map from key to node, plus a doubly linked list in order of use. `get` moves the node to the front; `put` adds at the front and removes from the back when full. Both O(1). Code in [Python section 12](../python/README.md#12-classic-implementations-with-code).

---

## 12. Glossary

| Term | Meaning |
|---|---|
| Adjacency list | A graph stored as a map from each node to its list of neighbours |
| Amortised cost | Average cost per operation over a long sequence, even if some single calls are slow |
| Backtracking | Building a solution step by step and undoing steps that cannot work |
| BFS | Breadth-first search: explore nodes in order of distance, using a queue |
| Big-O | How cost grows with input size, ignoring constant factors |
| Bellman-Ford | Shortest paths that allow negative edge weights; also detects negative cycles |
| Deque | Double-ended queue: O(1) add and remove at both ends |
| DFS | Depth-first search: go as deep as possible first, using a stack or recursion |
| Dijkstra | Shortest paths when all edge weights are ≥ 0, using a heap |
| Dynamic programming (DP) | Solving a problem from stored answers to smaller, overlapping sub-problems |
| Fenwick tree | Array structure for prefix sums with updates, both O(log n); also called a binary indexed tree |
| Heap | Tree in a list where each parent ≤ its children; gives the minimum in O(1) |
| Kadane's algorithm | One-pass method for the best sum of a contiguous run |
| Lazy deletion | Marking an item as dead and skipping it later, instead of removing it immediately |
| Master theorem | Formula for the cost of divide-and-conquer recursions |
| Memoisation | Caching a function's results so repeated calls are free (`functools.cache`) |
| Monotonic stack / deque | Stack or deque kept in sorted order by popping items that break the order |
| Negative cycle | A loop in a graph whose edge weights sum to less than 0 |
| OHLC | Open, high, low, close: the four prices that summarise a time bar |
| Prefix sum | Running total; any range sum is the difference of two prefix sums |
| Quickselect | Partition-based method to find the k-th smallest item in O(n) on average |
| Sliding window | A range [left, right] moved along an array, updated in O(1) per step |
| Stable sort | A sort that keeps equal items in their original order |
| Topological sort | An order of nodes where every edge points forward; exists only without cycles |
| Two pointers | Two indices moved towards each other (or together) to avoid a double loop |
| Union-find | Structure that merges groups and tells whether two items share a group, almost O(1) |
| VWAP | Volume-weighted average price: sum(price × size) / sum(size) |
