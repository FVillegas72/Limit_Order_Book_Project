"""Exploratory ex-ante one-trader deviations from three pre-specified profiles."""
from concurrent.futures import ProcessPoolExecutor
from heapq import heappush, heappop

import numpy as np
import pandas as pd
from scipy.stats import norm

from experiments import SEED, Session, mean_se
from market import draw_market

PROFILES = {20: (17,19), 40: (20,20), 80: (20,17)}
EQ_COUNTS = {'quick': (80,96), 'full': (3000,8192)}


def focal_utility(session, ab, ash, side, deviation):
    """Only the focal agent on one side deviates. All orders obey price-time priority."""
    target = 0 if side == 'buyer' else session.b
    bids, asks = [], []
    for time, g in enumerate(session.order):
        if g < session.b:
            v = session.values[g]
            quote = v - (deviation if g == target else ab) * session.cent
            if not asks or quote < asks[0][0]:
                heappush(bids, (-quote, time, g))
                continue
            price, _, seller = heappop(asks)
            buyer = g
        else:
            c = session.costs[g - session.b]
            quote = c + (deviation if g == target else ash) * session.cent
            if not bids or -bids[0][0] < quote:
                heappush(asks, (quote, time, g))
                continue
            neg_price, _, buyer = heappop(bids)
            price, seller = -neg_price, g
        if buyer == target:
            return (session.values[buyer] - price) / session.unit
        if seller == target:
            return (price - session.costs[seller - session.b]) / session.unit
    return 0.


def profile_job(args):
    mode, b, side = args
    s = 40
    ab, ash = PROFILES[b]
    incumbent = ab if side == 'buyer' else ash
    # Include the baseline exactly, and a no-trade option (shade 1.00).
    levels = sorted(set(range(0,41,2)) | {incumbent, 50, 60, 80, 100})
    rows, best = [], None
    for experiment, reps in zip((41,42), EQ_COUNTS[mode]):
        u = np.empty((reps,len(levels)))
        for r in range(reps):
            session = Session(draw_market(b,s,seed=SEED,experiment=experiment,replication=r))
            u[r] = [focal_utility(session, ab, ash, side, a) for a in levels]
        gains = u - u[:,[levels.index(incumbent)]]
        if experiment == 41:
            best = levels[int(np.argmax(gains.mean(axis=0)))]
        # Simultaneous 95% two-sided bounds within each candidate across both
        # roles and every non-incumbent grid deviation (Bonferroni).
        total_tests = sum(len(set(range(0,41,2)) | {x,50,60,80,100})-1 for x in (ab,ash))
        z = norm.isf(.025/total_tests)
        for j, a in enumerate(levels):
            gain, se = mean_se(gains[:,j])
            utility, utility_se = mean_se(u[:,j])
            rows.append(dict(experiment=experiment,replications=reps,buyers=b,sellers=s,rho=b/s,
                             alpha_b=ab/100,alpha_s=ash/100,side=side,deviation=a/100,
                             incumbent=incumbent/100,screen_selected=a==best,utility=utility,
                             utility_se=utility_se,gain=gain,gain_se=se,
                             simultaneous_lower=gain-z*se,simultaneous_upper=gain+z*se))
    return rows


def run(mode,out,workers):
    jobs = [(mode,b,side) for b in PROFILES for side in ('buyer','seller')]
    if workers > 1:
        with ProcessPoolExecutor(max_workers=workers) as pool:
            groups = list(pool.map(profile_job,jobs))
    else:
        groups = list(map(profile_job,jobs))
    frame = pd.DataFrame(row for group in groups for row in group)
    frame.to_csv(out/'deviations.csv',index=False,float_format='%.12g')
    rows = []
    for b,g in frame[frame.experiment==42].groupby('buyers'):
        high = g.loc[g.gain.idxmax()]
        rows.append(dict(buyers=b,sellers=40,rho=b/40,alpha_b=high.alpha_b,alpha_s=high.alpha_s,
                         max_grid_gain=high.gain,side=high.side,deviation=high.deviation,
                         simultaneous_lower=g.simultaneous_lower.max(),
                         simultaneous_upper=g.simultaneous_upper.max()))
    pd.DataFrame(rows).to_csv(out/'candidate_regret.csv',index=False,float_format='%.12g')
