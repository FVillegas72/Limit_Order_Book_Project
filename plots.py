"""Regenerate all figures and derived tables directly from the experimental CSVs."""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import PercentFormatter
import numpy as np
import pandas as pd

from experiments import BALANCED, RATIOS, SELLERS, TARGET_ALPHA

COLORS = ['#11676C', '#9E4D21', '#57458C', '#326BA2']
TARGETS = {.5:(.808,.948,.950,.983), 1.:(.723,.963,.964,.988), 2.:(.809,.964,.964,.990)}


def read(out, name):
    return pd.read_csv(out/(name+'.csv'))


def targets_and_symmetry(out):
    peaks = read(out,'selected_shading')
    scaling = read(out,'scaling')
    comparisons = []
    for rho,(truth,shaded,r40,r320) in TARGETS.items():
        p = peaks[(peaks.sellers==40) & (peaks.rho==rho)].iloc[0]
        vals = [('truth_eta',40,0,truth,p.truth_eta,p.truth_eta_se),
                ('selected_eta',40,p.tau,shaded,p.eta,p.eta_se)]
        tau = TARGET_ALPHA[rho]/50
        for m,old in [(40,r40),(320,r320)]:
            k = scaling[(scaling.sellers==m)&(scaling.rho==rho)&(scaling.tau==tau)].iloc[0]
            vals.append(('fixed_R',m,tau,old,k.R,k.R_se))
        for metric,m,t,old,new,se in vals:
            comparisons.append(dict(metric=metric,sellers=m,rho=rho,tau=t,prior=old,
                                    estimate=new,se=se,difference=new-old))
    pd.DataFrame(comparisons).to_csv(out/'prior_comparison.csv',index=False,float_format='%.12g')
    swapped = []
    for m in SELLERS[:-1]:
        a = scaling[(scaling.sellers==m)&(scaling.rho==2)].set_index('tau')
        b = scaling[(scaling.sellers==2*m)&(scaling.rho==.5)].set_index('tau')
        for t in a.index:
            diff = a.loc[t,'R']-b.loc[t,'R']
            se = np.hypot(a.loc[t,'R_se'],b.loc[t,'R_se'])
            swapped.append(dict(buyers=2*m,sellers=m,reflected_buyers=m,reflected_sellers=2*m,
                                tau=t,R=a.loc[t,'R'],reflected_R=b.loc[t,'R'],
                                difference=diff,difference_se=se))
    pd.DataFrame(swapped).to_csv(out/'reflected_sizes.csv',index=False,float_format='%.12g')


def axes_pair():
    fig, axes = plt.subplots(1,2,figsize=(8.2,3.15),layout='constrained')
    for ax in axes:
        ax.spines[['right','top']].set_visible(False)
        ax.grid(axis='y',color='#dce4e2',linewidth=.7)
        ax.set_axisbelow(True)
        ax.tick_params(length=3)
    return fig,axes


def save(fig, out, name):
    dest = out/'figures'
    dest.mkdir(exist_ok=True)
    for ext in ['png','pdf']:
        metadata = {'CreationDate': None, 'ModDate': None} if ext == 'pdf' else None
        fig.savefig(dest/f'{name}.{ext}',dpi=230,facecolor='white',metadata=metadata)
    plt.close(fig)


def curve(ax, g, label, color):
    ax.plot(g.alpha,g.eta,color=color,label=label,linewidth=1.8)
    ax.fill_between(g.alpha,g.eta-1.96*g.eta_se,g.eta+1.96*g.eta_se,
                    alpha=.14,color=color,lw=0)
    peak = g.loc[g.cda.idxmax()]
    ax.scatter(peak.alpha,peak.eta,s=23,color=color,edgecolors='white',linewidths=.6,zorder=4)


def format_shading(ax):
    ax.set_xlabel('Common per-side shading, α')
    ax.set_xlim(-.003,.253)
    ax.yaxis.set_major_formatter(PercentFormatter(1,decimals=0))
    ax.legend(loc='lower center',ncol=2,handlelength=1.4,frameon=False,columnspacing=1.1)


