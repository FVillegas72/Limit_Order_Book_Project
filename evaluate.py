"""Per-realization welfare decomposition before any cross-market aggregation."""
from dataclasses import dataclass
from decimal import Decimal

from cda import Auction, simulate
from market import shade
from matching import Matching, OfflineBook


@dataclass(frozen=True)
class Evaluation:
    auction: Auction
    compatible: Matching
    unrestricted: Matching
    excluded_loss: Decimal
    greedy_loss: Decimal


def evaluate(book: OfflineBook, alpha_b=0, alpha_s=0):
    ab, ash = shade(alpha_b), shade(alpha_s)
    with book.market.arithmetic(ab, ash):
        auction = simulate(book.market, ab, ash)
        compatible = book.compatible(ab + ash)
        optimum = book.unrestricted()
        return Evaluation(auction, compatible, optimum,
                          optimum.welfare - compatible.welfare,
                          compatible.welfare - auction.welfare)
