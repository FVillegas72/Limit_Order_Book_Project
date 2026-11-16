# Understanding Continuous Double Auctions, Their Applications and Equilibria in Limit Order Books

The results directory includes the CSVs and publication figures in PNG and vector PDF. AUDIT.md contains the finite and limiting offline proofs and model conventions.

## Run

Extract the archive and enter the cda_study directory. The recorded run used CPython 3.12.14. Use Python 3.11 or 3.12 with the pinned dependencies.

    python -m venv .venv
    source .venv/bin/activate
    python -m pip install -r requirements.txt
    python run_all.py --mode quick --workers 2
    python run_all.py --mode full --workers 4

On Windows, activate with .venv\Scripts\activate. A single worker works without multiprocessing. The number of workers affects wall time only. Default outputs are results/quick and results/full. Use --out PATH to reproduce in a separate directory. Both modes run all unit tests, experiments, accounting checks, and figures. The quick mode sizes and grids are identical but its Monte Carlo estimates are only for debugging. Run python -m unittest discover -p 'test*.py' for tests alone.

The two CSVs under validation are the user-supplied Phase 1–2 artifacts used as inputs. The runner checks their hashes. To independently regenerate these Phase 1–2 validations, run python validate_phase12.py --mode quick --output check_quick.csv and repeat with --mode full --output check_full.csv.

## Design

| Experiment ID | Sizes and shades | Quick / full replications per size pair |
|---|---|---|
| 31, welfare search | Balanced sides of 2, 5, 10, 20, 40, 100, 200 plus 40 and 320 sellers at ratios 0.5, 1, 2. Identical size pairs are computed once. Per-side α is 0 to 0.25 by 0.01. | 80 / 3,000 |
| 32, independent evaluation | Same sizes. Evaluate the selected shade, truthful, α = 0.01, α = 0.25, and the ratio-specific previous shade. | 96 / 4,096 |
| 33, fixed-shading scaling | 20, 40, 80, 160, 320 sellers at all three ratios. Total τ = 0, 0.26, 0.28, 0.32 for every size and ratio. | 96 / 4,096 |
| 41, deviation selection | 40 sellers and all three prior profiles. Ex-ante single-trader deviations for each side. | 80 / 3,000 |
| 42, independent deviation evaluation | Same profiles. Evaluate all deviations on fresh markets. | 96 / 8,192 |

The master seed is 20261115. Independent PCG64 streams use the Phase 1–2 keyed draw_market function. The seed key includes the experiment, buyer count, seller count, and zero-based replication. Repeated requests for a market within an experiment produce exactly the same profile and arrival order for all tested shades. Buyer and seller deviation experiments within a profile use the same draws. All prices are raw shifted quotes. The reference simulator uses Decimal and price-time heaps. The experiment loop uses exact integers on the market's own decimal scale and price heaps; homogeneous within-side shading makes equal-quote traders interchangeable for aggregate statistics. The tagged-deviator simulator keeps trader identity and arrival time. Only aggregation converts realized results to floating point.

## Code and tables

| File | Contents |
|---|---|
| market.py, cda.py, matching.py, evaluate.py | Phase 1–2 market generation, detailed trade ledger, unrestricted and compatible optima, and per-realization losses. |
| experiments.py | Aggregate replay, independent search/evaluation/scaling design, and paired mean and ratio uncertainties. |
| equilibrium.py | Tagged-trader order-book replay and independent finite-grid deviation checks. |
| plots.py | Figures, comparison tables |
| tests.py, test_experiments.py, test_equilibrium.py, check_results.py | Independent reference checks, analytical benchmarks and table accounting audits. |
| shading_grid.csv, holdout.csv, scaling.csv | All core metrics and Monte Carlo SEs by size and shade. |
| grid_peaks.csv, selected_shading.csv | Best search-grid value and statistically retained candidates. The integer selected column is in hundredths per side. The alpha, candidate_alphas, and tau columns are in original units. A tie in sample welfare selects the lowest grid value. |
| prior_comparison.csv, reflected_sizes.csv | Direct differences from earlier targets and comparisons of exactly swapped side sizes at common fixed thresholds. |
| optimal_welfare_check.csv | Measured unrestricted welfare versus the exact finite-market expectation. |
| deviations.csv, candidate_regret.csv | Each side's deviation utility and gain, independent confirmation, and profile-level maximum gain bounds. |
| run_config.json | Seed, stream IDs, sample counts, numerical environment and principal grids for the run. |

## Reading the metrics

Rows describe markets of the indicated integer sizes. cda, off and star are **mean total** CDA welfare, compatible optimal welfare, and unrestricted optimal welfare. excluded and greedy equal means of star − off and off − cda, respectively. trades is mean executed volume. buyer_aggregate and seller_aggregate average total utilities for each side. buyer_per_trader and seller_per_trader divide by the full corresponding population, including unexecuted orders. cda_per_seller normalizes market welfare by the number of sellers.

eta and R are ratios of expectations estimated by ratios of sample means with denominators star and off, respectively. off_eta is off/star, and eta = R × off_eta. excluded_share and greedy_share divide the corresponding mean loss by mean star. gain_eta is the paired shaded-minus-truthful welfare gain divided by mean star. gain_over_truth is the same gain in total welfare units. A zero denominator yields an undefined ratio, and individual zero-welfare realizations stay in the sample. _se is one Monte Carlo standard error. For a ratio r, the estimated SE is sd(X − rY)/(sqrt(n) × mean(Y)). Pointwise 95% intervals use ±1.96 SE. Reflecting independently sampled reciprocal markets gives the combined SE by adding the two variance estimates.

The grid peak set retains shades for which no rival demonstrates greater mean welfare after a within-size two-sided Bonferroni correction across 325 paired comparisons. The independent evaluation avoids reporting an optimistically selected sample maximum. Normal intervals are large-sample approximations and do not capture model uncertainty.

Deviation candidates are given in equilibrium.py. Deviations include 0 to 0.40 by 0.02, 0.50, 0.60, 0.80, 1.00 and the incumbent. A designated buyer or seller can choose a constant shade before learning their type. The mean gain is paired against the incumbent. Each candidate's 95% grid-regret interval takes maxima of simultaneous lower and upper bounds over both sides; it includes the zero-gain incumbent. These bounds apply to the specified finite grid. The comparisons do not establish equilibria against all constant shades or type-dependent Bayesian strategies.
