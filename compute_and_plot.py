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

    fig, ax = plt.subplots(figsize=(7, 7))
    sc = ax.scatter(coords[:, 0], coords[:, 1], c=accessib[0].values,
            cmap='plasma', linewidths=0, alpha=.6, s=3, zorder=10)
    segs = LineCollection(es, colors='gray', linewidths=.1, alpha=.5)
    # ax.add_collection(segs)
    cb = fig.colorbar(sc, shrink=.75)
    cb.outline.set_visible(False)
    if shppath: # Plot border
        mapx, mapy = get_shp_points(shppath)
        ax.plot(mapx, mapy, c='dimgray')

    ax.axis('off')
    plt.tight_layout()
    plt.savefig(plotpath)

##########################################################
def call_accessib_binary(g, level, xnetpath, outpath):
    """Call binary to calculate accessibility"""
    info(inspect.stack()[0][3] + '()')
    xnet.igraph2xnet(g, xnetpath)
    info('Graph in xnet format available in {}'.format(xnetpath))
    cmd = 'Build_Linux/CVAccessibility -l "{}" "{}" "{}"'.format(level,
            xnetpath, outpath)
    info('{}'.format(cmd))
    stream = subprocess.Popen(cmd, shell=True)
    stream.wait()
    
##########################################################
def main():
    info(inspect.stack()[0][3] + '()')
    t0 = time.time()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--graphml', required=True, help='Graph in graphml format')
    parser.add_argument('--level', required=True, type=int, help='Number of steps')
    parser.add_argument('--undirected', action='store_true', help='Remove direction')
    parser.add_argument('--shp', help='Border shapefile (optional)')
    parser.add_argument('--outdir', default='/tmp/out/', help='Output directory')
    args = parser.parse_args()

    if not os.path.isdir(args.outdir): os.mkdir(args.outdir)
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
        call_accessib_binary(g, args.level, xnetpath, accessibpath)

    accessib = pd.read_csv(accessibpath, header=None)
    plotpath  = accessibpath.replace('.txt', '.png')
    plot_graph(g, coords, accessib, args.shp, plotpath)

    info('Elapsed time:{}'.format(time.time()-t0))

##########################################################
if __name__ == "__main__":
    main()
