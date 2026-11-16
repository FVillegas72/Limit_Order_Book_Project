"""Single-unit continuous double auction with raw additive quotes."""
from dataclasses import dataclass
from decimal import Decimal
from heapq import heappop, heappush

from market import Market, shade


@dataclass(frozen=True)
class Trade:
    buyer: int
    seller: int
    bid: Decimal
    ask: Decimal
    price: Decimal
    resting_side: str
    time: int


@dataclass(frozen=True)
class Auction:
    trades: tuple
    buyer_utilities: tuple
    seller_utilities: tuple
    welfare: Decimal


def simulate(market: Market, alpha_b=0, alpha_s=0) -> Auction:
    """Buyers have global IDs 0..b-1. Seller j has global ID b+j.
    Trade records use side-local IDs. Time is the zero-based execution arrival.
    """
    ab, ash = shade(alpha_b), shade(alpha_s)
    with market.arithmetic(ab, ash):
        bids = [v - ab for v in market.values]
        asks = [c + ash for c in market.costs]
        buyer_u = [Decimal(0)] * len(bids)
        seller_u = [Decimal(0)] * len(asks)
        buy_book, sell_book, trades = [], [], []
        welfare = Decimal(0)
        for time, trader in enumerate(market.arrival):
            if trader < len(bids):
                i = trader
                if not sell_book or bids[i] < sell_book[0][0]:
                    heappush(buy_book, (-bids[i], time, i))
                    continue
                price, _, j = heappop(sell_book)
                resting = "seller"
            else:
                j = trader - len(bids)
                if not buy_book or -buy_book[0][0] < asks[j]:
                    heappush(sell_book, (asks[j], time, j))
                    continue
                _, _, i = heappop(buy_book)
                price = bids[i]
                resting = "buyer"
            trades.append(Trade(i, j, bids[i], asks[j], price, resting, time))
            buyer_u[i] = market.values[i] - price
            seller_u[j] = price - market.costs[j]
            welfare += market.values[i] - market.costs[j]
        return Auction(tuple(trades), tuple(buyer_u), tuple(seller_u), welfare)
