#!/usr/bin/env python3
"""Plot accessibility of a spatial map"""

import argparse
import time
import os
from os.path import join as pjoin
import inspect

import sys
import numpy as np
from itertools import product
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib; matplotlib.use('Agg')
from datetime import datetime
import igraph
from myutils import info, create_readme
from matplotlib.collections import LineCollection

##########################################################
def main():
    info(inspect.stack()[0][3] + '()')
    t0 = time.time()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--graphml', required=True, help='Graph in graphml format')
    parser.add_argument('--accessib', required=True, help='Accessibility (txt)')
    parser.add_argument('--outdir', default='/tmp/out/', help='Output directory')
    args = parser.parse_args()

    if not os.path.isdir(args.outdir): os.mkdir(args.outdir)
    readmepath = create_readme(sys.argv, args.outdir)
    g = igraph.Graph.Read(args.graphml)
    info('Graph is directed: {}'.format(g.is_directed()))
    info('Graph is simple(): {}'.format(g.is_directed()))
    info('nvertices:{}'.format(g.vcount()))
    info('nedges: {}'.format(g.ecount()))

    if ('x' in g.vertex_attributes()) and ('y' in g.vertex_attributes()):
        coords = np.zeros((g.vcount(), 2))
        for i in range(g.vcount()):
            coords[i, :] = np.array([float(g.vs['x'][i]), float(g.vs['y'][i])])
    else:
        coords = np.array(g.layout('fr'))

    accessib = pd.read_csv(args.accessib, header=None)
    plot_graph(g, coords, accessib, args.outdir)

    info('Elapsed time:{}'.format(time.time()-t0))

##########################################################
def plot_graph(g, coords, accessib, outdir):
    """Plot the graph, per se"""
    info(inspect.stack()[0][3] + '()')

    es = []
    for e in g.es:
        es.append([ [float(g.vs[e.source]['x']), float(g.vs[e.source]['y'])],
                [float(g.vs[e.target]['x']), float(g.vs[e.target]['y'])], ])

    fig, ax = plt.subplots(figsize=(20, 20))
    sc = ax.scatter(coords[:, 0], coords[:, 1], c=accessib[0].values,
            cmap='plasma', linewidths=0, alpha=.5)
    segs = LineCollection(es, colors='k', linewidths=.2, alpha=.5)
    ax.add_collection(segs)
    plt.colorbar(sc)
    plt.savefig(pjoin(outdir, 'accessib.pdf'))

##########################################################
if __name__ == "__main__":
    main()
