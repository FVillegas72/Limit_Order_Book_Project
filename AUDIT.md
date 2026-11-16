# Offline matching and the uniform-market benchmarks

## Finite market

Write the values in decreasing order as $v_1,\ldots,v_b$ and costs in increasing order as $c_1,\ldots,c_s$. For any feasible cardinality $k$, the top $k$ values and bottom $k$ costs are feasible. Start with a witness, replace any selected buyer by a higher-valued unselected buyer and any selected seller by a cheaper unselected seller. Each replacement preserves every edge used. The greatest welfare at size $k$ is therefore

$$F(k)=\sum_{i=1}^k (v_i-c_i),\qquad F(0)=0.$$

Feasibility of these sets is equivalent to $v_{k+1-i}\ge c_i+\tau$ for every $i=1,\ldots,k$. Sufficiency follows by matching in this order. If the inequality fails at $i$, the $i$ lowest selected buyers can use at most the $i-1$ cheapest selected sellers. This proves necessity.

Compute the maximum feasible count $K$ by scanning buyers in ascending order with a pointer to the cheapest remaining seller. Skip a buyer who cannot afford that seller even after allowing for the threshold. Otherwise assign this seller to this buyer and advance the pointer. To see optimality, consider a maximum matching of the remaining market. When the buyer can trade, some maximum matching pairs these two traders. If either one is unused, replace its counterpart's match. If both have other partners, swap their partners. The other buyer is at least as strong, and the freed seller was affordable to the current buyer. If both are unused, matching them would increase cardinality. This proves the greedy step by induction. Use this scan for the count only.

Every count from 0 to $K$ is feasible by deletion. The increments $v_i-c_i$ of $F$ are nonincreasing. If $k^*$ counts the strictly positive increments up to $\min(b,s)$, the smallest constrained welfare-maximizing count is $k_\tau=\min(k^*,K)$. Use the low-to-high pairing on the corresponding extreme sets to return a matching certificate. Zero marginal increments are omitted offline. The CDA itself executes quote equality. Sorting costs $O(N\log N)$ for $N=b+s$. Each threshold query after sorting takes $O(N)$ time and the complete implementation uses $O(N)$ space.

* Pairing failure. With $v=(.90,.60)$, $c=(.10,.40)$ and $\tau=.30$, testing top against bottom gives gaps $.80,.20$ and wrongly returns $.80$. The compatible pairs $(.60,.10)$ and $(.90,.40)$ give $1.00$.
* Cardinality failure. With $v=(.90,.40)$, $c=(.10,.60)$ and $\tau=.25$, two feasible trades give $.60$ together. The single pair $(.90,.10)$ gives $.80$.

## Uniform large-market limit

Assume $s=m$, $b/m\to\rho>0$, and independent uniform values and costs. At rank $xm$ from the top of demand and the bottom of supply, respectively, the endpoints approach $1-x/\rho$ and $x$. Uniform convergence of the empirical distribution functions for the two uniform samples gives uniform quantile errors tending to zero, including near the extremes. Under nested samples this holds almost surely. Equivalently the limits below hold in probability for freshly drawn markets.

For $k/m\to q$ with $0\le q\le\min(1,\rho)$, the best possible welfare per seller at this size, when feasible, approaches
$$f(q)=\int_0^q[1-x/\rho-x]dx=q-\tfrac12(1+1/\rho)q^2.$$
Its unrestricted maximizer is $q^*=\rho/(1+\rho)$ and $w^*=f(q^*)=\rho/[2(1+\rho)]$.

For feasibility, sort the selected buyers from the lowest up. At position $xm$ among them their value approaches $1-q/\rho+x/\rho$. Compare with cost $x$. The limiting minimum compatible-pair surplus is the smaller endpoint of this affine difference on $[0,q]$,
$$\min(1-q/\rho,1-q).$$
Thus $q\le\min(1,\rho)(1-\tau)$ for $0\le\tau\le1$. For any positive volume strictly inside this bound the minimum has slack, and uniform quantile convergence implies feasibility with probability tending to one. Above the bound there is either a strict shortfall or insufficient traders. Squeezing between interior and exterior volumes gives the limit of $K/m$, even when feasibility at the exact boundary varies across samples. At $\tau=1$ only an endpoint pair could trade, with probability zero. At $\tau>1$ the graph is empty.

