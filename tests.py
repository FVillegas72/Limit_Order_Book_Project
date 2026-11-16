"""Independent oracles and regression cases for the Phase 1–2 model."""
from decimal import Decimal as D
from itertools import permutations, product
import unittest

from cda import simulate
from evaluate import evaluate
from market import Market, draw_market
from matching import OfflineBook


def enumerate_matchings(values, costs, tau):
    """Visit every partial injection, including the empty matching."""
    best_weight, largest = D(0), 0

    def visit(i, available, weight, count):
        nonlocal best_weight, largest
        if i == len(values):
            best_weight = max(best_weight, weight)
            largest = max(largest, count)
            return
        visit(i + 1, available, weight, count)
        for j in available:
            gap = values[i] - costs[j]
            if gap >= tau:
                visit(i + 1, available - {j}, weight + gap, count + 1)

    visit(0, set(range(len(costs))), D(0), 0)
    return best_weight, largest


def scan_book(market, ab, ash, floor_bids=False):
    """Independent slow oracle. Lists preserve time order for equal quotes."""
    b = len(market.values)
    bids = [v - ab for v in market.values]
    if floor_bids:
        bids = [max(D(0), p) for p in bids]
    asks = [c + ash for c in market.costs]
    buyers, sellers, trades = [], [], []
    for t, g in enumerate(market.arrival):
        if g < b:
            i = g
            candidates = [j for j in sellers if asks[j] <= bids[i]]
            if not candidates:
                buyers.append(i)
                continue
            j = min(candidates, key=asks.__getitem__)
            sellers.remove(j)
            price, resting = asks[j], "seller"
        else:
            j = g - b
            candidates = [i for i in buyers if bids[i] >= asks[j]]
            if not candidates:
                sellers.append(j)
                continue
            i = max(candidates, key=bids.__getitem__)
            buyers.remove(i)
            price, resting = bids[i], "buyer"
        trades.append((i, j, price, resting, t))
    return trades


def tape(result):
    return [(t.buyer, t.seller, t.price, t.resting_side, t.time) for t in result.trades]


