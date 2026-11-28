# DRW: Posted Interview Questions

Questions candidates have publicly reported from DRW interviews, with full worked solutions,
grouped by topic and linked to the matching prep pages in this repo. Each term is explained the
first time it appears; a glossary is at the end.

**How to read this page.** Most public reports give a problem *title* or a one-line description,
not the exact wording. Where that is the case, the question below is written out in its standard
form; the solution and numbers are ours, checked by the code blocks (outputs shown are from real
runs). Sources are listed at the end; reports are from roughly 2016–2026, and third-party prep sites
are less reliable than first-hand reports. Practise each question for five minutes before reading
the answer.

Contents:

1. [The process, as reported](#1-the-process-as-reported)
2. [Probability and expected value](#2-probability-and-expected-value)
3. [Brainteasers and games](#3-brainteasers-and-games)
4. [Trading, market making and finance](#4-trading-market-making-and-finance)
5. [Statistics and linear algebra](#5-statistics-and-linear-algebra)
6. [Coding and data structures](#6-coding-and-data-structures)
7. [C++, systems and design](#7-c-systems-and-design)
8. [Checking the answers](#8-checking-the-answers)
9. [How to use this for the quant developer loop](#9-how-to-use-this-for-the-quant-developer-loop)
10. [Sources](#10-sources)
11. [Glossary](#11-glossary)

---

## 1. The process, as reported

| Stage | Engineering / quant developer | Quant trading / research |
|---|---|---|
| Online assessment (OA) | Coding test, most often reported on Codility: about 3 problems in 150 minutes, scored on correctness *and* performance. Some older reports mention HackerRank with C/C++/Java only. | About 6–7 questions in 45 minutes (researcher reports up to ~16 in 75 minutes): probability, expected value, statistics, Markov chains, linear algebra (including eigenvalues of an inverse and matrix calculus). Typed numeric answers; webcam-proctored. |
| Phone / video screen | About 45 minutes, technical plus behavioural; questions on past projects | Probability and brainteasers, answered quickly |
| Further rounds | Coding (often C++), data structures, CS fundamentals (memory, virtual memory, address spaces), design of trading components | Trading intuition and market making, more probability |
| Final / onsite | Several back-to-back technical and behavioural interviews; some reports mention a take-home | Several technical interviews; for some programmes a coding challenge and a trading simulation |

Reported themes: the process can take one to two months with several interviews; questions are
"classic but must be answered quickly"; and several candidates say to work through the "green
book" (*A Practical Guide to Quantitative Finance Interviews*, Xinfeng Zhou).

---

## 2. Probability and expected value

**Q1. Probability of n heads in a row; expected tosses until n heads in a row.**
- `P(n heads in n tosses) = 1/2ⁿ`.
- Expected tosses until n in a row: `E_n = 2^(n+1) − 2` (2, 6, 14 for n = 1, 2, 3).
- Why: to get n in a row you first need n − 1 in a row (`E_{n−1}`), then one more toss; with probability ½ it fails and you start over: `E_n = (E_{n−1} + 1) + ½·E_n`, so `E_n = 2E_{n−1} + 2`.
- See [probability P1](../probability/README.md#3-classic-problems).

**Q2. Probability of exactly 2 heads in 3 tosses.**
- `C(3, 2)·(½)³ = 3/8`. At least 2 heads: `3/8 + 1/8 = 1/2`.

**Q3. X and Y are i.i.d. (independent and identically distributed) positive random variables. Is `E[X/Y]` greater than, equal to, or less than 1?**
- `E[X/Y] = E[X]·E[1/Y]` (independence). `1/y` is convex, so by Jensen's inequality `E[1/Y] ≥ 1/E[Y]`. So `E[X/Y] ≥ E[X]/E[Y] = 1`, with equality only if Y is constant.
- Example: Uniform(1, 2): `1.5 × ln 2 ≈ 1.040`.
- Trap: symmetry suggests "X/Y and Y/X have the same distribution, so the mean is 1". They do have the same distribution, but that gives `E[X/Y] = E[Y/X]`, not 1.

**Q4. Expected absolute difference of two dice.**
- `E|D₁ − D₂| = Σ |i − j| / 36`. Differences 1..5 occur 10, 8, 6, 4, 2 times: `(10 + 16 + 18 + 16 + 10)/36 = 70/36 = 35/18 ≈ 1.94`.

**Q5. You roll a 20-sided die, your opponent a 6-sided die. Probability you roll strictly higher?**
- `P = Σ_{b=1}^{6} (1/6)·(20 − b)/20 = (19 + 18 + ... + 14)/120 = 99/120 = 33/40`.

**Q6. Shuffle a deck. Probability the ten of spades comes before all 12 face cards?**
- Only the relative order of these 13 cards matters, and each is equally likely to be first: `1/13`.

**Q7. Expected value of bills drawn without replacement.** (Standard form: a bag holds one bill each of $1, $5, $10, $20, $50, $100; draw 3 without replacement. Expected total?)
- Linearity: each draw has expected value equal to the mean bill, `186/6 = 31`, with or without replacement. `E = 3 × 31 = $93`.

**Q8. Optimal stopping card game.** (Standard form: draw cards one at a time from a shuffled deck; each red pays +$1 and each black −$1; you may stop at any time. What is the game worth?)
- Dynamic programming over (reds left, blacks left): `V(r, b) = max(0, [r(1 + V(r−1, b)) + b(−1 + V(r, b−1))] / (r + b))`, with `V(r, 0) = r` and `V(0, b) = 0`.
- Full deck: `V(26, 26) ≈ $2.62` (computed in section 8).
- Insight: you can always guarantee ≥ 0 by drawing the whole deck (the total is 0), so the option to stop is worth about $2.62.
- Related variant: "stop at any time and bet that the next card is red": the answer is exactly ½ whatever you do (the fraction of reds left is a martingale).

**Q9. Roll a die repeatedly until a roll equals the previous roll. Expected number of rolls?**
- After the first roll, each roll matches the previous with probability 1/6 (geometric): `E = 1 + 6 = 7`.

**Q10. HHT vs THH: which appears first, and with what probability?**
- `P(THH first) = 3/4`. THH wins unless the first two tosses are HH (probability ¼): any T before the first HH means THH completes first, because the T is followed by the HH.
- This is **Penney's game**: for any pattern, there is another that beats it more often than not.

**Q11. Expected waiting time for three consecutive heads.** `2⁴ − 2 = 14` (Q1).

**Q12. Gambler's ruin on a fair coin.** Start at $k, stop at $0 or $N: `P(reach N) = k/N`, expected duration `k(N − k)`. See [probability P7](../probability/README.md#3-classic-problems).

**Q13. The secretary problem.** n candidates in random order; accept or reject each immediately; maximise the chance of choosing the best.
- Reject the first `n/e` (about 37%), then take the first candidate better than all of those. `P(best) → 1/e ≈ 0.368`.

**Q14. Expected number of chord intersections inside a circle.** (Standard form: n chords, each joining two uniformly random points on the circle.)
- Two random chords cross with probability 1/3: of the 3 equally likely ways to pair up 4 random points, only 1 pairing crosses.
- Linearity over pairs: `E = C(n, 2)/3`.

**Q15. Conditional marble draw with three colours.** (Standard form: 3 red, 4 blue, 5 green; draw 2 without replacement. Given at least one red, probability both are red?)
- `P(both red) = C(3,2)/C(12,2) = 3/66`; `P(≥ 1 red) = 1 − C(9,2)/C(12,2) = 30/66`. Ratio: `1/10`.

**Q16. Gamma function ratio.** Compute `Γ(5.5)/Γ(3.5)`.
- `Γ(x + 1) = x·Γ(x)`, so `Γ(5.5) = 4.5 × 3.5 × Γ(3.5)` and the ratio is `15.75`. Also know `Γ(n) = (n − 1)!` and `Γ(½) = √π`.
- Related OA item: the area of the "squircle" `|x|⁴ + |y|⁴ ≤ 1` is `4Γ(1 + 1/4)² / Γ(1 + 1/2) ≈ 3.708`.

**Q17. Markov chain stationary distribution.** For transition matrix P, solve `π P = π`, `Σ πᵢ = 1`. Two states with `P(A→B) = p`, `P(B→A) = q`: `π_A = q/(p + q)`.

---

## 3. Brainteasers and games

**Q18. Twelve balls, one is heavier or lighter; find it with three weighings on a balance.**
- Weigh 4 vs 4.
- **If they balance**, the odd ball is among the other 4 (A, B, C, D), and the 8 weighed balls are known good (G). Weigh A B C vs G G G. If it balances, D is odd: weigh D vs G to find heavy or light. If it tips, you know the direction, and weighing A vs B finds the ball (if they balance, it is C).
- **If it tips** (say left side heavy), call the left balls H1–H4 ("maybe heavy") and the right balls L1–L4 ("maybe light"). Weigh H1 H2 L1 vs H3 L2 G:
  - balance → the odd ball is H4, L3 or L4: weigh L3 vs L4; the lighter one is it, and if they balance it is H4 (heavy);
  - left heavy → H1 or H2 heavy, or L2 light: weigh H1 vs H2; the heavier one is it, and if they balance it is L2;
  - left light → L1 light or H3 heavy: weigh L1 vs G; if L1 is lighter it is L1, otherwise H3.
- Insight: 3 weighings give 3³ = 27 outcomes, enough for 24 cases (12 balls × heavy/light).

**Q19. Marble piles: when does the first player win?** (Standard Nim: several piles; each turn take any number from one pile; whoever takes the last marble wins.)
- The first player wins exactly when the **XOR** (bitwise exclusive or) of the pile sizes is non-zero; the winning move makes it zero.

**Q20. Guess two-thirds of the average** (everyone picks 0–100; closest to ⅔ of the mean wins).
- The only Nash equilibrium (no one gains by changing alone) is 0, by repeated elimination: no one rational picks above 66.7, so no one picks above 44.4, and so on. In real games the winning number is usually 20–35: good answers discuss how rational you think the others are.

**Q21. Pirate game** (5 pirates, 100 coins, senior pirate proposes a split, a majority including the proposer must accept or he is thrown overboard).
- Work backwards from 2 pirates. The senior keeps 98 and gives 1 coin each to pirates 3 and 5 (counting the senior as 1): `98, 0, 1, 0, 1`.

**Q22. Market making the population guessing game.** ("Make me a market on the population of [a country / city]".)
- Give a two-sided quote (bid and ask) wide enough to be safe, e.g. "50 at 90 million". Update when the interviewer buys or sells (they know the answer, so their trades carry information). Narrow the spread as you learn. Say your reasoning: anchors, ranges, how confident you are.
- See [market making, adverse selection](../market-making/README.md#3-adverse-selection).

**Q23. The AKQ game** (a simplified poker game with a three-card deck, one card each, one bet).
- Standard form: each player gets one of A, K, Q. Player 1 may bet or check; if player 1 bets, player 2 calls or folds; the higher card wins.
- Player 1 bets the A always, checks the K, and bluffs with the Q some of the time. Player 2 calls with the A, folds the Q, and calls with the K some of the time.
- Indifference fixes both frequencies (pot P, bet B):
  - **Player 2 with the K** must be indifferent to calling. A call risks B to win P + B, so bluffs must make up `B/(P + 2B)` of player 1's bets. Player 1 bets every A, so if they bluff a Q with frequency q, then `q/(1 + q) = B/(P + 2B)`.
  - **Player 1 with the Q** must be indifferent to bluffing. A bluff loses B if called and wins P if not, so it must be called with probability `P/(P + B)`. Player 2 holds the A (always calls) or the K half the time each, so the K calls with frequency `c` where `½ + ½c = P/(P + B)`, giving `c = (P − B)/(P + B)`.
  - Example, pot 2 and bet 1: bluffs are ¼ of bets, so q = ⅓; the K calls ⅓ of the time. With a bet of pot size or bigger, the K never calls and the Q bluffs half the time.
- Insight: in optimal play you bluff *so that* the opponent cannot profit from either always calling or always folding.

---

## 4. Trading, market making and finance

**Q24. Fair value from the order book.** Bid 99.98 × 900, ask 100.02 × 100.
- **Microprice** = `(bid × ask_size + ask × bid_size) / (bid_size + ask_size) = 100.016`, above the mid of 100.000: the thin ask is likely to be taken next.

**Q25. Implied probabilities and bookmaker overround.** Decimal odds 2.10 / 3.40 / 3.60.
- Implied probability = `1/odds`. They sum to `1.0481`: the **overround** of 4.81% is the bookmaker's margin. Fair probabilities divide by the sum: 45.4%, 28.1%, 26.5%.

**Q26. Glosten-Milgrom zero-profit quotes.** The market maker sets bid = `E[value | a sell arrives]` and ask = `E[value | a buy arrives]`. The spread widens with the share of informed traders. Full derivation: [market making §3](../market-making/README.md#3-adverse-selection).

**Q27. VaR vs Expected Shortfall.** VaR (value at risk) is a loss quantile (e.g. the 99% one-day loss level); it says nothing about losses beyond it, and it is not subadditive (merging two books can show *more* VaR than the sum). Expected Shortfall is the average loss beyond VaR: it sees the tail and is subadditive. See [finance §4](../finance/README.md#4-risk-measures).

**Q28. Duration-neutral hedge with two bonds.** Long $10m of bond A (DV01 $850 per bp per $10m); hedge with bond B (DV01 $450 per $10m).
- `notional_B = −notional_A × DV01_A / DV01_B = −$18.89m`.

**Q29. Portfolio standard deviation with varying correlation.** 60/40 weights, vols 20% and 10%.
- `σ_p = √(w₁²σ₁² + w₂²σ₂² + 2w₁w₂ρσ₁σ₂)`: 8.0% at ρ = −1, 12.6% at 0, 14.4% at 0.5, 16.0% at +1 (a straight weighted average only at ρ = +1).

**Q30. Bond price change from duration and convexity.** Modified duration 7, convexity 60, price 100, yields +100 bp.
- `ΔP ≈ P(−D·Δy + ½·C·Δy²) = 100(−0.07 + 0.003) = −6.70`; duration alone says −7.00. Convexity always helps a long bond position.

**Q31. "Inflation news comes out higher than expected. What happens and what do you do?"** (reported for trading roles)
- Rates price more central bank hikes: front-end yields rise most (curve flattens), SOFR futures and Treasury futures fall, the dollar tends to rise, breakeven inflation rises. Then talk about positioning, risk limits and what is already priced in.

**Q32. Futures exchange data feed delay.** (Reported title only.) Likely angles: if your feed is slower than competitors', your quotes are stale when the price moves, so you get **picked off** (adverse selection). Expected loss ≈ probability of a price move during the delay × the move size × your quoted size; the fix is to widen or pull quotes when the market moves fast, and to measure latency per venue.

---

## 5. Statistics and linear algebra

**Q33. Inverse regression prediction bias.** You regress y on x and get slope `b_yx`. To predict x from y, can you use `1/b_yx`?
- No. `b_yx = ρ σ_y/σ_x` and `b_xy = ρ σ_x/σ_y`, so `b_yx · b_xy = ρ²`. Using `1/b_yx` instead of `b_xy` overstates the slope by `1/ρ²` and overreacts to extreme y. Each regression shrinks towards the mean in its own direction (regression to the mean).

**Q34. OLS vs ridge vs lasso.**
- **OLS** (ordinary least squares): minimise squared errors; unbiased but high variance when features are correlated.
- **Ridge**: adds `λ‖β‖²`; shrinks all coefficients smoothly; good with many correlated features.
- **Lasso**: adds `λ‖β‖₁`; sets some coefficients to exactly zero (feature selection); unstable when features are highly correlated.
- See [statistics §5](../statistics/README.md#5-regularisation).

**Q35. Eigenvalues of an inverse (and of polynomials of A).** If `A v = λ v`, then `A⁻¹ v = (1/λ) v` and `(A² + A) v = (λ² + λ) v`. Symmetric A with eigenvalues 2 and 5: `A⁻¹` has ½ and ⅕; `A² + A` has 6 and 30.

**Q36. Matrix calculus: derivative of an inverse.** From `A A⁻¹ = I`: `d(A⁻¹) = −A⁻¹ (dA) A⁻¹`. For a scalar parameter t: `d/dt A(t)⁻¹ = −A⁻¹ A′ A⁻¹`. Also: `∂(xᵀAx)/∂x = (A + Aᵀ)x`, `∂ log det A / ∂A = A⁻ᵀ`.

**Q37. Correlation between consecutive streak lengths.** (Reported title only; hard.) In fair coin tosses, successive run lengths are independent geometric variables, each with mean 2, so the correlation is 0. With a biased coin, heads-runs and tails-runs alternate with different means, but they are still independent. A good answer explains why: a run ends at the first change, after which the next run starts fresh. In a *fixed* number of tosses the run lengths must add up to the total, which makes consecutive runs slightly negatively correlated; say which version you are answering.

**Q38. Moments, covariance, CLT tails** (reported OA families). Know `Var(aX + bY) = a²Var X + b²Var Y + 2ab Cov(X, Y)`, and that a sample mean of n draws has standard deviation `σ/√n`: `P(mean > μ + 2σ/√n) ≈ 2.3%`.

---

## 6. Coding and data structures

Reported engineering topics: a queue from two stacks, a coin-change variant, merge sort, graph
algorithms, a rook on a chessboard with walls, median of a data stream, and order books.

**Q39–Q41. Queue from two stacks, merge sort, rook with walls.**

```python
from collections import deque


class TwoStackQueue:
    """Problem: a first-in-first-out queue using only two stacks.
    Approach: push onto `inbox`; to pop, if `outbox` is empty, move everything from
    inbox to outbox (which reverses the order), then pop from outbox.
    Cost: O(1) amortised per operation; each item moves between stacks once.
    """

    def __init__(self) -> None:
        self.inbox: list[int] = []
        self.outbox: list[int] = []

    def push(self, x: int) -> None:
        self.inbox.append(x)

    def pop(self) -> int:
        if not self.outbox:
            while self.inbox:
                self.outbox.append(self.inbox.pop())
        return self.outbox.pop()            # IndexError if the queue is empty


def merge_sort(a: list[int]) -> list[int]:
    """Problem: sort a list, stably, in O(n log n) even in the worst case.
    Approach: sort each half recursively, then merge the two sorted halves.
    Cost: O(n log n) time (a = 2, b = 2, d = 1), O(n) extra memory.
    """
    if len(a) <= 1:
        return a
    mid = len(a) // 2
    left, right = merge_sort(a[:mid]), merge_sort(a[mid:])
    out, i, j = [], 0, 0
    while i < len(left) and j < len(right):
        if left[i] <= right[j]:             # <= keeps equal items in order: stable
            out.append(left[i])
            i += 1
        else:
            out.append(right[j])
            j += 1
    return out + left[i:] + right[j:]


def rook_moves(board: list[str], start: tuple[int, int], goal: tuple[int, int]) -> int:
    """Problem: fewest rook moves from start to goal on a board with walls ('#').
    A move slides any number of empty squares in one direction, stopping before a
    wall or the edge (and it may stop on any square on the way).
    Approach: BFS where each node's neighbours are all squares reachable in one
    slide. Stop sliding in a direction once a square already has a smaller distance.
    Cost: O(rows x cols x (rows + cols)) time, O(rows x cols) memory.
    """
    rows, cols = len(board), len(board[0])
    dist = {start: 0}
    q = deque([start])
    while q:
        r, c = q.popleft()
        if (r, c) == goal:
            return dist[r, c]
        for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nr, nc = r + dr, c + dc
            while 0 <= nr < rows and 0 <= nc < cols and board[nr][nc] != "#":
                if (nr, nc) in dist and dist[nr, nc] <= dist[r, c]:
                    break                   # this ray was already explored at least as well
                if (nr, nc) not in dist:
                    dist[nr, nc] = dist[r, c] + 1
                    q.append((nr, nc))
                nr, nc = nr + dr, nc + dc
    return -1


q = TwoStackQueue()
for x in (1, 2, 3):
    q.push(x)
first = q.pop()
q.push(4)
print(first, q.pop(), q.pop(), q.pop())                  # 1 2 3 4
print(merge_sort([5, 2, 9, 1, 5, 6, 0]))                 # [0, 1, 2, 5, 5, 6, 9]
board = ["....#",
         ".##.#",
         "...#.",
         "#...."]
print(rook_moves(board, (0, 0), (3, 4)))                 # 4
```

Output:

```text
1 2 3 4
[0, 1, 2, 5, 5, 6, 9]
4
```

**Q42. Coin-change variant.** Fewest coins: `dp[a] = 1 + min(dp[a − c])`. Number of ways: `ways[a] += ways[a − c]`, looping over coins in the *outer* loop so each combination is counted once (inner loop over coins counts orderings instead). See [DSA §8](../dsa/README.md#8-dynamic-programming-and-backtracking).

**Q43. Median from a data stream.** Two heaps: a max-heap for the lower half and a min-heap for the upper half, sizes within one of each other. O(log n) per insert, O(1) per median. Code: [Python §12](../python/README.md#12-classic-implementations-with-code), [`streaming.py`](../../src/quantprep/classics/streaming.py).

**Q44. Codility-style OA problems** (titles reported by one prep site). "Maximum income, already holding one asset" is a best-time-to-buy-and-sell variant: track the best value of "holding" and "not holding" at each step (two-state DP). Practise medium array/DP/graph problems with a timer, and test edge cases yourself, because performance and hidden tests count.

---

## 7. C++, systems and design

**Q45. Fixed-size memory pool allocator.**

```cpp
// Fixed-size memory pool: O(1) allocate and free, no system calls on the hot path.
// Problem: orders are created and destroyed millions of times a second; malloc/new
// is too slow and unpredictable. Approach: one preallocated array of slots; free
// slots form a singly linked "free list" threaded through the slots themselves.
#include <cstddef>
#include <iostream>
#include <memory>
#include <new>
#include <utility>

template <class T>
class Pool {
    union Slot {                        // a slot holds either a T or the next free index
        Slot() {}
        ~Slot() {}
        T value;
        Slot* next;
    };
    std::unique_ptr<Slot[]> slots_;
    Slot* free_ = nullptr;
    std::size_t capacity_, used_ = 0;

public:
    explicit Pool(std::size_t n) : slots_(new Slot[n]), capacity_(n) {
        for (std::size_t i = 0; i < n; ++i)              // build the free list
            slots_[i].next = i + 1 < n ? &slots_[i + 1] : nullptr;
        free_ = n ? &slots_[0] : nullptr;
    }
    Pool(const Pool&) = delete;                          // owns raw memory: no copies
    Pool& operator=(const Pool&) = delete;

    template <class... Args>
    T* create(Args&&... args) {
        if (!free_) throw std::bad_alloc();
        Slot* s = free_;
        free_ = s->next;
        ++used_;
        return std::construct_at(&s->value, std::forward<Args>(args)...);  // placement new
    }
    void destroy(T* p) noexcept {
        std::destroy_at(p);                                  // run the destructor
        Slot* s = reinterpret_cast<Slot*>(p);                // value is at offset 0
        s->next = free_;
        free_ = s;
        --used_;
    }
    std::size_t used() const { return used_; }
    std::size_t capacity() const { return capacity_; }
};

struct Order {
    long id;
    long price_ticks;
    int qty;
};

int main() {
    Pool<Order> pool(3);
    Order* a = pool.create(1L, 10010L, 5);
    Order* b = pool.create(2L, 10020L, 3);
    std::cout << "used " << pool.used() << "/" << pool.capacity() << '\n';
    pool.destroy(a);
    Order* c = pool.create(3L, 9990L, 7);                    // reuses a's slot (LIFO)
    std::cout << "reused slot: " << std::boolalpha << (static_cast<void*>(c) == static_cast<void*>(a))
              << ", order " << c->id << " @ " << c->price_ticks << '\n';
    pool.create(4L, 10000L, 1);
    try {
        pool.create(5L, 10000L, 1);
    } catch (const std::bad_alloc&) {
        std::cout << "pool full at " << pool.used() << '\n';
    }
    pool.destroy(b);
    std::cout << "used " << pool.used() << '\n';
}
```

Output:

```text
used 2/3
reused slot: true, order 3 @ 9990
pool full at 3
used 2
```

Points to mention: O(1) allocate and free; no fragmentation (all slots the same size); good cache
locality (one contiguous block); not thread-safe as written (use one pool per thread, or a lock-free
free list with care about the ABA problem); and `construct_at`/`destroy_at` handle object lifetime.

**Q46. Order matching engine / order management system with price-time priority.** Limit, market, stop and cancel orders. Design:
- Prices as integer ticks; each side a sorted map from price to a FIFO queue; best price at `begin()`.
- Hash map from order ID to its location for O(1) cancel.
- Market orders sweep levels until filled; stop orders wait in a separate book keyed by trigger price and become market orders once the last trade crosses the trigger.
- Working C++ code: [DSA in C++ §8](../dsa/cpp.md#8-trading-flavoured-vwap-order-book-fenwick-tree); design: [system design, matching engine](../system-design/README.md).

**Q47. Automated trading system architecture.** Market data handler → normalised book → strategy/pricing → risk checks (position, order size, price bands, kill switch) → order gateway → exchange; drop copies to the position and P&L service. Talk about latency budgets, single-threaded hot paths, and what happens when each component fails. See [system design](../system-design/README.md).

**Q48. Virtual memory and address spaces** (reported follow-up to a coding question).
- Each process sees its own **virtual address space**; the hardware memory management unit (MMU) maps pages (usually 4 KB) to physical memory using page tables, cached in the TLB (translation lookaside buffer).
- Touching an unmapped page causes a **page fault**: the OS maps it (minor fault) or reads it from disk (major fault, milliseconds).
- Low-latency practice: pre-fault and lock memory (`mlock`), use huge pages (2 MB) to cut TLB misses, avoid allocation on the hot path.
- Layout of a process: code, static data, heap (grows up), memory-mapped regions, stack (grows down, per thread).

---

## 8. Checking the answers

```python
import math
from fractions import Fraction
from functools import cache
from itertools import product

import numpy as np

rng = np.random.default_rng(0)

# Expected absolute difference of two dice: sum |i - j| / 36
print("E|D1 - D2| =", Fraction(sum(abs(i - j) for i, j in product(range(1, 7), repeat=2)), 36))

# d20 vs d6: P(d20 strictly higher)
print("P(d20 > d6) =", Fraction(sum(a > b for a in range(1, 21) for b in range(1, 7)), 120))

# Chords from uniform endpoints: P(two random chords cross) = 1/3
a = rng.random((200_000, 4)) * 2 * math.pi
p1 = np.sort(a[:, :2], axis=1)
inside = (a[:, 2] > p1[:, 0]) & (a[:, 2] < p1[:, 1])
inside2 = (a[:, 3] > p1[:, 0]) & (a[:, 3] < p1[:, 1])
print(f"P(two chords cross) ~ {np.mean(inside != inside2):.4f} (exact 1/3)")


# Red/black card game: +1 per red, -1 per black, stop whenever you like
@cache
def value(r: int, b: int) -> float:
    """Best expected future gain with r red and b black cards left."""
    if r == 0:
        return 0.0
    if b == 0:
        return float(r)
    draw = (r * (1 + value(r - 1, b)) + b * (-1 + value(r, b - 1))) / (r + b)
    return max(0.0, draw)


print(f"red/black game value, full deck: {value(26, 26):.4f}")

# Squircle |x|^4 + |y|^4 <= 1: area = 4 Gamma(1 + 1/p)^2 / Gamma(1 + 2/p)
p = 4
area = 4 * math.gamma(1 + 1 / p) ** 2 / math.gamma(1 + 2 / p)
pts = rng.random((400_000, 2)) * 2 - 1
print(f"squircle area {area:.4f}, Monte Carlo {4 * np.mean((pts**4).sum(axis=1) <= 1):.4f}")
print(f"Gamma(5.5)/Gamma(3.5) = {math.gamma(5.5) / math.gamma(3.5):.4f} (= 4.5 x 3.5)")


# Penney's game: P(HHT appears before THH)
def first(a_pat: str, b_pat: str, trials: int = 40_000) -> float:
    wins = 0
    for _ in range(trials):
        s = ""
        while True:
            s += "H" if rng.random() < 0.5 else "T"
            if s.endswith(a_pat):
                wins += 1
                break
            if s.endswith(b_pat):
                break
    return wins / trials


print(f"P(HHT before THH) ~ {first('HHT', 'THH'):.3f} (exact 0.25)")

# Marbles: 3 red, 4 blue, 5 green; draw 2. P(both red | at least one red)
both = Fraction(math.comb(3, 2), math.comb(12, 2))
at_least_one = 1 - Fraction(math.comb(9, 2), math.comb(12, 2))
print("P(both red | >= 1 red) =", both / at_least_one)

# E[X / Y] for i.i.d. positive X, Y: >= 1 by Jensen. Example: Uniform(1, 2)
x, y = rng.uniform(1, 2, (2, 400_000))
print(f"E[X/Y] ~ {np.mean(x / y):.4f}  exact 1.5*ln 2 = {1.5 * math.log(2):.4f}")

# Roll a die until a roll matches the previous one: expected number of rolls = 1 + 6
counts = []
for _ in range(40_000):
    prev, n = int(rng.integers(6)), 1
    while True:
        cur, n = int(rng.integers(6)), n + 1
        if cur == prev:
            break
        prev = cur
    counts.append(n)
print(f"rolls until a repeat ~ {np.mean(counts):.3f} (exact 7)")
```

Output:

```text
E|D1 - D2| = 35/18
P(d20 > d6) = 33/40
P(two chords cross) ~ 0.3345 (exact 1/3)
red/black game value, full deck: 2.6245
squircle area 3.7081, Monte Carlo 3.7075
Gamma(5.5)/Gamma(3.5) = 15.7500 (= 4.5 x 3.5)
P(HHT before THH) ~ 0.248 (exact 0.25)
P(both red | >= 1 red) = 1/10
E[X/Y] ~ 1.0401  exact 1.5*ln 2 = 1.0397
rolls until a repeat ~ 7.013 (exact 7)
```

```python
import math

# Duration-neutral hedge: hold bond A, hedge with bond B so total DV01 = 0
dv01_a, dv01_b, notional_a = 850.0, 450.0, 10e6            # $ per bp per $10m / per $10m
hedge_b = -notional_a * dv01_a / dv01_b
print(f"sell ${-hedge_b / 1e6:.2f}m of bond B")            # ratio of DV01s

# Portfolio standard deviation as correlation varies
w1, w2, s1, s2 = 0.6, 0.4, 0.20, 0.10
for rho in (-1.0, 0.0, 0.5, 1.0):
    sd = math.sqrt(w1**2 * s1**2 + w2**2 * s2**2 + 2 * w1 * w2 * rho * s1 * s2)
    print(f"rho {rho:+.1f}: sd {sd:.2%}")

# Bond price change from duration and convexity
D, C, P, dy = 7.0, 60.0, 100.0, 0.01                       # modified duration, convexity
dP = P * (-D * dy + 0.5 * C * dy**2)
print(f"+100 bp: {dP:+.2f}  (duration alone {-P * D * dy:+.2f})")

# Bookmaker odds -> implied probabilities and overround
decimal_odds = {"home": 2.10, "draw": 3.40, "away": 3.60}
raw = {k: 1 / o for k, o in decimal_odds.items()}
overround = sum(raw.values()) - 1
fair = {k: round(v / sum(raw.values()), 4) for k, v in raw.items()}
print(f"overround {overround:.2%}, fair probabilities {fair}")

# Fair value off the order book: microprice weights each side by the OTHER side's size
bid, ask, bid_size, ask_size = 99.98, 100.02, 900, 100
micro = (bid * ask_size + ask * bid_size) / (bid_size + ask_size)
print(f"mid {(bid + ask) / 2:.3f}, microprice {micro:.3f}")
```

Output:

```text
sell $18.89m of bond B
rho -1.0: sd 8.00%
rho +0.0: sd 12.65%
rho +0.5: sd 14.42%
rho +1.0: sd 16.00%
+100 bp: -6.70  (duration alone -7.00)
overround 4.81%, fair probabilities {'home': 0.4543, 'draw': 0.2806, 'away': 0.265}
mid 100.000, microprice 100.016
```

---

## 9. How to use this for the quant developer loop

The analytics / quant developer loop draws mostly from sections 6–7 (coding, C++, systems) and
from probability and finance questions asked *quickly*. Priorities:

1. **Codility-style coding under time pressure**: 3 problems in 150 minutes, so practise with a timer and test performance and edge cases yourself. See [DSA](../dsa/README.md) and [DSA in C++](../dsa/cpp.md).
2. **C++ depth**: memory, virtual memory, allocators, containers and their costs, move semantics, concurrency basics.
3. **Fast probability**: Q1–Q17 aloud, under two minutes each.
4. **Finance numbers**: Q24–Q31, plus Greeks and DV01 from [analytics-dev](../analytics-dev/README.md).
5. **Past projects**: be ready to go two levels deep on every line of your CV.
6. **Behaviour**: [culture fit](../behavioral/culture-fit.md).

---

## 10. Sources

Candidate-reported questions and process details were taken from these public pages (accessed November 2026). Glassdoor pages could not be fetched directly; their content here is from search-result summaries.

- Glassdoor, DRW interview pages: [quantitative developer](https://www.glassdoor.com/Interview/DRW-Quantitative-Developer-Interview-Questions-EI_IE235115.0,3_KO4,26.htm), [quantitative trader](https://www.glassdoor.com/Interview/DRW-Quantitative-Trader-Interview-Questions-EI_IE235115.0,3_KO4,23.htm), [quantitative researcher](https://www.glassdoor.com/Interview/DRW-Quantitative-Researcher-Interview-Questions-EI_IE235115.0,3_KO4,27.htm), [software engineer](https://www.glassdoor.com/Interview/DRW-Software-Engineer-Interview-Questions-EI_IE235115.0,3_KO4,21.htm)
- [Quantt: DRW interview process, OA and questions](https://www.quantt.co.uk/resources/drw-interview)
- [QuantVault: DRW interview questions](https://quantvault.org/drw-interview-questions.html) and [interview process](https://quantvault.org/drw-interview-process.html)
- [Wall Street Oasis: DRW interviews](https://www.wallstreetoasis.com/company/drw/interview)
- [JoinTaro: DRW software engineer internship experience](https://www.jointaro.com/interviews/companies/drw/experiences/software-engineer-internship-london-england-october-1-2024-no-offer-positive-c520fb87/)
- [Blind: DRW senior software engineer interview](https://www.teamblind.com/post/drw-senior-software-engineer-interview-2fu5tboo)

---

## 11. Glossary

| Term | Meaning |
|---|---|
| ABA problem | In lock-free code, a value changes from A to B and back to A, fooling a compare-and-swap |
| Green book | *A Practical Guide to Quantitative Finance Interviews* (Xinfeng Zhou), a common prep book |
| i.i.d. | Independent and identically distributed |
| Jensen's inequality | For convex f, `E[f(X)] ≥ f(E[X])` |
| Microprice | Mid-price adjusted towards the side with less size: `(bid·ask_size + ask·bid_size)/(bid_size + ask_size)` |
| Nash equilibrium | A set of strategies where no player gains by changing theirs alone |
| Nim | A game of taking objects from piles; solved with the XOR of pile sizes |
| Overround | How much bookmaker implied probabilities sum above 100%: the bookmaker's margin |
| Page fault | Accessing a virtual page not currently mapped to physical memory |
| Penney's game | Two players pick coin patterns; the one appearing first wins; non-transitive |
| Picked off | Having a stale quote traded against by someone with newer information |
| TLB | Translation lookaside buffer: cache of virtual-to-physical page mappings |
| Virtual memory | Each process sees its own address space, mapped to physical memory by the OS and MMU |
