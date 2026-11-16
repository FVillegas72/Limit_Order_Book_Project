"""Run all Phase 1–2 checks and regenerate the offline benchmark validation CSV."""
import argparse
import csv
from math import sqrt
from pathlib import Path
from statistics import mean, stdev
import unittest

from market import draw_market
from matching import OfflineBook
from tests import ModelTests

SEED = 17641
EXPERIMENT = 12
THRESHOLDS = ('0', '.30', '.60')
MEASURES = ('q_star', 'w_star', 'q_max', 'q_off', 'w_off')
MODES = {'quick': ((128, 512), 8), 'full': ((128, 4096), 64)}


def benchmarks(b, s, tau):
    rho = b / s
    q_star = rho / (1 + rho)
    q_max = min(rho, 1) * max(1 - tau, 0)
    q_off = min(q_max, q_star)
    w_off = q_off - (1 + 1 / rho) * q_off ** 2 / 2
    return (q_star, q_star / 2, q_max, q_off, w_off)


def validation_rows(mode):
    sizes, reps = MODES[mode]
    for s in sizes:
        for b in [s // 2, s, 2 * s]:
            samples = {tau: [] for tau in THRESHOLDS}
            for r in range(reps):
                market = draw_market(b, s, seed=SEED, experiment=EXPERIMENT, replication=r)
                book = OfflineBook(market)
                star = book.unrestricted()
                for tau in THRESHOLDS:
                    feasible = book.compatible(tau)
                    samples[tau].append((len(star.pairs) / s, float(star.welfare) / s,
                                         book.max_cardinality(tau) / s, len(feasible.pairs) / s,
                                         float(feasible.welfare) / s))
            for tau in THRESHOLDS:
                limits = benchmarks(b, s, float(tau))
                row = dict(seed=SEED, experiment=EXPERIMENT, replications=reps,
                           buyers=b, sellers=s, rho=b / s, tau=tau,
                           exact_E_w_star=b / (2 * (b + s + 1)), exact_E_q_star=b / (b + s))
                for name, data, limit in zip(MEASURES, zip(*samples[tau]), limits):
                    row[name + '_mean'] = mean(data)
                    row[name + '_se'] = stdev(data) / sqrt(reps)
                    row[name + '_limit'] = limit
                yield row


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--mode', choices=MODES, default='quick')
    parser.add_argument('--output', type=Path, help='Override the default CSV path')
    args = parser.parse_args()
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(ModelTests)
    if not unittest.TextTestRunner(verbosity=2).run(suite).wasSuccessful():
        raise SystemExit(1)
    rows = list(validation_rows(args.mode))
    out = args.output or Path(__file__).parent / 'results' / f'validation_{args.mode}.csv'
    out.parent.mkdir(exist_ok=True, parents=True)
    with out.open('w', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=rows[0])
        writer.writeheader()
        writer.writerows(rows)
    print(f'Wrote {len(rows)} benchmark rows to {out}')


if __name__ == '__main__':
    main()
