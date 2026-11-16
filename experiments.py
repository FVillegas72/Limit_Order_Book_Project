"""Exact-price CDA experiments, with market-level paired uncertainty estimates."""
from concurrent.futures import ProcessPoolExecutor
from dataclasses import dataclass
from decimal import Decimal
from heapq import heappush, heappop
from itertools import combinations
from math import sqrt
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import norm

from market import draw_market
from matching import OfflineBook

SEED = 20261115
GRID = tuple(range(26))  # Hundredths of a unit per side
BALANCED = [2, 5, 10, 20, 40, 100, 200]
SELLERS = [20, 40, 80, 160, 320]
RATIOS = [.5, 1., 2.]
FIXED = (0, 13, 14, 16)
TARGET_ALPHA = {.5: 13, 1.: 16, 2.: 14}
COUNTS = {'quick': (80, 96, 96), 'full': (3000, 4096, 4096)}
FIELDS = ('cda', 'star', 'off', 'trades', 'buyer_aggregate', 'seller_aggregate')


class Session:
    """A common exact decimal grid for one market. No rounding or bid clipping."""
    def __init__(self, market):
        places = max(market.decimal_places, 2)
        self.unit = 10 ** places
        self.cent = self.unit // 100
        self.b = len(market.values)
        self.s = len(market.costs)
        with market.arithmetic(Decimal('.01')):
            values = [int(x * self.unit) for x in market.values]
            costs = [int(x * self.unit) for x in market.costs]
        self.values, self.costs = values, costs
        self.order = market.arrival
        # Use disjoint signs so that both a zero value and a zero cost are legal.
        events = values + [-1 - c for c in costs]
        self.events = [events[g] for g in market.arrival]
        self.offline = OfflineBook(market)
        self.star = float(self.offline.prefix[-1])

    def auction(self, a):
        shift = a * self.cent
        tau = 2 * shift
        bids, asks = [], []
        welfare = buyer_u = count = 0
        # Within-side quotes share a constant shift. Heaps can store true types.
        # Equal-priced traders have identical types; aggregates are FIFO-invariant.
        for event in self.events:
            if event >= 0:
                v = event
                if not asks or v - asks[0] < tau:
                    heappush(bids, -v)
                    continue
                gap = v - heappop(asks)
                buyer_u += gap - shift  # resting ask = c + shift
            else:
                c = -1 - event
                if not bids or -bids[0] - c < tau:
                    heappush(asks, c)
                    continue
                gap = -heappop(bids) - c
                buyer_u += shift  # resting bid = v - shift
            welfare += gap
            count += 1
        return welfare / self.unit, count, buyer_u / self.unit, (welfare - buyer_u) / self.unit

    def row(self, a):
        welfare, count, buyer, seller = self.auction(a)
        if a == 0:
            off = self.star
        else:
            # The audited size scan and welfare prefix; no need to build a certificate.
            k = self.offline.max_cardinality(Decimal(2 * a).scaleb(-2))
            off = float(self.offline.prefix[min(k, len(self.offline.prefix) - 1)])
        if not (0 <= welfare <= off + 1e-12 and off <= self.star + 1e-12):
            raise ArithmeticError('Welfare ordering failed')
        return welfare, self.star, off, count, buyer, seller


def ratio_se(x, y):
    """Delta method on paired market-level (numerator, denominator) observations."""
    if y.mean() == 0:
        return np.nan, np.nan
    ratio = x.mean() / y.mean()
    se = (x - ratio * y).std(ddof=1) / (sqrt(len(x)) * y.mean())
    return ratio, se


def mean_se(x):
    return x.mean(), x.std(ddof=1) / sqrt(len(x))


@dataclass(frozen=True)
class Design:
    experiment: int
    b: int
    s: int
    levels: tuple
    reps: int


