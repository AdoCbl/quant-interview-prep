"""Tests for quantprep.classics.

Most tests are "differential": run many random operations on our structure and on Python's
built-in equivalent, and check they always agree. This finds edge cases a few hand-written
examples would miss.
"""

import bisect
import heapq
import math
import random
import statistics

import pytest

from quantprep.black_scholes import bs_price
from quantprep.classics.binary_search import (
    binary_search,
    bisect_root,
    count_in_range,
    first_true,
    isqrt,
    lower_bound,
    search_rotated,
    upper_bound,
)
from quantprep.classics.hash_map import HashMap
from quantprep.classics.heap import MinHeap, top_k
from quantprep.classics.lru_cache import LRUCache, LRUCacheOrdered, lru_memoize
from quantprep.classics.streaming import RunningMeanVar, RunningMedian, sliding_window_max
from quantprep.classics.trie import Trie
from quantprep.classics.union_find import UnionFind


# ---------- hash map ----------
def test_hash_map_matches_dict():
    rng = random.Random(0)
    ours, ref = HashMap(), {}
    for _ in range(20_000):
        key = rng.randrange(500)          # small key range → many overwrites and deletes
        op = rng.random()
        if op < 0.5:
            ours[key] = ref[key] = rng.random()
        elif op < 0.8:
            if key in ref:
                del ours[key], ref[key]
            else:
                with pytest.raises(KeyError):
                    del ours[key]
        else:
            assert ours.get(key) == ref.get(key)
        assert len(ours) == len(ref)
    assert dict(ours.items()) == ref
    assert sorted(ours) == sorted(ref)


def test_hash_map_string_keys_and_nan():
    m = HashMap()
    nan = float("nan")
    m["AAPL"] = 1
    m[nan] = 2                            # found via the identity check, since nan != nan
    assert m["AAPL"] == 1 and m[nan] == 2 and "MSFT" not in m


# ---------- binary search ----------
def test_bounds_match_bisect():
    rng = random.Random(1)
    for _ in range(500):
        a = sorted(rng.randrange(20) for _ in range(rng.randrange(15)))
        x = rng.randrange(-2, 22)
        assert lower_bound(a, x) == bisect.bisect_left(a, x)
        assert upper_bound(a, x) == bisect.bisect_right(a, x)
        i = binary_search(a, x)
        assert (i == -1 and x not in a) or a[i] == x
        assert count_in_range(a, 5, 10) == sum(5 <= v <= 10 for v in a)


def test_first_true_and_isqrt():
    assert first_true(0, 100, lambda n: n * 3 >= 50) == 17
    assert first_true(0, 10, lambda n: False) == 10
    for n in range(2000):
        assert isqrt(n) == math.isqrt(n)


def test_search_rotated():
    base = list(range(0, 40, 3))
    for shift in range(len(base)):
        a = base[shift:] + base[:shift]
        for x in range(-1, 41):
            i = search_rotated(a, x)
            assert (i == -1 and x not in a) or a[i] == x


def test_bisect_root_recovers_implied_vol():
    S, K, T, r, true_vol = 100.0, 105.0, 0.75, 0.04, 0.27
    price = bs_price(S, K, T, r, true_vol)
    vol = bisect_root(lambda v: bs_price(S, K, T, r, v) - price, 1e-4, 5.0, tol=1e-12)
    assert abs(vol - true_vol) < 1e-8


# ---------- LRU cache ----------
@pytest.mark.parametrize("cls", [LRUCache, LRUCacheOrdered])
def test_lru_eviction_order(cls):
    c = cls(2)
    c.put("a", 1); c.put("b", 2)
    assert c.get("a") == 1               # "a" becomes most recent
    c.put("c", 3)                        # evicts "b"
    assert c.get("b") is None and c.get("a") == 1 and c.get("c") == 3
    assert len(c) == 2


def test_lru_implementations_agree():
    rng = random.Random(2)
    a, b = LRUCache(5), LRUCacheOrdered(5)
    for _ in range(5000):
        k = rng.randrange(12)
        if rng.random() < 0.5:
            v = rng.random(); a.put(k, v); b.put(k, v)
        else:
            assert a.get(k) == b.get(k)
    assert a.keys_oldest_first() == list(b._data)


def test_lru_memoize_caches_and_counts_calls():
    calls = []

    @lru_memoize(maxsize=2)
    def slow_square(x):
        calls.append(x)
        return x * x

    assert [slow_square(v) for v in (2, 2, 3, 2, 4, 3)] == [4, 4, 9, 4, 16, 9]
    assert calls == [2, 3, 4, 3]         # 3 was evicted when 4 arrived (2 was more recent)
    assert slow_square.__name__ == "slow_square"


# ---------- heap ----------
def test_min_heap_sorts():
    rng = random.Random(3)
    data = [rng.random() for _ in range(1000)]
    h = MinHeap(data[:500])              # heapify path
    for x in data[500:]:
        h.push(x)                        # push path
    assert [h.pop() for _ in range(len(h))] == sorted(data)
    with pytest.raises(IndexError):
        h.pop()


def test_top_k():
    rng = random.Random(4)
    data = [rng.randrange(10_000) for _ in range(5000)]
    assert top_k(data, 10) == heapq.nlargest(10, data)
    assert top_k(data, 0) == []


# ---------- streaming ----------
def test_running_median():
    rng = random.Random(5)
    rm, seen = RunningMedian(), []
    for _ in range(1000):
        x = rng.gauss(0, 1)
        rm.add(x); seen.append(x)
        assert rm.median() == pytest.approx(statistics.median(seen))


def test_sliding_window_max():
    rng = random.Random(6)
    v = [rng.randrange(100) for _ in range(300)]
    for k in (1, 2, 7, 300):
        assert sliding_window_max(v, k) == [max(v[i:i + k]) for i in range(len(v) - k + 1)]


def test_running_mean_var_is_stable():
    data = [1e9 + x for x in (4.0, 7.0, 13.0, 16.0)]   # large offset breaks the naive formula
    rmv = RunningMeanVar()
    for x in data:
        rmv.add(x)
    assert rmv.mean == pytest.approx(statistics.mean(data))
    assert rmv.variance == pytest.approx(30.0)


# ---------- union-find and trie ----------
def test_union_find():
    uf = UnionFind(6)
    assert uf.union(0, 1) and uf.union(1, 2) and uf.union(3, 4)
    assert not uf.union(0, 2)            # already connected
    assert uf.connected(0, 2) and not uf.connected(2, 3)
    assert uf.groups == 3                # {0,1,2}, {3,4}, {5}


def test_trie():
    t = Trie()
    for w in ["USD", "USDJPY", "USDCAD", "EURUSD", "US"]:
        t.insert(w)
    assert t.contains("USD") and not t.contains("USDJ")
    assert t.starts_with("USDJ") and not t.starts_with("GBP")
    assert t.words_with_prefix("USD") == ["USD", "USDCAD", "USDJPY"]
    assert t.words_with_prefix("X") == []