class ModelTests(unittest.TestCase):
    def test_two_by_two_early_execution(self):
        m = Market([.90, .45], [.40, .80], [1, 2, 0, 3])
        book = OfflineBook(m)
        honest = evaluate(book)
        self.assertEqual(tape(honest.auction),
                         [(1, 0, D('.45'), 'buyer', 1), (0, 1, D('.90'), 'buyer', 3)])
        self.assertEqual(honest.auction.welfare, D('.15'))
        self.assertEqual(honest.greedy_loss, D('.35'))
        shaded = evaluate(book, '.125', '.125')
        self.assertEqual(tape(shaded.auction), [(0, 0, D('.525'), 'seller', 2)])
        self.assertEqual(shaded.auction.welfare, D('.50'))
        self.assertEqual((shaded.excluded_loss, shaded.greedy_loss), (0, 0))
        blocked = evaluate(book, '.30', '.30')
        self.assertEqual((blocked.excluded_loss, blocked.greedy_loss), (D('.50'), 0))

    def test_threshold_can_require_different_partners(self):
        book = OfflineBook(Market([.9, .6], [.1, .4], range(4)))
        self.assertEqual(book.compatible('.3').pairs, ((1, 0), (0, 1)))
        self.assertEqual(book.compatible('.3').welfare, 1)

    def test_cardinality_can_sacrifice_welfare(self):
        book = OfflineBook(Market([.9, .4], [.1, .6], range(4)))
        self.assertEqual(book.max_cardinality('.25'), 2)
        self.assertEqual(book.compatible('.25').pairs, ((0, 0),))
        self.assertEqual(book.compatible('.25').welfare, D('.8'))

    def test_price_time_priority(self):
        # A later better quote beats the older quote; best-price ties use FIFO.
        for m, expected in [
            (Market([.7, .9, .9], [.2, .2], [0, 2, 1, 3, 4]), [(2, 0), (1, 1)]),
            (Market([.9, .9], [.3, .1, .1], [2, 4, 3, 0, 1]), [(0, 2), (1, 1)])]:
            self.assertEqual([(t.buyer, t.seller) for t in simulate(m).trades], expected)

    def test_housekeeping_crosses_utilities_and_losses(self):
        for r in range(144):
            b, s = ((3, 11), (9, 9), (15, 4))[r % 3]
            m = draw_market(b, s, seed=701, experiment=2, replication=r)
            ab, ash = ((D(0), D(0)), (D('.12'), D('.18')),
                       (D('.45'), D('.25')), (D(1), D('.30')))[r % 4]
            result = evaluate(OfflineBook(m), ab, ash)
            a = result.auction
            self.assertEqual(tape(a), scan_book(m, ab, ash))
            buys, sells = set(), set()
            for t in a.trades:
                self.assertNotIn(t.buyer, buys)
                self.assertNotIn(t.seller, sells)
                buys.add(t.buyer)
                sells.add(t.seller)
                self.assertEqual(t.bid, m.values[t.buyer] - ab)
                self.assertEqual(t.ask, m.costs[t.seller] + ash)
                self.assertGreaterEqual(t.bid, t.ask)
                bt, st = m.arrival.index(t.buyer), m.arrival.index(b + t.seller)
                self.assertEqual(t.price, t.bid if bt < st else t.ask)
                self.assertEqual(a.buyer_utilities[t.buyer], m.values[t.buyer] - t.price)
                self.assertEqual(a.seller_utilities[t.seller], t.price - m.costs[t.seller])
            for utilities, executed in [(a.buyer_utilities, buys), (a.seller_utilities, sells)]:
                for i, u in enumerate(utilities):
                    self.assertGreaterEqual(u, 0)
                    if i not in executed:
                        self.assertEqual(u, 0)
            self.assertEqual(sum(a.buyer_utilities) + sum(a.seller_utilities), a.welfare)
            self.assertGreaterEqual(result.excluded_loss, 0)
            self.assertGreaterEqual(result.greedy_loss, 0)
            self.assertEqual(result.excluded_loss + result.greedy_loss,
                             result.unrestricted.welfare - a.welfare)

    def test_exhaustive_offline_oracle(self):
        markets = [Market(x[:2], x[2:], range(4))
                   for x in product([0, .5, 1], repeat=4)]
        markets += [draw_market(1 + r % 5, 1 + (r // 5) % 5, seed=318,
                                experiment=1, replication=r) for r in range(125)]
        for m in markets:
            book = OfflineBook(m)
            for tau in map(D, ['0', '.125', '.50', '1', '1.1']):
                w, k = enumerate_matchings(m.values, m.costs, tau)
                actual = book.compatible(tau)
                self.assertEqual((actual.welfare, book.max_cardinality(tau)), (w, k))
                self.assertEqual(len({i for i, j in actual.pairs}), len(actual.pairs))
                self.assertEqual(len({j for i, j in actual.pairs}), len(actual.pairs))
                gaps = [m.values[i] - m.costs[j] for i, j in actual.pairs]
                self.assertTrue(all(gap >= tau for gap in gaps))
                self.assertEqual(sum(gaps), w)
                if tau == 0:
                    self.assertEqual(book.unrestricted().welfare, w)
                    self.assertEqual(sum(m.values[i] - m.costs[j]
                                         for i, j in book.unrestricted().pairs), w)

    def test_truthful_tape_all_arrival_orders(self):
        for order in permutations(range(4)):
            m = Market([.9, .45], [.4, .8], order)
            self.assertEqual(tape(simulate(m)), scan_book(m, 0, 0))

    def test_equal_total_shading_and_equality_at_decimal_boundary(self):
        for order in permutations(range(4)):
            m = Market([.9, .3], [.1, .4], order)
            base = simulate(m, 0, '.2')
            for delta in map(D, ['.01', '.10', '.20']):
                a = simulate(m, delta, D('.20') - delta)
                expected = [(i, j, p - delta, side, t) for i, j, p, side, t in tape(base)]
                self.assertEqual(tape(a), expected)
                self.assertEqual(a.welfare, base.welfare)
        m = Market([.3], [.1], [1, 0])
        self.assertEqual(len(simulate(m, .1, .1).trades), 1)
        self.assertEqual(len(simulate(m, '.100000000000000000000000000001', '.1').trades), 0)
        self.assertEqual(OfflineBook(m).max_cardinality('.200000000000000000000000000001'), 0)

    def test_unclipped_quotes_and_domain_edges(self):
        m = Market([.05], [0], [0, 1])
        self.assertEqual(simulate(m, .1, 0).trades, ())
        self.assertEqual(len(scan_book(m, D('.1'), 0, floor_bids=True)), 1)
        for m in [Market([], [], []), Market([1], [], [0]), Market([], [0], [0])]:
            result = evaluate(OfflineBook(m))
            self.assertEqual((result.auction.welfare, result.compatible.pairs), (0, ()))
        m = Market([.5], [.5], [0, 1])
        self.assertEqual(len(simulate(m).trades), 1)
        self.assertEqual(OfflineBook(m).max_cardinality(0), 1)
        self.assertEqual(OfflineBook(m).unrestricted().pairs, ())
        with self.assertRaises(ValueError):
            Market([.1], [.2], [0, 0])
        with self.assertRaises(ValueError):
            simulate(m, -.1, 0)
        with self.assertRaises(ValueError):
            OfflineBook(m).compatible('NaN')

    def test_keyed_draw_and_common_random_numbers(self):
        keys = dict(seed=808, experiment=3, replication=7)
        m = draw_market(12, 17, **keys)
        draw_market(5, 2, **keys)
        self.assertEqual(m, draw_market(12, 17, **keys))
        self.assertNotEqual(m, draw_market(12, 17, **(keys | {'experiment': 1})))
        for ab in map(D, ['0', '.12', '.23']):
            self.assertEqual(tape(simulate(m, ab, ab)), scan_book(m, ab, ab, floor_bids=True))

    def test_reciprocal_sizes_under_reflection(self):
        for r in range(24):
            m = draw_market(5, 10, seed=94, experiment=7, replication=r)
            b, s = len(m.values), len(m.costs)
            reflected = Market([1 - c for c in m.costs], [1 - v for v in m.values],
                               [s + g if g < b else g - b for g in m.arrival])
            a = simulate(m, '.09', '.17')
            mirror = simulate(reflected, '.17', '.09')
            self.assertEqual([(t.seller, t.buyer, 1 - t.price) for t in a.trades],
                             [(t.buyer, t.seller, t.price) for t in mirror.trades])
            self.assertEqual(a.welfare, mirror.welfare)

    def test_large_uniform_unrestricted_benchmark(self):
        # Independent seeds. The fixed tolerance is in welfare per seller.
        s = 4096
        for b in [s // 2, s, 2 * s]:
            totals = [OfflineBook(draw_market(b, s, seed=229, experiment=1, replication=r))
                      .unrestricted().welfare for r in range(12)]
            empirical = float(sum(totals)) / (s * len(totals))
            self.assertLess(abs(empirical - b / (2 * (b + s))), .008)


if __name__ == '__main__':
    unittest.main(verbosity=2)
