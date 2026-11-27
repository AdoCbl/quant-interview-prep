# Data Structures and Algorithms in C++

The C++ companion to the [Python DSA page](README.md): the standard library containers and
algorithms you need, the bugs interviewers watch for, and the same patterns written in modern
C++ (C++20). Each term is explained the first time it appears; a glossary is at the end.

Every program in sections 4–8 is complete (the one-line snippet in section 2 is a fragment). Compile and run one with
`clang++ -std=c++20 -O2 -Wall -Wextra -Wpedantic -Werror file.cpp -o prog && ./prog`.
The block after each one shows its output. All of them also run cleanly under the address and
undefined-behaviour sanitizers (`-fsanitize=address,undefined`). Header-only code with tests lives in
[`cpp/`](../../cpp/) (`make -C cpp test`).

Contents:

1. [Containers and their costs](#1-containers-and-their-costs)
2. [Algorithms worth knowing by name](#2-algorithms-worth-knowing-by-name)
3. [Bugs interviewers look for](#3-bugs-interviewers-look-for)
4. [Arrays: two pointers, sliding window, prefix sums](#4-arrays-two-pointers-sliding-window-prefix-sums)
5. [Stacks, heaps and hashing](#5-stacks-heaps-and-hashing)
6. [Graphs](#6-graphs)
7. [Intervals, binary search and dynamic programming](#7-intervals-binary-search-and-dynamic-programming)
8. [Trading-flavoured: VWAP, order book, Fenwick tree](#8-trading-flavoured-vwap-order-book-fenwick-tree)
9. [Performance habits for low-latency code](#9-performance-habits-for-low-latency-code)
10. [Interview questions](#10-interview-questions)
11. [Glossary](#11-glossary)

---

## 1. Containers and their costs

| Container | Structure | Access / find | Insert / erase | Use it for |
|---|---|---|---|---|
| `std::vector` | Contiguous array | O(1) by index | O(1) amortised at the end; O(n) in the middle | The default. Cache-friendly. Also your stack. |
| `std::deque` | Blocks of arrays | O(1) by index | O(1) at both ends | Queues, sliding windows |
| `std::list` | Doubly linked list | O(n) | O(1) given an iterator | Order queues where iterators must stay valid |
| `std::unordered_map` / `unordered_set` | Hash table with chained buckets | O(1) average | O(1) average | Lookups by key; counting |
| `std::map` / `set` | Red-black tree (balanced binary search tree) | O(log n) | O(log n) | Sorted keys, `lower_bound`, best price level |
| `std::priority_queue` | Binary heap on a vector | O(1) top | O(log n) push / pop | Top-k, Dijkstra, scheduling. **Max-heap by default.** |
| `std::array` | Fixed-size array on the stack | O(1) | — | Small fixed sizes, no allocation |
| `std::string_view`, `std::span` | Non-owning view | O(1) | — | Pass substrings / subarrays without copying |

Python equivalents: `list` ≈ `vector`, `deque` ≈ `deque`, `dict` ≈ `unordered_map`, `heapq` ≈
`priority_queue` (but min-heap), `bisect` ≈ `lower_bound`. There is no built-in sorted map in Python.

---

## 2. Algorithms worth knowing by name

| Call | Does | Cost |
|---|---|---|
| `std::sort(b, e, cmp)` | Sort (introsort, not stable) | O(n log n) |
| `std::stable_sort` | Sort keeping equal items in order | O(n log n) |
| `std::nth_element(b, b + k, e)` | Puts the k-th smallest at position k, smaller ones before it | O(n) average |
| `std::partial_sort` | Sorts only the first k | O(n log k) |
| `std::lower_bound` / `upper_bound` | First position `>= x` / `> x` in a sorted range | O(log n) |
| `std::accumulate`, `std::partial_sum` (`<numeric>`) | Sum, prefix sums | O(n) |
| `std::unique` + `erase` | Remove adjacent duplicates (sort first) | O(n) |
| `std::iota` | Fill 0, 1, 2, ... | O(n) |
| `std::ranges::sort(v)` (C++20) | Same as `sort`, but on a whole container | O(n log n) |

Erase-remove idiom (C++20 has `std::erase_if(v, pred)` for this):

```cpp
v.erase(std::remove_if(v.begin(), v.end(), [](int x) { return x < 0; }), v.end());
```

---

## 3. Bugs interviewers look for

| Bug | Example | Fix |
|---|---|---|
| Unsigned underflow | `for (size_t i = v.size() - 1; i >= 0; --i)` never ends; `v.size() - 1` is huge when `v` is empty | Use `int` / `std::ssize(v)`, or loop `for (auto i = v.size(); i-- > 0;)` |
| Integer overflow | `(lo + hi) / 2`, sums of prices × quantities in `int` | `lo + (hi - lo) / 2`; use `long long` / `std::int64_t` |
| `map[key]` inserts | Reading `m[k]` to check existence creates the key | `find`, `contains` (C++20), or `count` |
| Iterator invalidation | `push_back` on a vector while holding a pointer or iterator into it | Keep indices, `reserve` first, or use `list` / `deque` (end inserts keep `deque` references valid) |
| Max-heap default | `priority_queue<int>` gives the largest first | `priority_queue<int, vector<int>, greater<>>` for a min-heap |
| Comparator not strict | `sort` with `<=` is undefined behaviour | Comparators must be "strictly less than" |
| Copying big objects | `void f(vector<int> v)` copies | `const vector<int>&`, or take by value and `std::move` in on purpose |
| Dangling references | Returning a reference or `string_view` to a local | Return by value (move and copy elision make it cheap) |
| `double` as a price key | `map<double, ...>` with 100.1 + 0.2 ≠ 100.3 | Integer ticks (`int64_t` price in ticks) |
| `std::endl` in loops | Flushes every line: slow output | `'\n'` |

---

## 4. Arrays: two pointers, sliding window, prefix sums

Same ideas as [Python section 4](README.md#4-arrays-two-pointers-sliding-window-prefix-sums). Note
`std::optional` for "maybe no answer", and `if (auto it = m.find(k); it != m.end())` (an
if-statement with an initialiser), which looks up once instead of twice.

```cpp
// Arrays: two pointers, sliding window, prefix sums, Kadane, max drawdown
#include <algorithm>
#include <iostream>
#include <optional>
#include <string>
#include <unordered_map>
#include <utility>
#include <vector>

std::optional<std::pair<int, int>> two_sum_sorted(const std::vector<int>& a, int target) {
    int i = 0, j = static_cast<int>(a.size()) - 1;  // int, not size_t: j can reach -1
    while (i < j) {
        const int s = a[i] + a[j];
        if (s == target) return std::pair{i, j};
        if (s < target) ++i; else --j;
    }
    return std::nullopt;
}

int longest_unique_run(const std::string& s) {
    std::unordered_map<char, int> last;
    int best = 0, start = 0;
    for (int i = 0; i < static_cast<int>(s.size()); ++i) {
        if (auto it = last.find(s[i]); it != last.end() && it->second >= start)
            start = it->second + 1;
        last[s[i]] = i;
        best = std::max(best, i - start + 1);
    }
    return best;
}

long long count_subarrays_with_sum(const std::vector<int>& a, long long k) {
    std::unordered_map<long long, long long> seen{{0, 1}};
    long long total = 0, count = 0;
    for (int x : a) {
        total += x;
        if (auto it = seen.find(total - k); it != seen.end()) count += it->second;
        ++seen[total];
    }
    return count;
}

double max_drawdown(const std::vector<double>& p) {
    double peak = p.front(), worst = 0.0;
    for (double x : p) {
        peak = std::max(peak, x);
        worst = std::max(worst, 1.0 - x / peak);
    }
    return worst;
}

int main() {
    if (auto r = two_sum_sorted({1, 3, 4, 6, 8, 11}, 10))
        std::cout << r->first << ' ' << r->second << '\n';
    std::cout << longest_unique_run("abcabcbb") << '\n';
    std::cout << count_subarrays_with_sum({1, 2, -1, 2, 1, -2, 3}, 3) << '\n';

    const std::vector<double> prices{100, 104, 98, 95, 103, 110, 99, 107};
    double best = 0, cur = 0;                       // Kadane on daily changes
    for (std::size_t i = 1; i < prices.size(); ++i) {
        const double d = prices[i] - prices[i - 1];
        cur = std::max(d, cur + d);
        best = std::max(best, cur);
    }
    std::cout << best << ' ' << max_drawdown(prices) << '\n';
}
```

Output:

```text
2 3
3
6
15 0.1
```

---

## 5. Stacks, heaps and hashing

`std::vector` with `push_back` / `back` / `pop_back` is the usual stack. `std::priority_queue`
takes three template arguments: element type, underlying container, comparator.
`std::greater<>` turns it into a min-heap. Tuples and pairs compare lexicographically (first
element, then second), which gives heap ordering for free.

```cpp
// Stacks, heaps, hashing: brackets, monotonic stack, k-th largest, top-k, k-way merge
#include <functional>
#include <iostream>
#include <queue>
#include <string>
#include <tuple>
#include <unordered_map>
#include <utility>
#include <vector>

bool is_balanced(const std::string& s) {
    std::vector<char> st;                           // vector as a stack: no std::stack needed
    for (char c : s) {
        if (c == '(' || c == '[' || c == '{') { st.push_back(c); continue; }
        const char want = c == ')' ? '(' : c == ']' ? '[' : c == '}' ? '{' : 0;
        if (!want) continue;
        if (st.empty() || st.back() != want) return false;
        st.pop_back();
    }
    return st.empty();
}

std::vector<int> days_until_higher(const std::vector<int>& p) {
    std::vector<int> out(p.size(), 0), st;
    for (int i = 0; i < static_cast<int>(p.size()); ++i) {
        while (!st.empty() && p[st.back()] < p[i]) {
            out[st.back()] = i - st.back();
            st.pop_back();
        }
        st.push_back(i);
    }
    return out;
}

int kth_largest(const std::vector<int>& a, int k) {
    // min-heap: std::priority_queue is a MAX-heap by default, so pass std::greater
    std::priority_queue<int, std::vector<int>, std::greater<>> heap;
    for (int x : a) {
        heap.push(x);
        if (static_cast<int>(heap.size()) > k) heap.pop();
    }
    return heap.top();
}

int main() {
    std::cout << std::boolalpha << is_balanced("{[()()]}") << ' ' << is_balanced("([)]") << '\n';
    for (int d : days_until_higher({73, 74, 75, 71, 69, 72, 76, 73})) std::cout << d << ' ';
    std::cout << '\n' << kth_largest({3, 2, 1, 5, 6, 4}, 2) << '\n';

    // Top-k by count: count with a hash map, then a size-k min-heap of (count, name)
    std::unordered_map<std::string, int> cnt;
    for (const char* s : {"AAPL", "MSFT", "AAPL", "TSLA", "AAPL", "MSFT"}) ++cnt[s];
    using Item = std::pair<int, std::string>;
    std::priority_queue<Item, std::vector<Item>, std::greater<>> top;
    for (const auto& [name, c] : cnt) {
        top.emplace(c, name);
        if (top.size() > 2) top.pop();
    }
    std::vector<Item> res;
    for (; !top.empty(); top.pop()) res.push_back(top.top());
    for (auto it = res.rbegin(); it != res.rend(); ++it) std::cout << it->second << '=' << it->first << ' ';
    std::cout << '\n';

    // k-way merge of sorted streams: heap of (value, stream, index)
    const std::vector<std::vector<int>> streams{{1, 4, 9}, {2, 3, 10}, {5}};
    using Node = std::tuple<int, std::size_t, std::size_t>;
    std::priority_queue<Node, std::vector<Node>, std::greater<>> h;
    for (std::size_t s = 0; s < streams.size(); ++s) h.emplace(streams[s][0], s, 0);
    while (!h.empty()) {
        auto [v, s, i] = h.top();
        h.pop();
        std::cout << v << ' ';
        if (i + 1 < streams[s].size()) h.emplace(streams[s][i + 1], s, i + 1);
    }
    std::cout << '\n';
}
```

Output:

```text
true false
1 1 4 2 1 1 0 0
5
AAPL=3 MSFT=2
1 2 3 4 5 9 10
```

---

## 6. Graphs

Adjacency lists are `vector<vector<int>>` (or `vector<vector<pair<int, double>>>` with weights)
over node numbers 0..n−1. Map names to numbers first. Use `queue` for BFS and a min-heap for
Dijkstra. The union-find uses **path halving** (point each node at its grandparent while walking
up) and **union by size**.

```cpp
// Graphs: BFS on a grid, topological sort, Dijkstra, union-find, Bellman-Ford arbitrage
#include <cmath>
#include <functional>
#include <iostream>
#include <limits>
#include <numeric>
#include <queue>
#include <stdexcept>
#include <string>
#include <utility>
#include <vector>

int bfs_grid(const std::vector<std::string>& g, int sr, int sc, int tr, int tc) {
    const int R = static_cast<int>(g.size()), C = static_cast<int>(g[0].size());
    std::vector<std::vector<int>> dist(R, std::vector<int>(C, -1));
    std::queue<std::pair<int, int>> q;
    dist[sr][sc] = 0;
    q.emplace(sr, sc);
    constexpr int dr[] = {1, -1, 0, 0}, dc[] = {0, 0, 1, -1};
    while (!q.empty()) {
        auto [r, c] = q.front();
        q.pop();
        if (r == tr && c == tc) return dist[r][c];
        for (int k = 0; k < 4; ++k) {
            const int nr = r + dr[k], nc = c + dc[k];
            if (nr < 0 || nr >= R || nc < 0 || nc >= C || g[nr][nc] != '.' || dist[nr][nc] != -1)
                continue;
            dist[nr][nc] = dist[r][c] + 1;
            q.emplace(nr, nc);
        }
    }
    return -1;
}

// Kahn's algorithm. edges[u] = nodes that depend on u.
std::vector<int> topo(const std::vector<std::vector<int>>& edges) {
    std::vector<int> indeg(edges.size(), 0), order;
    for (const auto& out : edges) for (int v : out) ++indeg[v];
    std::queue<int> ready;
    for (int u = 0; u < static_cast<int>(edges.size()); ++u) if (indeg[u] == 0) ready.push(u);
    while (!ready.empty()) {
        const int u = ready.front();
        ready.pop();
        order.push_back(u);
        for (int v : edges[u]) if (--indeg[v] == 0) ready.push(v);
    }
    if (order.size() != edges.size()) throw std::runtime_error("cycle");
    return order;
}

std::vector<double> dijkstra(const std::vector<std::vector<std::pair<int, double>>>& g, int src) {
    std::vector<double> dist(g.size(), std::numeric_limits<double>::infinity());
    using QE = std::pair<double, int>;
    std::priority_queue<QE, std::vector<QE>, std::greater<>> pq;
    dist[src] = 0;
    pq.emplace(0.0, src);
    while (!pq.empty()) {
        auto [d, u] = pq.top();
        pq.pop();
        if (d > dist[u]) continue;                      // stale entry
        for (auto [v, w] : g[u])
            if (d + w < dist[v]) { dist[v] = d + w; pq.emplace(dist[v], v); }
    }
    return dist;
}

struct UnionFind {
    std::vector<int> parent, size;
    explicit UnionFind(int n) : parent(n), size(n, 1) { std::iota(parent.begin(), parent.end(), 0); }
    int find(int x) {
        while (parent[x] != x) x = parent[x] = parent[parent[x]];   // path halving
        return x;
    }
    bool unite(int a, int b) {
        a = find(a), b = find(b);
        if (a == b) return false;
        if (size[a] < size[b]) std::swap(a, b);
        parent[b] = a;
        size[a] += size[b];
        return true;
    }
};

struct Edge { int from, to; double rate; };

bool has_arbitrage(int n, const std::vector<Edge>& edges) {
    std::vector<double> dist(n, 0.0);                     // start from every node
    for (int i = 0; i < n - 1; ++i)
        for (const auto& e : edges) dist[e.to] = std::min(dist[e.to], dist[e.from] - std::log(e.rate));
    for (const auto& e : edges)
        if (dist[e.from] - std::log(e.rate) < dist[e.to] - 1e-12) return true;
    return false;
}

int main() {
    std::cout << bfs_grid({"..#.", ".##.", "...."}, 0, 0, 0, 3) << '\n';

    // 0 fixings, 1 ois_curve, 2 fx, 3 swap_pv, 4 risk
    for (int u : topo({{1}, {3}, {4}, {4}, {}})) std::cout << u << ' ';
    std::cout << '\n';

    // 0 NY, 1 CHI, 2 LDN, 3 TKY (latency in microseconds)
    std::vector<std::vector<std::pair<int, double>>> g{{{1, 7}, {2, 30}}, {{2, 35}, {3, 70}}, {{3, 45}}, {}};
    for (double d : dijkstra(g, 0)) std::cout << d << ' ';
    std::cout << '\n';

    UnionFind uf(6);
    uf.unite(0, 1); uf.unite(2, 3); uf.unite(1, 3);
    std::cout << std::boolalpha << (uf.find(0) == uf.find(2)) << ' ' << (uf.find(0) == uf.find(5)) << '\n';

    // 0 USD, 1 EUR, 2 GBP
    std::cout << has_arbitrage(3, {{0, 1, 0.90}, {1, 2, 0.86}, {2, 0, 1.30},
                                   {1, 0, 1.10}, {2, 1, 1.15}, {0, 2, 0.76}}) << '\n';
}
```

Output:

```text
7
0 2 1 3 4
0 7 30 75
true false
true
```

Nodes in the topological order: 0 fixings, 2 fx, 1 ois_curve, 3 swap_pv, 4 risk.

---

## 7. Intervals, binary search and dynamic programming

Edit distance keeps only two rows of the table (`prev`, `cur`), so memory is O(m) instead of
O(n·m). This is the standard follow-up question.

```cpp
// Intervals, binary search on the answer, dynamic programming
#include <algorithm>
#include <functional>
#include <iostream>
#include <numeric>
#include <queue>
#include <string>
#include <utility>
#include <vector>

using Interval = std::pair<int, int>;

std::vector<Interval> merge(std::vector<Interval> iv) {   // by value: we sort our own copy
    std::sort(iv.begin(), iv.end());
    std::vector<Interval> out;
    for (const auto& [s, e] : iv) {
        if (!out.empty() && s <= out.back().second) out.back().second = std::max(out.back().second, e);
        else out.emplace_back(s, e);
    }
    return out;
}

int max_concurrent(std::vector<Interval> iv) {
    std::sort(iv.begin(), iv.end());
    std::priority_queue<int, std::vector<int>, std::greater<>> ends;
    std::size_t best = 0;
    for (const auto& [s, e] : iv) {
        while (!ends.empty() && ends.top() <= s) ends.pop();
        ends.push(e);
        best = std::max(best, ends.size());
    }
    return static_cast<int>(best);
}

int min_daily_capacity(const std::vector<int>& orders, int days) {
    auto fits = [&](int cap) {
        int used = 1, load = 0;
        for (int q : orders) {
            if (load + q > cap) { ++used; load = 0; }
            load += q;
        }
        return used <= days;
    };
    int lo = *std::max_element(orders.begin(), orders.end());
    int hi = std::accumulate(orders.begin(), orders.end(), 0);
    while (lo < hi) {
        const int mid = lo + (hi - lo) / 2;              // no overflow, unlike (lo + hi) / 2
        if (fits(mid)) hi = mid; else lo = mid + 1;
    }
    return lo;
}

int coin_change(const std::vector<int>& coins, int amount) {
    std::vector<int> dp(amount + 1, amount + 1);
    dp[0] = 0;
    for (int a = 1; a <= amount; ++a)
        for (int c : coins) if (c <= a) dp[a] = std::min(dp[a], dp[a - c] + 1);
    return dp[amount] > amount ? -1 : dp[amount];
}

int lis(const std::vector<int>& a) {
    std::vector<int> tails;
    for (int x : a) {
        auto it = std::lower_bound(tails.begin(), tails.end(), x);
        if (it == tails.end()) tails.push_back(x); else *it = x;
    }
    return static_cast<int>(tails.size());
}

int edit_distance(const std::string& s, const std::string& t) {
    std::vector<int> prev(t.size() + 1), cur(t.size() + 1);   // two rows: O(m) memory
    std::iota(prev.begin(), prev.end(), 0);
    for (std::size_t i = 1; i <= s.size(); ++i) {
        cur[0] = static_cast<int>(i);
        for (std::size_t j = 1; j <= t.size(); ++j)
            cur[j] = std::min({prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (s[i - 1] != t[j - 1])});
        std::swap(prev, cur);
    }
    return prev[t.size()];
}

int main() {
    for (auto [s, e] : merge({{1, 3}, {8, 10}, {2, 6}, {15, 18}, {17, 20}})) std::cout << s << '-' << e << ' ';
    std::cout << '\n' << max_concurrent({{0, 30}, {5, 10}, {15, 20}, {25, 35}}) << '\n';
    std::cout << min_daily_capacity({1, 2, 3, 4, 5, 6, 7, 8, 9, 10}, 5) << '\n';
    std::cout << coin_change({1, 5, 10, 25}, 63) << ' ' << coin_change({2}, 3) << '\n';
    std::cout << lis({10, 9, 2, 5, 3, 7, 101, 18}) << ' ' << edit_distance("kitten", "sitting") << '\n';
}
```

Output:

```text
1-6 8-10 15-20
2
15
6 -1
4 3
```

---

## 8. Trading-flavoured: VWAP, order book, Fenwick tree

The order book is the classic quant-developer exercise. Design points to say out loud:

- **Prices as integer ticks**, never `double`, so comparisons and map keys are exact.
- **Each side is a sorted map** of price → FIFO queue of orders: `std::map<price, level, std::greater<>>` for bids (best = highest first), plain `std::map` for asks. The best price is `begin()`, in O(1).
- **Price-time priority**: match the best price first, and within a price the oldest order first.
- **O(1) cancel**: a hash map from order ID to (side, price, iterator into the level's list). `std::list` iterators stay valid when other elements are inserted or erased, which is why a list is used here.
- **Production versions** replace the tree with a flat array indexed by tick (prices sit in a narrow band) and the list with an intrusive linked list in a preallocated pool, so there are no allocations on the hot path. See the tested version in [`src/quantprep/systems/order_book.py`](../../src/quantprep/systems/order_book.py) and [system design](../system-design/README.md).

```cpp
// Trading-flavoured: rolling VWAP, price-time priority order book, Fenwick tree
#include <algorithm>
#include <cstdint>
#include <deque>
#include <functional>
#include <iterator>
#include <iostream>
#include <list>
#include <map>
#include <tuple>
#include <unordered_map>
#include <vector>

class RollingVWAP {
    struct Trade { double t, px, qty; };
    std::deque<Trade> trades_;
    double window_, pv_ = 0, vol_ = 0;
public:
    explicit RollingVWAP(double window) : window_(window) {}
    double add(double t, double px, double qty) {
        trades_.push_back({t, px, qty});
        pv_ += px * qty;
        vol_ += qty;
        while (trades_.front().t <= t - window_) {
            pv_ -= trades_.front().px * trades_.front().qty;
            vol_ -= trades_.front().qty;
            trades_.pop_front();
        }
        return pv_ / vol_;
    }
};

// Prices are integer ticks, never doubles: exact comparison and hashing.
class OrderBook {
    struct Order { std::uint64_t id; std::int64_t qty; };
    using Level = std::list<Order>;                          // FIFO queue at one price
    std::map<std::int64_t, Level, std::greater<>> bids_;     // best (highest) first
    std::map<std::int64_t, Level> asks_;                     // best (lowest) first
    struct Loc { bool buy; std::int64_t px; Level::iterator it; };
    std::unordered_map<std::uint64_t, Loc> index_;           // id -> where it rests: O(1) cancel

    template <class Book>
    std::int64_t match(Book& book, bool buy, std::int64_t px, std::int64_t qty) {
        while (qty > 0 && !book.empty()) {
            auto lvl = book.begin();
            if (buy ? lvl->first > px : lvl->first < px) break;   // no longer crosses
            auto& q = lvl->second;
            while (qty > 0 && !q.empty()) {
                const std::int64_t fill = std::min(qty, q.front().qty);
                std::cout << "  fill " << fill << " @ " << lvl->first << " vs order " << q.front().id << '\n';
                qty -= fill;
                if ((q.front().qty -= fill) == 0) { index_.erase(q.front().id); q.pop_front(); }
            }
            if (q.empty()) book.erase(lvl);
        }
        return qty;
    }
public:
    void add(std::uint64_t id, bool buy, std::int64_t px, std::int64_t qty) {
        qty = buy ? match(asks_, true, px, qty) : match(bids_, false, px, qty);
        if (qty == 0) return;
        auto rest = [&](auto& book) {
            auto& lvl = book[px];
            lvl.push_back({id, qty});
            index_[id] = {buy, px, std::prev(lvl.end())};    // list iterators stay valid
        };
        buy ? rest(bids_) : rest(asks_);
    }
    bool cancel(std::uint64_t id) {
        auto f = index_.find(id);
        if (f == index_.end()) return false;
        auto drop = [&](auto& book) {
            auto lvl = book.find(f->second.px);
            lvl->second.erase(f->second.it);
            if (lvl->second.empty()) book.erase(lvl);
        };
        f->second.buy ? drop(bids_) : drop(asks_);
        index_.erase(f);
        return true;
    }
    void top() const {
        std::cout << "  bid " << (bids_.empty() ? 0 : bids_.begin()->first)
                  << " ask " << (asks_.empty() ? 0 : asks_.begin()->first) << '\n';
    }
};

class Fenwick {
    std::vector<double> t_;
public:
    explicit Fenwick(int n) : t_(n + 1, 0.0) {}
    void add(int i, double x) { for (++i; i < static_cast<int>(t_.size()); i += i & -i) t_[i] += x; }
    double prefix(int i) const { double s = 0; for (; i > 0; i -= i & -i) s += t_[i]; return s; }
};

int main() {
    RollingVWAP v(60);
    double vwap = 0;
    for (auto [t, p, q] : {std::tuple{0., 100.0, 200.}, {20., 100.5, 100.}, {50., 101.0, 300.}, {70., 100.8, 100.}})
        vwap = v.add(t, p, q);
    std::cout << "vwap " << vwap << '\n';

    OrderBook ob;
    ob.add(1, false, 10010, 5);   // asks
    ob.add(2, false, 10010, 3);
    ob.add(3, false, 10020, 4);
    ob.add(4, true, 9990, 6);     // bid
    ob.top();
    std::cout << "buy 7 @ 10015:\n";
    ob.add(5, true, 10015, 7);    // takes all of order 1 and 2 of order 2 (time priority)
    ob.top();
    std::cout << "cancel 2: " << std::boolalpha << ob.cancel(2) << '\n';
    ob.top();

    Fenwick fw(10);
    fw.add(2, 100); fw.add(5, 300); fw.add(7, 50); fw.add(2, 25);
    std::cout << "volume at ticks 0..5: " << fw.prefix(6) << '\n';
}
```

Output:

```text
vwap 100.86
  bid 9990 ask 10010
buy 7 @ 10015:
  fill 5 @ 10010 vs order 1
  fill 2 @ 10010 vs order 2
  bid 9990 ask 10010
cancel 2: true
  bid 9990 ask 10020
volume at ticks 0..5: 425
```

---

## 9. Performance habits for low-latency code

- **Contiguous memory beats clever structures**: a sorted `vector` searched with `lower_bound` often beats `std::map` for small n, because of cache misses (a main-memory access costs about 100 ns, an L1 cache hit about 1 ns).
- **`reserve`** vectors and hash maps when the size is known: no repeated reallocation.
- **No allocation on the hot path**: preallocate pools, reuse buffers, avoid `std::function` and `shared_ptr` in tight loops.
- **Move, don't copy**: `std::move` big objects into containers; use `emplace_back` to construct in place.
- **Pass small types by value** (`int`, `double`, `string_view`, `span`), big ones by `const&`.
- **Structure of arrays** (one array per field) when a loop reads one field over many records: better cache use and SIMD (one instruction on several numbers).
- **`noexcept` move constructors**: otherwise `vector` copies instead of moving when it grows.
- **Measure**: compile with `-O2`, benchmark with a real workload, and check with a profiler (`perf`) before optimising.

---

## 10. Interview questions

1. **`std::map` vs `std::unordered_map`?**
   `map`: a balanced tree, O(log n), sorted, supports `lower_bound`, stable iterators. `unordered_map`: a hash table, O(1) on average, unordered, rehashing invalidates iterators, and slower than expected because each node is a separate allocation. Open-addressing tables (`absl::flat_hash_map`) are faster still.

2. **When does `vector::push_back` invalidate iterators?**
   When `size() == capacity()`, it allocates a bigger buffer (usually 1.5–2× larger), moves the elements, and invalidates every iterator, pointer and reference. Otherwise only `end()` is invalidated.

3. **Why is a vector's growth factor geometric?**
   Doubling makes the total copying for n pushes at most about 2n, so each push is O(1) amortised. Growing by a fixed amount would make it O(n²) in total.

4. **How do you hash a `pair<int, int>` for `unordered_map`?**
   Write a hash struct that mixes the two values, e.g. `h1 ^ (h2 + 0x9e3779b9 + (h1 << 6) + (h1 >> 2))`, or encode both into one 64-bit key (`(uint64_t)a << 32 | (uint32_t)b`).

5. **What does `std::move` actually do?**
   Nothing at run time: it is a cast to an rvalue reference, which lets overload resolution pick the move constructor. The moved-from object is valid but unspecified.

6. **Recursion depth in C++?**
   The stack is typically 8 MB on Linux (1 MB on Windows), so deep DFS on 10⁶ nodes can crash. Use an explicit stack.

7. **`nth_element` vs a heap for the k-th smallest?**
   `nth_element` is O(n) average but needs all the data in memory and reorders it. A size-k heap is O(n log k) and works on a stream.

---

## 11. Glossary

| Term | Meaning |
|---|---|
| Amortised O(1) | Average cost per operation over many calls, although an occasional call is slow |
| Cache miss | Data not in the CPU cache, so it is fetched from main memory (about 100 ns) |
| Copy elision | The compiler builds a returned object directly in its destination, with no copy |
| Erase-remove idiom | `v.erase(remove_if(...), v.end())`: delete matching elements from a vector |
| Intrusive list | A linked list whose next/prev pointers live inside the objects themselves |
| Iterator invalidation | An iterator becoming unusable because its container changed |
| Lexicographic order | Compare first elements, then second elements on a tie, and so on |
| Path halving | In union-find, pointing each visited node at its grandparent to flatten the tree |
| Red-black tree | Self-balancing binary search tree used by `std::map` |
| Rvalue reference | `T&&`: a reference to a temporary, which can be moved from |
| Sanitizer | Compiler instrumentation that catches memory errors (`address`) and undefined behaviour (`undefined`) at run time |
| SIMD | Single instruction, multiple data: one CPU instruction on several numbers |
| Structure of arrays | Storing each field in its own array instead of an array of structs |
| Undefined behaviour | Code whose result the C++ standard does not define (overflow of signed integers, out-of-bounds access); anything may happen |