Consequently $q_{\max}=\min(1,\rho)(1-\tau)_+$, $q_\tau=\min(q^*,q_{\max})$, and $w_{\rm off}=f(q_\tau)$. The offline welfare plateau is $0\le\tau\le\delta(\rho)=\min(1,\rho)/(1+\rho)$, inclusive. In common per-side shading the boundary is $\alpha=\delta/2$. All volumes and normalized welfare are bounded, so the expectation limits hold too. These statements concern the offline benchmarks. The CDA efficiency and the common shading that maximizes expected CDA welfare require separate analysis.

## Exact finite-sample check

Initially the $s$ units belong to sellers. An unrestricted efficient allocation leaves the units with the top $s$ of the pooled $N=b+s$ values and costs, treating a seller's cost as the value of retaining the unit. Subtract the initial sum of sellers' costs from the final sum of the top $s$ pooled draws. Since the $r$-th ascending uniform order statistic has expectation $r/(N+1)$, this gives $E[W^*]=bs/[2(N+1)]$. The efficient count is the number of buyers in those top $s$ positions, so $E[k^*]=bs/N$ for $N>0$. This gives a sharper simulation check than the limit for small markets.

## Online matching and welfare

With one constant shade per side, a different split of the same total moves all submitted quotes by the same constant. For instance increasing buyer shading by $d$ and decreasing seller shading by $d$ lowers every quote and execution price by $d$. Book priority, crossing decisions and hence all matched identities are preserved by induction. Executed buyers gain $d$ and executed sellers lose $d$ apiece. Negative bids are allowed. With strictly positive asks almost surely, replacing negative bids by zero cannot create a trade, provided the relative arrival order of other traders is preserved. A deliberately constructed zero-cost, zero-shade seller can distinguish the two rules at the boundary.

For every realization, $W_{\rm CDA}\le W_{\rm off}\le W^*$. Set $L_{\rm excluded}=W^*-W_{\rm off}$ and $L_{\rm greedy}=W_{\rm off}-W_{\rm CDA}$. They sum to the full welfare gap. Later experiments should aggregate numerators and denominators separately for $\eta=E[W_{\rm CDA}]/E[W^*]$ and $R=E[W_{\rm CDA}]/E[W_{\rm off}]$. An individual observation with zero optimal welfare contributes its zeros to those sums. A zero aggregate denominator makes the corresponding ratio undefined.

A further exact symmetry is available for future checks. Transform each buyer of value $v$ to a seller of cost $1-v$, each seller of cost $c$ to a buyer of value $1-c$, preserve the arrival sequence and swap the side-specific shades. Each match has the same surplus and mirrored price $1-p$. Joint uniformity therefore makes the welfare laws identical for sizes $(b,s)$ and $(s,b)$ with common shading. Holding the seller population fixed while changing the ratio from $1/2$ to $2$ compares different total market sizes, so exact equality does not follow.

## Literature conventions

Zhan and Friedman (2007) examine three markup rules. Their standard rule is multiplicative. In the original shift specification (p. 2990) the value range is 0 to 200 and the shift on each side is 100 times their markup parameter. On the unit interval this gives a per-side shade equal to half their parameter. Under common shifting their parameter therefore equals our total shading. Their Figure 6 separates losses by trader position relative to the competitive equilibrium price, while our decomposition uses two offline matching benchmarks. Cervone, Galavotti and LiCalzi (2009, equations 1–2 and accompanying text) distinguish Zhan and Friedman's shift formulation, which floors the buyer bid at zero and leaves the seller's ask uncapped, from their own version which also caps the ask. Brinkman and Wellman (2017, section 3) display the shift rule as value minus or plus the distribution width times the shading parameter, with no truncation in those displayed equations, and describe a random ordering of limit orders. Our unit-width additive implementation uses raw quotes on both sides. Brinkman and Wellman also evaluate a richer dynamic financial-market game. Published efficiency levels and equilibrium parameters are specific to their model, strategy units and market sizes.

* [Zhan and Friedman, journal article](https://doi.org/10.1016/j.jedc.2006.10.004)
* [Brinkman and Wellman, working paper](https://strategicreasoning.org/wp-content/uploads/2017/05/shading-efficiency-limit-1.pdf)
* [Cervone, Galavotti and LiCalzi, working paper](https://www.unive.it/web/fileadmin/user_upload/dipartimenti/DMAN/pubblicazioni_scientifiche/working_papers/2009/2009wp187.pdf)