def summarize(design):
    d = design
    data = np.empty((d.reps, len(d.levels), len(FIELDS)))
    for r in range(d.reps):
        market = draw_market(d.b, d.s, seed=SEED, experiment=d.experiment, replication=r)
        session = Session(market)
        for j, level in enumerate(d.levels):
            data[r, j] = session.row(level)
    baseline = data[:, d.levels.index(0), 0]
    rows = []
    for j, level in enumerate(d.levels):
        w, star, off, vol, buyer, seller = data[:, j].T
        row = dict(experiment=d.experiment, buyers=d.b, sellers=d.s, rho=d.b/d.s,
                   replications=d.reps, alpha=level/100, tau=level/50)
        for name, x in zip(FIELDS, data[:, j].T):
            row[name], row[name+'_se'] = mean_se(x)
        for name, x in [('excluded', star-off), ('greedy', off-w),
                        ('buyer_per_trader', buyer/d.b), ('seller_per_trader', seller/d.s),
                        ('cda_per_seller', w/d.s), ('gain_over_truth', w-baseline)]:
            row[name], row[name+'_se'] = mean_se(x)
        for name, x, y in [('eta', w, star), ('R', w, off), ('off_eta', off, star),
                           ('gain_eta', w-baseline, star),
                           ('excluded_share', star-off, star), ('greedy_share', off-w, star)]:
            row[name], row[name+'_se'] = ratio_se(x, y)
        rows.append(row)
    best = int(np.argmax(data[:, :, 0].mean(axis=0)))
    peak = {}
    if d.experiment == 31:
        # Approximate simultaneous family of pairwise normal intervals within this market size.
        pairs = list(combinations(range(len(d.levels)), 2))
        z = norm.isf(.025 / len(pairs))
        candidates = set(d.levels)
        for i, j in pairs:
            delta, se = mean_se(data[:, i, 0] - data[:, j, 0])
            if delta > z * se:
                candidates.discard(d.levels[j])
            elif delta < -z * se:
                candidates.discard(d.levels[i])
        peak = dict(buyers=d.b, sellers=d.s, rho=d.b/d.s, selected=d.levels[best],
                    candidate_alphas=' '.join(f'{a/100:.2f}' for a in sorted(candidates)))
    return rows, peak


def run_jobs(jobs, workers):
    if workers == 1:
        return [summarize(d) for d in jobs]
    with ProcessPoolExecutor(max_workers=workers) as pool:
        return list(pool.map(summarize, jobs))


def save_table(results, out, name):
    frame = pd.DataFrame(row for rows, _ in results for row in rows)
    frame.to_csv(out / (name+'.csv'), index=False, float_format='%.12g')
    return frame


def run(mode, out: Path, workers):
    out.mkdir(parents=True, exist_ok=True)
    n_grid, n_holdout, n_scale = COUNTS[mode]
    sizes = sorted({(n,n) for n in BALANCED} |
                   {(int(s*r),s) for s in [40,320] for r in RATIOS})
    grid_jobs = [Design(31,b,s,GRID,n_grid) for b,s in sizes]
    grid = run_jobs(grid_jobs, workers)
    save_table(grid, out, 'shading_grid')
    peaks = pd.DataFrame(p for _,p in grid)
    peaks.to_csv(out/'grid_peaks.csv', index=False)
    print(f'Grid complete: {len(sizes)} size pairs', flush=True)
    jobs = []
    for p in peaks.itertuples():
        # Also evaluate the first and last grid points and the previously reported shade.
        levels = {0, 1, 25, p.selected, TARGET_ALPHA[p.rho]}
        jobs.append(Design(32, p.buyers, p.sellers, tuple(sorted(levels)), n_holdout))
    held = save_table(run_jobs(jobs, workers), out, 'holdout')
    selected = held.merge(peaks, on=['buyers','sellers','rho'])
    selected = selected[np.rint(100*selected.alpha) == selected.selected]
    truth = held[held.alpha == 0][['buyers','sellers','eta','eta_se','cda','trades']]
    truth = truth.rename(columns={k:'truth_'+k for k in ['eta','eta_se','cda','trades']})
    selected.merge(truth, on=['buyers','sellers']).to_csv(
        out/'selected_shading.csv', index=False, float_format='%.12g')
    print('Independent evaluation complete', flush=True)
    jobs = [Design(33,int(s*r),s,FIXED,n_scale) for s in SELLERS for r in RATIOS]
    save_table(run_jobs(jobs, workers), out, 'scaling')
    print('Fixed-shading scaling complete', flush=True)
