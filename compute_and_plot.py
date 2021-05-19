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
from myutils import info, create_readme, xnet
from myutils.geo import get_shp_points
import myutils.plot
from matplotlib.collections import LineCollection
import subprocess
import pickle

#############################################################
def plot_graph(g, coords, accessib, shppath, plotpath):
    """Plot the grpah, with vertices colored by accessibility."""
    info(inspect.stack()[0][3] + '()')

    es = []
    for e in g.es:
        es.append([ [float(g.vs[e.source]['x']), float(g.vs[e.source]['y'])],
                [float(g.vs[e.target]['x']), float(g.vs[e.target]['y'])], ])

    fig, ax = plt.subplots(figsize=(9, 9))
    sc = ax.scatter(coords[:, 0], coords[:, 1], c=accessib[0].values,
            cmap='plasma', linewidths=0, alpha=.6, s=2, zorder=10)
    segs = LineCollection(es, colors='gray', linewidths=.1, alpha=.5)
    ax.add_collection(segs)
    cb = fig.colorbar(sc, shrink=.75)
    cb.outline.set_visible(False)
    if shppath: # Plot border
        mapx, mapy = get_shp_points(shppath)
        ax.plot(mapx, mapy, c='dimgray')

    ax.axis('off')
    plt.tight_layout()
    plt.savefig(plotpath)

#############################################################
def plot_graph_quantiles(g, coords, accessib, shppath, plotpath):
    """Plot the grpah, with vertices colored by accessibility."""
    info(inspect.stack()[0][3] + '()')

    es = []
    for e in g.es:
        es.append([ [float(g.vs[e.source]['x']), float(g.vs[e.source]['y'])],
                [float(g.vs[e.target]['x']), float(g.vs[e.target]['y'])], ])

    # colours = myutils.plot.palettes['saturated']
    colours = ['blue',
               'green',
               'red']
    fig, ax = plt.subplots(figsize=(9, 9))
    quantiles = np.quantile(accessib[0], [0.00, .333, .667, 1.00])

    for i, a in enumerate(quantiles[:-1]):
        b = quantiles[i+1]
        inds = np.where( (accessib[0] >= a) & (accessib[0] < b))
        ax.scatter(coords[:, 0][inds], coords[:, 1][inds],
                   c=colours[i], linewidths=0, alpha=.6, s=2, zorder=10,
                   label='{}-quantile'.format(i+1))

    segs = LineCollection(es, colors='gray', linewidths=.1, alpha=.5)
    # ax.add_collection(segs)
    plt.legend(markerscale=3)
    if shppath: # Plot border
        mapx, mapy = get_shp_points(shppath)
        ax.plot(mapx, mapy, c='dimgray')

    ax.axis('off')
    plt.tight_layout()
    plt.savefig(plotpath)
##########################################################
def call_accessib_binary(g, randomwalk, level, xnetpath, outpath, njobs):
    """Call binary to calculate accessibility"""
    info(inspect.stack()[0][3] + '()')
    dynamics = '-r' if randomwalk else ''
    xnet.igraph2xnet(g, xnetpath)
    info('Graph in xnet format available in {}'.format(xnetpath))
    cmd = 'Build_Linux/CVAccessibility {} -j {} -l "{}" "{}" "{}"'.  \
        format(dynamics, njobs, level, xnetpath, outpath)
    info('{}'.format(cmd))
    stream = subprocess.Popen(cmd, shell=True)
    stream.wait()

##########################################################
def main():
    info(inspect.stack()[0][3] + '()')
    t0 = time.time()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--graphml', required=True, help='Graph in graphml format')
    parser.add_argument('--randomwalk', action='store_true',
            help='Computation based on random walk dynamics (*not* self-avoiding)')
    parser.add_argument('--level', required=True, type=int, help='Number of steps')
    parser.add_argument('--undirected', action='store_true', help='Remove direction')
    parser.add_argument('--shp', help='Border shapefile (optional)')
    parser.add_argument('--njobs', default=1, help='Maximum number of jobs')
    parser.add_argument('--outdir', default='/tmp/out/', help='Output directory')
    args = parser.parse_args()

    os.makedirs(args.outdir, exist_ok=True)
    readmepath = create_readme(sys.argv, args.outdir)
    suff = os.path.splitext(os.path.basename(args.graphml))[0]
    graphpkl = pjoin(args.outdir, 'graph.pkl')

    g = igraph.Graph.Read(args.graphml)
    g.simplify()

    if args.undirected: g.to_undirected()

    info('Graph is directed: {}'.format(g.is_directed()))
    info('nvertices:{}'.format(g.vcount()))
    info('nedges: {}'.format(g.ecount()))

    if ('x' in g.vertex_attributes()) and ('y' in g.vertex_attributes()):
        xx = np.array(g.vs['x']).astype(float)
        yy = np.array(g.vs['y']).astype(float)
        coords = np.concatenate((xx, yy)).reshape(len(xx), 2, order='F')
    else:
        coords = np.array(g.layout('fr'))

    accessibpath = pjoin(args.outdir, '{}_{}_acc{:02d}.txt'. \
            format(suff, 'directed' if g.is_directed() else 'undirected',
                args.level))

    if not os.path.exists(accessibpath):
        xnetpath = pjoin(args.outdir, suff + '.xnet')
        call_accessib_binary(g, args.randomwalk, args.level, xnetpath,
                             accessibpath, args.njobs)
    else:
        info('Loading pre-computed accessibility:{}'.format(accessibpath))

    accessib = pd.read_csv(accessibpath, header=None)
    plotpath  = accessibpath.replace('.txt', '.pdf')
    plot_graph(g, coords, accessib, args.shp, plotpath)
    plot_graph_quantiles(g, coords, accessib, args.shp,
                         plotpath.replace('.pdf', '_quant.pdf'))

    info('Elapsed time:{}'.format(time.time()-t0))

##########################################################
if __name__ == "__main__":
    main()
