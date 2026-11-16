from decimal import Decimal
import unittest

from cda import simulate
from equilibrium import focal_utility
from experiments import Session
from market import Market, draw_market


class DeviationTests(unittest.TestCase):
    def test_focal_side_truth_and_nontrivial_deviation(self):
        for r in range(25):
            m = draw_market(6,9,seed=17,experiment=9,replication=r)
            before = simulate(m,'.17','.19')
            session = Session(m)
            for side,base,utilities in [('buyer',17,before.buyer_utilities),
                                        ('seller',19,before.seller_utilities)]:
                self.assertEqual(focal_utility(session,17,19,side,base),float(utilities[0]))
                # Raising an individual's shading by .04 has the same quotes as
                # changing only its true type and retaining uniform side shading.
                values,costs = list(m.values),list(m.costs)
                if side=='buyer':
                    values[0] -= Decimal('.04')
                else:
                    costs[0] += Decimal('.04')
                if values[0] < 0 or costs[0] > 1:
                    continue
                modified = simulate(Market(values,costs,m.arrival),'.17','.19')
                trades = [t for t in modified.trades if getattr(t,side)==0]
                u = 0 if not trades else (m.values[0]-trades[0].price if side=='buyer'
                                          else trades[0].price-m.costs[0])
                self.assertEqual(focal_utility(session,17,19,side,base+4),float(u))
