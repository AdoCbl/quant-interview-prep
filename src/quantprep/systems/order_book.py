"""A limit order book with price-time priority, the core of an exchange matching engine.

Rules:
- A buy order matches against the lowest-priced sell orders first (best price first).
- At the same price, the order that arrived first fills first (time priority, "first in,
  first out").
- Whatever is left of an incoming order after matching rests in the book at its price.

Data structures (the part interviewers care about):
- For each side, a dict  price -> deque of resting orders at that price, in arrival order.
- For each side, a sorted list of the prices that have orders, kept with bisect, so the best
  price is at one end of the list.
- A dict  order id -> order, so a cancel finds its order in O(1).
- Cancels are "lazy": the order is marked dead (quantity 0) and skipped when it reaches the
  front of its queue. That avoids an O(n) removal from the middle of a deque.

Prices are integers in ticks (the minimum price step), never floats, so that equal prices
always compare equal.

Real engines in C++ often replace the sorted list with an array indexed by tick (prices
cluster near the touch) and the deque with an intrusive linked list, but the logic is the same.
"""

import bisect
from collections import deque
from dataclasses import dataclass
from typing import Literal

Side = Literal["buy", "sell"]


@dataclass
class Order:
    order_id: int
    side: Side
    price: int        # in ticks
    qty: int          # remaining quantity; 0 means filled or cancelled


@dataclass(frozen=True)
class Fill:
    taker_id: int     # the incoming order
    maker_id: int     # the resting order it traded with
    price: int        # trades happen at the resting order's price
    qty: int


class OrderBook:
    def __init__(self) -> None:
        self._levels: dict[Side, dict[int, deque[Order]]] = {"buy": {}, "sell": {}}
        self._prices: dict[Side, list[int]] = {"buy": [], "sell": []}  # sorted ascending
        self._orders: dict[int, Order] = {}

    # ----- queries -----
    def best_bid(self) -> int | None:
        return self._prices["buy"][-1] if self._prices["buy"] else None

    def best_ask(self) -> int | None:
        return self._prices["sell"][0] if self._prices["sell"] else None

    def depth(self, side: Side, levels: int = 5) -> list[tuple[int, int]]:
        """[(price, total quantity)] from the best price outward."""
        prices = self._prices[side]
        ordered = reversed(prices) if side == "buy" else iter(prices)
        out = []
        for p in ordered:
            total = sum(o.qty for o in self._levels[side][p])
            if total:
                out.append((p, total))
            if len(out) == levels:
                break
        return out

    # ----- commands -----
    def add_limit(self, order_id: int, side: Side, price: int, qty: int) -> list[Fill]:
        if qty <= 0:
            raise ValueError("quantity must be positive")
        if order_id in self._orders:
            raise ValueError(f"duplicate order id {order_id}")
        fills = self._match(order_id, side, price, qty)
        remaining = qty - sum(f.qty for f in fills)
        if remaining > 0:
            self._rest(Order(order_id, side, price, remaining))
        return fills

    def cancel(self, order_id: int) -> bool:
        order = self._orders.pop(order_id, None)
        if order is None:
            return False          # unknown, or already fully filled
        order.qty = 0             # lazy delete: skipped when it reaches the front
        self._drop_dead_front(order.side, order.price)
        return True

    # ----- internals -----
    def _crosses(self, side: Side, limit: int, best: int) -> bool:
        return best <= limit if side == "buy" else best >= limit

    def _match(self, taker_id: int, side: Side, limit: int, qty: int) -> list[Fill]:
        other: Side = "sell" if side == "buy" else "buy"
        fills: list[Fill] = []
        while qty > 0:
            best = self.best_ask() if side == "buy" else self.best_bid()
            if best is None or not self._crosses(side, limit, best):
                break
            queue = self._levels[other][best]
            maker = queue[0]
            traded = min(qty, maker.qty)
            fills.append(Fill(taker_id, maker.order_id, best, traded))
            qty -= traded
            maker.qty -= traded
            if maker.qty == 0:
                self._orders.pop(maker.order_id, None)
            self._drop_dead_front(other, best)
        return fills

    def _rest(self, order: Order) -> None:
        levels = self._levels[order.side]
        if order.price not in levels:
            levels[order.price] = deque()
            bisect.insort(self._prices[order.side], order.price)
        levels[order.price].append(order)
        self._orders[order.order_id] = order

    def _drop_dead_front(self, side: Side, price: int) -> None:
        """Remove filled/cancelled orders from the front of a level, and empty levels."""
        queue = self._levels[side].get(price)
        if queue is None:
            return
        while queue and queue[0].qty == 0:
            queue.popleft()
        if not queue:
            del self._levels[side][price]
            prices = self._prices[side]
            prices.pop(bisect.bisect_left(prices, price))