def render(out):
    plt.rcParams.update({'font.size':9,'axes.titlesize':11,'axes.titleweight':'bold',
                         'axes.titlelocation':'left','text.color':'#183236',
                         'axes.labelcolor':'#183236','pdf.fonttype':42})
    grid, scale = read(out,'shading_grid'),read(out,'scaling')
    fig,axes = axes_pair()
    for ax,sizes in zip(axes,[BALANCED[:4],BALANCED[4:]]):
        for i,n in enumerate(sizes):
            curve(ax,grid[(grid.buyers==n)&(grid.sellers==n)],f'n = {n}',COLORS[i])
        ax.set_title(f'{sizes[0]} to {sizes[-1]} traders per side')
        format_shading(ax)
        ax.set_ylim(.50,1.015)
    axes[0].set_ylabel('Welfare efficiency, η')
    save(fig,out,'balanced_welfare')
    fig,axes = axes_pair()
    for ax,m in zip(axes,[40,320]):
        for i,rho in enumerate(RATIOS):
            curve(ax,grid[(grid.rho==rho)&(grid.sellers==m)],f'ρ = {rho:g}',COLORS[i])
        ax.set_title(f'{m} sellers')
        format_shading(ax)
        ax.set_ylim(.62,1.012)
    axes[0].set_ylabel('Welfare efficiency, η')
    save(fig,out,'imbalance')
    fig,axes = axes_pair()
    g = grid[(grid.buyers==40)&(grid.sellers==40)]
    ax,vol = axes
    for field,label,c in [('greedy_share','Greedy loss',COLORS[0]),
                          ('excluded_share','Excluded loss',COLORS[1])]:
        ax.plot(g.alpha,g[field],color=c,linewidth=2,label=label)
    ax.plot(g.alpha,1-g.eta,color=COLORS[2],ls='--',label='Total loss')
    ax.set_ylabel('Share of expected unrestricted welfare')
    ax.yaxis.set_major_formatter(PercentFormatter(1,decimals=0))
    ax.legend(frameon=False)
    vol.plot(g.alpha,g.trades,color=COLORS[0],linewidth=2)
    vol.axhline(20,color='#777777',linestyle=':',label='Expected efficient count')
    vol.set_ylabel('Mean completed trades')
    vol.legend(frameon=False)
    for ax,title in zip(axes,['Welfare lost at each stage','Executed volume']):
        ax.set_title(title)
        ax.set_xlabel('Common per-side shading, α')
    save(fig,out,'losses_and_volume')
    fig,axes = axes_pair()
    for ax,truthful in zip(axes,[True,False]):
        for i,rho in enumerate(RATIOS):
            tau = 0 if truthful else TARGET_ALPHA[rho]/50
            g = scale[(scale.rho==rho)&(scale.tau==tau)].sort_values('sellers')
            label = f'ρ = {rho:g}' if truthful else f'ρ = {rho:g}, τ = {tau:.2f}'
            ax.errorbar(g.sellers,g.R,yerr=1.96*g.R_se,marker='o',ms=4,capsize=2,
                        lw=1.7,color=COLORS[i],label=label)
        ax.set_xscale('log',base=2)
        ax.set_xticks(SELLERS,labels=[str(n) for n in SELLERS])
        ax.set_xlabel('Sellers, m')
        ax.yaxis.set_major_formatter(PercentFormatter(1,decimals=0))
        ax.set_title('Truthful orders' if truthful else 'Fixed positive shading')
        ax.legend(frameon=False,fontsize=8,loc='best')
    axes[0].set_ylabel('Matching efficiency, R')
    axes[0].set_ylim(.665,.84)
    axes[1].set_ylim(.91,1.003)
    save(fig,out,'scaling')
    targets_and_symmetry(out)
