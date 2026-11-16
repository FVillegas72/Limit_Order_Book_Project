from decimal import Decimal
import unittest

import numpy as np

from evaluate import evaluate
from market import Market, draw_market
from matching import OfflineBook
from experiments import Session, GRID, ratio_se


class ExperimentTests(unittest.TestCase):
    def test_summary_against_price_time_tape(self):
        markets = [Market([.3,.3], [.1,0], [1,0,3,2]),
                   Market([1,.05], [.8,.4], [2,1,3,0])]
        markets += [draw_market(1+r%12, 2+r%9, seed=29, experiment=0, replication=r)
                    for r in range(32)]
        for m in markets:
            session, book = Session(m), OfflineBook(m)
            for a in GRID:
                alpha = Decimal(a).scaleb(-2)
                r = evaluate(book, alpha, alpha)
                expected = [r.auction.welfare, r.unrestricted.welfare, r.compatible.welfare,
                            len(r.auction.trades), sum(r.auction.buyer_utilities),
                            sum(r.auction.seller_utilities)]
                np.testing.assert_allclose(session.row(a), list(map(float, expected)),
                                           rtol=0, atol=1e-13)

    def test_ratio_zero_market_and_paired_uncertainty(self):
        x, y = np.array([0.,1.,2.]), np.array([0.,2.,4.])
        self.assertEqual(ratio_se(x,y), (.5,0.))
        self.assertTrue(np.isnan(ratio_se(x*0,y*0)[0]))
