"""Run the tested experiments and regenerate the Phase 3–4 deliverables."""
import argparse
import json
import os
from pathlib import Path
import platform
import unittest
from importlib.metadata import version

from check_results import validate_inputs, validate_outputs
import experiments
import equilibrium
import plots


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--mode',choices=['quick','full'],default='quick')
    ap.add_argument('--workers',type=int,default=min(4,os.cpu_count() or 1))
    ap.add_argument('--out',type=Path,help='Destination directory for the selected mode')
    opts=ap.parse_args()
    if opts.workers<1:
        ap.error('--workers must be positive')
    validate_inputs()
    base=Path(__file__).resolve().parent
    suite=unittest.defaultTestLoader.discover(str(base),pattern='test*.py')
    if not unittest.TextTestRunner(verbosity=2).run(suite).wasSuccessful():
        raise SystemExit(1)
    out=opts.out or base/'results'/opts.mode
    experiments.run(opts.mode,out,opts.workers)
    validate_outputs(out,opts.mode)
    equilibrium.run(opts.mode,out,opts.workers)
    plots.render(out)
    meta=dict(mode=opts.mode,python=platform.python_version(),seed=experiments.SEED,
              grid_reps=experiments.COUNTS[opts.mode][0],
              holdout_reps=experiments.COUNTS[opts.mode][1],
              scaling_reps=experiments.COUNTS[opts.mode][2],
              deviation_reps=equilibrium.EQ_COUNTS[opts.mode],grid_cents=list(experiments.GRID),
              fixed_scaling_tau=[a/50 for a in experiments.FIXED],
              balanced_sizes=experiments.BALANCED,imbalance_sellers=[40,320],
              scaling_sellers=experiments.SELLERS,ratios=experiments.RATIOS,
              experiment_ids=dict(grid=31,holdout=32,scaling=33,screen=41,confirmation=42),
              packages={s:version(s) for s in ['numpy','pandas','scipy','matplotlib','reportlab']})
    (out/'run_config.json').write_text(json.dumps(meta,indent=2)+'\n')
    print(f'Completed {opts.mode} run in {out}')


if __name__=='__main__':
    main()
