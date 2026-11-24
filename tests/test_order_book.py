import pytest

from quantprep.systems.order_book import Fill, OrderBook


def test_resting_orders_and_best_prices():
    ob = OrderBook()
    assert ob.add_limit(1, "buy", 99, 10) == []
    assert ob.add_limit(2, "buy", 100, 5) == []
    assert ob.add_limit(3, "sell", 102, 7) == []
    assert (ob.best_bid(), ob.best_ask()) == (100, 102)
    assert ob.depth("buy") == [(100, 5), (99, 10)]


def test_price_then_time_priority():
    ob = OrderBook()
    ob.add_limit(1, "sell", 101, 5)   # first at 101
    ob.add_limit(2, "sell", 101, 5)   # second at 101
    ob.add_limit(3, "sell", 100, 5)   # better price, arrived last
    fills = ob.add_limit(4, "buy", 101, 12)
    assert fills == [Fill(4, 3, 100, 5), Fill(4, 1, 101, 5), Fill(4, 2, 101, 2)]
    assert ob.depth("sell") == [(101, 3)]
    assert ob.best_bid() is None      # fully filled, nothing rests


def test_partial_fill_rests_remainder():
    ob = OrderBook()
    ob.add_limit(1, "sell", 100, 3)
    fills = ob.add_limit(2, "buy", 100, 10)
    assert fills == [Fill(2, 1, 100, 3)]
    assert ob.best_bid() == 100 and ob.depth("buy") == [(100, 7)]
    assert ob.best_ask() is None


def test_no_trade_when_prices_do_not_cross():
    ob = OrderBook()
    ob.add_limit(1, "sell", 101, 3)
    assert ob.add_limit(2, "buy", 100, 3) == []
    assert (ob.best_bid(), ob.best_ask()) == (100, 101)


def test_cancel_removes_order_and_empty_level():
    ob = OrderBook()
    ob.add_limit(1, "buy", 100, 5)
    ob.add_limit(2, "buy", 100, 5)
    assert ob.cancel(1)
    assert not ob.cancel(1)                       # already cancelled
    assert ob.add_limit(3, "sell", 100, 5) == [Fill(3, 2, 100, 5)]   # skips cancelled #1
    assert ob.best_bid() is None
    assert not ob.cancel(2)                       # fully filled, can't cancel


def test_invalid_input():
    ob = OrderBook()
    ob.add_limit(1, "buy", 100, 5)
    with pytest.raises(ValueError):
        ob.add_limit(1, "buy", 100, 5)
    with pytest.raises(ValueError):
        ob.add_limit(2, "buy", 100, 0)
