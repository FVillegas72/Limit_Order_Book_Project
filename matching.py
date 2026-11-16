"""Offline welfare for a graph defined by a common surplus threshold."""
from dataclasses import dataclass
from decimal import Decimal

from market import Market, shade


@dataclass(frozen=True)
class Matching:
    pairs: tuple
    welfare: Decimal


class OfflineBook:
    """Sort once per realization, then reuse for any number of thresholds."""

    def __init__(self, market: Market):
        self.market = market
        self.buyers = sorted(range(len(market.values)), key=market.values.__getitem__,
                             reverse=True)
        self.sellers = sorted(range(len(market.costs)), key=market.costs.__getitem__)
        self.prefix = [Decimal(0)]
        with market.arithmetic():
            for i, j in zip(self.buyers, self.sellers):
                marginal = market.values[i] - market.costs[j]
                if marginal <= 0:
                    break
                self.prefix.append(self.prefix[-1] + marginal)

    def unrestricted(self):
        k = len(self.prefix) - 1
        pairs = tuple(zip(self.buyers[:k], self.sellers[:k]))
        return Matching(pairs, self.prefix[k])

    def max_cardinality(self, tau):
        """Count feasible pairs by spending the weakest sufficient buyer first."""
        threshold = shade(tau)
        market = self.market
        k = 0
        with market.arithmetic(threshold):
            for i in reversed(self.buyers):
                if k == len(self.sellers):
                    break
                if market.values[i] - market.costs[self.sellers[k]] >= threshold:
                    k += 1
        return k

    def compatible(self, tau):
        k = min(self.max_cardinality(tau), len(self.prefix) - 1)
        # Weakest selected buyer with cheapest selected seller, up to strongest.
        pairs = tuple(zip(reversed(self.buyers[:k]), self.sellers[:k]))
        return Matching(pairs, self.prefix[k])
