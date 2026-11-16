"""Audit final tables and report finite-sample analytical checks independently."""
import hashlib
from pathlib import Path

import numpy as np
import pandas as pd

from experiments import COUNTS, GRID, FIXED

VALIDATION_SHA256 = {
    'validation_full.csv':'d192869feaedfcd764d3cd97e250000c279ebf53ec4a380f6a01bcb4d94b6b67',
    'validation_quick.csv':'25a9a2d4e214f132615349f812197081a25c1d96afeebacb19cd27d040ec8af0',
}


def validate_inputs():
    for name,expected in VALIDATION_SHA256.items():
        file = Path(__file__).parent/'validation'/name
        if hashlib.sha256(file.read_bytes()).hexdigest() != expected:
            raise ValueError(f'Archived validation mismatch: {file}')


def validate_outputs(out,mode):
    checks = []
    for i,name in enumerate(['shading_grid','holdout','scaling']):
        df = pd.read_csv(out/(name+'.csv'))
        assert (df.replications==COUNTS[mode][i]).all()
        assert not df.duplicated(['buyers','sellers','tau']).any()
        if name=='shading_grid':
            assert len(df)==12*len(GRID)
        if name=='scaling':
            assert len(df)==15*len(FIXED)
        assert (df.trades <= df[['buyers','sellers']].min(axis=1)).all()
        for observed,expected in [
            (df.excluded+df.greedy,df.star-df.cda),
            (df.buyer_aggregate+df.seller_aggregate,df.cda),
            (df.buyer_per_trader*df.buyers,df.buyer_aggregate),
            (df.seller_per_trader*df.sellers,df.seller_aggregate),
            (df.eta,df.R*df.off_eta), (df.eta,df.cda/df.star),
            (df.R,df.cda/df.off), (df.tau,2*df.alpha)]:
            np.testing.assert_allclose(observed,expected,atol=2e-9,rtol=2e-10)
        for r in df[df.alpha==0].itertuples():
            exact = r.buyers*r.sellers/(2*(r.buyers+r.sellers+1))
            checks.append(dict(experiment=r.experiment,buyers=r.buyers,sellers=r.sellers,
                               estimate=r.star,exact=exact,se=r.star_se,
                               standardized_error=(r.star-exact)/r.star_se))
    pd.DataFrame(checks).to_csv(out/'optimal_welfare_check.csv',index=False,float_format='%.12g')
