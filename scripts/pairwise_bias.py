# Perform tests of pairwise random numbers as presented in Appendix A
# WARNING: This script can take a while to run

import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from pandas.util import hash_pandas_object
import hashlib
import sciris as sc
import os
import scipy.stats as sps

import matplotlib
matplotlib.rcParams['pdf.fonttype'] = 42

from starsim.utils import combine_rands

import warnings
warnings.filterwarnings("ignore", "overflow encountered in scalar subtract")
warnings.filterwarnings("ignore", "overflow encountered in scalar multiply")

np.random.seed(0) # Shouldn't matter, but for reproducibility
 
n = 4 #6 # Number of nodes, 4 or 6

reps = [100_000, 2_000_000][1]
edge_prob = 0.5 # Edge probability

figdir = os.path.join(os.getcwd(), 'figs', f'ERCorr_n{n}_reps{reps}')
sc.path(figdir).mkdir(parents=True, exist_ok=True)


def hash(df):
    return hashlib.sha256(hash_pandas_object(df, index=True).values).hexdigest()[:6]


def random():
    n1, n2 = np.triu_indices(n=n, k=1)
    r = np.random.rand(len(n1))
    edge = r < edge_prob
    return n1[edge], n2[edge]


def modulo():
    r1 = np.random.rand(n)
    r2 = np.random.rand(n)

    n1, n2 = np.triu_indices(n=n, k=1)
    r = np.mod(r1[n1] + r2[n2], 1)
    edge = r < edge_prob
    return n1[edge], n2[edge]


def middle_sq():
    r1 = np.random.randint(low=0, high=np.iinfo(np.uint64).max, dtype=np.uint64, size=n)
    r2 = np.random.randint(low=0, high=np.iinfo(np.uint64).max, dtype=np.uint64, size=n)

    n1, n2 = np.triu_indices(n=n, k=1)

    a = r1[n1]
    b = r2[n2]
    x = a * b
    y = x.copy()
    z = y + b

    # Round 1
    x = x*x + y
    x = np.bitwise_or(np.right_shift(x, 32), np.left_shift(x, 32))

    # Round 2
    x = x*x + z
    x = np.bitwise_or(np.right_shift(x, 32), np.left_shift(x, 32))

    # Round 3
    x = x*x + y
    x = np.bitwise_or(np.right_shift(x, 32), np.left_shift(x, 32))

    # Round 4
    x = x*x + z
    t = x.copy()
    x = np.bitwise_or(np.right_shift(x, 32), np.left_shift(x, 32))
    
    # Round 5 and xor
    x = np.right_shift(x*x + y, 32)
    r = t ** x

    edge = r < edge_prob

    return n1[edge], n2[edge]


g = np.random.PCG64DXSM()
def xor():
    r1 = g.random_raw(n)
    r2 = g.random_raw(n)

    n1, n2 = np.triu_indices(n=n, k=1)
    r = combine_rands(r1[n1], r2[n2])
    edge = r < edge_prob
    return n1[edge], n2[edge]


def make_graph(trans_fn):
    # Align transmissions from tx_in if provided
    els = {}
    counts = {}
 
    T = sc.tic()
    for _ in np.arange(reps):
        p1, p2 = trans_fn()
        df = pd.DataFrame({'p1':p1, 'p2':p2}).sort_values(['p1', 'p2']).reset_index(drop=True)
        
        h = hash(df)

        if h not in els:
            els[h] = df

        counts[h] = counts.get(h, 0) + 1
    dt = sc.toc(T, doprint=False, output=True)

    df = pd.DataFrame(counts.values(), index=pd.Index(counts.keys(), name='Graph Hash'), columns=['Counts'])
    return els, df, dt


if __name__ == '__main__':

    # Do transmissions via each method in parallel
    results = sc.parallelize(make_graph, iterkwargs=[
        {'trans_fn':random},
        {'trans_fn':modulo},
        {'trans_fn':middle_sq},
        {'trans_fn':xor}
        ], kwargs=None, die=True, serial=False)
    tx, cnt, times = zip(*results)

    df = pd.concat(cnt, axis=1) \
        .fillna(0) \
        .astype(int)
    df.columns = [
        'True Random',
        'Modulo',
        'Middle Square',
        'XOR'
    ]

    # Manipulate results
    df.reset_index(inplace=True)
    df.to_csv( os.path.join(figdir, 'results.csv') )

    dfm = df.melt(id_vars='Graph Hash', var_name='Method', value_name='Count')

    chisq = []
    f_exp = df['True Random']
    for method in df.columns[2:]:
        f_obs = df[method]
        T = df[['True Random', method]]
        chisq.append((method, sps.chi2_contingency(T).pvalue)) # Chi-square test of independence of variables in a contingency table.
    x2df = pd.DataFrame(chisq, columns=['Method', 'P-Value']).set_index('Method')
    x2df.to_csv( os.path.join(figdir, 'chisq.csv') )

    # Plot
    fig, ax = plt.subplots(figsize=(8,5))
    g = sns.barplot(data=dfm, x='Graph Hash', y='Count', hue='Method', ax=ax)
    plt.xticks(rotation=90)
    g.figure.tight_layout()
    g.figure.savefig(os.path.join(figdir, 'graph_hist.pdf'), bbox_inches='tight', transparent=True)
    plt.close(g.figure)

    txc = tx[0].copy()
    for i in range(1, len(tx)):
        txc.update(tx[i])
    for h, v in txc.items():
        print(f'\nUnique graph #{h}')
        print(v)

    print(times)
