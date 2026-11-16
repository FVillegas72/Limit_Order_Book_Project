"""Market inputs, exact decimal arithmetic, and reproducible uniform draws."""
from dataclasses import dataclass
from decimal import Context, Decimal, MAX_EMAX, MIN_EMIN, localcontext
from operator import index

import numpy as np


def amount(x):
    """Floats mean their shortest printable decimal. Strings allow exact fixtures."""
    value = Decimal(str(x))
    if not value.is_finite():
        raise ValueError("Amounts must be finite")
    return value


def shade(x):
    value = amount(x)
    if value < 0:
        raise ValueError("Shading must be nonnegative")
    return value


@dataclass(frozen=True, init=False)
class Market:
    values: tuple
    costs: tuple
    arrival: tuple
    decimal_places: int

    def __init__(self, values, costs, arrival):
        values = tuple(map(amount, values))
        costs = tuple(map(amount, costs))
        participants = values + costs
        if any(x < 0 or x > 1 for x in participants):
            raise ValueError("Values and costs must be in [0, 1]")
        order = tuple(map(index, arrival))
        if len(order) != len(participants) or set(order) != set(range(len(order))):
            raise ValueError("Arrival must be a permutation of all participant IDs")
        places = max((max(0, -x.as_tuple().exponent) for x in participants), default=0)
        object.__setattr__(self, "values", values)
        object.__setattr__(self, "costs", costs)
        object.__setattr__(self, "arrival", order)
        object.__setattr__(self, "decimal_places", places)

    def arithmetic(self, *shades):
        """Enough digits for exact quotes, differences, and sums over the market."""
        places = max([self.decimal_places] + [-x.as_tuple().exponent for x in shades])
        integer_digits = max([1] + [x.adjusted() + 1 for x in shades])
        precision = integer_digits + places + len(str(len(self.arrival))) + 2
        return localcontext(Context(prec=precision, Emin=MIN_EMIN, Emax=MAX_EMAX))


def draw_market(n_buyers, n_sellers, *, seed, experiment, replication):
    """A given set of keys always yields the same profile and uniform permutation."""
    b, s = index(n_buyers), index(n_sellers)
    if min(b, s) < 0:
        raise ValueError("Side sizes must be nonnegative")
    keys = [index(x) for x in (seed, experiment, b, s, replication)]
    rng = np.random.Generator(np.random.PCG64(np.random.SeedSequence(keys)))
    return Market(rng.random(b), rng.random(s), rng.permutation(b + s))
