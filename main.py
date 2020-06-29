#!/usr/bin/env python3
"""Accessibility from a map"""

import argparse
import logging
import time
from os.path import join as pjoin
from logging import debug, info
import igraph
import xnet
import subprocess
import shlex
import numpy as np
import os

##########################################################
def main():
    t0 = time.time()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--graphml', required=True, help='graphml')
    parser.add_argument('--level', default=5, help='Acessibility param')
    parser.add_argument('--outdir', default='/tmp/out/', help='outdir')
    args = parser.parse_args()
    
    if not os.path.isdir(args.outdir): os.mkdir(args.outdir)
    
    logging.basicConfig(format='[%(asctime)s] %(message)s',
    datefmt='%Y%m%d %H:%M', level=logging.INFO)

    xnetgraphpath = os.path.join(args.outdir, 'out.xnet')
    accessibilitypath = os.path.join(args.outdir, 'accessibility.txt')

    info('Loading graph...')
    g = igraph.Graph.Read(args.graphml)

    for attr in ['ref', 'highway', 'osmid', 'id']:
        del(g.vs[attr])
    for attr in g.es.attributes():
        del(g.es[attr])

    if not os.path.exists(accessibilitypath):
        info('Converting to xnet...')
        xnet.igraph2xnet(g, xnetgraphpath)

        cmd = 'Build_Linux/CVAccessibility -l {} {} {}'.\
            format(args.level, xnetgraphpath, accessibilitypath)

        info('Running {}'.format(cmd))
        proc = subprocess.Popen(shlex.split(cmd), stdout=subprocess.PIPE)
        out, err = proc.communicate()
        # acc = out.decode('utf-8').strip().split('\n')
        # acc = np.array([float(a) for a in acc])
        if err: info('err:{}'.format(err.decode('utf-8')))

    with open(accessibilitypath) as fh:
        aux = fh.read().strip().split('\n')
        acc = np.array([float(a) for a in aux])

    g.simplify()
    g.to_undirected()

    visual = dict(
        bbox = (1200, 1200),
        vertex_size = 1.5,
        vertex_shape = 'circle',
        vertex_frame_width = 0,
        edge_arrow_width=.5,
        edge_arrow_size=.5
    )

    info('accessibility {} ({})'.format(np.mean(acc), np.std(acc)))
    # g.vs['accessibility'] = acc
    # plotalpha = 0.8
    plotalpha = 1
    mincolour = 0.3
    acc1 = (acc / np.max(acc)) *  (1 - mincolour)
    colours = [ [mincolour, mincolour, mincolour + c, plotalpha] for c in acc1 ]
    coords = [(float(x), -float(y)) for x, y in zip(g.vs['x'], g.vs['y'])]

    visual['vertex_size'] = 0.0
    visual['edge_width'] = 1
    igraph.plot(g, os.path.join(args.outdir, 'skel.pdf'),
            layout=coords, **visual)

    visual['vertex_size'] = 2.0
    visual['edge_width'] = 0
    igraph.plot(g, os.path.join(args.outdir, 'acc_all.pdf'),
            layout=coords, vertex_color=colours, **visual)

    ###########################################################
    # generate plots for diff levels
    for thresh in [0.35, 0.5, 0.75]:
        acc1 = np.ones(len(acc))
        quantile = thresh * np.max(acc)
        info('accessibility quantile: {:.2f} ({}%)'.format(quantile,
                int(thresh*100)))
        inds = np.where(acc > quantile)
        acc1[inds] = 0

        colours = [ [c, c, c, plotalpha] for c in acc1 ]
        visual['vertex_size'] = 2.0
        visual['edge_width'] = 0
        gpath = os.path.join(args.outdir, 'acc_thresh_{}.pdf'.format(thresh))
        igraph.plot(g, gpath, layout=coords, vertex_color=colours, **visual)
    
###########################################################
if __name__ == "__main__":
    main()

